using System.Text.Json;

namespace VanEngine.Core.VAN.State;

public sealed class MemoryStore : IDisposable
{
    private readonly string _dbPath;
    private readonly List<MemoryEntry> _entries;

    public MemoryStore(string dbPath)
    {
        _dbPath = dbPath;
        _entries = new List<MemoryEntry>();
    }

    public int Count => _entries.Count;

    public void Index(string hash, string summary, string[] tags)
    {
        var existing = _entries.FindIndex(e => e.Hash == hash);
        var entry = new MemoryEntry
        {
            Hash = hash,
            Summary = summary,
            Tags = tags,
            LastAccessed = DateTime.UtcNow,
            AccessCount = 0
        };

        if (existing >= 0)
        {
            entry.AccessCount = _entries[existing].AccessCount;
            _entries[existing] = entry;
        }
        else
        {
            _entries.Add(entry);
        }
    }

    public List<MemoryEntry> Search(string query, int maxResults = 5)
    {
        var queryLower = query.ToLowerInvariant();
        var queryTags = queryLower.Split(' ', StringSplitOptions.RemoveEmptyEntries);

        var scored = _entries
            .Select(e => new
            {
                Entry = e,
                Score = ComputeRelevance(e, queryLower, queryTags)
            })
            .Where(x => x.Score > 0)
            .OrderByDescending(x => x.Score)
            .Take(maxResults)
            .Select(x =>
            {
                x.Entry.AccessCount++;
                x.Entry.LastAccessed = DateTime.UtcNow;
                return x.Entry;
            })
            .ToList();

        return scored;
    }

    public List<MemoryEntry> GetByTag(string tag, int maxResults = 10)
    {
        return _entries
            .Where(e => e.Tags.Contains(tag, StringComparer.OrdinalIgnoreCase))
            .OrderByDescending(e => e.LastAccessed)
            .Take(maxResults)
            .ToList();
    }

    public List<MemoryEntry> GetAll() => _entries.ToList();

    public void Evict(string hash)
    {
        _entries.RemoveAll(e => e.Hash == hash);
    }

    public async Task SaveAsync(string path, CancellationToken ct = default)
    {
        var json = JsonSerializer.Serialize(_entries, new JsonSerializerOptions { WriteIndented = true });
        await File.WriteAllTextAsync(path, json, ct);
    }

    public async Task LoadAsync(string path, CancellationToken ct = default)
    {
        if (!File.Exists(path)) return;
        var json = await File.ReadAllTextAsync(path, ct);
        var loaded = JsonSerializer.Deserialize<List<MemoryEntry>>(json);
        if (loaded != null)
        {
            _entries.Clear();
            _entries.AddRange(loaded);
        }
    }

    private static double ComputeRelevance(MemoryEntry entry, string queryLower, string[] queryTags)
    {
        double score = 0;

        if (entry.Summary.ToLowerInvariant().Contains(queryLower))
            score += 5;

        foreach (var tag in entry.Tags)
        {
            if (queryLower.Contains(tag.ToLowerInvariant()))
                score += 3;
        }

        foreach (var qt in queryTags)
        {
            foreach (var tag in entry.Tags)
            {
                if (tag.Equals(qt, StringComparison.OrdinalIgnoreCase))
                    score += 10;
            }
        }

        score += Math.Log10(entry.AccessCount + 1) * 0.5;

        return score;
    }

    public void Dispose() => _entries.Clear();
}

public sealed class MemoryEntry
{
    public string Hash { get; set; } = string.Empty;
    public string Summary { get; set; } = string.Empty;
    public string[] Tags { get; set; } = Array.Empty<string>();
    public DateTime LastAccessed { get; set; }
    public int AccessCount { get; set; }
}
