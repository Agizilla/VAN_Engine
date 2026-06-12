using VanEngine.Compiler.AST;
using VanEngine.Compiler.Bootstrap;
using VanEngine.Compiler.Parser;
using VanEngine.Compiler.Registry;

namespace VanEngine.Compiler.Runtime;

public sealed class CortexRuntime : IDisposable
{
    private readonly VanFunctionRegistry _registry;
    private readonly VanContext _context;
    private readonly BootstrapLoader? _bootstrapLoader;

    public CortexRuntime(string? bootstrapPath = null)
    {
        _registry = new VanFunctionRegistry();
        _context = new VanContext();
        _bootstrapLoader = bootstrapPath != null ? new BootstrapLoader(bootstrapPath) : null;
    }

    public VanContext Context => _context;
    public VanFunctionRegistry Registry => _registry;

    public async Task InitializeAsync(CancellationToken ct = default)
    {
        if (_bootstrapLoader?.Exists == true)
        {
            var bootstrapEnvelopes = await _bootstrapLoader.LoadAsync(ct);
            foreach (var env in bootstrapEnvelopes)
            {
                await ExecuteEnvelopeAsync(env);
            }
        }
    }

    public async Task ExecuteFileAsync(string path)
    {
        var text = await File.ReadAllTextAsync(path);
        var envelopes = ParseText(text);
        foreach (var env in envelopes)
            await ExecuteEnvelopeAsync(env);
    }

    public async Task<object> ExecuteStringAsync(string vanText)
    {
        var envelopes = ParseText(vanText);
        object? lastResult = null;
        foreach (var env in envelopes)
            lastResult = await ExecuteEnvelopeAsync(env);
        return lastResult ?? new { result = "empty" };
    }

    public async Task<object> ExecuteEnvelopeAsync(AstEnvelope envelope)
    {
        _context.Envelope = envelope;

        if (envelope.BlockType == VanEngine.Core.VAN.VanBlockType.State && envelope.Data.Count >= 2)
        {
            string key = envelope.Data[0]?.ToString() ?? string.Empty;
            string value = envelope.Data[1]?.ToString() ?? string.Empty;

            if (double.TryParse(value, out double num))
                _context.Set(key, num);
            else if (bool.TryParse(value, out bool flag))
                _context.Set(key, flag);
            else
                _context.Set(key, value);
        }

        if (_registry.TryGetExecutor(envelope, out var executor) && executor != null)
        {
            return await executor(_context, envelope);
        }

        return await FallbackExecutor(envelope);
    }

    private static List<AstEnvelope> ParseText(string text)
    {
        var parser = new VanParser(text.AsSpan());
        return parser.Parse();
    }

    private Task<object> FallbackExecutor(AstEnvelope envelope)
    {
        var result = new
        {
            carrier = envelope.Carrier,
            modulation = envelope.Modulation,
            data = envelope.Data,
            state_count = _context.Count,
            q_factor = envelope.QFactor,
            block_type = envelope.BlockType.ToString()
        };
        return Task.FromResult<object>(result);
    }

    public VanEngine.Core.VAN.VanBlockType ResolveBlockType(AstEnvelope envelope)
    {
        if (envelope.Header.StartsWith("STATE:", StringComparison.OrdinalIgnoreCase))
            return VanEngine.Core.VAN.VanBlockType.State;
        return VanEngine.Core.VAN.VanBlockType.Transition;
    }

    public void Dispose()
    {
        _context.Clear();
    }
}
