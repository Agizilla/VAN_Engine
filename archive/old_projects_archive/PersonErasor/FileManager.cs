using System.Text;
using SovereignIDE.Core.Exceptions;
using SovereignIDE.Core.Models;
using SovereignIDE.Core.Validation;

namespace SovereignIDE.Core.FileSystem;

/// <summary>
/// Safe file I/O manager with validation and rollback support.
/// 
/// Contract:
/// - All paths MUST be validated before use
/// - File operations MUST be atomic where possible
/// - Errors MUST be copy-pasteable
/// </summary>
public class FileManager
{
    private readonly string _rootPath;
    private readonly string _sessionId;

    public FileManager(string rootPath, string sessionId)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(rootPath, nameof(rootPath));
        ArgumentException.ThrowIfNullOrWhiteSpace(sessionId, nameof(sessionId));

        _rootPath = Path.GetFullPath(rootPath);
        _sessionId = sessionId;

        // Ensure root exists
        Directory.CreateDirectory(_rootPath);
    }

    /// <summary>
    /// Writes file from manifest entry to disk.
    /// 
    /// Contract:
    /// - Path MUST be valid relative path
    /// - Content MUST NOT be null for created/modified files
    /// - Creates parent directories automatically
    /// - Overwrites existing files
    /// </summary>
    /// <exception cref="PathValidationException">Invalid path</exception>
    /// <exception cref="FileOperationException">Write failed</exception>
    public void WriteFile(FileEntry entry)
    {
        ArgumentNullException.ThrowIfNull(entry, nameof(entry));

        // Validate path
        PathValidator.ValidatePath(entry.Path, _sessionId);

        // Validate content
        ContentValidator.ValidateFileContent(entry, _sessionId);

        if (string.IsNullOrEmpty(entry.Content))
        {
            throw new ContentValidationException(
                $"Cannot write file '{entry.Path}' with null/empty content",
                $"File state: {entry.State}",
                _sessionId
            );
        }

        try
        {
            var fullPath = Path.Combine(_rootPath, entry.Path);
            var directory = Path.GetDirectoryName(fullPath);

            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }

            // Decode content based on encoding
            if (entry.ContentEncoding == "base64")
            {
                var bytes = Convert.FromBase64String(entry.Content);
                File.WriteAllBytes(fullPath, bytes);
            }
            else
            {
                File.WriteAllText(fullPath, entry.Content, Encoding.UTF8);
            }

            Console.WriteLine($"✅ Wrote: {entry.Path}");
        }
        catch (Exception ex) when (ex is not SovereignException)
        {
            throw new FileOperationException(
                $"Failed to write file: {ex.Message}",
                entry.Path,
                $"Writing file from manifest",
                _sessionId,
                ex
            );
        }
    }

    /// <summary>
    /// Reads file from disk into FileEntry.
    /// </summary>
    /// <exception cref="PathValidationException">Invalid path</exception>
    /// <exception cref="FileOperationException">Read failed</exception>
    public FileEntry ReadFile(string relativePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(relativePath, nameof(relativePath));

        // Validate path
        PathValidator.ValidatePath(relativePath, _sessionId);

        try
        {
            var fullPath = Path.Combine(_rootPath, relativePath);

            if (!File.Exists(fullPath))
            {
                throw new FileOperationException(
                    $"File not found: {relativePath}",
                    relativePath,
                    "Reading file",
                    _sessionId
                );
            }

            var content = File.ReadAllText(fullPath, Encoding.UTF8);
            var fileInfo = new FileInfo(fullPath);

            return new FileEntry
            {
                Path = relativePath,
                State = FileState.Unchanged,
                Content = content,
                ContentEncoding = "utf-8",
                Lines = content.Split('\n').Length,
                Size = (int)fileInfo.Length,
                LastModifiedDate = fileInfo.LastWriteTimeUtc
            };
        }
        catch (Exception ex) when (ex is not SovereignException)
        {
            throw new FileOperationException(
                $"Failed to read file: {ex.Message}",
                relativePath,
                "Reading file from disk",
                _sessionId,
                ex
            );
        }
    }

    /// <summary>
    /// Deletes file from disk.
    /// </summary>
    public void DeleteFile(string relativePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(relativePath, nameof(relativePath));

        PathValidator.ValidatePath(relativePath, _sessionId);

        try
        {
            var fullPath = Path.Combine(_rootPath, relativePath);

            if (File.Exists(fullPath))
            {
                File.Delete(fullPath);
                Console.WriteLine($"🗑️  Deleted: {relativePath}");
            }
        }
        catch (Exception ex)
        {
            throw new FileOperationException(
                $"Failed to delete file: {ex.Message}",
                relativePath,
                "Deleting file",
                _sessionId,
                ex
            );
        }
    }

    /// <summary>
    /// Writes multiple files in a batch.
    /// If any fail, attempts rollback (best-effort).
    /// </summary>
    public BatchResult WriteBatch(List<FileEntry> files)
    {
        var written = new List<string>();
        var failed = new List<(string path, Exception error)>();

        foreach (var file in files)
        {
            try
            {
                WriteFile(file);
                written.Add(file.Path);
            }
            catch (Exception ex)
            {
                failed.Add((file.Path, ex));

                // Rollback on first failure
                Console.WriteLine($"⚠️  Batch write failed at '{file.Path}', rolling back...");
                RollbackBatch(written);
                break;
            }
        }

        return new BatchResult
        {
            Successful = written,
            Failed = failed,
            RolledBack = failed.Count > 0
        };
    }

    private void RollbackBatch(List<string> writtenPaths)
    {
        foreach (var path in writtenPaths)
        {
            try
            {
                DeleteFile(path);
            }
            catch
            {
                Console.WriteLine($"⚠️  Rollback failed for: {path}");
            }
        }
    }

    /// <summary>
    /// Scans directory tree and builds file list.
    /// </summary>
    public List<FileEntry> ScanDirectory(string? relativePath = null)
    {
        var scanPath = string.IsNullOrWhiteSpace(relativePath)
            ? _rootPath
            : Path.Combine(_rootPath, relativePath);

        if (!Directory.Exists(scanPath))
            return new List<FileEntry>();

        var files = new List<FileEntry>();
        var allFiles = Directory.GetFiles(scanPath, "*.*", SearchOption.AllDirectories);

        foreach (var fullPath in allFiles)
        {
            try
            {
                var relPath = Path.GetRelativePath(_rootPath, fullPath);
                var fileInfo = new FileInfo(fullPath);

                files.Add(new FileEntry
                {
                    Path = relPath.Replace("\\", "/"), // Normalize to forward slashes
                    State = FileState.Unchanged,
                    Lines = File.ReadAllLines(fullPath).Length,
                    Size = (int)fileInfo.Length,
                    LastModifiedDate = fileInfo.LastWriteTimeUtc
                });
            }
            catch
            {
                // Skip unreadable files
            }
        }

        return files;
    }

    /// <summary>
    /// Checks if file exists on disk.
    /// </summary>
    public bool FileExists(string relativePath)
    {
        PathValidator.ValidatePath(relativePath, _sessionId);
        var fullPath = Path.Combine(_rootPath, relativePath);
        return File.Exists(fullPath);
    }
}

/// <summary>
/// Result of batch file write operation.
/// </summary>
public class BatchResult
{
    public required List<string> Successful { get; init; }
    public required List<(string path, Exception error)> Failed { get; init; }
    public required bool RolledBack { get; init; }
}
