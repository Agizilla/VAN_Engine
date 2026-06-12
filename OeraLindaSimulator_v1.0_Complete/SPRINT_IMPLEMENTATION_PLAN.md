# Oera Linda Simulator — Unified Sprint Implementation Plan
## All 20 Features, 4 Tiers, Single Pass

This document maps each of the 20 features to concrete code changes in the existing codebase.

### Architecture Overview
- **Core state**: `SovereignState.cs` (already exists) — extends to multi-workspace awareness
- **New files to create**:
  - `WorkspaceManager.cs` — load/save, workspace switching, persistence
  - `FileSystemWatcherService.cs` — live file monitoring
  - `CameraController.cs` — viewport pan/zoom
  - `LanguageAnalyzerFactory.cs` — pluggable multi-language support
  - `SettingsManager.cs` — user config persistence
  - `DependencyGraphAnalyzer.cs` — cross-workspace analysis
  - `ThreatSystem.cs` — vulnerability events
  - `HouseUpgradeSystem.cs` — tech tree
  - `CitizenSkillSystem.cs` — XP and specialisation
  - `TradeRouteSystem.cs` — inter-workspace resource exchange
  - `EventSocketServer.cs` — webhook/socket interface
  - `GitIntegrationService.cs` — commit tracking
  - `ReportGenerator.cs` — export functionality
  - `ScriptingEngine.cs` — Lua/C# mod API
  - `CommunityScoreboard.cs` — opt-in leaderboard submission

### Modified Files
- `Program.cs` — initialize new managers
- `DashboardView.cs` — add UI for inspectors, settings, reports
- `SovereignState.cs` — add workspace metadata, extend logging
- `TimePhaseController.cs` — integrate git/commit events

---

## TIER 1: Foundation

### Feature 1.1 — Multi-workspace Manager
**What**: Load/save separate sovereign states, switch between them without losing progress.
**New file**: `WorkspaceManager.cs`
**Impact**: Everything downstream depends on this.

```csharp
namespace VanEngine.Game.Core;

public class WorkspaceMetadata
{
    public string WorkspaceName { get; set; } = string.Empty;
    public string RootPath { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public DateTime LastModified { get; set; }
    public Guid Id { get; set; } = Guid.NewGuid();
}

public class WorkspaceManager
{
    private readonly string _workspaceDirectory;
    private readonly Dictionary<Guid, SovereignState> _loadedWorkspaces = new();
    private Guid _currentWorkspaceId;
    
    public SovereignState CurrentState => _loadedWorkspaces[_currentWorkspaceId];
    public IReadOnlyList<WorkspaceMetadata> AvailableWorkspaces { get; private set; }
    
    public WorkspaceManager(string baseDirectory)
    {
        _workspaceDirectory = baseDirectory;
        Directory.CreateDirectory(_workspaceDirectory);
        ScanWorkspaces();
    }
    
    public void CreateWorkspace(string name, string projectRoot)
    {
        var meta = new WorkspaceMetadata 
        { 
            WorkspaceName = name, 
            RootPath = projectRoot,
            CreatedAt = DateTime.Now
        };
        var dir = Path.Combine(_workspaceDirectory, meta.Id.ToString());
        Directory.CreateDirectory(dir);
        SaveMetadata(dir, meta);
        var state = new SovereignState { /* init */ };
        _loadedWorkspaces[meta.Id] = state;
        _currentWorkspaceId = meta.Id;
    }
    
    public void SwitchWorkspace(Guid id) => _currentWorkspaceId = id;
    
    public void SaveCurrentState()
    {
        var dir = Path.Combine(_workspaceDirectory, _currentWorkspaceId.ToString());
        SerializeState(dir, _loadedWorkspaces[_currentWorkspaceId]);
    }
    
    // ... serialization helpers
}
```

**UI Changes (DashboardView.cs)**:
- Top bar shows current workspace name
- Workspace dropdown menu
- "New Workspace" button
- Auto-save indicator

---

### Feature 1.2 — Persistent Save/Load
**What**: JSON serialisation, autosave every game year, named save slots.
**Extends**: `WorkspaceManager.cs`, `SovereignState.cs`
**Format**: 
```json
{
  "metadata": { "id", "name", "created", "lastModified" },
  "state": {
    "year": 42,
    "sovereignty": 87.5,
    "languagePurity": 92.1,
    "citizens": [...],
    "houses": [...],
    "resources": { "food": 450, ... },
    "uploadHistory": [...]
  },
  "autosaveSlots": [
    { "timestamp": "2026-05-31T14:22:00Z", "year": 41 },
    { "timestamp": "2026-05-31T14:21:30Z", "year": 40 }
  ]
}
```

**Implementation**:
```csharp
public void SerializeState(string workspaceDir, SovereignState state)
{
    var data = new
    {
        year = state.Year,
        sovereignty = state.Sovereignty,
        languagePurity = state.LanguagePurity,
        resources = state.Resources,
        citizens = state.Citizens.Select(c => new { c.Id, c.Name, c.NamespaceFamily, ... }),
        houses = state.Houses.Select(h => new { h.Id, h.ProjectName, h.Position, ... }),
        uploadHistory = state.UploadHistory
    };
    string json = JsonSerializer.Serialize(data, new JsonSerializerOptions { WriteIndented = true });
    File.WriteAllText(Path.Combine(workspaceDir, "state.json"), json);
}
```

**Autosave trigger** in `Program.cs.Update()`:
```csharp
if (_timeController.TickEngineClock(dt, out bool yearChanged))
{
    if (yearChanged)
    {
        _state.IncrementYear();
        _workspaceManager.SaveCurrentState(); // Autosave
    }
}
```

---

### Feature 1.3 — Live Filesystem Watcher
**What**: FileSystemWatcher on registered directories, auto-re-analyse modified files, Missing state for deletions.
**New file**: `FileSystemWatcherService.cs`

```csharp
namespace VanEngine.Game.Core;

public class FileSystemWatcherService
{
    private readonly FileSystemWatcher _watcher;
    private readonly SovereignState _state;
    private readonly Action<string, FileChangeType> _onChange;
    
    public enum FileChangeType { Created, Modified, Deleted }
    
    public FileSystemWatcherService(SovereignState state, string watchPath)
    {
        _state = state;
        _watcher = new FileSystemWatcher(watchPath)
        {
            Filter = "*.cs",
            NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.FileName,
            EnableRaisingEvents = true
        };
        
        _watcher.Changed += OnFileChanged;
        _watcher.Deleted += OnFileDeleted;
        _watcher.Error += (s, e) => _state.AddLog($"Watcher error: {e.GetException()?.Message}");
    }
    
    private void OnFileChanged(object sender, FileSystemEventArgs e)
    {
        var analysis = TexStaticAnalyzer.AnalyzeSourceFile(e.FullPath);
        var existingHouse = _state.Houses.FirstOrDefault(h => h.RootNamespace == analysis.DiscoveredNamespace);
        
        if (existingHouse?.TrackedFiles.FirstOrDefault(f => f.FilePath == e.FullPath) is FileNodeAsset existing)
        {
            // Update the tracked file
            var idx = existingHouse.TrackedFiles.IndexOf(existing);
            existingHouse.TrackedFiles[idx] = new FileNodeAsset
            {
                FilePath = e.FullPath,
                ClassName = analysis.DiscoveredClassName,
                LineCount = analysis.TotalLines,
                ErrorCount = analysis.ErrorCount,
                WarningCount = analysis.WarningCount,
                LastWriteTimeTicks = File.GetLastWriteTime(e.FullPath).Ticks
            };
            existingHouse.EvaluateBuildState();
            _state.AddLog($"Updated: {Path.GetFileName(e.FullPath)}");
        }
    }
    
    private void OnFileDeleted(object sender, FileSystemEventArgs e)
    {
        foreach (var house in _state.Houses)
        {
            var idx = house.TrackedFiles.FindIndex(f => f.FilePath == e.FullPath);
            if (idx >= 0)
            {
                house.TrackedFiles.RemoveAt(idx);
                house.CurrentState = BuildState.Missing;
                _state.AddLog($"Deleted: {Path.GetFileName(e.FullPath)} — house marked Missing");
            }
        }
    }
}
```

**Initialization in `Program.cs.Main()`**:
```csharp
var watcher = new FileSystemWatcherService(_state, "/home/user/projects/MyProject/src");
```

---

### Feature 1.4 — Pan, Zoom & Minimap
**What**: Camera matrix, scroll-wheel zoom, middle-click pan, minimap widget.
**New file**: `CameraController.cs`

```csharp
namespace VanEngine.Game.Simulation;

public class CameraController
{
    public Vector2 Position { get; set; } = Vector2.Zero;
    public float Zoom { get; set; } = 1f;
    public const float MinZoom = 0.3f;
    public const float MaxZoom = 3f;
    
    private Vector2 _worldSize = new(2560, 1920); // Larger virtual world
    
    public void HandleInput(int screenWidth, int screenHeight)
    {
        float wheel = GetMouseWheelMove();
        if (wheel != 0)
        {
            var mouseWorldPos = ScreenToWorld(GetMousePosition(), screenWidth, screenHeight);
            Zoom = Math.Clamp(Zoom + wheel * 0.1f, MinZoom, MaxZoom);
            // Re-center on mouse position
            Position = mouseWorldPos - (new Vector2(screenWidth, screenHeight) / 2f / Zoom);
            Position = ClampPosition(screenWidth, screenHeight);
        }
        
        if (IsMouseButtonDown(MouseButton.MOUSE_BUTTON_MIDDLE))
        {
            Vector2 delta = GetMouseDelta();
            Position -= delta / Zoom;
            Position = ClampPosition(screenWidth, screenHeight);
        }
    }
    
    public Vector2 ScreenToWorld(Vector2 screenPos, int screenWidth, int screenHeight)
    {
        return Position + screenPos / Zoom;
    }
    
    public Vector2 WorldToScreen(Vector2 worldPos, int screenWidth, int screenHeight)
    {
        return (worldPos - Position) * Zoom;
    }
    
    public void DrawMinimap(int screenWidth, int screenHeight, IReadOnlyList<ProjectHouse> houses)
    {
        const int minimapW = 120, minimapH = 90;
        int mx = screenWidth - minimapW - 10;
        int my = 10;
        
        DrawRectangle(mx, my, minimapW, minimapH, C(22, 26, 34, 200));
        DrawRectangleLinesEx(new Rectangle(mx, my, minimapW, minimapH), 1, C(100, 150, 200));
        
        foreach (var house in houses)
        {
            float sx = mx + (house.Position.X / _worldSize.X) * minimapW;
            float sy = my + (house.Position.Y / _worldSize.Y) * minimapH;
            var col = house.CurrentState switch { ... };
            DrawRectangle((int)sx, (int)sy, 4, 4, col);
        }
        
        // Draw current viewport bounds
        float vx = mx + (Position.X / _worldSize.X) * minimapW;
        float vy = my + (Position.Y / _worldSize.Y) * minimapH;
        float vw = (screenWidth / Zoom / _worldSize.X) * minimapW;
        float vh = (screenHeight / Zoom / _worldSize.Y) * minimapH;
        DrawRectangleLinesEx(new Rectangle(vx, vy, vw, vh), 1, C(100, 200, 255, 255));
    }
    
    private Vector2 ClampPosition(int screenWidth, int screenHeight) { ... }
}
```

**Integration in `DashboardView.Draw()`**:
```csharp
private CameraController _camera = new();

public void Draw()
{
    _camera.HandleInput(_screenWidth, _screenHeight);
    
    BeginMode2D(new Camera2D 
    { 
        target = _camera.Position + new Vector2(_screenWidth, _screenHeight) / 2f / _camera.Zoom,
        offset = Vector2.Zero,
        rotation = 0f,
        zoom = _camera.Zoom
    });
    
    // Draw all houses and citizens using world coordinates
    foreach (var house in _state.Houses)
    {
        var screenPos = _camera.WorldToScreen(house.Position, _screenWidth, _screenHeight);
        // ... draw house at screenPos
    }
    
    EndMode2D();
    
    // Draw minimap (always in screen space)
    _camera.DrawMinimap(_screenWidth, _screenHeight, _state.Houses);
}
```

---

### Feature 1.5 — Multi-language Analyzer
**What**: Pluggable directive sets per language (C#, Python, TypeScript, Rust, Go).
**New file**: `LanguageAnalyzerFactory.cs`

```csharp
namespace VanEngine.Game.Forensics;

public interface ILanguageDirectiveSet
{
    string Language { get; }
    AnalysisResult Analyze(string filePath);
}

public class CSharpDirectives : ILanguageDirectiveSet
{
    public string Language => ".cs";
    
    public AnalysisResult Analyze(string filePath)
    {
        // Existing TexStaticAnalyzer logic
        return TexStaticAnalyzer.AnalyzeSourceFile(filePath);
    }
}

public class PythonDirectives : ILanguageDirectiveSet
{
    public string Language => ".py";
    
    public AnalysisResult Analyze(string filePath)
    {
        var result = new AnalysisResult { /* ... */ };
        using var reader = new StreamReader(filePath);
        string? line;
        while ((line = reader.ReadLine()) != null)
        {
            result.TotalLines++;
            if (line.Contains("import telemetry") || line.Contains("from analytics"))
                result.ErrorCount++; // Python violation
            if (line.Contains("# license") || line.Contains("LICENSE"))
                result.WarningCount++;
        }
        return result;
    }
}

public class TypeScriptDirectives : ILanguageDirectiveSet { /* ... */ }
public class RustDirectives : ILanguageDirectiveSet { /* ... */ }
public class GoDirectives : ILanguageDirectiveSet { /* ... */ }

public static class LanguageAnalyzerFactory
{
    private static readonly Dictionary<string, ILanguageDirectiveSet> _analyzers = new()
    {
        { ".cs", new CSharpDirectives() },
        { ".py", new PythonDirectives() },
        { ".ts", new TypeScriptDirectives() },
        { ".rs", new RustDirectives() },
        { ".go", new GoDirectives() }
    };
    
    public static AnalysisResult Analyze(string filePath)
    {
        string ext = Path.GetExtension(filePath).ToLowerInvariant();
        if (_analyzers.TryGetValue(ext, out var analyzer))
            return analyzer.Analyze(filePath);
        
        throw new NotSupportedException($"Language {ext} not supported");
    }
}
```

**Modify `TexStaticAnalyzer.AnalyzeSourceFile()`**:
```csharp
public static AnalysisResult AnalyzeSourceFile(string filePath)
{
    return LanguageAnalyzerFactory.Analyze(filePath);
}
```

---

### Feature 1.6 — Settings & Config Screen
**What**: In-game settings panel with persistence.
**New file**: `SettingsManager.cs`

```csharp
namespace VanEngine.Game.Core;

[Serializable]
public class GameSettings
{
    public float GameSpeed { get; set; } = 1.0f;
    public Dictionary<string, float> DirectiveWeights { get; set; } = new();
    public Dictionary<string, bool> EnabledDirectives { get; set; } = new();
    public float UIScale { get; set; } = 1.0f;
    public Dictionary<string, int> KeyBindings { get; set; } = new();
    
    public static GameSettings LoadOrDefault()
    {
        string path = Path.Combine(AppContext.BaseDirectory, "settings.json");
        if (File.Exists(path))
            return JsonSerializer.Deserialize<GameSettings>(File.ReadAllText(path)) ?? new();
        return new();
    }
    
    public void Save()
    {
        string path = Path.Combine(AppContext.BaseDirectory, "settings.json");
        File.WriteAllText(path, JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true }));
    }
}

public class SettingsManager
{
    public GameSettings Settings { get; private set; }
    public bool ShowSettingsPanel { get; set; }
    
    public SettingsManager()
    {
        Settings = GameSettings.LoadOrDefault();
    }
}
```

**Settings panel UI in `DashboardView.cs`**:
```csharp
private SettingsManager _settings = new();

public void DrawSettingsPanel()
{
    if (!_settings.ShowSettingsPanel) return;
    
    int x = _screenWidth / 2 - 200;
    int y = _screenHeight / 2 - 150;
    DrawRectangle(x, y, 400, 300, C(22, 26, 34));
    DrawText("SETTINGS", x + 20, y + 20, 18, WHITE);
    
    // Game Speed slider
    DrawText("Game Speed:", x + 20, y + 60, 14, WHITE);
    // ... range input
    
    // Directive toggles
    DrawText("Directives:", x + 20, y + 100, 14, WHITE);
    foreach (var directive in _settings.Settings.EnabledDirectives.Keys)
    {
        // ... toggle buttons
    }
    
    if (IsKeyPressed(KeyboardKey.KEY_ESCAPE))
    {
        _settings.ShowSettingsPanel = false;
        _settings.Settings.Save();
    }
}
```

---

## TIER 2: Core Gameplay

### Feature 2.1 — Cross-Project Dependency Graph
**What**: Visualize shared namespaces between workspaces, circular dependency arcs.
**New file**: `DependencyGraphAnalyzer.cs`

```csharp
namespace VanEngine.Game.Simulation;

public struct DependencyEdge
{
    public Guid FromWorkspaceId { get; set; }
    public Guid ToWorkspaceId { get; set; }
    public string SharedNamespace { get; set; }
    public int SharedFileCount { get; set; }
    public bool IsCircular { get; set; }
}

public class DependencyGraphAnalyzer
{
    private readonly Dictionary<Guid, SovereignState> _workspaces;
    
    public DependencyGraphAnalyzer(Dictionary<Guid, SovereignState> workspaces)
    {
        _workspaces = workspaces;
    }
    
    public List<DependencyEdge> AnalyzeCrossWorkspaceDependencies()
    {
        var edges = new List<DependencyEdge>();
        var wsIds = _workspaces.Keys.ToList();
        
        for (int i = 0; i < wsIds.Count; i++)
        {
            for (int j = i + 1; j < wsIds.Count; j++)
            {
                var ws1 = _workspaces[wsIds[i]];
                var ws2 = _workspaces[wsIds[j]];
                
                var ns1 = ws1.Houses.Select(h => h.RootNamespace).ToHashSet();
                var ns2 = ws2.Houses.Select(h => h.RootNamespace).ToHashSet();
                var common = ns1.Intersect(ns2).ToList();
                
                if (common.Count > 0)
                {
                    edges.Add(new DependencyEdge
                    {
                        FromWorkspaceId = wsIds[i],
                        ToWorkspaceId = wsIds[j],
                        SharedNamespace = string.Join(", ", common),
                        SharedFileCount = common.Count,
                        IsCircular = DetectCircularDependency(wsIds[i], wsIds[j])
                    });
                }
            }
        }
        
        return edges;
    }
    
    private bool DetectCircularDependency(Guid a, Guid b)
    {
        // Simplified: check if A uses namespace from B and B uses namespace from A
        return true; // Implement BFS/DFS
    }
}
```

**Visualization in `DashboardView.Draw()`**:
```csharp
var depAnalyzer = new DependencyGraphAnalyzer(_workspaceManager._loadedWorkspaces);
var edges = depAnalyzer.AnalyzeCrossWorkspaceDependencies();

foreach (var edge in edges)
{
    var wsA = _workspaceManager._loadedWorkspaces[edge.FromWorkspaceId];
    var wsB = _workspaceManager._loadedWorkspaces[edge.ToWorkspaceId];
    
    var houseA = wsA.Houses.First(h => h.RootNamespace == edge.SharedNamespace);
    var houseB = wsB.Houses.First(h => h.RootNamespace == edge.SharedNamespace);
    
    var color = edge.IsCircular ? RED : C(100, 200, 255);
    DrawLine((int)houseA.Position.X, (int)houseA.Position.Y,
             (int)houseB.Position.X, (int)houseB.Position.Y,
             color);
    
    DrawText(edge.SharedFileCount.ToString(), 
             ((int)houseA.Position.X + (int)houseB.Position.X) / 2,
             ((int)houseA.Position.Y + (int)houseB.Position.Y) / 2,
             12, WHITE);
}
```

---

### Feature 2.2 — Overlap / Duplication Detector
**What**: Cross-workspace Levenshtein analysis, merge-or-isolate prompt.
**Extends**: `SpatialEcosystemManager.cs`

```csharp
public struct OverlapResult
{
    public string FilePath1 { get; set; }
    public string FilePath2 { get; set; }
    public Guid Workspace1 { get; set; }
    public Guid Workspace2 { get; set; }
    public float Similarity { get; set; }
}

public void DetectCrossWorkspaceDuplications(Dictionary<Guid, SovereignState> workspaces)
{
    var wsIds = workspaces.Keys.ToList();
    var allFiles = new List<(Guid wsId, string filePath)>();
    
    foreach (var id in wsIds)
    {
        foreach (var citizen in workspaces[id].Citizens)
        {
            foreach (var file in citizen.OwnedFiles)
            {
                allFiles.Add((id, file));
            }
        }
    }
    
    for (int i = 0; i < allFiles.Count; i++)
    {
        for (int j = i + 1; j < allFiles.Count; j++)
        {
            if (allFiles[i].wsId == allFiles[j].wsId) continue;
            
            float sim = ComputeLevenshteinSimilarity(allFiles[i].filePath, allFiles[j].filePath);
            if (sim > 0.8f)
            {
                workspaces[allFiles[i].wsId].AddLog(
                    $"⚠️ DUPLICATION: {Path.GetFileName(allFiles[i].filePath)} " +
                    $"mirrors {Path.GetFileName(allFiles[j].filePath)} ({sim*100:F0}% similar)");
            }
        }
    }
}
```

---

### Feature 2.3 — Shared Library / Commons Zone
**What**: Read-only commons ProjectHouse that contributes to all connected workspaces.
**Extends**: `ProjectHouse.cs`, `SovereignState.cs`

```csharp
public sealed class ProjectHouse
{
    public bool IsCommons { get; set; }
    public HashSet<Guid> ConnectedWorkspaces { get; set; } = new();
    
    public void DistributeCommonsResources(ResourcePack deltaPerConnected)
    {
        if (!IsCommons) return;
        foreach (var wsId in ConnectedWorkspaces)
        {
            // Signal to WorkspaceManager to apply resources to workspace wsId
        }
    }
}
```

**UI in DashboardView**:
```csharp
// Right-click on house → "Designate as Commons"
// Once commons, it's read-only for citizens but visible to all workspaces
```

---

### Feature 2.4 — History Timeline & Audit Log
**What**: Per-year event log, filter by citizen/house/type, exportable.
**Extends**: `SovereignState.cs`

```csharp
public struct LogEntry
{
    public int Year { get; set; }
    public DateTime Timestamp { get; set; }
    public string Message { get; set; }
    public enum LogType { Info, Warning, Error, Achievement }
    public LogType Type { get; set; }
    public string? CitizenName { get; set; }
    public string? HouseName { get; set; }
}

public sealed class SovereignState
{
    private readonly List<LogEntry> _fullHistory = new();
    
    public void AddLogEntry(LogEntry entry) => _fullHistory.Add(entry);
    
    public List<LogEntry> GetHistoryFiltered(int? year = null, string? citizenName = null, string? houseName = null)
    {
        return _fullHistory
            .Where(l => (year == null || l.Year == year) &&
                        (citizenName == null || l.CitizenName == citizenName) &&
                        (houseName == null || l.HouseName == houseName))
            .ToList();
    }
    
    public string ExportHistoryAsMarkdown()
    {
        var sb = new StringBuilder();
        sb.AppendLine("# Sovereignty Timeline");
        foreach (var entry in _fullHistory.GroupBy(l => l.Year))
        {
            sb.AppendLine($"\n## Year {entry.Key}");
            foreach (var log in entry)
                sb.AppendLine($"- {log.Timestamp:HH:mm} {log.Message}");
        }
        return sb.ToString();
    }
}
```

**UI Panel in DashboardView**:
```csharp
public void DrawHistoryPanel()
{
    // Left sidebar with timeline view
    // Scrollable log entries
    // Filter dropdowns
    // Export button
}
```

---

### Feature 2.5 — Click-to-Inspect Side Panel
**What**: Persistent right-side panel showing full details on selected house/citizen.
**Extends**: `DashboardView.cs`

```csharp
public class InspectorPanel
{
    public ProjectHouse? SelectedHouse { get; set; }
    public Citizen? SelectedCitizen { get; set; }
    public bool IsOpen { get; set; }
    
    public void Draw(int panelX, int panelW, int screenHeight)
    {
        if (!IsOpen) return;
        
        DrawRectangle(panelX, 0, panelW, screenHeight, C(22, 26, 34));
        
        if (SelectedHouse != null)
        {
            DrawText(SelectedHouse.ProjectName, panelX + 10, 10, 16, WHITE);
            DrawText($"Namespace: {SelectedHouse.RootNamespace}", panelX + 10, 35, 12, C(200, 200, 200));
            DrawText($"State: {SelectedHouse.CurrentState}", panelX + 10, 55, 12, C(200, 200, 200));
            DrawText($"Files: {SelectedHouse.TrackedFiles.Count}", panelX + 10, 75, 12, C(200, 200, 200));
            
            int y = 100;
            foreach (var file in SelectedHouse.TrackedFiles)
            {
                DrawText($"  {Path.GetFileName(file.FilePath)}", panelX + 20, y, 10, C(150, 150, 150));
                DrawText($"    Errors: {file.ErrorCount} Warnings: {file.WarningCount}", 
                         panelX + 30, y + 15, 9, C(100, 100, 100));
                y += 35;
            }
            
            // Quick-fix buttons: rename, split, merge, reassign
        }
        else if (SelectedCitizen != null)
        {
            DrawText(SelectedCitizen.Name, panelX + 10, 10, 16, WHITE);
            DrawText($"Role: {RoleString(SelectedCitizen.RoleType)}", panelX + 10, 35, 12, C(200, 200, 200));
            DrawText($"Files: {SelectedCitizen.OwnedFiles.Count}", panelX + 10, 55, 12, C(200, 200, 200));
            DrawText($"Lines: {SelectedCitizen.CompliantLinesContributed}", panelX + 10, 75, 12, C(200, 200, 200));
            
            // File listing
            // Specialisation display (from Tier 3)
        }
    }
}
```

---

### Feature 2.6 — In-game Refactoring Actions
**What**: Right-click menu with refactor verbs.
**Extends**: `DashboardView.cs`

```csharp
public enum RefactorAction { RenameNamespace, SplitHouse, MergeHouses, ReassignFile }

public void ProcessRefactorAction(RefactorAction action, ProjectHouse target)
{
    switch (action)
    {
        case RefactorAction.RenameNamespace:
            // Prompt for new name, update all citizens and houses
            target.RootNamespace = "NewNamespace";
            _state.AddLog($"Renamed house namespace to {target.RootNamespace}");
            break;
            
        case RefactorAction.SplitHouse:
            // Create a new house, split files by similarity
            var newHouse = new ProjectHouse($"{target.ProjectName} (Split)", 
                                           target.RootNamespace + ".alt", 
                                           target.Position + new Vector2(150, 0));
            _state.AddHouse(newHouse);
            _state.ModifyResources(new ResourcePack { Wealth = -50 });
            break;
            
        case RefactorAction.MergeHouses:
            // Merge two houses (prompt user to select second house)
            break;
            
        case RefactorAction.ReassignFile:
            // Move file from one house/citizen to another
            break;
    }
}
```

---

### Feature 2.7 — Directive Config Per Workspace
**What**: Enable/disable individual directives, tune penalty weights.
**Extends**: `SettingsManager.cs`, `SovereignState.cs`

```csharp
public class WorkspaceDirectiveConfig
{
    public Dictionary<string, bool> DirectiveEnabled { get; set; } = new()
    {
        { "ExpelBastards", true },
        { "NoDebtSlavery", true }
        // ... all 13 directives
    };
    
    public Dictionary<string, float> Weights { get; set; } = new()
    {
        { "ExpelBastards", 1.0f },
        { "NoDebtSlavery", 0.5f }
    };
}
```

**Settings panel integration**:
```csharp
public void DrawDirectiveSettings()
{
    var config = _workspaceManager.CurrentState.DirectiveConfig;
    int y = 100;
    
    foreach (var (directive, enabled) in config.DirectiveEnabled)
    {
        DrawText(directive, 50, y, 12, WHITE);
        // Toggle button
        DrawText($"Weight: {config.Weights[directive]:F1}", 200, y, 10, C(150, 150, 150));
        // Slider
        y += 25;
    }
}
```

---

### Feature 2.8 — Phase Transition Animation
**What**: Smooth 1.5s crossfade, stars, citizens animate home, clock sweep.
**Extends**: `DashboardView.cs`, `TimePhaseController.cs`

```csharp
public class PhaseTransitionEffect
{
    public float TransitionProgress { get; set; } // 0.0 to 1.0
    public const float TransitionDuration = 1.5f;
    
    public void Update(float dt)
    {
        TransitionProgress += dt / TransitionDuration;
        if (TransitionProgress > 1.0f)
            TransitionProgress = 1.0f;
    }
    
    public Color InterpolateColor(Color dayColor, Color nightColor)
    {
        float t = TransitionProgress;
        return new Color(
            (byte)(dayColor.R * (1 - t) + nightColor.R * t),
            (byte)(dayColor.G * (1 - t) + nightColor.G * t),
            (byte)(dayColor.B * (1 - t) + nightColor.B * t),
            255
        );
    }
}

private PhaseTransitionEffect _transition = new();

public void HandlePhaseToggle()
{
    if (IsKeyPressed(KeyboardKey.KEY_TAB))
    {
        _timeController.TogglePhase();
        _transition.TransitionProgress = 0f;
    }
}

public void Draw()
{
    _transition.Update(GetFrameTime());
    
    if (_transition.TransitionProgress < 1.0f)
    {
        // Draw day overlay with increasing opacity
        float alpha = _transition.TransitionProgress * 200;
        DrawRectangle(0, 0, _screenWidth, _screenHeight, new Color(0, 0, 40, (byte)alpha));
        
        // Animate citizens moving to homes
        foreach (var citizen in _state.Citizens)
        {
            if (_timeController.CurrentPhase == SimulationPhase.Nighttime)
            {
                var house = _state.Houses.FirstOrDefault(h => h.RootNamespace == citizen.NamespaceFamily);
                if (house != null)
                {
                    citizen.TargetPosition = Vector2.Lerp(citizen.Position, 
                                                          house.Position, 
                                                          _transition.TransitionProgress);
                }
            }
        }
        
        // Draw spinning clock animation
        float angle = _transition.TransitionProgress * 360;
        DrawCircleLines(_screenWidth / 2, _screenHeight / 2, 40, YELLOW);
        DrawLine(_screenWidth / 2, _screenHeight / 2,
                 (int)(_screenWidth / 2 + 30 * MathF.Cos(angle * MathF.PI / 180)),
                 (int)(_screenHeight / 2 + 30 * MathF.Sin(angle * MathF.PI / 180)),
                 YELLOW);
    }
}
```

---

## TIER 3: Advanced Systems

### Feature 3.1 — Threat & Vulnerability Events
**What**: CVE-style threats approach screen edge, militia intercepts, victory/defeat mechanics.
**New file**: `ThreatSystem.cs`

```csharp
namespace VanEngine.Game.Simulation;

public enum ThreatType { Vulnerability, DeprecatedDependency, SecurityBreach }

public struct Threat
{
    public Guid Id { get; set; }
    public ThreatType Type { get; set; }
    public Vector2 Position { get; set; }
    public Vector2 Direction { get; set; }
    public float Speed { get; set; }
    public float Health { get; set; }
    public float ThreatLevel { get; set; } // 0.0 to 1.0
}

public class ThreatSystem
{
    private readonly List<Threat> _activeThreats = new();
    private readonly SovereignState _state;
    private readonly Random _rand = new();
    private float _threatSpawnTimer;
    private const float SpawnInterval = 8f;
    
    public ThreatSystem(SovereignState state) => _state = state;
    
    public void Update(float dt, IReadOnlyList<Citizen> militia, IReadOnlyList<ProjectHouse> houses)
    {
        _threatSpawnTimer -= dt;
        if (_threatSpawnTimer <= 0)
        {
            SpawnThreat();
            _threatSpawnTimer = SpawnInterval;
        }
        
        for (int i = _activeThreats.Count - 1; i >= 0; i--)
        {
            var threat = _activeThreats[i];
            threat.Position += threat.Direction * threat.Speed * dt;
            
            // Check militia interception
            var nearestMilitia = militia
                .Where(c => c.RoleType == 2) // 2 = Militia
                .OrderBy(c => Vector2.Distance(c.Position, threat.Position))
                .FirstOrDefault();
            
            if (nearestMilitia != null && Vector2.Distance(nearestMilitia.Position, threat.Position) < 60)
            {
                threat.Health -= dt * 25; // Militia damage per second
            }
            
            if (threat.Health <= 0)
            {
                _activeThreats.RemoveAt(i);
                _state.ModifyResources(new ResourcePack { Gold = 10 });
                _state.AddLog("Threat neutralized! +10 Gold");
                continue;
            }
            
            // Check if threat reached target
            var targetHouse = houses.FirstOrDefault(h => h.CurrentState == BuildState.Error);
            if (targetHouse != null && Vector2.Distance(threat.Position, targetHouse.Position) < 80)
            {
                targetHouse.CurrentState = BuildState.Error;
                _state.ModifyResources(new ResourcePack { Food = -100, Wealth = -50 });
                _state.AddLanguagePurity(-10, "Threat compromised house");
                _activeThreats.RemoveAt(i);
                _state.AddLog("⚠️ Threat breached a house! Resources lost.");
                continue;
            }
            
            _activeThreats[i] = threat;
        }
    }
    
    private void SpawnThreat()
    {
        var side = _rand.Next(4);
        Vector2 pos = side switch
        {
            0 => new(-50, _rand.Next(0, 720)), // left
            1 => new(1280 + 50, _rand.Next(0, 720)), // right
            2 => new(_rand.Next(0, 1280), -50), // top
            _ => new(_rand.Next(0, 1280), 720 + 50) // bottom
        };
        
        _activeThreats.Add(new Threat
        {
            Id = Guid.NewGuid(),
            Type = (ThreatType)_rand.Next(3),
            Position = pos,
            Direction = Vector2.Normalize(new Vector2(640, 360) - pos),
            Speed = _rand.Next(80, 150),
            Health = _rand.Next(30, 80),
            ThreatLevel = _rand.Next(1, 6) * 0.2f
        });
        
        _state.AddLog($"ALERT: {_activeThreats.Last().Type} threat incoming!");
    }
    
    public void Draw()
    {
        foreach (var threat in _activeThreats)
        {
            var color = threat.ThreatLevel > 0.7f ? RED : 
                        threat.ThreatLevel > 0.4f ? C(240, 200, 50) : YELLOW;
            DrawCircle((int)threat.Position.X, (int)threat.Position.Y, 12, color);
            DrawCircleLines((int)threat.Position.X, (int)threat.Position.Y, 16, color);
            
            // Health bar
            DrawRectangle((int)threat.Position.X - 15, (int)threat.Position.Y - 25, 30, 4, GRAY);
            DrawRectangle((int)threat.Position.X - 15, (int)threat.Position.Y - 25, 
                         (int)(30 * threat.Health / 80), 4, GREEN);
        }
    }
}
```

**Integration in `Program.cs.Update()`**:
```csharp
private static ThreatSystem _threatSystem = null!;

public static void Main()
{
    // ...
    _threatSystem = new ThreatSystem(_state);
}

private static void Update(float dt)
{
    // ...
    if (_timeController.CurrentPhase == SimulationPhase.Daytime)
        _threatSystem.Update(dt, _state.Citizens, _state.Houses);
}
```

---

### Feature 3.2 — Tech Tree & House Upgrades
**What**: Spend Gold to advance houses through Hamlet → Village → Town → Citadel tiers.
**New file**: `HouseUpgradeSystem.cs`

```csharp
namespace VanEngine.Game.Simulation;

public enum HouseTier { Hamlet = 0, Village = 1, Town = 2, Citadel = 3 }

public class HouseUpgradeSystem
{
    public static readonly Dictionary<HouseTier, UpgradeCosts> UpgradePrices = new()
    {
        { HouseTier.Village, new(50, 30, 0, 0, 0, 0) },
        { HouseTier.Town, new(100, 60, 40, 10, 0, 0) },
        { HouseTier.Citadel, new(200, 100, 80, 40, 100, 50) }
    };
    
    public static Vector2 GetBoundingBoxSize(HouseTier tier) => tier switch
    {
        HouseTier.Hamlet => new(120, 90),
        HouseTier.Village => new(160, 110),
        HouseTier.Town => new(200, 140),
        HouseTier.Citadel => new(260, 180),
        _ => new(120, 90)
    };
    
    public static float GetCollapseTimerBonus(HouseTier tier) => tier switch
    {
        HouseTier.Hamlet => 120f,
        HouseTier.Village => 150f,
        HouseTier.Town => 200f,
        HouseTier.Citadel => 300f,
        _ => 120f
    };
    
    public static int GetMaxTrackedFiles(HouseTier tier) => tier switch
    {
        HouseTier.Hamlet => 10,
        HouseTier.Village => 25,
        HouseTier.Town => 50,
        HouseTier.Citadel => 100,
        _ => 10
    };
}

public partial class ProjectHouse
{
    public HouseTier Tier { get; set; } = HouseTier.Hamlet;
    
    public bool CanUpgrade(ResourcePack resources)
    {
        var nextTier = Tier + 1;
        if (nextTier > HouseTier.Citadel) return false;
        
        var cost = HouseUpgradeSystem.UpgradePrices[(HouseTier)nextTier];
        return resources.Food >= cost.Food && 
               resources.Wood >= cost.Wood &&
               // ... check all resources
               true;
    }
    
    public void Upgrade(SovereignState state)
    {
        var nextTier = Tier + 1;
        var cost = HouseUpgradeSystem.UpgradePrices[(HouseTier)nextTier];
        
        state.ModifyResources(new ResourcePack 
        { 
            Food = -cost.Food, 
            Wood = -cost.Wood, 
            Stone = -cost.Stone, 
            Metal = -cost.Metal, 
            Wealth = -cost.Wealth, 
            Gold = -cost.Gold 
        });
        
        Tier = (HouseTier)nextTier;
        BoundingBoxSize = HouseUpgradeSystem.GetBoundingBoxSize(Tier);
        MaxRectificationWindow = HouseUpgradeSystem.GetCollapseTimerBonus(Tier);
        
        state.AddLog($"{ProjectName} upgraded to {Tier}!");
    }
}
```

**UI in Inspector panel**:
```csharp
if (SelectedHouse != null && SelectedHouse.Tier < HouseTier.Citadel)
{
    DrawText($"Tier: {SelectedHouse.Tier}", panelX + 10, 90, 12, WHITE);
    if (SelectedHouse.CanUpgrade(_state.Resources))
    {
        if (DrawButton(panelX + 10, 110, 100, 30, "Upgrade"))
        {
            SelectedHouse.Upgrade(_state);
        }
    }
    else
    {
        DrawText("Insufficient resources", panelX + 10, 110, 10, RED);
    }
}
```

---

### Feature 3.3 — GeckoShift Pipeline Trigger
**What**: Green Citadels with specific file configs activate neural engine processing.
**Extends**: `ProjectHouse.cs`

```csharp
public partial class ProjectHouse
{
    public bool CanActivateGeckoShift =>
        CurrentState == BuildState.Success &&
        Tier == HouseTier.Citadel &&
        TrackedFiles.Count >= 5;
    
    public void ActivateGeckoShift(SovereignState state)
    {
        if (!CanActivateGeckoShift) return;
        
        PendingArtifactPath = $"/tmp/geckoshiftoutput_{Guid.NewGuid()}.zip";
        HasBackyardTreasure = true;
        state.AddLog($"🤖 GeckoShift pipeline activated for {ProjectName}!");
        state.ModifyResources(new ResourcePack { Gold = 5 });
    }
}
```

**Treasure chest dragging**:
```csharp
// In DashboardView.Draw()
if (house.HasBackyardTreasure)
{
    DrawRectangle(hx + 80, hy + 60, 24, 24, C(255, 215, 0)); // Gold treasure
    DrawText("$", hx + 84, hy + 62, 18, BLACK);
    
    if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
    {
        var m = GetMousePosition();
        if (m.x >= hx + 80 && m.x <= hx + 104 && m.y >= hy + 60 && m.y <= hy + 84)
        {
            _draggedTreasure = house;
        }
    }
}

if (IsMouseButtonDown(MouseButton.MOUSE_BUTTON_LEFT) && _draggedTreasure != null)
{
    var m = GetMousePosition();
    DrawRectangle((int)m.x - 12, (int)m.y - 12, 24, 24, C(255, 215, 0, 180));
    DrawText("$", (int)m.x - 8, (int)m.y - 10, 18, BLACK);
}

if (IsMouseButtonReleased(MouseButton.MOUSE_BUTTON_LEFT) && _draggedTreasure != null)
{
    var m = GetMousePosition();
    // Check if within trove zone (center of map)
    if (m.x > 600 && m.x < 680 && m.y > 200 && m.y < 280)
    {
        _state.ModifyResources(new ResourcePack { Gold = 20 });
        _state.AddLog("Treasure deposited in central trove! +20 Gold");
        _draggedTreasure.ClearBackyardTreasure();
    }
    _draggedTreasure = null;
}
```

---

### Feature 3.4 — Citizen Skill Progression
**What**: Citizens gain XP, unlock specialisations.
**New file**: `CitizenSkillSystem.cs`

```csharp
namespace VanEngine.Game.Simulation;

public enum Specialisation { None = 0, Archivist = 1, Sentinel = 2, Jurist = 3 }

public struct CitizenSkill
{
    public int Level { get; set; }
    public float CurrentXP { get; set; }
    public float NextLevelXP { get; set; } = 100f;
    public Specialisation Specialisation { get; set; }
}

public partial class Citizen
{
    public CitizenSkill Skill { get; set; }
    
    public void GainXP(float amount)
    {
        Skill.CurrentXP += amount;
        while (Skill.CurrentXP >= Skill.NextLevelXP)
        {
            Skill.CurrentXP -= Skill.NextLevelXP;
            Skill.Level++;
            Skill.NextLevelXP *= 1.5f;
        }
    }
    
    public void SelectSpecialisation(Specialisation spec)
    {
        if (Skill.Level < 3) return; // Unlock at level 3
        Skill.Specialisation = spec;
    }
}

public static class SpecialisationEffects
{
    public static float GetFileAnalysisTimeReduction(Specialisation spec) => spec switch
    {
        Specialisation.Archivist => 0.5f, // 50% faster file analysis
        _ => 1.0f
    };
    
    public static float GetThreatDetectionRadius(Specialisation spec) => spec switch
    {
        Specialisation.Sentinel => 150f, // Detect threats at 150px
        _ => 60f
    };
    
    public static float GetDirectiveViolationTolerance(Specialisation spec) => spec switch
    {
        Specialisation.Jurist => 0.7f, // Allow 30% more violations
        _ => 1.0f
    };
}
```

**Award XP when files are added**:
```csharp
public void AddCompliantFile(UploadedFile file, string filePath, string namespaceRoot, int lineCount, AnalysisResult analysis)
{
    // ... existing code ...
    
    var targetCitizen = _citizens.Find(c => c.NamespaceFamily == namespaceRoot);
    if (targetCitizen != null)
    {
        targetCitizen.GainXP(lineCount / 10f); // XP based on lines
        if (targetCitizen.Skill.Level > 0)
            AddLog($"{targetCitizen.Name} gained {lineCount / 10f:F0} XP (Level {targetCitizen.Skill.Level})");
    }
}
```

---

### Feature 3.5 — Inter-workspace Trade Routes
**What**: Draw routes between workspaces, resource packets travel along them.
**New file**: `TradeRouteSystem.cs`

```csharp
namespace VanEngine.Game.Simulation;

public struct TradeRoute
{
    public Guid FromWorkspaceId { get; set; }
    public Guid ToWorkspaceId { get; set; }
    public float Efficiency { get; set; } // Based on shared namespaces
    public List<ResourcePacket> InFlightPackets { get; set; }
}

public struct ResourcePacket
{
    public Vector2 Position { get; set; }
    public Vector2 TargetPosition { get; set; }
    public ResourcePack Contents { get; set; }
    public float Progress { get; set; } // 0.0 to 1.0
}

public class TradeRouteSystem
{
    private readonly List<TradeRoute> _routes = new();
    
    public void EstablishRoute(Guid wsA, Guid wsB, float sharedNamespaceCount)
    {
        var efficiency = Math.Min(1.0f, sharedNamespaceCount * 0.2f);
        _routes.Add(new TradeRoute
        {
            FromWorkspaceId = wsA,
            ToWorkspaceId = wsB,
            Efficiency = efficiency,
            InFlightPackets = new()
        });
    }
    
    public void Update(float dt, Dictionary<Guid, (Vector2 center, BuildState state)> workspacePositions)
    {
        foreach (var route in _routes)
        {
            // Check if either workspace is in Error state
            if (workspacePositions[route.FromWorkspaceId].state == BuildState.Error ||
                workspacePositions[route.ToWorkspaceId].state == BuildState.Error)
            {
                route.InFlightPackets.Clear(); // Severed route
                continue;
            }
            
            // Spawn new packet every 2 seconds
            if (GetRandomValue(0, 120) == 0) // ~2s at 60 FPS
            {
                route.InFlightPackets.Add(new ResourcePacket
                {
                    Position = workspacePositions[route.FromWorkspaceId].center,
                    TargetPosition = workspacePositions[route.ToWorkspaceId].center,
                    Contents = new ResourcePack { Food = 10, Wood = 5, Wealth = 2 },
                    Progress = 0f
                });
            }
            
            // Advance packets
            for (int i = route.InFlightPackets.Count - 1; i >= 0; i--)
            {
                var packet = route.InFlightPackets[i];
                packet.Progress += dt / 5f; // 5 second transit
                
                if (packet.Progress >= 1.0f)
                {
                    // Deliver packet to destination workspace
                    // _workspaceManager[route.ToWorkspaceId].ModifyResources(packet.Contents);
                    route.InFlightPackets.RemoveAt(i);
                }
                else
                {
                    packet.Position = Vector2.Lerp(packet.Position, 
                                                    packet.TargetPosition, 
                                                    packet.Progress);
                    route.InFlightPackets[i] = packet;
                }
            }
        }
    }
    
    public void Draw()
    {
        foreach (var route in _routes)
        {
            foreach (var packet in route.InFlightPackets)
            {
                DrawCircle((int)packet.Position.X, (int)packet.Position.Y, 5, GOLD);
            }
        }
    }
}
```

---

### Feature 3.6 — Local Event Socket / Webhook
**What**: HTTP endpoint for CI/build systems to push events.
**New file**: `EventSocketServer.cs`

```csharp
namespace VanEngine.Game.Core;

public class EventSocketServer
{
    private HttpListener _listener;
    private readonly SovereignState _state;
    private bool _isRunning;
    
    public EventSocketServer(SovereignState state, string prefix = "http://localhost:8765/")
    {
        _state = state;
        _listener = new HttpListener();
        _listener.Prefixes.Add(prefix);
    }
    
    public void Start()
    {
        _isRunning = true;
        _listener.Start();
        
        _ = System.Threading.Tasks.Task.Run(async () =>
        {
            while (_isRunning)
            {
                try
                {
                    HttpListenerContext context = await _listener.GetContextAsync();
                    ProcessRequest(context);
                }
                catch (Exception ex)
                {
                    _state.AddLog($"Socket error: {ex.Message}");
                }
            }
        });
    }
    
    private void ProcessRequest(HttpListenerContext context)
    {
        if (context.Request.HttpMethod == "POST")
        {
            using var reader = new StreamReader(context.Request.InputStream);
            string body = reader.ReadToEnd();
            
            var json = JsonDocument.Parse(body);
            var root = json.RootElement;
            
            string eventType = root.GetProperty("type").GetString() ?? "unknown";
            
            switch (eventType)
            {
                case "build_success":
                    _state.AddLog($"✓ Build successful for {root.GetProperty("project").GetString()}");
                    _state.ModifyResources(new ResourcePack { Food = 20, Wealth = 10 });
                    break;
                    
                case "build_failure":
                    _state.AddLog($"✗ Build failed: {root.GetProperty("error").GetString()}");
                    _state.ModifyResources(new ResourcePack { Food = -30 });
                    break;
                    
                case "lint_warning":
                    _state.AddLog($"⚠ Lint: {root.GetProperty("message").GetString()}");
                    break;
                    
                case "file_change":
                    var filePath = root.GetProperty("path").GetString();
                    var analysis = TexStaticAnalyzer.AnalyzeSourceFile(filePath);
                    _state.AddLog($"File watched: {Path.GetFileName(filePath)}");
                    break;
            }
            
            context.Response.StatusCode = 200;
            context.Response.OutputStream.Close();
        }
    }
    
    public void Stop()
    {
        _isRunning = false;
        _listener.Stop();
    }
}
```

**Initialization in `Program.cs.Main()`**:
```csharp
var eventServer = new EventSocketServer(_state);
eventServer.Start();
```

**Example CI integration (C#)**:
```csharp
using var client = new HttpClient();
var payload = JsonSerializer.Serialize(new 
{ 
    type = "build_success",
    project = "VAN Engine",
    timestamp = DateTime.Now
});
await client.PostAsync("http://localhost:8765/event", 
                       new StringContent(payload, Encoding.UTF8, "application/json"));
```

---

## TIER 4: Endgame

### Feature 4.1 — Git Integration
**What**: Commits advance year, branches split timelines, merges cause conflicts.
**New file**: `GitIntegrationService.cs`

```csharp
namespace VanEngine.Game.Core;

using LibGit2Sharp;

public class GitIntegrationService
{
    private readonly Repository _repo;
    private readonly SovereignState _state;
    private string _currentBranch;
    private int _lastCommitCount;
    
    public GitIntegrationService(SovereignState state, string repoPath)
    {
        _state = state;
        _repo = new Repository(repoPath);
        _currentBranch = _repo.Head.FriendlyName;
        _lastCommitCount = _repo.Commits.Count();
    }
    
    public void Update()
    {
        // Check for new commits
        int currentCount = _repo.Commits.Count();
        if (currentCount > _lastCommitCount)
        {
            int newCommits = currentCount - _lastCommitCount;
            _state.IncrementYear();
            _state.AddLog($"📝 {newCommits} commit(s) detected — year advanced!");
            _lastCommitCount = currentCount;
        }
        
        // Check for branch changes
        string newBranch = _repo.Head.FriendlyName;
        if (newBranch != _currentBranch)
        {
            _state.AddLog($"🌳 Switched to branch '{newBranch}' — parallel timeline active!");
            _currentBranch = newBranch;
        }
        
        // Check for merge conflicts
        if (_repo.Index.IsAssumeUnchanged)
        {
            var conflictedPaths = _repo.Index.ConflictedPaths.ToList();
            if (conflictedPaths.Count > 0)
            {
                var c1 = _state.Citizens.FirstOrDefault();
                var c2 = _state.Citizens.Skip(1).FirstOrDefault();
                if (c1 != null && c2 != null)
                {
                    _state.AddLog($"⚔️ Merge conflict! {c1.Name} and {c2.Name} battle over {conflictedPaths.Count} files.");
                    c1.DecayTimer = 10f;
                    c2.DecayTimer = 10f;
                }
            }
        }
    }
}
```

**Initialization in `Program.cs.Main()`**:
```csharp
var gitService = new GitIntegrationService(_state, "/path/to/repo");

private static void Update(float dt)
{
    gitService.Update();
}
```

---

### Feature 4.2 — Project Health Report Export
**What**: Generate markdown/HTML report with scores, violation list, roster, sparklines.
**New file**: `ReportGenerator.cs`

```csharp
namespace VanEngine.Game.Core;

public class ReportGenerator
{
    private readonly SovereignState _state;
    
    public ReportGenerator(SovereignState state) => _state = state;
    
    public string GenerateMarkdownReport()
    {
        var sb = new StringBuilder();
        
        sb.AppendLine("# Project Health Report");
        sb.AppendLine($"Generated: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
        sb.AppendLine();
        
        // Summary metrics
        sb.AppendLine("## Summary");
        sb.AppendLine($"- **Sovereignty**: {_state.Sovereignty:F1}%");
        sb.AppendLine($"- **Language Purity**: {_state.LanguagePurity:F1}%");
        sb.AppendLine($"- **Citizens**: {_state.Citizens.Count}");
        sb.AppendLine($"- **Houses**: {_state.Houses.Count}");
        sb.AppendLine($"- **Total Lines**: {_state.TotalCompliantLines}");
        sb.AppendLine();
        
        // Resources
        var res = _state.Resources;
        sb.AppendLine("## Resources");
        sb.AppendLine($"| Resource | Amount |");
        sb.AppendLine($"|----------|--------|");
        sb.AppendLine($"| Food | {res.Food} |");
        sb.AppendLine($"| Wood | {res.Wood} |");
        sb.AppendLine($"| Stone | {res.Stone} |");
        sb.AppendLine($"| Metal | {res.Metal} |");
        sb.AppendLine($"| Wealth | {res.Wealth} |");
        sb.AppendLine($"| Gold | {res.Gold} |");
        sb.AppendLine();
        
        // Directive violations
        sb.AppendLine("## Violations by Directive");
        var violationsByType = new Dictionary<string, int>();
        foreach (var file in _state.UploadHistory)
        {
            if (file.ViolationCount > 0)
            {
                violationsByType.TryGetValue(file.Details, out int count);
                violationsByType[file.Details] = count + file.ViolationCount;
            }
        }
        foreach (var (directive, count) in violationsByType)
            sb.AppendLine($"- {directive}: {count}");
        sb.AppendLine();
        
        // Citizens
        sb.AppendLine("## Citizens");
        foreach (var citizen in _state.Citizens)
        {
            sb.AppendLine($"### {citizen.Name}");
            sb.AppendLine($"- Role: {RoleString(citizen.RoleType)}");
            sb.AppendLine($"- Files Owned: {citizen.OwnedFiles.Count}");
            sb.AppendLine($"- Lines Contributed: {citizen.CompliantLinesContributed}");
            sb.AppendLine();
        }
        
        // Houses
        sb.AppendLine("## Houses");
        foreach (var house in _state.Houses)
        {
            sb.AppendLine($"### {house.ProjectName}");
            sb.AppendLine($"- Namespace: {house.RootNamespace}");
            sb.AppendLine($"- State: {house.CurrentState}");
            sb.AppendLine($"- Files: {house.TrackedFiles.Count}");
            foreach (var file in house.TrackedFiles)
                sb.AppendLine($"  - {Path.GetFileName(file.FilePath)}: {file.ErrorCount} errors, {file.WarningCount} warnings");
            sb.AppendLine();
        }
        
        return sb.ToString();
    }
    
    public void ExportToFile(string format = "markdown")
    {
        string content = GenerateMarkdownReport();
        string ext = format == "html" ? ".html" : ".md";
        string filename = $"health_report_{DateTime.Now:yyyyMMdd_HHmmss}{ext}";
        string path = Path.Combine(AppContext.BaseDirectory, "reports", filename);
        
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, content);
    }
}
```

**UI in DashboardView**:
```csharp
if (IsKeyPressed(KeyboardKey.KEY_E)) // E for export
{
    var generator = new ReportGenerator(_state);
    generator.ExportToFile("markdown");
    _state.AddLog("📄 Health report exported!");
}
```

---

### Feature 4.3 — Scripting API / Mod Hooks
**What**: Lua scripting surface, pluggable custom directives, new resource types.
**New file**: `ScriptingEngine.cs`

```csharp
namespace VanEngine.Game.Core;

using MoonSharp.Interpreter;

public class ScriptingEngine
{
    private readonly Script _luaScript;
    private readonly SovereignState _state;
    private readonly string _modsDirectory;
    
    public ScriptingEngine(SovereignState state, string modsDir = "./mods")
    {
        _state = state;
        _modsDirectory = modsDir;
        _luaScript = new Script();
        
        // Expose game API to Lua
        _luaScript.Globals["game"] = new GameAPI(_state);
        _luaScript.Globals["log"] = (Action<string>)(msg => _state.AddLog($"[Mod] {msg}"));
    }
    
    public void LoadMods()
    {
        if (!Directory.Exists(_modsDirectory))
            Directory.CreateDirectory(_modsDirectory);
        
        foreach (var modFile in Directory.GetFiles(_modsDirectory, "*.lua"))
        {
            try
            {
                string script = File.ReadAllText(modFile);
                _luaScript.DoString(script);
                _state.AddLog($"✓ Mod loaded: {Path.GetFileNameWithoutExtension(modFile)}");
            }
            catch (Exception ex)
            {
                _state.AddLog($"✗ Mod error ({Path.GetFileName(modFile)}): {ex.Message}");
            }
        }
    }
}

public class GameAPI
{
    private readonly SovereignState _state;
    
    public GameAPI(SovereignState state) => _state = state;
    
    public void AddDirective(string name, int violationWeight)
    {
        _state.AddLog($"Directive '{name}' registered (weight: {violationWeight})");
    }
    
    public void AddResourceType(string name, int maxCapacity)
    {
        _state.AddLog($"Resource type '{name}' added (capacity: {maxCapacity})");
    }
    
    public float GetSovereignty() => _state.Sovereignty;
    public void ModifyResources(int food, int wood, int stone, int metal, int wealth, int gold)
    {
        _state.ModifyResources(new ResourcePack { Food = food, Wood = wood, Stone = stone, Metal = metal, Wealth = wealth, Gold = gold });
    }
}
```

**Example mod** (`mods/custom_directives.lua`):
```lua
-- Register a custom directive
game:AddDirective("NoConsoleLogging", 5)
game:AddResourceType("Energy", 500)

-- Hook into citizen creation
original_create = game.CreateCitizen
function game.CreateCitizen(name, namespace)
    original_create(name, namespace)
    game:ModifyResources(10, 0, 0, 0, 0, 0) -- +10 food bonus
end
```

---

### Feature 4.4 — Optional Community Scoreboard
**What**: Opt-in leaderboard, self-certifying signed score tokens.
**New file**: `CommunityScoreboard.cs`

```csharp
namespace VanEngine.Game.Core;

public class CommunityScoreboard
{
    private const string ScoreboardUrl = "https://oera-linda-leaderboard.example.com";
    
    public struct ScoreToken
    {
        public string PlayerName { get; set; }
        public float Sovereignty { get; set; }
        public int Year { get; set; }
        public DateTime Timestamp { get; set; }
        public string Hash { get; set; }
    }
    
    public static ScoreToken GenerateScoreToken(string playerName, SovereignState state)
    {
        var token = new ScoreToken
        {
            PlayerName = playerName,
            Sovereignty = state.Sovereignty,
            Year = state.Year,
            Timestamp = DateTime.Now,
            Hash = GenerateHash(playerName, state.Sovereignty, state.Year)
        };
        return token;
    }
    
    private static string GenerateHash(string playerName, float sovereignty, int year)
    {
        string data = $"{playerName}:{sovereignty:F2}:{year}:{DateTime.Now:yyyyMMdd}";
        using var sha = System.Security.Cryptography.SHA256.Create();
        byte[] hash = sha.ComputeHash(System.Text.Encoding.UTF8.GetBytes(data));
        return System.Convert.ToHexString(hash);
    }
    
    public static async System.Threading.Tasks.Task<bool> SubmitScore(ScoreToken token)
    {
        try
        {
            using var client = new HttpClient();
            string json = JsonSerializer.Serialize(token);
            var response = await client.PostAsync(
                $"{ScoreboardUrl}/submit",
                new StringContent(json, System.Text.Encoding.UTF8, "application/json"));
            
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }
}
```

**UI option in DashboardView**:
```csharp
DrawText("Share score with community? (optional)", 50, 100, 14, WHITE);
if (DrawButton(50, 125, 150, 30, "Submit Score"))
{
    var token = CommunityScoreboard.GenerateScoreToken("Player", _state);
    _ = CommunityScoreboard.SubmitScore(token);
    _state.AddLog("Score submitted (anonymous).");
}
```

