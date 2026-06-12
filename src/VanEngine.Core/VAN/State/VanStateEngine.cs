using System.Text.Json;

namespace VanEngine.Core.VAN.State;

public sealed class VanStateEngine : IDisposable
{
    private readonly string _persistPath;
    private readonly Dictionary<string, object> _state;
    private readonly JsonSerializerOptions _jsonOptions;
    private bool _dirty;

    public VanStateEngine(string persistPath)
    {
        _persistPath = persistPath;
        _state = new Dictionary<string, object>();
        _jsonOptions = new JsonSerializerOptions { WriteIndented = true };
    }

    public int Count => _state.Count;
    public IReadOnlyCollection<string> Keys => _state.Keys;

    public T? Get<T>(string key)
    {
        return _state.TryGetValue(key, out var value) && value is T typed ? typed : default;
    }

    public void Set<T>(string key, T value)
    {
        _state[key] = value!;
        _dirty = true;
    }

    public bool Remove(string key) => _state.Remove(key);

    public void ApplyEnvelope(Compiler.AstEnvelope envelope)
    {
        if (envelope.BlockType != VanBlockType.State) return;
        if (envelope.Data.Count < 2) return;

        string key = envelope.Data[0]?.ToString() ?? string.Empty;
        string value = envelope.Data[1]?.ToString() ?? string.Empty;

        if (double.TryParse(value, out double num))
            Set(key, num);
        else if (bool.TryParse(value, out bool flag))
            Set(key, flag);
        else if (long.TryParse(value, out long longVal))
            Set(key, longVal);
        else
            Set(key, value);
    }

    public void Merge(Dictionary<string, object> external)
    {
        foreach (var kvp in external)
        {
            _state[kvp.Key] = kvp.Value;
        }
        _dirty = true;
    }

    public Dictionary<string, object> Snapshot()
    {
        return new Dictionary<string, object>(_state);
    }

    public async Task SaveAsync(CancellationToken ct = default)
    {
        if (!_dirty) return;
        var json = JsonSerializer.Serialize(_state, _jsonOptions);
        var dir = Path.GetDirectoryName(_persistPath);
        if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
            Directory.CreateDirectory(dir);
        await File.WriteAllTextAsync(_persistPath, json, ct);
        _dirty = false;
    }

    public async Task LoadAsync(CancellationToken ct = default)
    {
        if (!File.Exists(_persistPath)) return;
        var json = await File.ReadAllTextAsync(_persistPath, ct);
        var loaded = JsonSerializer.Deserialize<Dictionary<string, object>>(json);
        if (loaded != null)
        {
            _state.Clear();
            foreach (var kvp in loaded)
                _state[kvp.Key] = kvp.Value;
        }
        _dirty = false;
    }

    public void Save()
    {
        if (!_dirty) return;
        var json = JsonSerializer.Serialize(_state, _jsonOptions);
        var dir = Path.GetDirectoryName(_persistPath);
        if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
            Directory.CreateDirectory(dir);
        File.WriteAllText(_persistPath, json);
        _dirty = false;
    }

    public void Load()
    {
        if (!File.Exists(_persistPath)) return;
        var json = File.ReadAllText(_persistPath);
        var loaded = JsonSerializer.Deserialize<Dictionary<string, object>>(json);
        if (loaded != null)
        {
            _state.Clear();
            foreach (var kvp in loaded)
                _state[kvp.Key] = kvp.Value;
        }
        _dirty = false;
    }

    public void Dispose()
    {
        if (_dirty) Save();
        _state.Clear();
    }
}
