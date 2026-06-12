using System.Collections.Concurrent;

namespace VanEngine.Voice;

public sealed class VoiceLoRAEnginePool
{
    public static readonly VoiceLoRAEnginePool Instance = new();

    private readonly ConcurrentDictionary<string, VoiceLoRAEngine> _engines = new(StringComparer.Ordinal);

    private VoiceLoRAEnginePool() { }

    public VoiceLoRAEngine GetOrCreate(string onnxModelPath, int seed = 0)
    {
        string key = $"{onnxModelPath}:{seed}";
        return _engines.GetOrAdd(key, _ => new VoiceLoRAEngine(onnxModelPath, seed));
    }

    public void Evict(string onnxModelPath, int seed = 0)
    {
        string key = $"{onnxModelPath}:{seed}";
        if (_engines.TryRemove(key, out var engine))
            engine.Dispose();
    }

    public void EvictAll()
    {
        foreach (var kvp in _engines)
        {
            if (_engines.TryRemove(kvp.Key, out var engine))
                engine.Dispose();
        }
    }

    public int Count => _engines.Count;
}
