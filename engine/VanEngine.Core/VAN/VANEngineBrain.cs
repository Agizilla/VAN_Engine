using System.Collections.Concurrent;
using System.Diagnostics;
using VanEngine.Core.Services;

namespace VanEngine.Core.VAN;

public sealed class VANEngineBrain
{
    private static readonly Lazy<VANEngineBrain> LazyInstance = new(() => new VANEngineBrain());

    private readonly VanEngine _engine;
    private readonly ConcurrentDictionary<string, string> _tokens;
    private readonly ConcurrentQueue<BrainAuditEvent> _auditTrail;
    private readonly Stopwatch _uptime;
    private InferenceService? _inferenceService;

    public InferenceService InferenceService => _inferenceService ??= new InferenceService(this);

    private VANEngineBrain()
    {
        _engine = new VanEngine();
        _tokens = new ConcurrentDictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        _auditTrail = new ConcurrentQueue<BrainAuditEvent>();
        _uptime = Stopwatch.StartNew();
    }

    public static VANEngineBrain Instance => LazyInstance.Value;

    public Task<QueryResult> ExecuteQueryAsync(string query, IDictionary<string, object>? context = null)
    {
        if (string.IsNullOrWhiteSpace(query))
        {
            return Task.FromResult(QueryResult.Clarify("Please provide a query."));
        }

        var normalized = query.Trim();

        if (normalized.Contains("status", StringComparison.OrdinalIgnoreCase))
        {
            var stats = GetStats();
            return Task.FromResult(QueryResult.Ok(
                $"VAN_Engine is online. Tokens: {stats.TokenCount:N0}. Uptime: {stats.Uptime:g}.",
                "STATUS"));
        }

        if (normalized.Contains("help", StringComparison.OrdinalIgnoreCase))
        {
            return Task.FromResult(QueryResult.Clarify(
                "I can summarize the engine, report stats, store tokens, and inspect audit history."));
        }

        _engine.Metrics.RecordEnvelope();
        var response = $"Received query: {normalized}";
        _auditTrail.Enqueue(new BrainAuditEvent(DateTimeOffset.UtcNow, "query", normalized));
        return Task.FromResult(QueryResult.Ok(response, "EXECUTE"));
    }

    public async Task<QueryResult> ExecuteAlgorithmQueryAsync(string query)
    {
        if (string.IsNullOrWhiteSpace(query))
            return QueryResult.Clarify("Please provide a query for algorithm execution.");

        var result = await InferenceService.RunAsync(
            "You are VAN_Engine algorithm executor",
            query,
            InferenceTier.Smart);

        return result.Success
            ? QueryResult.Ok(result.Output, "ALGORITHM_COMPLETE")
            : QueryResult.Clarify(result.Error ?? "Algorithm execution failed");
    }

    public SelfTestResult SelfTest()
    {
        try
        {
            var stats = GetStats();
            return SelfTestResult.Ok($"Brain ready. Token count: {stats.TokenCount:N0}");
        }
        catch (Exception ex)
        {
            return SelfTestResult.Fail(ex.Message);
        }
    }

    public BrainStats GetStats()
    {
        return new BrainStats
        {
            TokenCount = _tokens.Count,
            AuditEventCount = _auditTrail.Count,
            Uptime = _uptime.Elapsed,
            ActiveISO = ["ISO_010", "ISO_012", "ISO_019", "ISO_020"]
        };
    }

    public bool StoreToken(string token, double w, double x, double y, double z, IReadOnlyList<string> appliesTo)
    {
        var stored = _tokens.TryAdd(token, $"{w},{x},{y},{z}:{string.Join('|', appliesTo)}");
        if (stored)
        {
            _auditTrail.Enqueue(new BrainAuditEvent(DateTimeOffset.UtcNow, "store_token", token));
        }

        return stored;
    }

    public string? LookupToken(string token)
    {
        return _tokens.TryGetValue(token, out var value) ? value : null;
    }

    public IReadOnlyList<BrainAuditEvent> GetAuditTrail(int count)
    {
        return _auditTrail
            .Reverse()
            .Take(Math.Max(0, count))
            .ToList();
    }
}

public sealed class QueryResult
{
    public bool Success { get; init; }
    public string Action { get; init; } = string.Empty;
    public string Message { get; init; } = string.Empty;
    public object? Data { get; init; }
    public List<string>? ClarificationQuestions { get; init; }

    public static QueryResult Ok(string message, string action) => new()
    {
        Success = true,
        Action = action,
        Message = message
    };

    public static QueryResult Clarify(string message) => new()
    {
        Success = false,
        Action = "HALT_AND_CLARIFY",
        Message = message,
        ClarificationQuestions = [message]
    };
}

public sealed class SelfTestResult
{
    public bool IsValid { get; init; }
    public string Diagnostics { get; init; } = string.Empty;

    public static SelfTestResult Ok(string diagnostics) => new()
    {
        IsValid = true,
        Diagnostics = diagnostics
    };

    public static SelfTestResult Fail(string diagnostics) => new()
    {
        IsValid = false,
        Diagnostics = diagnostics
    };
}

public sealed class BrainStats
{
    public long TokenCount { get; init; }
    public long AuditEventCount { get; init; }
    public TimeSpan Uptime { get; init; }
    public IReadOnlyList<string> ActiveISO { get; init; } = Array.Empty<string>();
}

public sealed record BrainAuditEvent(DateTimeOffset Timestamp, string Kind, string Payload)
{
    public Dictionary<string, object> ToDictionary()
    {
        return new()
        {
            ["timestamp"] = Timestamp,
            ["kind"] = Kind,
            ["payload"] = Payload
        };
    }
}

