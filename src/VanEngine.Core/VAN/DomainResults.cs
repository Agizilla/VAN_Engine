using VanEngine.Voice;

namespace VanEngine.Core.VAN;

public sealed class GCodePoint
{
    public double X { get; set; }
    public double Y { get; set; }
    public double Z { get; set; }
    public double Velocity { get; set; }
}

public sealed class LlmAttentionResult
{
    public double[,] GatedWeights { get; set; } = new double[0, 0];
    public string PreservedEntropy { get; set; } = string.Empty;
    public double QFactorApplied { get; set; }
    public double KneeSlopeApplied { get; set; }
    public long ProcessingTimeMs { get; set; }
}

public sealed class GCodeResult
{
    public List<GCodePoint> ProcessedPoints { get; set; } = new();
    public bool SmoothingApplied { get; set; }
    public double QFactorApplied { get; set; }
    public double KneeSlopeApplied { get; set; }
}

public sealed class PixelPhaseResult
{
    public double[,] ProcessedImage { get; set; } = new double[0, 0];
    public double NoiseFloorPreserved { get; set; }
    public double QFactorApplied { get; set; }
    public double KneeSlopeApplied { get; set; }
}

public sealed class SteelResonanceResult
{
    public double[] FilteredFrequencies { get; set; } = Array.Empty<double>();
    public bool ResonanceDetected { get; set; }
    public double QFactorApplied { get; set; }
    public double KneeSlopeApplied { get; set; }
}

public sealed class VoiceSynthesisResult
{
    public float[] AudioSamples { get; set; } = Array.Empty<float>();
    public string OutputPath { get; set; } = string.Empty;
    public VoiceFingerprint? Fingerprint { get; set; }
    public string? Error { get; set; }
}

public sealed class PersonaResult
{
    public float[] AudioSamples { get; set; } = Array.Empty<float>();
    public string OutputPath { get; set; } = string.Empty;
    public PersonaFingerprint? Fingerprint { get; set; }
    public string? Error { get; set; }
}

public sealed class VanSpectrogram
{
    public void Render(string title, double[] signal)
    {
        Console.WriteLine($"\n=== Spectrogram: {title} ===");
        Console.WriteLine($"Signal Length: {signal.Length}");
        Console.WriteLine($"Mean: {(signal.Length > 0 ? signal.Average() : 0):F4}");
        Console.WriteLine($"StdDev: {(signal.Length > 0 ? StandardDeviation(signal) : 0):F4}");
        Console.WriteLine($"Dynamic Range: {(signal.Length > 0 ? signal.Max() - signal.Min() : 0):F4}");
    }

    private static double StandardDeviation(double[] values)
    {
        if (values.Length == 0) return 0;
        double mean = values.Average();
        return Math.Sqrt(values.Sum(v => Math.Pow(v - mean, 2)) / values.Length);
    }
}
