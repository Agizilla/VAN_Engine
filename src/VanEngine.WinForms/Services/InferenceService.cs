using System.Collections.Concurrent;
using System.Diagnostics;
using VanEngine.WinForms.Models;

namespace VanEngine.WinForms.Services;

public class InferenceService
{
    private readonly BrainBridge _brainBridge;
    private readonly ConcurrentDictionary<string, string> _cache = new();

    public InferenceService(BrainBridge brainBridge)
    {
        _brainBridge = brainBridge;
    }

    public async Task<InferenceResult> RunAsync(string systemPrompt, string userPrompt, string tier, bool expectJson)
    {
        var startTime = Stopwatch.GetTimestamp();
        var cacheKey = $"{systemPrompt}:{userPrompt}:{tier}";

        if (tier == "fast" && _cache.TryGetValue(cacheKey, out var cached))
        {
            return new InferenceResult { Success = true, Output = cached, Tier = "fast", LatencyMs = GetElapsedMs(startTime), FromCache = true };
        }

        try
        {
            var result = await ExecuteInference(systemPrompt, userPrompt, tier);
            if (tier == "fast" && result.Success)
                _cache.TryAdd(cacheKey, result.Output);
            result.LatencyMs = GetElapsedMs(startTime);
            return result;
        }
        catch (Exception ex)
        {
            return new InferenceResult { Success = false, Error = ex.Message, Tier = tier, LatencyMs = GetElapsedMs(startTime) };
        }
    }

    private async Task<InferenceResult> ExecuteInference(string systemPrompt, string userPrompt, string tier)
    {
        return tier switch
        {
            "fast" => await FastInference(userPrompt),
            "smart" => await SmartInference(userPrompt),
            _ => await StandardInference(userPrompt)
        };
    }

    private Task<InferenceResult> FastInference(string userPrompt)
    {
        var lower = userPrompt.ToLower();
        if (lower.Contains("status") || lower.Contains("health"))
            return Task.FromResult(new InferenceResult { Success = true, Output = "VAN_Engine online. Use the main chat panel for detailed queries.", Tier = "fast" });
        if (lower.Contains("help"))
            return Task.FromResult(new InferenceResult { Success = true, Output = "Commands:\n- status / health: System status\n- lookup <token>: Find token\n- help: This message", Tier = "fast" });
        return Task.FromResult(new InferenceResult { Success = true, Output = $"Fast inference result for: {userPrompt[..Math.Min(200, userPrompt.Length)]}...", Tier = "fast" });
    }

    private async Task<InferenceResult> StandardInference(string userPrompt)
    {
        var response = await _brainBridge.QueryAsync(userPrompt);
        return new InferenceResult { Success = response.Success, Output = response.Message, Tier = "standard" };
    }

    private async Task<InferenceResult> SmartInference(string userPrompt)
    {
        var enhancedPrompt = $"[ALGORITHM MODE] Run 7-phase execution (Observe-Think-Plan-Build-Execute-Verify-Learn) on: {userPrompt}";
        var response = await _brainBridge.QueryAsync(enhancedPrompt);
        return new InferenceResult { Success = response.Success, Output = $"[Smart Tier - 7-Phase Algorithm]\n\n{response.Message}", Tier = "smart", Parsed = new { response.Action, response.Confidence } };
    }

    private static double GetElapsedMs(long startTimestamp) =>
        (Stopwatch.GetTimestamp() - startTimestamp) * 1000.0 / Stopwatch.Frequency;
}
