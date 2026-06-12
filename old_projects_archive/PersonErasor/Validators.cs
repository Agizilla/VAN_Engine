using System.Text;
using System.Text.RegularExpressions;
using SovereignIDE.Core.Exceptions;
using SovereignIDE.Core.Models;

namespace SovereignIDE.Core.Validation;

/// <summary>
/// Path validation with security-first design.
/// Contract: MUST block path traversal attacks and absolute paths.
/// </summary>
public static class PathValidator
{
    private static readonly char[] ForbiddenChars = { '<', '>', ':', '"', '|', '?', '*', '\0' };

    /// <summary>
    /// Validates that path is safe (relative, no traversal).
    /// </summary>
    /// <exception cref="PathValidationException">If path is invalid</exception>
    public static void ValidatePath(string path, string sessionId = "unknown")
    {
        if (string.IsNullOrWhiteSpace(path))
            throw new PathValidationException(
                "Path cannot be empty",
                path ?? "(null)",
                "Path validation",
                sessionId
            );

        // Block path traversal
        if (path.Contains(".."))
            throw new PathValidationException(
                "Path traversal not allowed",
                path,
                "Path contains '..'",
                sessionId
            );

        // Block absolute paths
        if (Path.IsPathRooted(path))
            throw new PathValidationException(
                "Absolute paths not allowed",
                path,
                "Path is rooted",
                sessionId
            );

        // Block forbidden characters
        if (path.IndexOfAny(ForbiddenChars) >= 0)
            throw new PathValidationException(
                "Path contains forbidden characters",
                path,
                $"Forbidden chars: {string.Join(", ", ForbiddenChars)}",
                sessionId
            );

        // Block URL-encoded traversal
        var lower = path.ToLowerInvariant();
        if (lower.Contains("%2e%2e") || lower.Contains("..%2f") || lower.Contains("%2e%2e%2f"))
            throw new PathValidationException(
                "URL-encoded path traversal detected",
                path,
                "Contains encoded '..' sequence",
                sessionId
            );

        // Block tilde expansion
        if (path.StartsWith("~"))
            throw new PathValidationException(
                "Tilde paths not allowed",
                path,
                "Path starts with '~'",
                sessionId
            );
    }

    /// <summary>
    /// Checks if path is valid without throwing.
    /// </summary>
    public static bool IsValidPath(string path)
    {
        try
        {
            ValidatePath(path);
            return true;
        }
        catch (PathValidationException)
        {
            return false;
        }
    }
}

/// <summary>
/// File state transition validator.
/// </summary>
public static class StateValidator
{
    /// <summary>
    /// Validates state transition is legal.
    /// </summary>
    /// <exception cref="StateTransitionException">If transition is invalid</exception>
    public static void ValidateTransition(FileState from, FileState to, string filePath, string sessionId = "unknown")
    {
        bool valid = (from, to) switch
        {
            (FileState.Unchanged, FileState.Modified) => true,
            (FileState.Unchanged, FileState.Deleted) => true,
            (FileState.Created, FileState.Modified) => true,
            (FileState.Created, FileState.Deleted) => true,
            (FileState.Modified, FileState.Deleted) => true,
            (FileState.Modified, FileState.Modified) => true, // Re-modified
            _ => false
        };

        if (!valid)
        {
            throw new StateTransitionException(
                $"Invalid state transition: {from} → {to}",
                $"File '{filePath}' cannot transition from {from} to {to}",
                sessionId
            );
        }
    }

    /// <summary>
    /// Checks if transition is valid without throwing.
    /// </summary>
    public static bool IsValidTransition(FileState from, FileState to)
    {
        return (from, to) switch
        {
            (FileState.Unchanged, FileState.Modified) => true,
            (FileState.Unchanged, FileState.Deleted) => true,
            (FileState.Created, FileState.Modified) => true,
            (FileState.Created, FileState.Deleted) => true,
            (FileState.Modified, FileState.Deleted) => true,
            (FileState.Modified, FileState.Modified) => true,
            _ => false
        };
    }
}

/// <summary>
/// Content encoding and format validator.
/// </summary>
public static class ContentValidator
{
    /// <summary>
    /// Validates file content matches declared encoding and state.
    /// </summary>
    /// <exception cref="ContentValidationException">If content is invalid</exception>
    public static void ValidateFileContent(FileEntry file, string sessionId = "unknown")
    {
        // Content requirements based on state
        if (file.State is FileState.Created or FileState.Modified)
        {
            if (string.IsNullOrEmpty(file.Content))
            {
                throw new ContentValidationException(
                    $"File '{file.Path}' is {file.State} but content is empty",
                    $"State: {file.State}",
                    sessionId
                );
            }
        }

        if (file.Content == null)
            return; // No content to validate

        // Validate encoding
        if (file.ContentEncoding == "base64")
        {
            try
            {
                Convert.FromBase64String(file.Content);
            }
            catch (FormatException ex)
            {
                throw new ContentValidationException(
                    $"File '{file.Path}' has invalid base64 content",
                    "Base64 decode failed",
                    sessionId,
                    ex
                );
            }
        }
        else if (file.ContentEncoding == "utf-8")
        {
            // Check for NULL bytes in text
            if (file.Content.Contains('\0'))
            {
                throw new ContentValidationException(
                    $"File '{file.Path}' contains NULL bytes in UTF-8 content",
                    "UTF-8 text cannot contain \\0",
                    sessionId
                );
            }

            // Validate UTF-8 encoding
            try
            {
                Encoding.UTF8.GetBytes(file.Content);
            }
            catch (EncoderFallbackException ex)
            {
                throw new ContentValidationException(
                    $"File '{file.Path}' contains invalid UTF-8 sequences",
                    "UTF-8 encoding validation failed",
                    sessionId,
                    ex
                );
            }
        }
    }
}

/// <summary>
/// Command security validator.
/// Contract: MUST detect dangerous commands and require approval.
/// </summary>
public static class CommandValidator
{
    private static readonly string[] DangerousPatterns =
    {
        @"rm\s+-[rf]{2}",
        @"rm\s+-[fr]{2}",
        @"del\s+/[fs]\s+/[fs]",
        @"format\s+",
        @"mkfs",
        @"dd\s+if=/dev/(zero|random)",
        @"shutdown",
        @"reboot",
        @"halt",
        @"chmod\s+777",
        @"chmod\s+-R\s+777",
        @"sudo\s+rm",
        @"sudo\s+shutdown",
        @">\s*/dev/(sda|hda)",
        @":\(\)\{.*:\|:&\s*\};:", // Fork bomb
        @"deltree",
        @"fdisk",
        @"mkfs\.",
    };

    /// <summary>
    /// Checks if command matches dangerous patterns.
    /// Contract: When true, command MUST require approval.
    /// </summary>
    public static bool IsDangerousCommand(string command)
    {
        if (string.IsNullOrWhiteSpace(command))
            return false;

        var lower = command.ToLowerInvariant();

        foreach (var pattern in DangerousPatterns)
        {
            if (Regex.IsMatch(lower, pattern, RegexOptions.IgnoreCase))
                return true;
        }

        return false;
    }

    /// <summary>
    /// Validates command and enforces approval if dangerous.
    /// </summary>
    /// <exception cref="DangerousCommandException">If command is dangerous but not approved</exception>
    public static void ValidateCommand(CommandEntry command, string sessionId = "unknown")
    {
        if (IsDangerousCommand(command.Command))
        {
            if (command.Status == CommandStatus.Pending && !command.RequiresApproval)
            {
                throw new DangerousCommandException(
                    "Dangerous command detected - approval required",
                    command.Command,
                    $"Command: {command.Command}",
                    sessionId
                );
            }
        }
    }
}

/// <summary>
/// Manifest version validator.
/// </summary>
public static class ManifestValidator
{
    private const string EXPECTED_VERSION = "4.0";

    /// <summary>
    /// Validates manifest version.
    /// </summary>
    /// <exception cref="UnsupportedVersionException">If version is not 4.0</exception>
    public static void ValidateVersion(string version, string sessionId = "unknown")
    {
        if (version != EXPECTED_VERSION)
        {
            throw new UnsupportedVersionException(
                $"Manifest version {version} is not supported. Expected: {EXPECTED_VERSION}",
                version,
                EXPECTED_VERSION,
                sessionId
            );
        }
    }

    /// <summary>
    /// Validates complete manifest structure.
    /// </summary>
    public static void ValidateManifest(ManifestV4 manifest, string sessionId = "unknown")
    {
        // Version check
        ValidateVersion(manifest.Version, sessionId);

        // Validate all file paths
        foreach (var file in manifest.Files)
        {
            PathValidator.ValidatePath(file.Path, sessionId);
            ContentValidator.ValidateFileContent(file, sessionId);
        }

        // Validate all commands
        foreach (var command in manifest.Commands)
        {
            CommandValidator.ValidateCommand(command, sessionId);
        }

        // Validate session ID format
        if (!Guid.TryParse(manifest.Context.SessionId, out _))
        {
            throw new ValidationException(
                "Invalid session ID format - must be GUID",
                $"SessionId: {manifest.Context.SessionId}",
                sessionId
            );
        }
    }
}

/// <summary>
/// History growth monitor.
/// Contract: MUST warn but NOT delete history automatically.
/// </summary>
public static class HistoryMonitor
{
    private const long WARN_THRESHOLD = 10_000_000;      // 10MB
    private const long CRITICAL_THRESHOLD = 50_000_000;  // 50MB

    public record HistoryStatus(
        long SizeBytes,
        bool ShouldWarn,
        bool IsCritical,
        string Message
    );

    /// <summary>
    /// Checks history size and returns status.
    /// </summary>
    public static HistoryStatus CheckHistorySize(List<HistoryEntry> history)
    {
        var json = System.Text.Json.JsonSerializer.Serialize(history);
        var sizeBytes = Encoding.UTF8.GetByteCount(json);
        var sizeMB = sizeBytes / 1_000_000.0;

        if (sizeBytes > CRITICAL_THRESHOLD)
        {
            return new HistoryStatus(
                sizeBytes,
                true,
                true,
                $"⚠️ CRITICAL: History size is {sizeMB:F1}MB. Consider archiving old entries."
            );
        }

        if (sizeBytes > WARN_THRESHOLD)
        {
            return new HistoryStatus(
                sizeBytes,
                true,
                false,
                $"ℹ️ History size: {sizeMB:F1}MB (growing, but not critical yet)"
            );
        }

        return new HistoryStatus(
            sizeBytes,
            false,
            false,
            $"History size: {sizeMB:F2}MB"
        );
    }
}
