# Manifest Validation Contracts v4.0

**Version:** 4.0  
**Last Updated:** 2026-03-28  
**Purpose:** Define all validation rules, security constraints, and error handling contracts for ManifestSchema_v4.json

---

## Core Validation Rules

### 1. Path Validation (SECURITY CRITICAL)

**Contract:**
```
MUST NOT allow path traversal attacks
MUST reject paths containing: "..", "~", absolute paths
MUST validate against OS-specific forbidden characters
MUST normalize path separators (/ vs \)
```

**Implementation:**
```csharp
public static bool IsValidRelativePath(string path)
{
    if (string.IsNullOrWhiteSpace(path))
        return false;
    
    // Block path traversal
    if (path.Contains(".."))
        return false;
    
    // Block absolute paths
    if (Path.IsPathRooted(path))
        return false;
    
    // Block forbidden characters (Windows + Unix)
    char[] forbidden = { '<', '>', ':', '"', '|', '?', '*', '\0' };
    if (path.IndexOfAny(forbidden) >= 0)
        return false;
    
    // Block directory traversal via alternate encodings
    if (path.Contains("%2e%2e") || path.Contains("..%2f"))
        return false;
    
    return true;
}
```

**Error Message Format:**
```
ERROR: Invalid file path
Path: "{path}"
Reason: {specific_violation}
Allowed: Relative paths only, no '..' or absolute paths
Example: "src/Parser.cs" ✓  |  "../../../etc/passwd" ✗
```

---

### 2. File State Transitions

**Valid Transitions:**
```
unchanged → modified
unchanged → deleted
created   → modified
created   → deleted
modified  → deleted

INVALID:
deleted   → anything (file is gone)
created   → unchanged (nonsensical)
```

**Contract:**
```csharp
public static bool IsValidStateTransition(FileState from, FileState to)
{
    return (from, to) switch
    {
        (FileState.Unchanged, FileState.Modified) => true,
        (FileState.Unchanged, FileState.Deleted) => true,
        (FileState.Created, FileState.Modified) => true,
        (FileState.Created, FileState.Deleted) => true,
        (FileState.Modified, FileState.Deleted) => true,
        (FileState.Modified, FileState.Modified) => true, // Re-modified
        _ => false
    };
}
```

---

### 3. Content Encoding Rules

**Contract:**
```
If contentEncoding == "utf-8":
  - content MUST be valid UTF-8
  - content MUST NOT contain NULL bytes (\0)
  
If contentEncoding == "base64":
  - content MUST be valid base64
  - MUST decode to valid binary
  
If content is NULL:
  - state MUST be "unchanged" OR "deleted"
  
If state is "created" OR "modified":
  - content MUST NOT be NULL
```

**Validation:**
```csharp
public static void ValidateFileContent(FileEntry file)
{
    if (file.State == FileState.Created || file.State == FileState.Modified)
    {
        if (string.IsNullOrEmpty(file.Content))
            throw new ValidationException($"File {file.Path} is {file.State} but content is empty");
    }
    
    if (file.ContentEncoding == "base64")
    {
        try
        {
            Convert.FromBase64String(file.Content ?? "");
        }
        catch (FormatException)
        {
            throw new ValidationException($"File {file.Path} has invalid base64 content");
        }
    }
    
    if (file.ContentEncoding == "utf-8" && file.Content?.Contains('\0') == true)
    {
        throw new ValidationException($"File {file.Path} contains NULL bytes in UTF-8 content");
    }
}
```

---

### 4. Command Execution Security

**Dangerous Commands (ALWAYS require approval):**
```
rm -rf
del /f /s /q
format
mkfs
dd if=/dev/zero
shutdown
reboot
chmod 777
sudo
su
```

**Contract:**
```csharp
public static bool IsDangerousCommand(string command)
{
    string[] dangerousPatterns = {
        "rm -rf", "rm -fr", "rm.*-r.*-f", "rm.*-f.*-r",
        "del /f /s", "del /s /f",
        "format ", "mkfs", 
        "dd if=/dev/zero", "dd if=/dev/random",
        "shutdown", "reboot", "halt",
        "chmod 777", "chmod -R 777",
        "sudo rm", "sudo shutdown",
        "> /dev/sda", "> /dev/hda",
        ":(){ :|:& };:" // Fork bomb
    };
    
    string lower = command.ToLowerInvariant();
    
    foreach (var pattern in dangerousPatterns)
    {
        if (Regex.IsMatch(lower, pattern.Replace(" ", "\\s+")))
            return true;
    }
    
    return false;
}
```

**Execution Contract:**
```
1. MUST validate command against dangerous patterns
2. MUST require approval for dangerous commands (override requiresApproval to TRUE)
3. MUST run in isolated process (no shell injection)
4. MUST capture stdout AND stderr
5. MUST timeout after 60 seconds (configurable)
6. MUST record exit code
```

---

### 5. Manifest Version Compatibility

**Contract:**
```
Parser MUST reject manifest.version != "4.0"
Parser SHOULD attempt graceful degradation for "3.x" if feasible
Parser MUST NOT attempt to parse unknown future versions
```

**Implementation:**
```csharp
public static ManifestV4 ParseManifest(string json)
{
    // Quick version check before full parse
    var versionCheck = JsonDocument.Parse(json);
    var version = versionCheck.RootElement.GetProperty("version").GetString();
    
    if (version != "4.0")
    {
        throw new UnsupportedVersionException(
            $"Manifest version {version} is not supported. Expected: 4.0"
        );
    }
    
    return JsonSerializer.Deserialize<ManifestV4>(json, JsonOptions);
}
```

---

### 6. History Growth Monitoring

**Contract:**
```
MUST track context.history size
SHOULD warn at 10MB
SHOULD suggest archival at 50MB
MUST NOT automatically delete history (user decision)
```

**Monitoring:**
```csharp
public class HistoryMonitor
{
    private const long WARN_THRESHOLD = 10_000_000;  // 10MB
    private const long CRITICAL_THRESHOLD = 50_000_000; // 50MB
    
    public void CheckHistory(ManifestV4 manifest)
    {
        var historyJson = JsonSerializer.Serialize(manifest.Context.History);
        var sizeBytes = Encoding.UTF8.GetByteCount(historyJson);
        
        if (sizeBytes > CRITICAL_THRESHOLD)
        {
            Logger.Warning($"⚠️ CRITICAL: History size is {sizeBytes / 1_000_000}MB");
            Logger.Warning("Consider archiving old entries to separate file.");
            Logger.Warning("Archive path suggestion: {0}", 
                Path.Combine(manifest.Context.ProjectRoot, "manifest-archive.json"));
        }
        else if (sizeBytes > WARN_THRESHOLD)
        {
            Logger.Info($"ℹ️ History size: {sizeBytes / 1_000_000}MB (growing)");
        }
    }
}
```

---

### 7. Session ID Uniqueness

**Contract:**
```
sessionId MUST be UUID v4
sessionId MUST be generated once per manifest creation
sessionId MUST persist across IDE restarts
sessionId MUST change only on explicit "New Session" action
```

**Generation:**
```csharp
public static string GenerateSessionId()
{
    return Guid.NewGuid().ToString();
}

public static bool IsValidSessionId(string sessionId)
{
    return Guid.TryParse(sessionId, out _);
}
```

---

### 8. Decision Recording Rules

**Contract:**
```
MUST include timestamp (ISO 8601)
MUST include agent (who decided)
MUST include decision summary
SHOULD include rationale
SHOULD include category
MAY include file references
```

**Recording:**
```csharp
public void RecordDecision(
    string agent,
    string decision,
    string rationale,
    DecisionCategory category,
    params string[] references)
{
    manifest.Decisions.Add(new Decision
    {
        Timestamp = DateTime.UtcNow,
        Agent = agent,
        Decision = decision,
        Rationale = rationale,
        Category = category,
        References = references.ToList()
    });
    
    Logger.Info($"📝 Decision recorded: {decision}");
}
```

---

## Error Handling Contracts

### 1. Copy-Pasteable Error Format

**Contract:**
```
ALL errors MUST be formatted for copy-paste to AI chat
MUST include context (what was being done)
MUST include data (what values caused the error)
MUST include stack trace (for debugging)
SHOULD automatically copy to clipboard
```

**Template:**
```
=== SOVEREIGN IDE ERROR ===
Message: {short_description}
Context: {what_operation_failed}
Time: {ISO_8601_timestamp}

Data:
  {key1}: {value1}
  {key2}: {value2}

Stack Trace:
{full_stack_trace}

Inner Exception:
{inner_exception_if_present}

Manifest Version: {manifest.version}
Session ID: {manifest.context.sessionId}

[This error has been copied to clipboard]
```

---

### 2. Exception Hierarchy

```
SovereignException (base)
├── ValidationException
│   ├── PathValidationException
│   ├── ContentValidationException
│   └── StateTransitionException
├── ExecutionException
│   ├── CommandExecutionException
│   ├── FileOperationException
│   └── ProcessTimeoutException
├── ParsingException
│   ├── JsonParsingException
│   └── ResponseParsingException
└── SecurityException
    ├── DangerousCommandException
    └── UnauthorizedPathException
```

**Base Contract:**
```csharp
public abstract class SovereignException : Exception
{
    public string Context { get; init; }
    public Dictionary<string, object> Data { get; } = new();
    public string SessionId { get; init; }
    
    protected SovereignException(
        string message, 
        string context, 
        string sessionId,
        Exception? inner = null)
        : base(message, inner)
    {
        Context = context;
        SessionId = sessionId;
    }
    
    public string ToCopyPasteFormat()
    {
        var sb = new StringBuilder();
        sb.AppendLine("=== SOVEREIGN IDE ERROR ===");
        sb.AppendLine($"Message: {Message}");
        sb.AppendLine($"Context: {Context}");
        sb.AppendLine($"Time: {DateTime.UtcNow:yyyy-MM-dd HH:mm:ss} UTC");
        sb.AppendLine();
        
        if (Data.Any())
        {
            sb.AppendLine("Data:");
            foreach (var kvp in Data)
                sb.AppendLine($"  {kvp.Key}: {kvp.Value}");
            sb.AppendLine();
        }
        
        sb.AppendLine($"Session ID: {SessionId}");
        sb.AppendLine();
        sb.AppendLine("Stack Trace:");
        sb.AppendLine(StackTrace);
        
        if (InnerException != null)
        {
            sb.AppendLine();
            sb.AppendLine("Inner Exception:");
            sb.AppendLine(InnerException.Message);
        }
        
        sb.AppendLine();
        sb.AppendLine("[This error has been copied to clipboard]");
        
        return sb.ToString();
    }
}
```

---

## UI Layout Validation

### Contract
```
If ui.type == "three-column":
  - MUST have exactly 3 columns
  
If ui.columns[i].width is integer:
  - MUST be positive
  
If ui.columns[i].width is string "1fr":
  - At least ONE column MUST use flex

If ui.columns[i].body.dataSource is specified:
  - MUST be valid JSON path into manifest
  - Examples: "manifest.files", "manifest.commands"
```

---

## Performance Constraints

### Contract
```
Manifest parsing MUST complete in <100ms for files <10MB
File write operations MUST batch if >10 files
Command execution MUST timeout after 60s (configurable)
UI updates MUST debounce to max 60fps
```

---

## Testing Requirements

### Unit Test Contracts
```
MUST test path validation with evil inputs:
  - "../../../etc/passwd"
  - "C:\\Windows\\System32"
  - "..\\..\\Users\\Administrator"
  - "path/with/../../traversal"
  - "path%2e%2e/encoded"
  
MUST test state transitions (all 16 combinations)

MUST test command danger detection:
  - "rm -rf /"
  - "sudo rm -rf /"
  - "del /f /s /q C:\\"
  - "format c:"
  - "chmod 777 -R /"
  
MUST test JSON parsing error handling:
  - Malformed JSON
  - Missing required fields
  - Invalid version
  - Invalid enum values
```

---

## Migration from v3.x to v4.0

**Contract:**
```
1. Check version field
2. If "3.x", attempt migration:
   - Add missing v4 fields with defaults
   - Rename changed fields
   - Validate all paths
3. If migration succeeds, save as v4.0
4. If migration fails, reject with clear error
```

**Migration Example:**
```csharp
public static ManifestV4 MigrateFromV3(string json)
{
    var v3 = JsonSerializer.Deserialize<ManifestV3>(json);
    
    return new ManifestV4
    {
        Version = "4.0",
        Context = new Context
        {
            Model = v3.ModelName ?? "Unknown",
            SessionId = Guid.NewGuid().ToString(),
            Owner = "Migrated",
            CreatedDate = DateTime.UtcNow,
            LastModifiedDate = DateTime.UtcNow,
            History = new List<HistoryEntry>
            {
                new()
                {
                    Timestamp = DateTime.UtcNow,
                    Agent = "System",
                    Action = "Migrated from v3.x to v4.0"
                }
            }
        },
        Files = v3.Files.Select(f => new FileEntry
        {
            Path = f.Path,
            State = FileState.Unchanged, // Default for migration
            Lines = f.Lines,
            Size = f.Size,
            LastModifiedDate = f.LastModifiedDate
        }).ToList(),
        Commands = new List<CommandEntry>(),
        Decisions = new List<Decision>(),
        Conversation = new List<ConversationTurn>()
    };
}
```

---

## Summary of Critical Contracts

1. **Path Validation**: MUST block traversal attacks
2. **Command Security**: MUST flag dangerous commands
3. **Error Format**: MUST be copy-pasteable
4. **State Transitions**: MUST follow valid graph
5. **Content Encoding**: MUST match declared type
6. **History Growth**: MUST monitor, SHOULD warn
7. **Version Check**: MUST reject unknown versions
8. **Session Persistence**: MUST survive restarts

---

**All contracts are MANDATORY for production deployment.**
