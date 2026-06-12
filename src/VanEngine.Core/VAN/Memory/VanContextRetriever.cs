using VanEngine.Core.VAN.State;

namespace VanEngine.Core.VAN.Memory;

public sealed class VanContextRetriever
{
    private readonly MemoryStore _store;
    private readonly VanStateEngine _state;

    public VanContextRetriever(MemoryStore store, VanStateEngine state)
    {
        _store = store;
        _state = state;
    }

    public ContextResult Retrieve(string query)
    {
        var result = new ContextResult();

        var memories = _store.Search(query, 3);
        result.Memories.AddRange(memories);

        foreach (var kvp in _state.Snapshot())
        {
            if (kvp.Key.Contains(query, StringComparison.OrdinalIgnoreCase) ||
                query.Contains(kvp.Key, StringComparison.OrdinalIgnoreCase))
            {
                result.StateMatches[kvp.Key] = kvp.Value;
            }
        }

        result.Confidence = ComputeConfidence(result);
        return result;
    }

    public ContextResult RetrieveByTags(string[] tags)
    {
        var result = new ContextResult();
        var memorySet = new HashSet<string>();

        foreach (var tag in tags)
        {
            var tagged = _store.GetByTag(tag, 5);
            foreach (var m in tagged)
            {
                if (memorySet.Add(m.Hash))
                    result.Memories.Add(m);
            }
        }

        result.Confidence = ComputeConfidence(result);
        return result;
    }

    public void IndexFromContext(string key, string value, string[] tags)
    {
        var hash = Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(
                System.Text.Encoding.UTF8.GetBytes($"{key}:{value}")
            )
        ).ToLowerInvariant()[..12];

        _store.Index(hash, value, tags);
    }

    private static double ComputeConfidence(ContextResult result)
    {
        double score = 0;
        score += Math.Min(result.Memories.Count * 20, 60);
        score += Math.Min(result.StateMatches.Count * 15, 40);
        return Math.Clamp(score, 0, 100);
    }
}

public sealed class ContextResult
{
    public List<MemoryEntry> Memories { get; set; } = new();
    public Dictionary<string, object> StateMatches { get; set; } = new();
    public double Confidence { get; set; }
    public bool HasResult => Memories.Count > 0 || StateMatches.Count > 0;
}
