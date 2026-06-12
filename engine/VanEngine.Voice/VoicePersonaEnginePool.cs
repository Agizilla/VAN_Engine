using System.Collections.Concurrent;

namespace VanEngine.Voice;

public sealed class VoicePersonaEnginePool
{
    public static readonly VoicePersonaEnginePool Instance = new();

    private readonly ConcurrentDictionary<string, VoicePersonaEngine> _engines = new(StringComparer.Ordinal);

    private VoicePersonaEnginePool() { }

    public VoicePersonaEngine GetOrCreate(string personaPath)
    {
        return _engines.GetOrAdd(personaPath, path =>
        {
            var engine = VoicePersonaEngine.FromAdapter(path);
            return engine;
        });
    }

    public void Evict(string personaPath)
    {
        if (_engines.TryRemove(personaPath, out var engine))
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
}
