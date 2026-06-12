using System.Collections.Concurrent;
using System.Text.Json;
using VanEngine.Game.Architecture;

namespace VanEngine.Game.Core;

public sealed class WorkspaceEntry
{
    public string Name { get; set; } = string.Empty;
    public string RootPath { get; set; } = string.Empty;
    public SovereignState State { get; set; } = new();
}

public sealed class WorkspaceRegistry
{
    public List<WorkspaceEntryData> Workspaces { get; set; } = new();
    public string ActiveWorkspace { get; set; } = "default";
}

public sealed class WorkspaceEntryData
{
    public string Name { get; set; } = string.Empty;
    public string RootPath { get; set; } = string.Empty;
}

public sealed class WorkspaceManager
{
    private readonly ConcurrentDictionary<string, WorkspaceEntry> _workspaces = new();
    private string _activeName = "default";
    private readonly object _switchLock = new();

    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        WriteIndented = true,
        IncludeFields = true,
    };

    public string RegistryPath { get; set; } = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "workspace_registry.json");

    public SovereignState ActiveState
    {
        get
        {
            if (_workspaces.TryGetValue(_activeName, out var entry))
                return entry.State;
            return _workspaces.Values.FirstOrDefault()?.State ?? new SovereignState();
        }
    }

    public string ActiveName => _activeName;
    public IEnumerable<string> WorkspaceNames => _workspaces.Keys;

    public WorkspaceManager()
    {
        _workspaces["default"] = new WorkspaceEntry
        {
            Name = "default",
            RootPath = AppDomain.CurrentDomain.BaseDirectory,
            State = new SovereignState(),
        };
    }

    public WorkspaceEntry CreateWorkspace(string name, string rootPath)
    {
        if (_workspaces.ContainsKey(name))
            throw new InvalidOperationException($"Workspace '{name}' already exists.");

        var entry = new WorkspaceEntry
        {
            Name = name,
            RootPath = rootPath,
            State = new SovereignState(),
        };
        entry.State.EnqueueLog($"Workspace '{name}' created at {rootPath}");
        _workspaces[name] = entry;
        SaveRegistry();
        return entry;
    }

    public bool DeleteWorkspace(string name)
    {
        if (name == "default") return false;
        if (_workspaces.TryRemove(name, out _))
        {
            if (_activeName == name)
                _activeName = "default";
            SaveRegistry();
            return true;
        }
        return false;
    }

    public bool SwitchTo(string name)
    {
        if (!_workspaces.ContainsKey(name)) return false;
        lock (_switchLock)
        {
            _activeName = name;
        }
        _workspaces[name].State.EnqueueLog($"Switched to workspace '{name}'");
        return true;
    }

    public WorkspaceEntry? GetWorkspace(string name)
    {
        _workspaces.TryGetValue(name, out var entry);
        return entry;
    }

    public void AddHouseToActive(ProjectHouse house)
    {
        if (_workspaces.TryGetValue(_activeName, out var entry))
            entry.State.AddHouse(house);
    }

    public void SaveRegistry()
    {
        var reg = new WorkspaceRegistry
        {
            ActiveWorkspace = _activeName,
        };
        foreach (var kvp in _workspaces)
        {
            reg.Workspaces.Add(new WorkspaceEntryData
            {
                Name = kvp.Key,
                RootPath = kvp.Value.RootPath,
            });
        }
        string json = JsonSerializer.Serialize(reg, JsonOpts);
        File.WriteAllText(RegistryPath, json);
    }

    public void LoadRegistry()
    {
        if (!File.Exists(RegistryPath)) return;
        try
        {
            string json = File.ReadAllText(RegistryPath);
            var reg = JsonSerializer.Deserialize<WorkspaceRegistry>(json, JsonOpts);
            if (reg == null) return;

            _workspaces.Clear();
            foreach (var w in reg.Workspaces)
            {
                var state = new SovereignState();
                _workspaces[w.Name] = new WorkspaceEntry
                {
                    Name = w.Name,
                    RootPath = w.RootPath,
                    State = state,
                };
            }

            if (_workspaces.IsEmpty)
            {
                _workspaces["default"] = new WorkspaceEntry
                {
                    Name = "default",
                    RootPath = AppDomain.CurrentDomain.BaseDirectory,
                    State = new SovereignState(),
                };
            }

            _activeName = reg.ActiveWorkspace;
            if (!_workspaces.ContainsKey(_activeName))
                _activeName = _workspaces.Keys.First();
        }
        catch { }
    }

    public void ForEachWorkspace(Action<string, SovereignState> action)
    {
        foreach (var kvp in _workspaces)
            action(kvp.Key, kvp.Value.State);
    }

    public Dictionary<(string, string), float> ComputeCrossWorkspaceSimilarity()
    {
        var result = new Dictionary<(string, string), float>();
        var names = _workspaces.Keys.ToList();

        for (int i = 0; i < names.Count; i++)
        {
            for (int j = i + 1; j < names.Count; j++)
            {
                var ws1 = _workspaces[names[i]].State;
                var ws2 = _workspaces[names[j]].State;

                var ns1 = ws1.Houses.Select(h => h.RootNamespace).Where(n => n != null).Distinct().ToList();
                var ns2 = ws2.Houses.Select(h => h.RootNamespace).Where(n => n != null).Distinct().ToList();

                float score = 0f;
                int pairs = 0;
                foreach (var a in ns1)
                {
                    foreach (var b in ns2)
                    {
                        score += ComputeLevenshteinSimilarity(a, b);
                        pairs++;
                    }
                }
                result[(names[i], names[j])] = pairs > 0 ? score / pairs : 0f;
            }
        }
        return result;
    }

    // ── Trade Routes ─────────────────────────────────────────────────
    public void EstablishTradeRoute(string from, string to)
    {
        if (!_workspaces.ContainsKey(from) || !_workspaces.ContainsKey(to)) return;
        if (from == to) return;

        var stateFrom = _workspaces[from].State;
        var stateTo = _workspaces[to].State;

        var nsFrom = stateFrom.Houses.Select(h => h.RootNamespace).Distinct().ToList();
        var nsTo = stateTo.Houses.Select(h => h.RootNamespace).Distinct().ToList();

        float efficiency = 1f;
        int shared = 0;
        foreach (var n in nsFrom)
            if (nsTo.Contains(n)) shared++;

        if (shared > 0) efficiency += shared * 0.5f;

        var route = new TradeRoute
        {
            Name = $"{from}→{to}",
            FromWorkspace = from,
            ToWorkspace = to,
            Efficiency = Math.Min(efficiency, 5f),
            IsActive = true,
        };

        stateFrom.AddTradeRoute(route);
        stateFrom.EnqueueLog($"Trade route established: {from} → {to} (eff: {route.Efficiency:F1})");
        stateFrom.AddTimelineEntry(stateFrom.Year, "event", $"Trade route {from}→{to} opened (eff:{route.Efficiency:F1})", "trade");

        bool fromError = stateFrom.Houses.Any(h => h.CurrentState == Architecture.BuildState.Error);
        bool toError = stateTo.Houses.Any(h => h.CurrentState == Architecture.BuildState.Error);
        if (fromError || toError)
        {
            route.IsActive = false;
            stateFrom.EnqueueLog($"Trade route {route.Name} severed: Error state detected");
        }
    }

    public void CheckTradeRouteStatus()
    {
        foreach (var kvp in _workspaces)
        {
            foreach (var route in kvp.Value.State.GetTradeRoutes())
            {
                if (!route.IsActive) continue;
                if (!_workspaces.ContainsKey(route.ToWorkspace)) { route.IsActive = false; continue; }

                var toState = _workspaces[route.ToWorkspace].State;
                bool toError = toState.Houses.Any(h => h.CurrentState == Architecture.BuildState.Error);
                if (toError)
                {
                    route.IsActive = false;
                    kvp.Value.State.EnqueueLog($"Trade route '{route.Name}' severed: destination in Error state");
                }
            }
        }
    }

    public void TickTradeRoutes()
    {
        foreach (var kvp in _workspaces)
        {
            kvp.Value.State.TickTradeRoutes();

            foreach (var route in kvp.Value.State.GetTradeRoutes())
            {
                if (!route.IsActive) continue;
                if (_workspaces.TryGetValue(route.FromWorkspace, out var fromWs) &&
                    _workspaces.TryGetValue(route.ToWorkspace, out var toWs))
                {
                    var fromHouses = fromWs.State.Houses;
                    var toHouses = toWs.State.Houses;

                    if (fromHouses.Count > 0 && toHouses.Count > 0)
                    {
                        var fromCenter = fromHouses.Average(h => h.Position.X + h.BoundingBoxSize.X / 2);
                        var fromCenterY = fromHouses.Average(h => h.Position.Y + h.BoundingBoxSize.Y / 2);
                        var toCenter = toHouses.Average(h => h.Position.X + h.BoundingBoxSize.X / 2);
                        var toCenterY = toHouses.Average(h => h.Position.Y + h.BoundingBoxSize.Y / 2);

                        float t = route.Progress;
                        route.PacketX = fromCenter + (toCenter - fromCenter) * t;
                        route.PacketY = fromCenterY + (toCenterY - fromCenterY) * t;
                    }
                }
            }
        }
    }

    public void DrawTradeRoutes()
    {
        foreach (var kvp in _workspaces)
        {
            foreach (var route in kvp.Value.State.GetTradeRoutes())
            {
                if (!route.IsActive) continue;
                if (!_workspaces.TryGetValue(route.FromWorkspace, out var fromWs) ||
                    !_workspaces.TryGetValue(route.ToWorkspace, out var toWs)) continue;

                var fromHouses = fromWs.State.Houses;
                var toHouses = toWs.State.Houses;
                if (fromHouses.Count == 0 || toHouses.Count == 0) continue;

                var f = fromHouses.First();
                var t = toHouses.First();
            }
        }
    }

    private static float ComputeLevenshteinSimilarity(string a, string b)
    {
        if (string.IsNullOrEmpty(a) || string.IsNullOrEmpty(b)) return 0;
        int distance = LevenshteinDistance(a, b);
        int maxLen = Math.Max(a.Length, b.Length);
        return 1.0f - (float)distance / maxLen;
    }

    private static int LevenshteinDistance(string s, string t)
    {
        int n = s.Length, m = t.Length;
        var d = new int[n + 1, m + 1];
        for (int i = 0; i <= n; i++) d[i, 0] = i;
        for (int j = 0; j <= m; j++) d[0, j] = j;
        for (int i = 1; i <= n; i++)
            for (int j = 1; j <= m; j++)
                d[i, j] = Math.Min(
                    Math.Min(d[i - 1, j] + 1, d[i, j - 1] + 1),
                    d[i - 1, j - 1] + (s[i - 1] == t[j - 1] ? 0 : 1));
        return d[n, m];
    }
}
