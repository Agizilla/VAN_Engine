using System.Text.Json.Serialization;

namespace SovereignIDE.Core.Models;

/// <summary>
/// Root manifest structure for Sovereign IDE.
/// Version 4.0 - Complete project state including files, commands, decisions, and conversation history.
/// </summary>
public record ManifestV4
{
    [JsonPropertyName("version")]
    public required string Version { get; init; }

    [JsonPropertyName("context")]
    public required ContextInfo Context { get; init; }

    [JsonPropertyName("files")]
    public required List<FileEntry> Files { get; init; }

    [JsonPropertyName("commands")]
    public List<CommandEntry> Commands { get; init; } = new();

    [JsonPropertyName("decisions")]
    public List<Decision> Decisions { get; init; } = new();

    [JsonPropertyName("conversation")]
    public List<ConversationTurn> Conversation { get; init; } = new();

    [JsonPropertyName("ui")]
    public UILayout? UI { get; init; }
}

/// <summary>
/// Context information about the session and project.
/// </summary>
public record ContextInfo
{
    [JsonPropertyName("model")]
    public required string Model { get; init; }

    [JsonPropertyName("sessionId")]
    public required string SessionId { get; init; }

    [JsonPropertyName("owner")]
    public required string Owner { get; init; }

    [JsonPropertyName("cumulativeTokens")]
    public long CumulativeTokens { get; init; }

    [JsonPropertyName("createdDate")]
    public DateTime CreatedDate { get; init; }

    [JsonPropertyName("lastModifiedDate")]
    public DateTime LastModifiedDate { get; init; }

    [JsonPropertyName("projectRoot")]
    public string? ProjectRoot { get; init; }

    [JsonPropertyName("handoffMode")]
    public bool HandoffMode { get; init; }

    [JsonPropertyName("handoffTarget")]
    public string? HandoffTarget { get; init; }

    [JsonPropertyName("handoffNotes")]
    public List<string> HandoffNotes { get; init; } = new();

    [JsonPropertyName("history")]
    public List<HistoryEntry> History { get; init; } = new();
}

/// <summary>
/// Single entry in the project history log.
/// </summary>
public record HistoryEntry
{
    [JsonPropertyName("timestamp")]
    public required DateTime Timestamp { get; init; }

    [JsonPropertyName("agent")]
    public required string Agent { get; init; }

    [JsonPropertyName("action")]
    public required string Action { get; init; }

    [JsonPropertyName("details")]
    public string? Details { get; init; }

    [JsonPropertyName("filesPaths")]
    public List<string> FilesPaths { get; init; } = new();
}

/// <summary>
/// Represents a file in the project with its current state.
/// </summary>
public record FileEntry
{
    [JsonPropertyName("path")]
    public required string Path { get; init; }

    [JsonPropertyName("state")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public required FileState State { get; init; }

    [JsonPropertyName("content")]
    public string? Content { get; init; }

    [JsonPropertyName("contentEncoding")]
    public string ContentEncoding { get; init; } = "utf-8";

    [JsonPropertyName("lines")]
    public int? Lines { get; init; }

    [JsonPropertyName("size")]
    public int? Size { get; init; }

    [JsonPropertyName("createdDate")]
    public DateTime? CreatedDate { get; init; }

    [JsonPropertyName("lastModifiedDate")]
    public DateTime? LastModifiedDate { get; init; }

    [JsonPropertyName("modelName")]
    public string? ModelName { get; init; }

    [JsonPropertyName("language")]
    public string? Language { get; init; }

    [JsonPropertyName("replacesVersion")]
    public string? ReplacesVersion { get; init; }
}

/// <summary>
/// File state relative to last sync.
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum FileState
{
    [JsonPropertyName("unchanged")]
    Unchanged,

    [JsonPropertyName("modified")]
    Modified,

    [JsonPropertyName("created")]
    Created,

    [JsonPropertyName("deleted")]
    Deleted
}

/// <summary>
/// Command to be executed (pending approval or completed).
/// </summary>
public record CommandEntry
{
    [JsonPropertyName("id")]
    public string Id { get; init; } = Guid.NewGuid().ToString();

    [JsonPropertyName("type")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public required CommandType Type { get; init; }

    [JsonPropertyName("command")]
    public required string Command { get; init; }

    [JsonPropertyName("package")]
    public string? Package { get; init; }

    [JsonPropertyName("version")]
    public string? Version { get; init; }

    [JsonPropertyName("when")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public ExecutionTiming When { get; init; } = ExecutionTiming.Manual;

    [JsonPropertyName("status")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public CommandStatus Status { get; init; } = CommandStatus.Pending;

    [JsonPropertyName("approvedBy")]
    public string? ApprovedBy { get; init; }

    [JsonPropertyName("executedDate")]
    public DateTime? ExecutedDate { get; init; }

    [JsonPropertyName("output")]
    public string? Output { get; init; }

    [JsonPropertyName("exitCode")]
    public int? ExitCode { get; init; }

    [JsonPropertyName("requiresApproval")]
    public bool RequiresApproval { get; init; } = true;
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum CommandType
{
    [JsonPropertyName("pip_install")]
    PipInstall,

    [JsonPropertyName("bash")]
    Bash,

    [JsonPropertyName("powershell")]
    PowerShell,

    [JsonPropertyName("cmd")]
    Cmd,

    [JsonPropertyName("dotnet")]
    DotNet,

    [JsonPropertyName("npm")]
    Npm,

    [JsonPropertyName("nuget")]
    NuGet
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum ExecutionTiming
{
    [JsonPropertyName("immediate")]
    Immediate,

    [JsonPropertyName("after_file_writes")]
    AfterFileWrites,

    [JsonPropertyName("manual")]
    Manual,

    [JsonPropertyName("on_startup")]
    OnStartup
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum CommandStatus
{
    [JsonPropertyName("pending")]
    Pending,

    [JsonPropertyName("approved")]
    Approved,

    [JsonPropertyName("rejected")]
    Rejected,

    [JsonPropertyName("executed")]
    Executed,

    [JsonPropertyName("failed")]
    Failed
}

/// <summary>
/// Architectural or process decision with rationale.
/// </summary>
public record Decision
{
    [JsonPropertyName("timestamp")]
    public required DateTime Timestamp { get; init; }

    [JsonPropertyName("agent")]
    public required string Agent { get; init; }

    [JsonPropertyName("decision")]
    public required string DecisionText { get; init; }

    [JsonPropertyName("rationale")]
    public string? Rationale { get; init; }

    [JsonPropertyName("category")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public DecisionCategory Category { get; init; } = DecisionCategory.Implementation;

    [JsonPropertyName("references")]
    public List<string> References { get; init; } = new();
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum DecisionCategory
{
    [JsonPropertyName("architectural")]
    Architectural,

    [JsonPropertyName("implementation")]
    Implementation,

    [JsonPropertyName("process")]
    Process,

    [JsonPropertyName("tooling")]
    Tooling,

    [JsonPropertyName("security")]
    Security
}

/// <summary>
/// Single turn in the conversation history.
/// </summary>
public record ConversationTurn
{
    [JsonPropertyName("role")]
    public required string Role { get; init; }

    [JsonPropertyName("content")]
    public required string Content { get; init; }

    [JsonPropertyName("timestamp")]
    public DateTime? Timestamp { get; init; }

    [JsonPropertyName("model")]
    public string? Model { get; init; }

    [JsonPropertyName("artifacts")]
    public List<string> Artifacts { get; init; } = new();

    [JsonPropertyName("tokens")]
    public TokenUsage? Tokens { get; init; }
}

public record TokenUsage
{
    [JsonPropertyName("input")]
    public int Input { get; init; }

    [JsonPropertyName("output")]
    public int Output { get; init; }
}

/// <summary>
/// UI layout specification for rendering.
/// </summary>
public record UILayout
{
    [JsonPropertyName("type")]
    public string Type { get; init; } = "three-column";

    [JsonPropertyName("theme")]
    public string Theme { get; init; } = "dark";

    [JsonPropertyName("columns")]
    public List<UIColumn> Columns { get; init; } = new();

    [JsonPropertyName("statusBar")]
    public StatusBarConfig? StatusBar { get; init; }

    [JsonPropertyName("pauseButton")]
    public PauseButtonConfig? PauseButton { get; init; }
}

public record UIColumn
{
    [JsonPropertyName("id")]
    public required string Id { get; init; }

    [JsonPropertyName("width")]
    public required object Width { get; init; } // int or string "1fr"

    [JsonPropertyName("header")]
    public UIHeader? Header { get; init; }

    [JsonPropertyName("body")]
    public UIBody? Body { get; init; }
}

public record UIHeader
{
    [JsonPropertyName("title")]
    public string? Title { get; init; }

    [JsonPropertyName("kicker")]
    public string? Kicker { get; init; }

    [JsonPropertyName("actions")]
    public List<string> Actions { get; init; } = new();
}

public record UIBody
{
    [JsonPropertyName("type")]
    public string? Type { get; init; }

    [JsonPropertyName("dataSource")]
    public string? DataSource { get; init; }

    [JsonPropertyName("tabs")]
    public List<string> Tabs { get; init; } = new();
}

public record StatusBarConfig
{
    [JsonPropertyName("visible")]
    public bool Visible { get; init; } = true;

    [JsonPropertyName("height")]
    public int Height { get; init; } = 24;
}

public record PauseButtonConfig
{
    [JsonPropertyName("visible")]
    public bool Visible { get; init; } = true;

    [JsonPropertyName("position")]
    public string Position { get; init; } = "top-right";

    [JsonPropertyName("size")]
    public ButtonSize? Size { get; init; }
}

public record ButtonSize
{
    [JsonPropertyName("width")]
    public int Width { get; init; } = 120;

    [JsonPropertyName("height")]
    public int Height { get; init; } = 40;
}
