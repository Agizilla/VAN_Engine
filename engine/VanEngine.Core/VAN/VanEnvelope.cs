namespace VanEngine.Core.VAN;

public sealed class VanEnvelope
{
    public VanBlockType BlockType { get; set; } = VanBlockType.Transition;
    public ProcessingMode Mode { get; set; } = ProcessingMode.Frya;
    public string Header { get; set; } = string.Empty;
    public string Carrier { get; set; } = string.Empty;
    public string Modulation { get; set; } = string.Empty;
    public double QFactor { get; set; } = 0.95;
    public string Dither { get; set; } = string.Empty;
    public List<object> Data { get; set; } = new();
    public List<string> DataTypes { get; set; } = new();
    public double[,]? DitherProfile2D { get; set; }
}
