using System.Collections.Concurrent;

namespace VanEngine.Core.Governance;

public sealed class ModuleContext
{
    public string ModuleName { get; }
    public IsolationSpace Workspace { get; } = new();
    public ResourceQuota Quota { get; } = new();
    public bool IsCrossVillage { get; }

    private readonly ConcurrentDictionary<string, object> _privateState = new();

    public ModuleContext(string name, bool isCrossVillage = false)
    {
        ModuleName = name;
        IsCrossVillage = isCrossVillage;
        Workspace.Initialize();
    }

    public void SetPrivateState(string key, object value) =>
        _privateState[key] = value;

    public bool TryGetPrivateState(string key, out object? value) =>
        _privateState.TryGetValue(key, out value);
}

public sealed class IsolationSpace
{
    private readonly ConcurrentDictionary<string, object> _data = new();

    public void Initialize()
    {
        _data.Clear();
    }

    public void Store(string key, object value) => _data[key] = value;

    public bool TryRetrieve(string key, out object? value) =>
        _data.TryGetValue(key, out value);

    public int Count => _data.Count;
}

public sealed class ResourceQuota
{
    public long MaxMemory { get; set; } = 100 * 1024 * 1024;
    public int MaxConcurrency { get; set; } = 1;
    public int MaxFileHandles { get; set; } = 64;
}
