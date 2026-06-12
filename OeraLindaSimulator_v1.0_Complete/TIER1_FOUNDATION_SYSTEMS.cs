// ============================================================================
// TIER 1: FOUNDATION SYSTEMS
// WorkspaceManager, FileSystemWatcher, CameraController, SettingsManager
// ============================================================================

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace VanEngine.Game.Core;

/// <summary>
/// Tracks metadata about a workspace (project/codebase).
/// </summary>
public class WorkspaceMetadata
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Name { get; set; } = string.Empty;
    public string RootPath { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public DateTime LastModified { get; set; } = DateTime.Now;
    public int Year { get; set; } = 1;
    public float Sovereignty { get; set; } = 100f;
    
    [JsonIgnore]
    public bool IsDirty { get; set; }
}

/// <summary>
/// Manages multiple independent workspaces, switching, and persistence.
/// One workspace = one project/codebase being tracked.
/// </summary>
public class WorkspaceManager
{
    private readonly string _workspacesDirectory;
    private readonly Dictionary<Guid, WorkspaceMetadata> _workspaces = new();
    private Guid _currentWorkspaceId = Guid.Empty;
    
    public event Action<Guid>? WorkspaceSwitched;
    public event Action<Guid>? WorkspaceCreated;
    public event Action<Guid>? WorkspaceDeleted;
    
    public WorkspaceMetadata? CurrentWorkspace => 
        _currentWorkspaceId != Guid.Empty && _workspaces.TryGetValue(_currentWorkspaceId, out var ws) 
            ? ws 
            : null;
    
    public IReadOnlyList<WorkspaceMetadata> AllWorkspaces => 
        _workspaces.Values.OrderByDescending(w => w.LastModified).ToList();
    
    public WorkspaceManager(string baseDirectory = "")
    {
        _workspacesDirectory = string.IsNullOrEmpty(baseDirectory)
            ? Path.Combine(AppContext.BaseDirectory, "workspaces")
            : baseDirectory;
            
        Directory.CreateDirectory(_workspacesDirectory);
        LoadWorkspaces();
    }
    
    /// <summary>
    /// Create a new workspace pointing to a local directory.
    /// </summary>
    public WorkspaceMetadata CreateWorkspace(string name, string rootPath)
    {
        if (!Directory.Exists(rootPath))
            throw new DirectoryNotFoundException($"Root path does not exist: {rootPath}");
        
        var metadata = new WorkspaceMetadata
        {
            Name = name,
            RootPath = Path.GetFullPath(rootPath),
            CreatedAt = DateTime.Now,
            LastModified = DateTime.Now
        };
        
        var workspaceDir = Path.Combine(_workspacesDirectory, metadata.Id.ToString());
        Directory.CreateDirectory(workspaceDir);
        SaveMetadata(workspaceDir, metadata);
        
        _workspaces[metadata.Id] = metadata;
        _currentWorkspaceId = metadata.Id;
        
        WorkspaceCreated?.Invoke(metadata.Id);
        return metadata;
    }
    
    /// <summary>
    /// Switch to an existing workspace.
    /// </summary>
    public bool SwitchWorkspace(Guid id)
    {
        if (!_workspaces.ContainsKey(id))
            return false;
        
        _currentWorkspaceId = id;
        WorkspaceSwitched?.Invoke(id);
        return true;
    }
    
    /// <summary>
    /// Save current workspace state.
    /// </summary>
    public void SaveCurrentWorkspace()
    {
        if (CurrentWorkspace is null)
            return;
        
        CurrentWorkspace.LastModified = DateTime.Now;
        var dir = Path.Combine(_workspacesDirectory, CurrentWorkspace.Id.ToString());
        SaveMetadata(dir, CurrentWorkspace);
    }
    
    /// <summary>
    /// Delete a workspace from disk.
    /// </summary>
    public bool DeleteWorkspace(Guid id)
    {
        if (!_workspaces.TryGetValue(id, out var ws))
            return false;
        
        var dir = Path.Combine(_workspacesDirectory, id.ToString());
        if (Directory.Exists(dir))
            Directory.Delete(dir, recursive: true);
        
        _workspaces.Remove(id);
        
        if (_currentWorkspaceId == id)
            _currentWorkspaceId = _workspaces.Keys.FirstOrDefault();
        
        WorkspaceDeleted?.Invoke(id);
        return true;
    }
    
    private void LoadWorkspaces()
    {
        try
        {
            foreach (var dir in Directory.EnumerateDirectories(_workspacesDirectory))
            {
                var metaPath = Path.Combine(dir, "meta.json");
                if (File.Exists(metaPath))
                {
                    var json = File.ReadAllText(metaPath);
                    var meta = JsonSerializer.Deserialize<WorkspaceMetadata>(json);
                    if (meta is not null)
                        _workspaces[meta.Id] = meta;
                }
            }
            
            if (_workspaces.Count > 0)
                _currentWorkspaceId = _workspaces.Keys.First();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Failed to load workspaces: {ex.Message}");
        }
    }
    
    private static void SaveMetadata(string workspaceDir, WorkspaceMetadata metadata)
    {
        var json = JsonSerializer.Serialize(metadata, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(Path.Combine(workspaceDir, "meta.json"), json);
    }
}

/// <summary>
/// Watches a directory for file changes and notifies on modifications.
/// </summary>
public class FileSystemWatcherService : IDisposable
{
    private readonly FileSystemWatcher _watcher;
    private readonly Action<string, FileChangeType>? _onChange;
    private readonly HashSet<string> _recentlyProcessed = new();
    private const int DebounceMs = 500;
    
    public enum FileChangeType { Created, Modified, Deleted, Renamed }
    
    public event Action<string, FileChangeType>? FileChanged;
    
    public FileSystemWatcherService(string watchPath, Action<string, FileChangeType>? callback = null)
    {
        _onChange = callback;
        _watcher = new FileSystemWatcher(watchPath)
        {
            Filter = "*.*",
            NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.FileName | NotifyFilters.DirectoryName,
            EnableRaisingEvents = true
        };
        
        _watcher.Changed += OnFileSystemEvent;
        _watcher.Created += OnFileSystemEvent;
        _watcher.Deleted += OnFileSystemEvent;
        _watcher.Renamed += OnRenamed;
        _watcher.Error += OnError;
    }
    
    private void OnFileSystemEvent(object sender, FileSystemEventArgs e)
    {
        if (_recentlyProcessed.Contains(e.FullPath))
            return;
        
        _recentlyProcessed.Add(e.FullPath);
        _ = System.Threading.Tasks.Task.Delay(DebounceMs).ContinueWith(_ =>
            _recentlyProcessed.Remove(e.FullPath));
        
        var changeType = e.ChangeType switch
        {
            WatcherChangeTypes.Created => FileChangeType.Created,
            WatcherChangeTypes.Deleted => FileChangeType.Deleted,
            _ => FileChangeType.Modified
        };
        
        _onChange?.Invoke(e.FullPath, changeType);
        FileChanged?.Invoke(e.FullPath, changeType);
    }
    
    private void OnRenamed(object sender, RenamedEventArgs e)
    {
        _onChange?.Invoke(e.OldFullPath, FileChangeType.Deleted);
        _onChange?.Invoke(e.FullPath, FileChangeType.Created);
    }
    
    private void OnError(object sender, ErrorEventArgs e)
    {
        System.Diagnostics.Debug.WriteLine($"FileSystemWatcher error: {e.GetException()?.Message}");
    }
    
    public void Dispose() => _watcher.Dispose();
}

/// <summary>
/// Camera for panning and zooming a 2D game world.
/// </summary>
public class CameraController
{
    public Vector2 Position { get; set; } = Vector2.Zero;
    public float Zoom { get; set; } = 1f;
    
    public const float MinZoom = 0.3f;
    public const float MaxZoom = 3f;
    private Vector2 _worldSize = new(2560, 1920);
    
    public void HandleInput(int screenWidth, int screenHeight)
    {
        // Scroll wheel zoom
        float wheel = 0; // GetMouseWheelMove() — integrate with Raylib
        if (wheel != 0)
        {
            var beforeZoom = Zoom;
            Zoom = Math.Clamp(Zoom + wheel * 0.1f, MinZoom, MaxZoom);
            // Re-center on mouse
            Position = ClampPosition(screenWidth, screenHeight);
        }
        
        // Middle-click pan
        // if (IsMouseButtonDown(MouseButton.MOUSE_BUTTON_MIDDLE))
        // {
        //     var delta = GetMouseDelta();
        //     Position -= delta / Zoom;
        //     Position = ClampPosition(screenWidth, screenHeight);
        // }
    }
    
    public Vector2 ScreenToWorld(Vector2 screenPos, int screenWidth, int screenHeight) =>
        Position + screenPos / Zoom;
    
    public Vector2 WorldToScreen(Vector2 worldPos, int screenWidth, int screenHeight) =>
        (worldPos - Position) * Zoom;
    
    public void DrawMinimap(int screenWidth, int screenHeight, IReadOnlyList<(Vector2 pos, int type)> entities)
    {
        const int minimapW = 140, minimapH = 100;
        int mx = screenWidth - minimapW - 10;
        int my = 10;
        
        // Background
        // DrawRectangle(mx, my, minimapW, minimapH, Color(22, 26, 34, 200));
        // DrawRectangleLinesEx(new Rectangle(mx, my, minimapW, minimapH), 1, Color(100, 150, 200));
        
        // Entity dots
        foreach (var (pos, type) in entities)
        {
            float sx = mx + (pos.X / _worldSize.X) * minimapW;
            float sy = my + (pos.Y / _worldSize.Y) * minimapH;
            // DrawCircle((int)sx, (int)sy, 2, entity_color);
        }
        
        // Viewport rectangle
        float vx = mx + (Position.X / _worldSize.X) * minimapW;
        float vy = my + (Position.Y / _worldSize.Y) * minimapH;
        float vw = (screenWidth / Zoom / _worldSize.X) * minimapW;
        float vh = (screenHeight / Zoom / _worldSize.Y) * minimapH;
        // DrawRectangleLinesEx(new Rectangle(vx, vy, vw, vh), 1, Color(100, 200, 255));
    }
    
    private Vector2 ClampPosition(int screenWidth, int screenHeight)
    {
        var maxX = _worldSize.X - (screenWidth / Zoom);
        var maxY = _worldSize.Y - (screenHeight / Zoom);
        return new Vector2(
            Math.Clamp(Position.X, 0, maxX),
            Math.Clamp(Position.Y, 0, maxY)
        );
    }
}

/// <summary>
/// Persisted user settings (game speed, UI scale, keybindings, etc.).
/// </summary>
[Serializable]
public class GameSettings
{
    public float GameSpeed { get; set; } = 1.0f;
    public float UIScale { get; set; } = 1.0f;
    public Dictionary<string, float> DirectiveWeights { get; set; } = new();
    public Dictionary<string, bool> EnabledDirectives { get; set; } = new();
    public Dictionary<string, int> KeyBindings { get; set; } = new();
    public bool EnableTelemetry { get; set; } = false;
    
    public static GameSettings LoadOrDefault()
    {
        string path = Path.Combine(AppContext.BaseDirectory, "settings.json");
        if (File.Exists(path))
        {
            try
            {
                var json = File.ReadAllText(path);
                return JsonSerializer.Deserialize<GameSettings>(json) ?? new();
            }
            catch { }
        }
        return new();
    }
    
    public void Save()
    {
        string path = Path.Combine(AppContext.BaseDirectory, "settings.json");
        var json = JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(path, json);
    }
}

