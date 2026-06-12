using VanEngine.Core.VAN.Compiler.Runtime;

namespace VanEngine.Core.VAN.Compiler;

public sealed class AstEnvelope
{
    public VanBlockType BlockType { get; set; } = VanBlockType.Transition;
    public string Header { get; set; } = string.Empty;
    public string Carrier { get; set; } = string.Empty;
    public string Modulation { get; set; } = string.Empty;
    public double QFactor { get; set; } = 0.95;
    public string Dither { get; set; } = string.Empty;
    public List<object> Data { get; set; } = new();
    public List<string> DataTypes { get; set; } = new();
    public Func<VanContext, Task<object>>? Executor { get; set; }
    public int LineNumber { get; set; }
    public string SourceFile { get; set; } = string.Empty;
}
