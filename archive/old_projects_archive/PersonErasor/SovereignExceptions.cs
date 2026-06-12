using System.Text;

namespace SovereignIDE.Core.Exceptions;

/// <summary>
/// Base exception for all Sovereign IDE errors.
/// All exceptions produce copy-pasteable error messages for AI debugging.
/// </summary>
public abstract class SovereignException : Exception
{
    public string Context { get; init; }
    public Dictionary<string, object> ErrorData { get; } = new();
    public string SessionId { get; init; }

    protected SovereignException(
        string message,
        string context,
        string sessionId = "unknown",
        Exception? inner = null)
        : base(message, inner)
    {
        Context = context;
        SessionId = sessionId;
    }

    /// <summary>
    /// Formats error for copy-paste into AI chat.
    /// Contract: MUST be readable by both humans and AI models.
    /// </summary>
    public string ToCopyPasteFormat()
    {
        var sb = new StringBuilder();
        sb.AppendLine("=== SOVEREIGN IDE ERROR ===");
        sb.AppendLine($"Message: {Message}");
        sb.AppendLine($"Context: {Context}");
        sb.AppendLine($"Time: {DateTime.UtcNow:yyyy-MM-dd HH:mm:ss} UTC");
        sb.AppendLine();

        if (ErrorData.Count > 0)
        {
            sb.AppendLine("Data:");
            foreach (var kvp in ErrorData)
                sb.AppendLine($"  {kvp.Key}: {kvp.Value}");
            sb.AppendLine();
        }

        sb.AppendLine($"Session ID: {SessionId}");
        sb.AppendLine();
        sb.AppendLine("Stack Trace:");
        sb.AppendLine(StackTrace ?? "(no stack trace)");

        if (InnerException != null)
        {
            sb.AppendLine();
            sb.AppendLine("Inner Exception:");
            sb.AppendLine($"  {InnerException.Message}");
            sb.AppendLine($"  {InnerException.StackTrace}");
        }

        sb.AppendLine();
        sb.AppendLine("[This error has been copied to clipboard]");

        return sb.ToString();
    }
}

/// <summary>
/// Validation errors (schema, contracts, business rules).
/// </summary>
public class ValidationException : SovereignException
{
    public ValidationException(string message, string context, string sessionId = "unknown", Exception? inner = null)
        : base(message, context, sessionId, inner)
    {
    }
}

/// <summary>
/// Path validation errors (security critical).
/// </summary>
public class PathValidationException : ValidationException
{
    public string InvalidPath { get; init; }

    public PathValidationException(string message, string invalidPath, string context, string sessionId = "unknown")
        : base(message, context, sessionId)
    {
        InvalidPath = invalidPath;
        ErrorData["InvalidPath"] = invalidPath;
        ErrorData["Reason"] = "Path traversal or absolute path detected";
        ErrorData["AllowedFormat"] = "Relative paths only (e.g., 'src/Parser.cs')";
    }
}

/// <summary>
/// Content validation errors (encoding, format).
/// </summary>
public class ContentValidationException : ValidationException
{
    public ContentValidationException(string message, string context, string sessionId = "unknown")
        : base(message, context, sessionId)
    {
    }
}

/// <summary>
/// State transition errors (invalid file state changes).
/// </summary>
public class StateTransitionException : ValidationException
{
    public StateTransitionException(string message, string context, string sessionId = "unknown")
        : base(message, context, sessionId)
    {
    }
}

/// <summary>
/// Execution errors (commands, file operations, processes).
/// </summary>
public class ExecutionException : SovereignException
{
    public ExecutionException(string message, string context, string sessionId = "unknown", Exception? inner = null)
        : base(message, context, sessionId, inner)
    {
    }
}

/// <summary>
/// Command execution failures.
/// </summary>
public class CommandExecutionException : ExecutionException
{
    public string Command { get; init; }
    public int? ExitCode { get; init; }

    public CommandExecutionException(
        string message,
        string command,
        int? exitCode,
        string context,
        string sessionId = "unknown",
        Exception? inner = null)
        : base(message, context, sessionId, inner)
    {
        Command = command;
        ExitCode = exitCode;
        ErrorData["Command"] = command;
        if (exitCode.HasValue)
            ErrorData["ExitCode"] = exitCode.Value;
    }
}

/// <summary>
/// File I/O failures.
/// </summary>
public class FileOperationException : ExecutionException
{
    public string FilePath { get; init; }

    public FileOperationException(
        string message,
        string filePath,
        string context,
        string sessionId = "unknown",
        Exception? inner = null)
        : base(message, context, sessionId, inner)
    {
        FilePath = filePath;
        ErrorData["FilePath"] = filePath;
    }
}

/// <summary>
/// Process timeout.
/// </summary>
public class ProcessTimeoutException : ExecutionException
{
    public int TimeoutSeconds { get; init; }

    public ProcessTimeoutException(
        string message,
        int timeoutSeconds,
        string context,
        string sessionId = "unknown")
        : base(message, context, sessionId)
    {
        TimeoutSeconds = timeoutSeconds;
        ErrorData["TimeoutSeconds"] = timeoutSeconds;
    }
}

/// <summary>
/// Parsing errors (JSON, response extraction).
/// </summary>
public class ParsingException : SovereignException
{
    public ParsingException(string message, string context, string sessionId = "unknown", Exception? inner = null)
        : base(message, context, sessionId, inner)
    {
    }
}

/// <summary>
/// JSON parsing failures.
/// </summary>
public class JsonParsingException : ParsingException
{
    public JsonParsingException(string message, string context, string sessionId = "unknown", Exception? inner = null)
        : base(message, context, sessionId, inner)
    {
    }
}

/// <summary>
/// Response parsing failures (AI output extraction).
/// </summary>
public class ResponseParsingException : ParsingException
{
    public ResponseParsingException(string message, string context, string sessionId = "unknown", Exception? inner = null)
        : base(message, context, sessionId, inner)
    {
    }
}

/// <summary>
/// Security violations.
/// </summary>
public class SecurityException : SovereignException
{
    public SecurityException(string message, string context, string sessionId = "unknown", Exception? inner = null)
        : base(message, context, sessionId, inner)
    {
    }
}

/// <summary>
/// Dangerous command detection.
/// </summary>
public class DangerousCommandException : SecurityException
{
    public string Command { get; init; }

    public DangerousCommandException(
        string message,
        string command,
        string context,
        string sessionId = "unknown")
        : base(message, context, sessionId)
    {
        Command = command;
        ErrorData["Command"] = command;
        ErrorData["Reason"] = "Command matches dangerous pattern (rm -rf, format, etc.)";
        ErrorData["RequiresApproval"] = true;
    }
}

/// <summary>
/// Unauthorized path access.
/// </summary>
public class UnauthorizedPathException : SecurityException
{
    public UnauthorizedPathException(string message, string context, string sessionId = "unknown")
        : base(message, context, sessionId)
    {
    }
}

/// <summary>
/// Unsupported manifest version.
/// </summary>
public class UnsupportedVersionException : SovereignException
{
    public string ReceivedVersion { get; init; }
    public string ExpectedVersion { get; init; }

    public UnsupportedVersionException(
        string message,
        string receivedVersion,
        string expectedVersion = "4.0",
        string sessionId = "unknown")
        : base(message, $"Manifest version mismatch", sessionId)
    {
        ReceivedVersion = receivedVersion;
        ExpectedVersion = expectedVersion;
        ErrorData["ReceivedVersion"] = receivedVersion;
        ErrorData["ExpectedVersion"] = expectedVersion;
    }
}
