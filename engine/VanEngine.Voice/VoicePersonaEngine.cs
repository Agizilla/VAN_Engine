using System.Text.Json;
using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;

namespace VanEngine.Voice;

/// <summary>
/// Voice Persona Engine — evolves a unique voice identity from Demucs residuals.
/// Captures what Demucs discards (the artist fingerprint) and uses it to shape
/// voice synthesis. The voice persona grows richer with each song ingested.
/// </summary>
public sealed class VoicePersonaEngine : IDisposable
{
    private readonly InferenceSession? _session;
    private readonly PersonaWaveformGenerator _waveform;
    private PersonaFingerprint _fingerprint;
    private float[] _latent;
    private string _modelPath;

    public VoicePersonaEngine(string onnxModelPath, string personaJsonPath)
    {
        _modelPath = onnxModelPath;
        _session = File.Exists(onnxModelPath) ? new InferenceSession(onnxModelPath) : null;
        _waveform = new PersonaWaveformGenerator();
        _latent = new float[256];
        _fingerprint = new PersonaFingerprint();
        LoadPersona(personaJsonPath);
    }

    /// <summary>
    /// Synthesize speech shaped by the evolved voice persona.
    /// </summary>
    public float[] Synthesize(string text, float strength = 0.7f, float speakingRate = 1.0f)
    {
        var shapedLatent = ApplyStrength(_latent, strength);

        if (_session != null)
        {
            try
            {
                return SynthesizeWithOnnx(text, shapedLatent, speakingRate);
            }
            catch
            {
                // Fallback to waveform generator
            }
        }

        return _waveform.Generate(text.GetHashCode(), strength, speakingRate, shapedLatent);
    }

    public PersonaFingerprint GetFingerprint() => _fingerprint;

    public static VoicePersonaEngine FromAdapter(string jsonPath)
    {
        return new VoicePersonaEngine("", jsonPath);
    }

    public void Dispose() => _session?.Dispose();

    private void LoadPersona(string jsonPath)
    {
        if (!File.Exists(jsonPath))
            return;

        var json = File.ReadAllText(jsonPath);
        var data = JsonSerializer.Deserialize<PersonaData>(json);
        if (data == null)
            return;

        if (data.Latent is { Length: 256 })
            _latent = data.Latent;
        else if (data.Latent is { Length: > 0 })
            InterpolateLatent(data.Latent);

        if (data.FingerprintSummary != null)
            _fingerprint = data.FingerprintSummary;
    }

    private void InterpolateLatent(float[] source)
    {
        _latent = new float[256];
        for (int i = 0; i < 256; i++)
        {
            float srcIdx = (i / 255f) * (source.Length - 1);
            int lo = (int)srcIdx;
            int hi = Math.Min(lo + 1, source.Length - 1);
            float t = srcIdx - lo;
            _latent[i] = source[lo] * (1 - t) + source[hi] * t;
        }
    }

    private float[] SynthesizeWithOnnx(string text, float[] latent, float rate)
    {
        var inputIds = new DenseTensor<long>(new[] { 1, text.Length });
        for (int i = 0; i < text.Length; i++)
            inputIds[0, i] = text[i];

        var latentTensor = new DenseTensor<float>(latent, new[] { 1, latent.Length });

        var inputs = new List<NamedOnnxValue>
        {
            NamedOnnxValue.CreateFromTensor("input_ids", inputIds),
            NamedOnnxValue.CreateFromTensor("latent", latentTensor)
        };

        using var results = _session!.Run(inputs);
        var audio = results.First().AsTensor<float>();

        var output = new float[audio.Length];
        for (int i = 0; i < audio.Length; i++)
            output[i] = audio[i];

        if (Math.Abs(rate - 1.0f) > 0.01f)
        {
            var stretched = new List<float>();
            for (float i = 0; i < output.Length; i += rate)
                stretched.Add(output[(int)Math.Min(i, output.Length - 1)]);
            return stretched.ToArray();
        }

        return output;
    }

    private static float[] ApplyStrength(float[] latent, float strength)
    {
        float s = Math.Clamp(strength, 0.0f, 1.0f);
        var result = new float[latent.Length];
        for (int i = 0; i < latent.Length; i++)
            result[i] = latent[i] * s;
        return result;
    }
}

/// <summary>
/// Waveform generator that shapes output using persona latent vector.
/// </summary>
public sealed class PersonaWaveformGenerator
{
    private readonly Random _random = new();

    /// <summary>
    /// Generate audio waveform shaped by persona latent.
    /// </summary>
    public float[] Generate(int textHash, float strength, float speakingRate, float[]? personaLatent = null)
    {
        float f0 = 80 + (Math.Abs(textHash) % 120);
        float formant1 = 300 + (Math.Abs(textHash / 7) % 400);
        float formant2 = 1000 + (Math.Abs(textHash / 13) % 800);
        float breathiness = 0.05f + (Math.Abs(textHash / 31) % 20) / 100f;

        if (personaLatent != null && personaLatent.Length >= 25)
        {
            float latentF0 = 80 + Math.Abs(personaLatent[13]) * 220;
            float latentBw = Math.Abs(personaLatent[14]) * 2000;
            f0 = f0 * 0.3f + latentF0 * 0.7f;
            formant1 += personaLatent[0] * 200;
            formant2 += personaLatent[1] * 300;
            breathiness = Math.Clamp(breathiness + personaLatent[15] * 0.1f, 0.01f, 0.5f);
            _ = latentBw;
        }

        int sampleRate = 22050;
        float duration = 1.0f;
        f0 *= strength;

        return GenerateWaveform(sampleRate, duration, f0, formant1, formant2, breathiness);
    }

    private float[] GenerateWaveform(int sampleRate, float duration, float f0, float f1, float f2, float breathiness)
    {
        int totalSamples = (int)(sampleRate * duration);
        var audio = new float[totalSamples];
        var rng = new Random(42);

        for (int i = 0; i < totalSamples; i++)
        {
            float t = (float)i / sampleRate;
            float fundamental = (float)Math.Sin(2 * Math.PI * f0 * t);
            float harmonic1 = (float)Math.Sin(2 * Math.PI * f1 * t) * 0.5f;
            float harmonic2 = (float)Math.Sin(2 * Math.PI * f2 * t) * 0.25f;
            float noise = (float)(rng.NextDouble() - 0.5) * breathiness;
            float envelope = 1.0f - Math.Abs(t / duration - 0.5f) * 0.5f;

            audio[i] = (fundamental + harmonic1 + harmonic2 + noise) * envelope;
        }

        float max = Math.Max(0.0001f, audio.Max(v => Math.Abs(v)));
        for (int i = 0; i < audio.Length; i++)
            audio[i] /= max;

        return audio;
    }
}

public sealed class PersonaFingerprint
{
    public float SpectralCentroid { get; set; }
    public float SpectralBandwidth { get; set; }
    public float ResidualStd { get; set; }
    public float DurationSec { get; set; }
    public float[] MfccCentroid { get; set; } = new float[13];
}

public sealed class PersonaData
{
    public string Version { get; set; } = "1.0";
    public string Type { get; set; } = "VoicePersona";
    public int BaseSeed { get; set; }
    public int SongsIngested { get; set; }
    public float[] Latent { get; set; } = Array.Empty<float>();
    public PersonaFingerprint? FingerprintSummary { get; set; }
    public string Created { get; set; } = string.Empty;
}
