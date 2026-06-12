using System.Text.Json;
using VanEngine.Core.VAN.Audit;
using VanEngine.Core.VAN.Compiler.Parser;
using VanEngine.Core.VAN.Compiler.Registry;
using VanEngine.Core.VAN.Security;

namespace VanEngine.Core.VAN.Compiler.Runtime;

public sealed class CortexRuntime : IDisposable
{
    private readonly VanFunctionRegistry _registry;
    private readonly VanContext _context;
    private readonly RighteousnessFilter _filter;
    private readonly AuditLog _audit;
    private bool _folkMotherMode;

    public CortexRuntime(RighteousnessFilter? filter = null, AuditLog? audit = null)
    {
        _registry = new VanFunctionRegistry();
        _context = new VanContext();
        _audit = audit ?? new AuditLog(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "audit.log"));
        _filter = filter ?? new RighteousnessFilter(_audit);
        _folkMotherMode = true;
    }

    public VanContext Context => _context;
    public VanFunctionRegistry Registry => _registry;
    public RighteousnessFilter Filter => _filter;
    public AuditLog Audit => _audit;
    public bool FolkMotherMode
    {
        get => _folkMotherMode;
        set => _folkMotherMode = value;
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

        if (_folkMotherMode && !_filter.IsRighteous(envelope))
        {
            _audit.Record("FolkMother",
                $"Envelope rejected by FolkMother consent: {envelope.Header}",
                AuditSeverity.Critical);
            return new { rejected = true, reason = "RighteousnessFilter blocked envelope" };
        }

        if (envelope.BlockType == VanBlockType.State && envelope.Data.Count >= 2)
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
            _audit.RecordEnvelope(envelope.Carrier, envelope.Modulation, "executed");
            return await executor(_context, envelope);
        }

        _audit.RecordEnvelope(envelope.Carrier, envelope.Modulation, "fallback");
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

    public void Dispose()
    {
        _audit.Dispose();
        _context.Clear();
    }
}
