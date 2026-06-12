using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text.Json;
using VanEngine.Core.VAN;

namespace VanEngine.Core.Services;

public sealed class InferenceService : IDisposable
{
    private readonly VANEngineBrain _brain;
    private readonly ConcurrentDictionary<string, object> _cache = new();
    private readonly SemaphoreSlim _semaphore = new(1, 1);
    private bool _disposed;

    private const int FAST_TIMEOUT_MS = 15000;
    private const int STANDARD_TIMEOUT_MS = 30000;
    private const int SMART_TIMEOUT_MS = 90000;

    public InferenceService(VANEngineBrain brain)
    {
        _brain = brain;
    }

    public async Task<InferenceResult> RunAsync(
        string systemPrompt,
        string userPrompt,
        InferenceTier tier = InferenceTier.Standard,
        bool expectJson = false,
        CancellationToken ct = default)
    {
        var startTime = Stopwatch.GetTimestamp();
        var cacheKey = $"{systemPrompt}:{userPrompt}:{tier}";

        if (tier == InferenceTier.Fast && _cache.TryGetValue(cacheKey, out var cached))
        {
            return InferenceResult.CreateSuccess(cached.ToString() ?? string.Empty, tier, Stopwatch.GetElapsedTime(startTime).TotalMilliseconds, fromCache: true);
        }

        var timeout = GetTimeout(tier);
        using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        cts.CancelAfter(timeout);

        try
        {
            var result = await ExecuteInference(systemPrompt, userPrompt, tier, expectJson, cts.Token);
            if (tier == InferenceTier.Fast && result.Success)
                _cache.TryAdd(cacheKey, result.Output);
            return result;
        }
        catch (OperationCanceledException)
        {
            return InferenceResult.CreateFailure($"Timeout after {timeout}ms", tier, Stopwatch.GetElapsedTime(startTime).TotalMilliseconds);
        }
        catch (Exception ex)
        {
            return InferenceResult.CreateFailure(ex.Message, tier, Stopwatch.GetElapsedTime(startTime).TotalMilliseconds);
        }
    }

    private Task<InferenceResult> ExecuteInference(string systemPrompt, string userPrompt, InferenceTier tier, bool expectJson, CancellationToken ct)
    {
        return tier switch
        {
            InferenceTier.Fast => FastInference(systemPrompt, userPrompt, expectJson, ct),
            InferenceTier.Standard => StandardInference(userPrompt, ct),
            InferenceTier.Smart => SmartInference(userPrompt, ct),
            _ => StandardInference(userPrompt, ct)
        };
    }

    private Task<InferenceResult> FastInference(string systemPrompt, string userPrompt, bool expectJson, CancellationToken ct)
    {
        var queryLower = userPrompt.ToLowerInvariant();

        if (queryLower.Contains("status") || queryLower.Contains("health"))
        {
            var stats = _brain.GetStats();
            var result = $"VAN_Engine online. Tokens: {stats.TokenCount:N0}. Uptime: {stats.Uptime:g}.";
            return Task.FromResult(InferenceResult.CreateSuccess(result, InferenceTier.Fast, 0));
        }

        if (queryLower.Contains("help"))
        {
            var help = """
                Available commands:
                - status / health: System status
                - help: This message
                - lookup <token>: Find token in index
                - store <token> (w,x,y,z): Store token
                - algorithm: Run full 7-phase Algorithm
                """;
            return Task.FromResult(InferenceResult.CreateSuccess(help, InferenceTier.Fast, 0));
        }

        if (queryLower.Contains("lookup"))
        {
            var tokenMatch = System.Text.RegularExpressions.Regex.Match(userPrompt, @"lookup\s+(\w+)");
            if (tokenMatch.Success)
            {
                var token = tokenMatch.Groups[1].Value;
                var result = _brain.LookupToken(token);
                if (result != null)
                    return Task.FromResult(InferenceResult.CreateSuccess($"Token '{token}': {result}", InferenceTier.Fast, 0));
                return Task.FromResult(InferenceResult.CreateSuccess($"Token '{token}' not found", InferenceTier.Fast, 0));
            }
        }

        return Task.FromResult(InferenceResult.CreateSuccess(
            $"Fast inference: Processing '{userPrompt[..Math.Min(100, userPrompt.Length)]}'",
            InferenceTier.Fast, 0));
    }

    private Task<InferenceResult> StandardInference(string userPrompt, CancellationToken ct)
    {
        var result = _brain.ExecuteQueryAsync(userPrompt).Result;
        return Task.FromResult(InferenceResult.CreateSuccess(result.Message, InferenceTier.Standard, 0, result.Data));
    }

    private async Task<InferenceResult> SmartInference(string userPrompt, CancellationToken ct)
    {
        var result = await _brain.ExecuteAlgorithmQueryAsync(userPrompt);
        return InferenceResult.CreateSuccess(result.Message, InferenceTier.Smart, 0, new { result.Action, result.Data });
    }

    private static int GetTimeout(InferenceTier tier) => tier switch
    {
        InferenceTier.Fast => FAST_TIMEOUT_MS,
        InferenceTier.Standard => STANDARD_TIMEOUT_MS,
        InferenceTier.Smart => SMART_TIMEOUT_MS,
        _ => STANDARD_TIMEOUT_MS
    };

    public void Dispose()
    {
        if (_disposed) return;
        _semaphore.Dispose();
        _disposed = true;
    }
}

public enum InferenceTier { Fast, Standard, Smart }

public class InferenceResult
{
    public bool Success { get; set; }
    public string Output { get; set; } = string.Empty;
    public object? Parsed { get; set; }
    public string? Error { get; set; }
    public double LatencyMs { get; set; }
    public InferenceTier Tier { get; set; }
    public bool FromCache { get; set; }

    public static InferenceResult CreateSuccess(string output, InferenceTier tier, double latencyMs, object? parsed = null, bool fromCache = false) =>
        new() { Success = true, Output = output, Parsed = parsed, LatencyMs = latencyMs, Tier = tier, FromCache = fromCache };

    public static InferenceResult CreateFailure(string error, InferenceTier tier, double latencyMs) =>
        new() { Success = false, Error = error, LatencyMs = latencyMs, Tier = tier };

    public string ToJson() => JsonSerializer.Serialize(this);
}
