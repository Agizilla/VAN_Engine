using System.Collections.Concurrent;

namespace VanEngine.Game.Core;

public sealed class FileWatcherService : IDisposable
{
    private readonly List<FileSystemWatcher> _watchers = new();
    private readonly ConcurrentDictionary<string, DateTime> _pendingEvents = new();
    private readonly SovereignState _state;
    private readonly Action<string> _onFileChanged;
    private readonly System.Threading.Timer _debounceTimer;
    private const int DebounceMs = 300;
    private bool _disposed;

    public bool IsActive { get; private set; }
    public int WatchedFiles { get; private set; }

    public FileWatcherService(SovereignState state, Action<string> onFileChanged)
    {
        _state = state;
        _onFileChanged = onFileChanged;
        _debounceTimer = new System.Threading.Timer(_ => FlushPending(), null, Timeout.Infinite, Timeout.Infinite);
    }

    public void WatchDirectory(string directoryPath)
    {
        if (!Directory.Exists(directoryPath)) return;

        var watcher = new FileSystemWatcher(directoryPath)
        {
            IncludeSubdirectories = true,
            NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.FileName | NotifyFilters.Size,
            EnableRaisingEvents = true,
        };

        watcher.Changed += OnFileEvent;
        watcher.Created += OnFileEvent;
        watcher.Deleted += OnFileEvent;
        watcher.Renamed += OnRenamed;
        watcher.Error += (_, e) =>
        {
            _state.EnqueueLog($"Watcher error: {e.GetException().Message}");
        };

        _watchers.Add(watcher);
        IsActive = true;

        var count = Directory.GetFiles(directoryPath, "*.*", SearchOption.AllDirectories).Length;
        WatchedFiles += count;
        _state.EnqueueLog($"FileWatcher active: {directoryPath} ({count} files)");
    }

    private void OnFileEvent(object sender, FileSystemEventArgs e)
    {
        if (_disposed) return;
        string ext = Path.GetExtension(e.FullPath).ToLowerInvariant();
        var validExts = new HashSet<string> { ".cs", ".py", ".rs", ".js", ".ts", ".go", ".c", ".cpp", ".cc", ".java", ".h", ".hpp" };
        if (!validExts.Contains(ext)) return;

        _pendingEvents[e.FullPath] = DateTime.UtcNow;
        _debounceTimer.Change(DebounceMs, Timeout.Infinite);
    }

    private void OnRenamed(object sender, RenamedEventArgs e)
    {
        if (_disposed) return;
        _pendingEvents[e.FullPath] = DateTime.UtcNow;
        _debounceTimer.Change(DebounceMs, Timeout.Infinite);
    }

    private void FlushPending()
    {
        if (_disposed) return;
        var now = DateTime.UtcNow;
        var toProcess = _pendingEvents
            .Where(kvp => (now - kvp.Value).TotalMilliseconds >= DebounceMs)
            .Select(kvp => kvp.Key)
            .ToList();

        foreach (var path in toProcess)
        {
            _pendingEvents.TryRemove(path, out _);

            if (File.Exists(path))
            {
                _state.EnqueueLog($"File changed: {Path.GetFileName(path)}");
                _onFileChanged(path);
            }
        }

        if (!_pendingEvents.IsEmpty)
            _debounceTimer.Change(DebounceMs, Timeout.Infinite);
    }

    public void UnwatchAll()
    {
        foreach (var w in _watchers)
        {
            w.EnableRaisingEvents = false;
            w.Dispose();
        }
        _watchers.Clear();
        _pendingEvents.Clear();
        IsActive = false;
        WatchedFiles = 0;
    }

    public void Dispose()
    {
        _disposed = true;
        _debounceTimer.Dispose();
        UnwatchAll();
    }
}
