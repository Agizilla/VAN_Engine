using System.Buffers;
using System.Diagnostics;
using System.Text;
using VanEngine.Core.Governance;
using VanEngine.Voice;

namespace VanEngine.Core.VAN;

public sealed class VanEngine
{
    private const double Epsilon = 1e-9;
    private const double MaxQ = 0.9999;
    private const double MinQ = 0.001;
    private const int ParallelThreshold = 1000;

    private readonly Dictionary<string, Func<VanEnvelope, object>> _processors;
    private readonly VanSpectrogram _spectrogram;
    private readonly VanCompiler _compiler;
    private readonly Metrics _metrics;
    private readonly Dictionary<double, double[]> _ditherCache;
    private readonly FryasComplianceEngine _compliance;
    private readonly CitadelLaws _citadelLaws;
    private readonly UniversalLaw _universalLaw;
    private readonly MarketRegulator _market;
    private readonly ForestGuardian _forest;

    private static readonly ArrayPool<double> DoublePool = ArrayPool<double>.Shared;

    public VanEngine(IVanExecutor? externalExecutor = null)
    {
        _processors = new Dictionary<string, Func<VanEnvelope, object>>
        {
            ["LLM-Attention"] = ProcessLlmAttention,
            ["5D-Gcode"] = ProcessGCode,
            ["Pixel-Phase"] = ProcessPixelPhase,
            ["Steel-Resonance"] = ProcessSteelResonance,
            ["Voice-Synthesis"] = ProcessVoiceSynthesis,
            ["Voice-Persona"] = ProcessVoicePersona
        };
        _spectrogram = new VanSpectrogram();
        _compiler = new VanCompiler(_processors, externalExecutor);
        _metrics = new Metrics();
        _ditherCache = new Dictionary<double, double[]>();
        _compliance = new FryasComplianceEngine(FryasDirective.AllDirectives);
        _citadelLaws = new CitadelLaws();
        _universalLaw = new UniversalLaw();
        _market = new MarketRegulator();
        _forest = new ForestGuardian();
    }

    public Metrics Metrics => _metrics;
    public VanCompiler Compiler => _compiler;
    public FryasComplianceEngine Compliance => _compliance;
    public CitadelLaws CitadelLaws => _citadelLaws;
    public UniversalLaw UniversalLaw => _universalLaw;
    public MarketRegulator Market => _market;
    public ForestGuardian Forest => _forest;

    public void RegisterCarrier(string carrier, Func<VanEnvelope, object> processor)
    {
        _processors[carrier] = processor;
    }

    #region Core Soft-Knee Downward Expander

    public double[] SoftKneeDownwardExpander(
        double[] signal,
        double noiseFloor,
        double kneeSlope = 2.0,
        double[]? ditherProfile = null)
    {
        if (signal == null || signal.Length == 0)
            return Array.Empty<double>();

        var output = new double[signal.Length];
        SoftKneeDownwardExpander(
            signal.AsSpan(),
            noiseFloor,
            kneeSlope,
            ditherProfile ?? ReadOnlySpan<double>.Empty,
            output.AsSpan());
        return output;
    }

    public void SoftKneeDownwardExpander(
        ReadOnlySpan<double> signal,
        double noiseFloor,
        double kneeSlope,
        ReadOnlySpan<double> ditherProfile,
        Span<double> destination)
    {
        double safeNoiseFloor = Math.Max(noiseFloor, Epsilon);
        double safeKneeSlope = Math.Clamp(kneeSlope, 0.1, 10.0);

        var ditherSpan = ditherProfile.Length > 0
            ? ditherProfile
            : GetOrCreateDither(signal, safeNoiseFloor).AsSpan();

        for (int i = 0; i < signal.Length; i++)
        {
            double magnitude = Math.Abs(signal[i]);

            if (magnitude > safeNoiseFloor)
            {
                destination[i] = signal[i];
            }
            else
            {
                double normalized = Math.Clamp(magnitude / safeNoiseFloor, 0, 1);
                double ratio = Math.Pow(normalized, safeKneeSlope);
                double expanded = signal[i] * ratio;
                destination[i] = expanded + (ditherSpan[i] * (1 - ratio));
            }
        }
    }

    public double[,] SoftKneeDownwardExpander2D(
        double[,] signal,
        double noiseFloor,
        double kneeSlope = 2.0,
        double[,]? ditherProfile = null)
    {
        if (signal == null) return new double[0, 0];

        int rows = signal.GetLength(0);
        int cols = signal.GetLength(1);

        if (rows == 0 || cols == 0)
            return new double[0, 0];

        double safeNoiseFloor = Math.Max(noiseFloor, Epsilon);
        double safeKneeSlope = Math.Clamp(kneeSlope, 0.1, 10.0);

        var output = new double[rows, cols];
        var dither = ditherProfile ?? GenerateDitherFromSignal2D(signal);

        bool useParallel = rows * cols > ParallelThreshold;

        if (useParallel)
        {
            Parallel.For(0, rows, i =>
            {
                for (int j = 0; j < cols; j++)
                {
                    double magnitude = Math.Abs(signal[i, j]);

                    if (magnitude > safeNoiseFloor)
                    {
                        output[i, j] = signal[i, j];
                    }
                    else
                    {
                        double normalized = Math.Clamp(magnitude / safeNoiseFloor, 0, 1);
                        double ratio = Math.Pow(normalized, safeKneeSlope);
                        double expanded = signal[i, j] * ratio;
                        output[i, j] = expanded + (dither[i, j] * (1 - ratio));
                    }
                }
            });
        }
        else
        {
            for (int i = 0; i < rows; i++)
                for (int j = 0; j < cols; j++)
                {
                    double magnitude = Math.Abs(signal[i, j]);

                    if (magnitude > safeNoiseFloor)
                    {
                        output[i, j] = signal[i, j];
                    }
                    else
                    {
                        double normalized = Math.Clamp(magnitude / safeNoiseFloor, 0, 1);
                        double ratio = Math.Pow(normalized, safeKneeSlope);
                        double expanded = signal[i, j] * ratio;
                        output[i, j] = expanded + (dither[i, j] * (1 - ratio));
                    }
                }
        }

        return output;
    }

    public double QToKneeSlope(double qFactor)
    {
        double safeQ = Math.Clamp(qFactor, MinQ, MaxQ);
        return 1.0 / (1.0 - safeQ);
    }

    private double[] GetOrCreateDither(ReadOnlySpan<double> signal, double noiseFloor)
    {
        if (_ditherCache.TryGetValue(noiseFloor, out var cached))
            return cached;

        double[] dither = GenerateDitherFromSignal(signal);
        _ditherCache[noiseFloor] = dither;
        return dither;
    }

    private double[] GenerateDitherFromSignal(ReadOnlySpan<double> signal)
    {
        var random = new Random(42);
        double std = Math.Max(StandardDeviation(signal), Epsilon);
        double mean = 0;

        for (int i = 0; i < signal.Length; i++)
            mean += signal[i];
        mean /= signal.Length;

        var dither = new double[signal.Length];
        for (int i = 0; i < signal.Length; i++)
            dither[i] = mean + (random.NextDouble() - 0.5) * std * 0.1;

        return dither;
    }

    private double[,] GenerateDitherFromSignal2D(double[,] signal)
    {
        int rows = signal.GetLength(0);
        int cols = signal.GetLength(1);
        var random = new Random(42);

        double sum = 0;
        double sumSq = 0;
        int count = rows * cols;

        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
            {
                double val = signal[i, j];
                sum += val;
                sumSq += val * val;
            }

        double mean = sum / count;
        double variance = Math.Max(sumSq / count - mean * mean, Epsilon);
        double std = Math.Sqrt(variance);

        var output = new double[rows, cols];
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
                output[i, j] = mean + (random.NextDouble() - 0.5) * std * 0.1;

        return output;
    }

    private static double StandardDeviation(ReadOnlySpan<double> values)
    {
        if (values.Length == 0) return Epsilon;

        double mean = 0;
        for (int i = 0; i < values.Length; i++)
            mean += values[i];
        mean /= values.Length;

        double sumOfSquares = 0;
        for (int i = 0; i < values.Length; i++)
            sumOfSquares += Math.Pow(values[i] - mean, 2);

        return Math.Sqrt(Math.Max(sumOfSquares / values.Length, Epsilon));
    }

    #endregion

    #region Domain-Specific Processors

    public LlmAttentionResult ProcessLlmAttention(VanEnvelope envelope)
    {
        using var scope = _metrics.BeginProcessing();
        double safeQ = Math.Clamp(envelope.QFactor, MinQ, MaxQ);
        double kneeSlope = QToKneeSlope(safeQ);

        var attentionWeights = envelope.Data[0] as double[,] ?? new double[0, 0];
        double noiseFloor = EstimateAttentionNoiseFloor(attentionWeights);

        var gatedWeights = SoftKneeDownwardExpander2D(
            attentionWeights,
            noiseFloor,
            kneeSlope,
            envelope.DitherProfile2D
        );

        _metrics.RecordEnvelope();
        return new LlmAttentionResult
        {
            GatedWeights = gatedWeights,
            PreservedEntropy = envelope.Dither,
            QFactorApplied = safeQ,
            KneeSlopeApplied = kneeSlope,
            ProcessingTimeMs = DateTime.Now.Ticks
        };
    }

    public GCodeResult ProcessGCode(VanEnvelope envelope)
    {
        using var scope = _metrics.BeginProcessing();
        double safeQ = Math.Clamp(envelope.QFactor * 0.9, MinQ, MaxQ);
        double kneeSlope = QToKneeSlope(safeQ);

        var toolpath = envelope.Data[0] as List<GCodePoint> ?? new List<GCodePoint>();
        var velocities = toolpath.Select(p => p.Velocity).ToArray();
        double noiseFloor = EstimateMechanicalNoiseFloor(velocities);

        var smoothedVelocities = SoftKneeDownwardExpander(velocities, noiseFloor, kneeSlope);

        _metrics.RecordEnvelope();
        return new GCodeResult
        {
            ProcessedPoints = ApplyVelocities(toolpath, smoothedVelocities),
            SmoothingApplied = true,
            QFactorApplied = safeQ,
            KneeSlopeApplied = kneeSlope
        };
    }

    public PixelPhaseResult ProcessPixelPhase(VanEnvelope envelope)
    {
        using var scope = _metrics.BeginProcessing();
        double safeQ = Math.Clamp(envelope.QFactor, MinQ, 0.98);
        double kneeSlope = QToKneeSlope(safeQ);

        var pixelMatrix = envelope.Data[0] as double[,] ?? new double[0, 0];
        double noiseFloor = EstimateVisualNoiseFloor(pixelMatrix);

        var denoised = SoftKneeDownwardExpander2D(pixelMatrix, noiseFloor, kneeSlope);

        _metrics.RecordEnvelope();
        return new PixelPhaseResult
        {
            ProcessedImage = denoised,
            NoiseFloorPreserved = noiseFloor,
            QFactorApplied = safeQ,
            KneeSlopeApplied = kneeSlope
        };
    }

    public SteelResonanceResult ProcessSteelResonance(VanEnvelope envelope)
    {
        using var scope = _metrics.BeginProcessing();
        double safeQ = Math.Clamp(envelope.QFactor, MinQ, MaxQ);
        double kneeSlope = QToKneeSlope(safeQ);

        var frequencies = envelope.Data[0] as double[] ?? Array.Empty<double>();
        double resonanceFloor = frequencies.Length > 0 ? frequencies.Average() * 0.1 : Epsilon;

        var filtered = SoftKneeDownwardExpander(frequencies, resonanceFloor, kneeSlope);

        _metrics.RecordEnvelope();
        return new SteelResonanceResult
        {
            FilteredFrequencies = filtered,
            ResonanceDetected = filtered.Any(f => f > resonanceFloor * 2),
            QFactorApplied = safeQ,
            KneeSlopeApplied = kneeSlope
        };
    }

    public VoiceSynthesisResult ProcessVoiceSynthesis(VanEnvelope envelope)
    {
        using var scope = _metrics.BeginProcessing();
        var onnxPath = envelope.Data.Count > 0 ? envelope.Data[0]?.ToString() : null;
        var text = envelope.Data.Count > 1 ? envelope.Data[1]?.ToString() ?? "Hello, this is a unique voice from the noise floor." : "Hello, this is a unique voice from the noise floor.";
        var seed = envelope.Data.Count > 2 && int.TryParse(envelope.Data[2]?.ToString(), out var s) ? s : 0;

        if (string.IsNullOrEmpty(onnxPath) || !File.Exists(onnxPath))
        {
            _metrics.RecordEnvelope();
            return new VoiceSynthesisResult
            {
                OutputPath = string.Empty,
                Error = $"ONNX model not found: {onnxPath ?? "(none provided)"}"
            };
        }

        double safeQ = Math.Clamp(envelope.QFactor, MinQ, MaxQ);
        float strength = (float)safeQ;

        var voiceEngine = VoiceLoRAEnginePool.Instance.GetOrCreate(onnxPath, seed);
        var audio = voiceEngine.Synthesize(text, strength);
        var fingerprint = voiceEngine.GetFingerprint();

        var outputPath = $"voice_output_{DateTime.Now.Ticks}.wav";
        SaveWav(audio, outputPath);

        _metrics.RecordEnvelope();
        return new VoiceSynthesisResult
        {
            AudioSamples = audio,
            OutputPath = outputPath,
            Fingerprint = fingerprint,
            Error = null
        };
    }

    public PersonaResult ProcessVoicePersona(VanEnvelope envelope)
    {
        using var scope = _metrics.BeginProcessing();
        var personaPath = envelope.Data.Count > 0 ? envelope.Data[0]?.ToString() : null;
        var text = envelope.Data.Count > 1 ? envelope.Data[1]?.ToString() ?? "A voice shaped by the music it consumed." : "A voice shaped by the music it consumed.";
        var strength = envelope.Data.Count > 2 && float.TryParse(envelope.Data[2]?.ToString(), out var s) ? s : 0.7f;

        if (string.IsNullOrEmpty(personaPath) || !File.Exists(personaPath))
        {
            _metrics.RecordEnvelope();
            return new PersonaResult
            {
                OutputPath = string.Empty,
                Error = $"Persona JSON not found: {personaPath ?? "(none provided)"}"
            };
        }

        var personaEngine = VoicePersonaEnginePool.Instance.GetOrCreate(personaPath);
        var audio = personaEngine.Synthesize(text, strength);
        var fingerprint = personaEngine.GetFingerprint();

        var outputPath = $"voice_persona_{DateTime.Now.Ticks}.wav";
        SaveWav(audio, outputPath);

        _metrics.RecordEnvelope();
        return new PersonaResult
        {
            AudioSamples = audio,
            OutputPath = outputPath,
            Fingerprint = fingerprint,
            Error = null
        };
    }

    #endregion

    #region Noise Floor Estimation

    private static double EstimateAttentionNoiseFloor(double[,] attentionMatrix)
    {
        var values = new List<double>();
        for (int i = 0; i < attentionMatrix.GetLength(0); i++)
            for (int j = 0; j < attentionMatrix.GetLength(1); j++)
                values.Add(attentionMatrix[i, j]);

        double mean = values.Average();
        double std = StandardDeviation(values.ToArray());
        return Math.Max(mean + std, Epsilon);
    }

    private static double EstimateMechanicalNoiseFloor(double[] velocities)
    {
        double mean = velocities.Average();
        double std = StandardDeviation(velocities.AsSpan());
        return Math.Max(mean + std, Epsilon);
    }

    private static double EstimateVisualNoiseFloor(double[,] pixelMatrix)
    {
        var values = new List<double>();
        int rows = pixelMatrix.GetLength(0);
        int cols = pixelMatrix.GetLength(1);

        for (int i = 0; i < rows; i += Math.Max(1, rows / 10))
            for (int j = 0; j < cols; j += Math.Max(1, cols / 10))
                values.Add(pixelMatrix[i, j]);

        double mean = values.Average();
        double std = StandardDeviation(values.ToArray());
        return Math.Max(mean + std * 0.5, Epsilon);
    }

    #endregion

    #region Token-Based Parser

    public VanEnvelope Demodulate(string rawVanText)
    {
        var envelope = new VanEnvelope();

        if (string.IsNullOrWhiteSpace(rawVanText))
            return envelope;

        var trimmed = rawVanText.AsSpan();
        int pos = 0;

        SkipWhitespace(trimmed, ref pos);

        if (pos >= trimmed.Length)
            return envelope;

        if (trimmed[pos] == '[')
        {
            pos++;
            int labelStart = pos;
            while (pos < trimmed.Length && trimmed[pos] != ':' && trimmed[pos] != ']')
                pos++;
            var label = trimmed.Slice(labelStart, pos - labelStart).ToString().Trim();

            if (pos < trimmed.Length && trimmed[pos] == ':')
            {
                pos++;
                int headerStart = pos;
                while (pos < trimmed.Length && trimmed[pos] != ']')
                    pos++;
                var header = trimmed.Slice(headerStart, pos - headerStart).ToString().Trim();
                envelope.Header = $"{label}:{header}";
                envelope.BlockType = label.Equals("STATE", StringComparison.OrdinalIgnoreCase)
                    ? VanBlockType.State
                    : VanBlockType.Transition;
            }
            if (pos < trimmed.Length)
                pos++;
        }

        SkipWhitespace(trimmed, ref pos);

        if (pos < trimmed.Length && trimmed[pos] == '{')
        {
            pos++;
            SkipWhitespace(trimmed, ref pos);

            while (pos < trimmed.Length && trimmed[pos] != '}')
            {
                SkipWhitespace(trimmed, ref pos);
                if (pos >= trimmed.Length || trimmed[pos] == '}')
                    break;

                int keyStart = pos;
                while (pos < trimmed.Length && trimmed[pos] != ':')
                    pos++;

                if (pos >= trimmed.Length) break;
                var key = trimmed.Slice(keyStart, pos - keyStart).ToString().Trim();
                pos++;
                SkipWhitespace(trimmed, ref pos);

                switch (key)
                {
                    case "CARRIER":
                        envelope.Carrier = ReadValue(trimmed, ref pos);
                        break;
                    case "MODULATION":
                        envelope.Modulation = ReadValue(trimmed, ref pos);
                        break;
                    case "Q-FACTOR":
                        var qStr = ReadValue(trimmed, ref pos);
                        if (double.TryParse(qStr, out double q))
                            envelope.QFactor = Math.Clamp(q, MinQ, MaxQ);
                        break;
                    case "DITHER":
                        envelope.Dither = ReadValue(trimmed, ref pos);
                        break;
                    case "DATA":
                        envelope.Data = ReadDataArray(trimmed, ref pos);
                        break;
                    case "DATATYPES":
                        envelope.DataTypes = ReadStringArray(trimmed, ref pos);
                        break;
                    default:
                        SkipValue(trimmed, ref pos);
                        break;
                }

                SkipWhitespace(trimmed, ref pos);
                if (pos < trimmed.Length && trimmed[pos] == ';')
                    pos++;
            }
        }

        return envelope;
    }

    private static void SkipWhitespace(ReadOnlySpan<char> input, ref int pos)
    {
        while (pos < input.Length && char.IsWhiteSpace(input[pos]))
            pos++;
    }

    private static string ReadValue(ReadOnlySpan<char> input, ref int pos)
    {
        SkipWhitespace(input, ref pos);
        if (pos >= input.Length) return string.Empty;

        if (input[pos] == '"')
        {
            pos++;
            int start = pos;
            while (pos < input.Length && input[pos] != '"')
                pos++;
            var val = input.Slice(start, pos - start).ToString();
            if (pos < input.Length) pos++;
            return val;
        }

        int valStart = pos;
        while (pos < input.Length && input[pos] != ';' && input[pos] != '}' && input[pos] != ',' && !char.IsWhiteSpace(input[pos]))
            pos++;

        return input.Slice(valStart, pos - valStart).ToString();
    }

    private static void SkipValue(ReadOnlySpan<char> input, ref int pos)
    {
        while (pos < input.Length && input[pos] != ';' && input[pos] != '}')
        {
            if (input[pos] == '"')
            {
                pos++;
                while (pos < input.Length && input[pos] != '"') pos++;
                if (pos < input.Length) pos++;
            }
            else
            {
                pos++;
            }
        }
    }

    private static List<object> ReadDataArray(ReadOnlySpan<char> input, ref int pos)
    {
        var list = new List<object>();
        SkipWhitespace(input, ref pos);

        if (pos >= input.Length || input[pos] != '[')
            return list;
        pos++;
        SkipWhitespace(input, ref pos);

        while (pos < input.Length && input[pos] != ']')
        {
            SkipWhitespace(input, ref pos);
            if (pos >= input.Length || input[pos] == ']')
                break;

            if (input[pos] == '"')
            {
                pos++;
                int start = pos;
                while (pos < input.Length && input[pos] != '"')
                {
                    if (input[pos] == '\\') pos++;
                    pos++;
                }
                list.Add(input.Slice(start, pos - start).ToString());
                if (pos < input.Length) pos++;
            }
            else if (char.IsDigit(input[pos]) || input[pos] == '-')
            {
                int start = pos;
                while (pos < input.Length && (char.IsDigit(input[pos]) || input[pos] == '.' || input[pos] == '-'))
                    pos++;
                if (double.TryParse(input.Slice(start, pos - start), out double num))
                    list.Add(num);
            }

            SkipWhitespace(input, ref pos);
            if (pos < input.Length && input[pos] == ',')
                pos++;
        }

        if (pos < input.Length && input[pos] == ']')
            pos++;

        return list;
    }

    private static List<string> ReadStringArray(ReadOnlySpan<char> input, ref int pos)
    {
        var list = new List<string>();
        SkipWhitespace(input, ref pos);

        if (pos >= input.Length || input[pos] != '[')
            return list;
        pos++;
        SkipWhitespace(input, ref pos);

        while (pos < input.Length && input[pos] != ']')
        {
            SkipWhitespace(input, ref pos);
            if (pos >= input.Length || input[pos] == ']')
                break;

            if (input[pos] == '"')
            {
                pos++;
                int start = pos;
                while (pos < input.Length && input[pos] != '"')
                    pos++;
                list.Add(input.Slice(start, pos - start).ToString());
                if (pos < input.Length) pos++;
            }

            SkipWhitespace(input, ref pos);
            if (pos < input.Length && input[pos] == ',')
                pos++;
        }

        if (pos < input.Length && input[pos] == ']')
            pos++;

        return list;
    }

    #endregion

    #region Visualization

    public void VisualizeSpectrogram(VanEnvelope envelope, double[] signal)
    {
        _spectrogram.Render(envelope.Header, signal);
    }

    #endregion

    #region Helpers

    private static void SaveWav(float[] samples, string path)
    {
        int sampleRate = 22050;
        int channels = 1;
        int bitsPerSample = 16;

        using var stream = new FileStream(path, FileMode.Create);
        using var writer = new BinaryWriter(stream);

        int dataSize = samples.Length * (bitsPerSample / 8);
        int fileSize = 36 + dataSize;

        writer.Write(Encoding.ASCII.GetBytes("RIFF"));
        writer.Write(fileSize);
        writer.Write(Encoding.ASCII.GetBytes("WAVE"));
        writer.Write(Encoding.ASCII.GetBytes("fmt "));
        writer.Write(16);
        writer.Write((short)1);
        writer.Write((short)channels);
        writer.Write(sampleRate);
        writer.Write(sampleRate * channels * (bitsPerSample / 8));
        writer.Write((short)(channels * (bitsPerSample / 8)));
        writer.Write((short)bitsPerSample);
        writer.Write(Encoding.ASCII.GetBytes("data"));
        writer.Write(dataSize);

        foreach (float sample in samples)
        {
            short val = (short)Math.Clamp(sample * short.MaxValue, short.MinValue, short.MaxValue);
            writer.Write(val);
        }
    }

    private static async Task SaveWavAsync(float[] samples, string path, CancellationToken ct = default)
    {
        int sampleRate = 22050;
        int channels = 1;
        int bitsPerSample = 16;

        await using var stream = new FileStream(path, FileMode.Create, FileAccess.Write, FileShare.None, 4096, useAsync: true);
        await using var writer = new BinaryWriter(stream);

        int dataSize = samples.Length * (bitsPerSample / 8);
        int fileSize = 36 + dataSize;

        writer.Write(Encoding.ASCII.GetBytes("RIFF"));
        writer.Write(fileSize);
        await stream.FlushAsync(ct);
        writer.Write(Encoding.ASCII.GetBytes("WAVE"));
        writer.Write(Encoding.ASCII.GetBytes("fmt "));
        writer.Write(16);
        writer.Write((short)1);
        writer.Write((short)channels);
        writer.Write(sampleRate);
        writer.Write(sampleRate * channels * (bitsPerSample / 8));
        writer.Write((short)(channels * (bitsPerSample / 8)));
        writer.Write((short)bitsPerSample);
        writer.Write(Encoding.ASCII.GetBytes("data"));
        writer.Write(dataSize);

        foreach (float sample in samples)
        {
            short val = (short)Math.Clamp(sample * short.MaxValue, short.MinValue, short.MaxValue);
            writer.Write(val);
        }

        await stream.FlushAsync(ct);
    }

    private static List<GCodePoint> ApplyVelocities(List<GCodePoint> toolpath, double[] velocities)
    {
        var result = new List<GCodePoint>();
        for (int i = 0; i < toolpath.Count && i < velocities.Length; i++)
        {
            result.Add(new GCodePoint
            {
                X = toolpath[i].X,
                Y = toolpath[i].Y,
                Z = toolpath[i].Z,
                Velocity = velocities[i]
            });
        }
        return result;
    }

    #endregion

    #region Fryas Tex Compliance

    public bool CheckCompliance(VanEnvelope envelope)
    {
        if (_compliance.IsExpelled(envelope.Carrier))
            return false;

        if (_compliance.IsQuarantined(envelope.Modulation))
            return false;

        _compliance.AssertNoLockIn(envelope.Carrier, "VAN");

        var cloudIndicators = new[] { "http", "https", "api.", "cloud", ".azure", ".aws", "telemetry" };
        foreach (var item in envelope.Data)
        {
            var str = item?.ToString() ?? "";
            foreach (var indicator in cloudIndicators)
            {
                if (str.Contains(indicator, StringComparison.OrdinalIgnoreCase))
                {
                    _compliance.ExpelVoluntaryCloudDependency(envelope.Carrier, indicator);
                    return false;
                }
            }
        }

        return true;
    }

    public bool CheckGovernance(VanEnvelope envelope)
    {
        if (_citadelLaws.IsQuarantined(envelope.Carrier))
            return false;

        if (!_citadelLaws.HasVotingRights(envelope.Carrier))
            return false;

        var dependencies = ExtractDependencies(envelope);
        if (!_citadelLaws.ValidateCitadelSelfSustenance(envelope.Carrier, dependencies))
            return false;

        return true;
    }

    public object ExecuteWithCompliance(VanEnvelope envelope, Dictionary<string, object>? state = null)
    {
        if (!CheckCompliance(envelope))
            return new { error = "Compliance violation - execution blocked", directive = "Frya's Tex" };

        if (!CheckGovernance(envelope))
            return new { error = "Governance violation - execution blocked", directive = "Citadel Laws" };

        if (!_citadelLaws.AcquireDefenderSlot().GetAwaiter().GetResult())
            return new { error = "No defender slots available (Law 8). Try later." };

        try
        {
            if (!_citadelLaws.MayGiveAdvice(envelope.Carrier))
                return new { error = "Advice cooldown in effect (Law 18-20). Wait before consulting again." };

            // Universal Law 2: Free choice of dependencies
            if (envelope.Modulation != null && !string.IsNullOrEmpty(envelope.Modulation))
            {
                if (!_universalLaw.ValidateFreeChoice(envelope.Carrier, envelope.Modulation))
                    return new { error = $"Law 2: {envelope.Modulation} forces additional dependencies. Free choice violated." };
            }

            // Universal Law 5: Public exposure requires service
            if (string.Equals(envelope.Modulation, "PublicAPI", StringComparison.OrdinalIgnoreCase))
            {
                if (!PublicServiceValidator.HasPublicServiceAttribute(typeof(VanEngine)))
                    return new { error = "Law 5: Public exposure requires public service attribute." };
            }

            // Universal Law 7: Forest memory limits
            var estimatedMemory = EstimateMemoryFootprint(envelope);
            if (!_forest.RequestTreeFelling(estimatedMemory, envelope.Carrier))
                return new { error = "Law 7: Forest capacity exceeded. Memory request denied." };

            var sw = Stopwatch.StartNew();

            _compliance.LogGratitude(
                $"Received envelope: {envelope.Header}",
                $"Processing {envelope.Carrier}/{envelope.Modulation}",
                "Hope for successful execution"
            );

            if (envelope.Data.Count == 0)
                _compliance.OfferProactiveAssistance(envelope.Carrier, "Envelope has empty DATA array");

            object? result;
            if (_compiler.TryExecute(envelope, state ?? new Dictionary<string, object>(), out var execResult))
            {
                _compliance.RegisterWork(envelope.Carrier, 1);
                _compliance.ResetLocalResourceFlag();
                result = execResult ?? new { };
            }
            else
            {
                _citadelLaws.RecordWoundedDefender(envelope.Carrier, "Execution failed");
                return new { error = "Execution failed" };
            }

            sw.Stop();

            // Law 8-10: Track market overhead
            _market.RecordSystemOverhead(sw.ElapsedTicks);
            _market.RecordUserWork(GetUserWorkTicks(envelope));

            return result;
        }
        catch (Exception ex)
        {
            _citadelLaws.RecordWoundedDefender(envelope.Carrier, ex.Message);
            throw;
        }
        finally
        {
            _citadelLaws.ReleaseDefenderSlot();
        }
    }

    private static long EstimateMemoryFootprint(VanEnvelope envelope)
    {
        long estimate = 256;
        foreach (var item in envelope.Data)
        {
            if (item is double[,] matrix)
                estimate += matrix.GetLength(0) * matrix.GetLength(1) * 8;
            else if (item is double[] arr)
                estimate += arr.Length * 8;
            else if (item is string str)
                estimate += str.Length * 2;
            else
                estimate += 64;
        }
        return estimate;
    }

    private static long GetUserWorkTicks(VanEnvelope envelope)
    {
        return envelope.Data.Count * 100;
    }

    private static List<string> ExtractDependencies(VanEnvelope envelope)
    {
        var deps = new List<string>();
        foreach (var item in envelope.Data)
        {
            var str = item?.ToString() ?? "";
            if (str.Contains("http", StringComparison.OrdinalIgnoreCase) ||
                str.Contains("cloud", StringComparison.OrdinalIgnoreCase) ||
                str.Contains("api.", StringComparison.OrdinalIgnoreCase))
                deps.Add(str);
        }
        if (!string.IsNullOrEmpty(envelope.Modulation) &&
            (envelope.Modulation.Contains("http", StringComparison.OrdinalIgnoreCase) ||
             envelope.Modulation.Contains("cloud", StringComparison.OrdinalIgnoreCase)))
            deps.Add(envelope.Modulation);
        return deps;
    }

    #endregion

    #region Juul Tokenization Pipeline

    public JuulMask[] TokenizeToJuul(ReadOnlySpan<char> fryasText)
    {
        var lexer = new JuulLexer(fryasText);
        return lexer.ToMaskArray();
    }

    public string JuulMasksToString(JuulMask[] masks)
    {
        return string.Join(" ", masks.Select(m => $"{(byte)m:X2}"));
    }

    #endregion
}
