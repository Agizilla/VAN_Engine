using System.Reflection;

namespace VanEngine.Core.VAN;

public sealed class VanCompiler
{
    private readonly Dictionary<string, Func<VanEnvelope, object>> _staticProcessors;
    private readonly IVanExecutor? _externalExecutor;
    private readonly Dictionary<string, Func<VanEnvelope, object>> _dynamicCache;

    public VanCompiler(Dictionary<string, Func<VanEnvelope, object>>? staticProcessors = null, IVanExecutor? externalExecutor = null)
    {
        _staticProcessors = staticProcessors ?? new();
        _externalExecutor = externalExecutor;
        _dynamicCache = new();
    }

    public Func<VanEnvelope, object> Compile(VanEnvelope envelope)
    {
        if (_staticProcessors.TryGetValue(envelope.Carrier, out var processor))
            return processor;

        string key = $"{envelope.Carrier}:{envelope.Modulation}";
        if (_dynamicCache.TryGetValue(key, out var cached))
            return cached;

        var compiled = BuildDynamicDelegate(envelope);
        _dynamicCache[key] = compiled;
        return compiled;
    }

    public bool TryExecute(VanEnvelope envelope, Dictionary<string, object> state, out object? result)
    {
        result = null;
        try
        {
            var processor = Compile(envelope);
            result = processor(envelope);
            return true;
        }
        catch
        {
            return false;
        }
    }

    private Func<VanEnvelope, object> BuildDynamicDelegate(VanEnvelope envelope)
    {
        return env =>
        {
            var result = new Dictionary<string, object>
            {
                ["carrier"] = env.Carrier,
                ["modulation"] = env.Modulation,
                ["q_factor"] = env.QFactor,
                ["dither"] = env.Dither,
                ["data_count"] = env.Data.Count,
                ["block_type"] = env.BlockType.ToString()
            };
            return result;
        };
    }
}
