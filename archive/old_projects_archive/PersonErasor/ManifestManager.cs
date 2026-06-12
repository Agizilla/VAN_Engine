using System.Text.Json;
using SovereignIDE.Core.Exceptions;
using SovereignIDE.Core.Models;
using SovereignIDE.Core.Validation;

namespace SovereignIDE.Core.Services;

/// <summary>
/// Manages manifest persistence with auto-save, versioning, and backups.
/// 
/// Features:
/// - Auto-save on changes
/// - Backup before overwrite
/// - Version history
/// - Recovery from corruption
/// </summary>
public class ManifestManager
{
    private readonly string _manifestPath;
    private readonly string _backupDirectory;
    private readonly System.Threading.Timer? _autoSaveTimer;
    private ManifestV4? _currentManifest;
    private bool _isDirty = false;
    private readonly int _maxBackups;

    public event EventHandler<ManifestV4>? ManifestChanged;
    public event EventHandler? ManifestSaved;
    public event EventHandler<string>? AutoSaveError;

    public ManifestV4? CurrentManifest
    {
        get => _currentManifest;
        private set
        {
            _currentManifest = value;
            ManifestChanged?.Invoke(this, value!);
        }
    }

    public bool IsDirty => _isDirty;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
    };

    public ManifestManager(
        string manifestPath,
        bool enableAutoSave = true,
        int autoSaveIntervalSeconds = 30,
        int maxBackups = 10)
    {
        _manifestPath = manifestPath;
        _backupDirectory = Path.Combine(
            Path.GetDirectoryName(manifestPath) ?? ".",
            ".manifest-backups"
        );
        _maxBackups = maxBackups;

        Directory.CreateDirectory(_backupDirectory);

        if (enableAutoSave)
        {
            _autoSaveTimer = new System.Threading.Timer(
                AutoSaveCallback,
                null,
                TimeSpan.FromSeconds(autoSaveIntervalSeconds),
                TimeSpan.FromSeconds(autoSaveIntervalSeconds)
            );
        }
    }

    /// <summary>
    /// Creates a new manifest with default structure.
    /// </summary>
    public ManifestV4 CreateNew(string projectRoot, string owner)
    {
        var manifest = new ManifestV4
        {
            Version = "4.0",
            Context = new ContextInfo
            {
                Model = "Human",
                SessionId = Guid.NewGuid().ToString(),
                Owner = owner,
                CreatedDate = DateTime.UtcNow,
                LastModifiedDate = DateTime.UtcNow,
                ProjectRoot = projectRoot,
                History = new List<HistoryEntry>
                {
                    new HistoryEntry
                    {
                        Timestamp = DateTime.UtcNow,
                        Agent = "System",
                        Action = "Created new manifest",
                        Details = $"Project root: {projectRoot}"
                    }
                }
            },
            Files = new List<FileEntry>(),
            Commands = new List<CommandEntry>(),
            Decisions = new List<Decision>(),
            Conversation = new List<ConversationTurn>()
        };

        CurrentManifest = manifest;
        _isDirty = true;

        return manifest;
    }

    /// <summary>
    /// Loads manifest from disk.
    /// 
    /// Contract:
    /// - Validates version
    /// - Validates structure
    /// - Attempts recovery if corrupted
    /// </summary>
    public ManifestV4 Load()
    {
        if (!File.Exists(_manifestPath))
        {
            throw new FileOperationException(
                "Manifest file not found",
                _manifestPath,
                "Loading manifest",
                "load-manifest"
            );
        }

        try
        {
            var json = File.ReadAllText(_manifestPath);
            var manifest = JsonSerializer.Deserialize<ManifestV4>(json, JsonOptions);

            if (manifest == null)
            {
                throw new JsonParsingException(
                    "Failed to deserialize manifest",
                    "Manifest deserialization returned null",
                    "load-manifest"
                );
            }

            // Validate
            ManifestValidator.ValidateManifest(manifest, manifest.Context.SessionId);

            CurrentManifest = manifest;
            _isDirty = false;

            return manifest;
        }
        catch (JsonException ex)
        {
            // Attempt recovery from latest backup
            var recovered = AttemptRecovery();
            if (recovered != null)
            {
                Console.WriteLine("⚠️ Manifest was corrupted, recovered from backup");
                return recovered;
            }

            throw new JsonParsingException(
                $"Failed to parse manifest: {ex.Message}",
                $"File: {_manifestPath}",
                "load-manifest",
                ex
            );
        }
    }

    /// <summary>
    /// Saves manifest to disk with backup.
    /// </summary>
    public void Save()
    {
        if (_currentManifest == null)
            throw new InvalidOperationException("No manifest to save");

        try
        {
            // Update last modified
            var updatedContext = _currentManifest.Context with
            {
                LastModifiedDate = DateTime.UtcNow
            };

            var updatedManifest = _currentManifest with
            {
                Context = updatedContext
            };

            // Validate before saving
            ManifestValidator.ValidateManifest(updatedManifest, updatedManifest.Context.SessionId);

            // Create backup if file exists
            if (File.Exists(_manifestPath))
            {
                CreateBackup();
            }

            // Serialize
            var json = JsonSerializer.Serialize(updatedManifest, JsonOptions);

            // Write atomically (write to temp, then move)
            var tempPath = _manifestPath + ".tmp";
            File.WriteAllText(tempPath, json);
            File.Move(tempPath, _manifestPath, overwrite: true);

            CurrentManifest = updatedManifest;
            _isDirty = false;

            ManifestSaved?.Invoke(this, EventArgs.Empty);
            Console.WriteLine($"💾 Saved manifest: {_manifestPath}");

            // Cleanup old backups
            CleanupOldBackups();
        }
        catch (Exception ex) when (ex is not SovereignException)
        {
            throw new FileOperationException(
                $"Failed to save manifest: {ex.Message}",
                _manifestPath,
                "Saving manifest",
                _currentManifest?.Context.SessionId ?? "unknown",
                ex
            );
        }
    }

    /// <summary>
    /// Marks manifest as dirty (needs save).
    /// </summary>
    public void MarkDirty()
    {
        _isDirty = true;
    }

    /// <summary>
    /// Updates manifest and marks dirty.
    /// </summary>
    public void Update(ManifestV4 manifest)
    {
        CurrentManifest = manifest;
        _isDirty = true;
    }

    /// <summary>
    /// Adds history entry and marks dirty.
    /// </summary>
    public void AddHistoryEntry(string agent, string action, string? details = null, params string[] filePaths)
    {
        if (_currentManifest == null)
            return;

        var entry = new HistoryEntry
        {
            Timestamp = DateTime.UtcNow,
            Agent = agent,
            Action = action,
            Details = details,
            FilesPaths = filePaths.ToList()
        };

        var updatedHistory = _currentManifest.Context.History.ToList();
        updatedHistory.Add(entry);

        var updatedContext = _currentManifest.Context with
        {
            History = updatedHistory
        };

        CurrentManifest = _currentManifest with
        {
            Context = updatedContext
        };

        _isDirty = true;
    }

    private void CreateBackup()
    {
        try
        {
            var timestamp = DateTime.UtcNow.ToString("yyyyMMdd-HHmmss");
            var backupPath = Path.Combine(_backupDirectory, $"manifest-{timestamp}.json");

            File.Copy(_manifestPath, backupPath);
            Console.WriteLine($"📦 Created backup: {Path.GetFileName(backupPath)}");
        }
        catch
        {
            // Backup failed, but don't block save
            Console.WriteLine("⚠️ Backup creation failed");
        }
    }

    private void CleanupOldBackups()
    {
        try
        {
            var backups = Directory.GetFiles(_backupDirectory, "manifest-*.json")
                .OrderByDescending(f => f)
                .Skip(_maxBackups)
                .ToList();

            foreach (var backup in backups)
            {
                File.Delete(backup);
            }

            if (backups.Count > 0)
            {
                Console.WriteLine($"🗑️  Cleaned up {backups.Count} old backups");
            }
        }
        catch
        {
            // Cleanup failed, not critical
        }
    }

    private ManifestV4? AttemptRecovery()
    {
        try
        {
            var backups = Directory.GetFiles(_backupDirectory, "manifest-*.json")
                .OrderByDescending(f => f)
                .ToList();

            foreach (var backup in backups)
            {
                try
                {
                    var json = File.ReadAllText(backup);
                    var manifest = JsonSerializer.Deserialize<ManifestV4>(json, JsonOptions);

                    if (manifest != null)
                    {
                        ManifestValidator.ValidateManifest(manifest, manifest.Context.SessionId);
                        CurrentManifest = manifest;
                        _isDirty = true; // Force save to restore main file
                        return manifest;
                    }
                }
                catch
                {
                    // This backup is also corrupted, try next
                    continue;
                }
            }
        }
        catch
        {
            // Recovery failed
        }

        return null;
    }

    private void AutoSaveCallback(object? state)
    {
        if (!_isDirty || _currentManifest == null)
            return;

        try
        {
            Save();
        }
        catch (Exception ex)
        {
            AutoSaveError?.Invoke(this, ex.Message);
        }
    }

    public void Dispose()
    {
        _autoSaveTimer?.Dispose();

        // Final save on dispose
        if (_isDirty && _currentManifest != null)
        {
            try
            {
                Save();
            }
            catch
            {
                // Best effort
            }
        }
    }
}
