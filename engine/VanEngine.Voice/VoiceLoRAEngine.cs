using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;

namespace VanEngine.Voice;

/// <summary>
/// Voice LoRA Engine — Zero-training voice synthesis.
/// Plugs into VAN Engine architecture via Voice-Synthesis carrier.
/// </summary>
public sealed class VoiceLoRAEngine : IDisposable
{
    private readonly InferenceSession _session;
    private readonly VoiceLoRA _lora;
    private readonly WaveformGenerator _waveform;

    public VoiceLoRAEngine(string onnxModelPath, int voiceSeed = 0)
    {
        _session = new InferenceSession(onnxModelPath);
        _lora = new VoiceLoRA(voiceSeed);
        _waveform = new WaveformGenerator();
    }

    /// <summary>
    /// Synthesize speech with unique voice from text.
    /// </summary>
    public float[] Synthesize(string text, float strength = 0.7f, float speakingRate = 1.0f)
    {
        var tokens = Tokenize(text);
        var inputTensor = new DenseTensor<long>(tokens, new[] { 1, tokens.Length });

        var inputs = new List<NamedOnnxValue>
        {
            NamedOnnxValue.CreateFromTensor("input_ids", inputTensor)
        };

        using var results = _session.Run(inputs);
        var spectrogram = results.First().AsTensor<float>();

        var voiced = _lora.ApplyToSpectrogram(spectrogram, strength);
        return _waveform.Generate(voiced, speakingRate);
    }

    /// <summary>
    /// Load voice adapter from JSON (saved by Python test harness).
    /// </summary>
    public static VoiceLoRAEngine FromAdapter(string onnxModelPath, string adapterJsonPath)
    {
        var json = File.ReadAllText(adapterJsonPath);
        var adapter = JsonSerializer.Deserialize<VoiceAdapterData>(json);
        return new VoiceLoRAEngine(onnxModelPath, adapter?.Seed ?? 0);
    }

    public VoiceFingerprint GetFingerprint() => _lora.GetFingerprint();

    public int Seed => _lora.Seed;

    private static long[] Tokenize(string text)
    {
        return Encoding.UTF8.GetBytes(text).Select(b => (long)b).ToArray();
    }

    public void Dispose()
    {
        _session?.Dispose();
    }
}

/// <summary>
/// Voice LoRA — Structured entropy injection from mathematical bounds.
/// Generates unique voice characteristics from a seed (no training data).
/// </summary>
public sealed class VoiceLoRA
{
    private readonly float[] _latent;
    private readonly Random _random;

    public int Seed { get; }

    public VoiceLoRA(int seed)
    {
        Seed = seed;
        _random = new Random(seed);
        _latent = GenerateLatent();
    }

    private float[] GenerateLatent()
    {
        var latent = new float[256];
        double f0 = 80 + _random.NextDouble() * 220;
        double formant1 = f0 * 3;
        double formant2 = f0 * 5;
        double formant3 = f0 * 7;
        double breathiness = _random.NextDouble();
        double vocalTract = 0.8 + _random.NextDouble() * 0.4;

        for (int i = 0; i < latent.Length; i++)
        {
            latent[i] = (float)(
                0.5 * Math.Sin(2 * Math.PI * f0 * i / latent.Length) +
                0.3 * Math.Sin(2 * Math.PI * formant1 * i / latent.Length) +
                0.15 * Math.Sin(2 * Math.PI * formant2 * i / latent.Length) +
                0.05 * Math.Sin(2 * Math.PI * formant3 * i / latent.Length)
            );
            latent[i] *= (float)vocalTract;
        }

        float max = Math.Max(0.0001f, latent.Max());
        for (int i = 0; i < latent.Length; i++)
            latent[i] /= max;

        return latent;
    }

    /// <summary>
    /// Apply voice characteristics to a spectrogram via soft-knee injection.
    /// </summary>
    public Tensor<float> ApplyToSpectrogram(Tensor<float> spectrogram, float strength)
    {
        var dims = spectrogram.Dimensions.ToArray();
        var result = new DenseTensor<float>(dims);
        var latentInterp = InterpolateLatent(dims[2]);

        for (int t = 0; t < dims[2]; t++)
        {
            float influence = latentInterp[t];
            float ratio = (float)Math.Pow(Math.Abs(influence), 1.5);

            for (int f = 0; f < dims[1]; f++)
            {
                float original = spectrogram[0, f, t];
                float injected = influence * ratio * strength;
                result[0, f, t] = original * (1 - ratio * strength) + injected;
            }
        }

        return result;
    }

    private float[] InterpolateLatent(int targetLength)
    {
        var result = new float[targetLength];
        for (int i = 0; i < targetLength; i++)
        {
            float idx = (float)i / targetLength * _latent.Length;
            int i0 = (int)Math.Floor(idx);
            int i1 = Math.Min(i0 + 1, _latent.Length - 1);
            float frac = idx - i0;
            result[i] = _latent[i0] * (1 - frac) + _latent[i1] * frac;
        }
        return result;
    }

    public VoiceFingerprint GetFingerprint()
    {
        return new VoiceFingerprint
        {
            Hash = ComputeHash(),
            F0Estimate = EstimateF0(),
            Breathiness = EstimateBreathiness()
        };
    }

    private string ComputeHash()
    {
        var bytes = _latent.SelectMany(BitConverter.GetBytes).ToArray();
        var hash = SHA256.HashData(bytes);
        return Convert.ToHexString(hash)[..16];
    }

    private float EstimateF0() => 150f;

    private float EstimateBreathiness()
    {
        double std = Math.Sqrt(_latent.Select(x => x * x).Average());
        return Math.Min(1f, (float)std * 2f);
    }
}

/// <summary>
/// Simplified Griffin-Lim waveform generator for voice synthesis.
/// </summary>
public sealed class WaveformGenerator
{
    private readonly Random _random = new();

    public float[] Generate(Tensor<float> spectrogram, float speakingRate)
    {
        var dims = spectrogram.Dimensions;
        int frames = dims[2];
        int hopLength = 256;
        int totalSamples = frames * hopLength;
        var audio = new float[totalSamples];

        for (int t = 0; t < frames - 1; t++)
        {
            for (int f = 0; f < dims[1]; f++)
            {
                float magnitude = spectrogram[0, f, t];
                float phase = (float)(_random.NextDouble() * 2 * Math.PI);
                float sample = magnitude * (float)Math.Cos(phase);

                int idx = t * hopLength + f;
                if (idx < totalSamples)
                    audio[idx] += sample;
            }
        }

        float max = Math.Max(0.0001f, audio.Max(v => Math.Abs(v)));
        for (int i = 0; i < audio.Length; i++)
            audio[i] /= max;

        if (Math.Abs(speakingRate - 1.0f) > 0.01f)
        {
            var stretched = new List<float>();
            for (float i = 0; i < audio.Length; i += speakingRate)
                stretched.Add(audio[(int)Math.Min(i, audio.Length - 1)]);
            return stretched.ToArray();
        }

        return audio;
    }
}

public sealed class VoiceFingerprint
{
    public string Hash { get; set; } = string.Empty;
    public float F0Estimate { get; set; }
    public float Breathiness { get; set; }
}

public sealed class VoiceAdapterData
{
    public string Version { get; set; } = "1.0";
    public string Type { get; set; } = "VoiceLoRA";
    public int Seed { get; set; }
    public int LatentDim { get; set; } = 256;
    public float Strength { get; set; } = 0.7f;
    public float SpeakingRate { get; set; } = 1.0f;
    public Dictionary<string, object> Fingerprint { get; set; } = new();
    public string TextSample { get; set; } = string.Empty;
    public string Created { get; set; } = string.Empty;
}
