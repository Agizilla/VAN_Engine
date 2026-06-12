# Response Parser Specification v4.0

**Version:** 4.0  
**Last Updated:** 2026-03-28  
**Purpose:** Define how to extract structured data from AI model responses (chatty format → manifest entries)

---

## Overview

AI models (DeepSeek, Claude, Gemini) produce **chatty responses** with embedded artifacts:
- Code blocks (```language ... ```)
- File paths (implicit or explicit)
- Commands (pip install, dotnet build, etc.)
- Decisions ("I decided to use X because Y")

This parser extracts those artifacts and converts them into **ManifestV4 entries**.

---

## Parsing Strategies

### Strategy 1: Markdown Code Blocks

**Pattern:**
```
```{language}
{content}
```
```

**Regex:**
```csharp
private static readonly Regex CodeBlockPattern = new(
    @"```(?<lang>\w+)?\s*\n(?<code>.*?)```",
    RegexOptions.Singleline | RegexOptions.Compiled
);
```

**Extraction:**
```csharp
public List<CodeBlock> ExtractCodeBlocks(string response)
{
    var blocks = new List<CodeBlock>();
    
    foreach (Match match in CodeBlockPattern.Matches(response))
    {
        blocks.Add(new CodeBlock
        {
            Language = match.Groups["lang"].Value,
            Content = match.Groups["code"].Value.Trim(),
            StartIndex = match.Index
        });
    }
    
    return blocks;
}
```

---

### Strategy 2: Filename Detection

**Heuristics:**

1. **Explicit markers:**
   ```
   // File: src/Parser.cs
   # File: config.json
   <!-- File: index.html -->
   ```

2. **Markdown headers before code:**
   ```
   ### `src/Parser.cs`
   
   ```csharp
   ...
   ```
   ```

3. **Context inference:**
   - If language is "csharp" and content contains "namespace", likely a .cs file
   - If language is "json" and content has "version" field, might be manifest
   - If language is "bash", might be a script or command

**Implementation:**
```csharp
public string? InferFilename(CodeBlock block, string surroundingContext)
{
    // Check for explicit file marker
    var fileMarkerPattern = new Regex(
        @"(?:File:|Filename:|Path:)\s*([^\n]+)",
        RegexOptions.IgnoreCase
    );
    
    var contextBefore = surroundingContext.Substring(
        Math.Max(0, block.StartIndex - 200),
        Math.Min(200, block.StartIndex)
    );
    
    var match = fileMarkerPattern.Match(contextBefore);
    if (match.Success)
    {
        return match.Groups[1].Value.Trim().Trim('`', '"', '\'');
    }
    
    // Check for markdown header
    var headerPattern = new Regex(@"###?\s+`?([^`\n]+)`?");
    match = headerPattern.Match(contextBefore);
    if (match.Success && match.Groups[1].Value.Contains("."))
    {
        return match.Groups[1].Value.Trim();
    }
    
    // Infer from language and content
    return block.Language switch
    {
        "csharp" when block.Content.Contains("namespace") => 
            InferCSharpFilename(block.Content),
        "json" when block.Content.Contains("\"version\"") =>
            "manifest.json",
        "markdown" when block.Content.StartsWith("#") =>
            "README.md",
        _ => null
    };
}

private string? InferCSharpFilename(string content)
{
    // Extract class name
    var classMatch = Regex.Match(content, @"class\s+(\w+)");
    if (classMatch.Success)
    {
        return $"{classMatch.Groups[1].Value}.cs";
    }
    
    return null;
}
```

---

### Strategy 3: Command Extraction

**Patterns:**

1. **Inline commands:**
   ```
   Run: pip install requests
   Execute: dotnet build
   ```

2. **Code blocks with "bash" or "shell":**
   ```bash
   npm install express
   ```

3. **Imperative statements:**
   ```
   Install the package: npm install lodash
   You should run: dotnet restore
   ```

**Implementation:**
```csharp
public List<CommandEntry> ExtractCommands(string response)
{
    var commands = new List<CommandEntry>();
    
    // Pattern 1: Explicit command markers
    var markerPattern = new Regex(
        @"(?:Run|Execute|Install|Command):\s*([^\n]+)",
        RegexOptions.IgnoreCase
    );
    
    foreach (Match match in markerPattern.Matches(response))
    {
        var cmd = match.Groups[1].Value.Trim();
        commands.Add(ParseCommand(cmd));
    }
    
    // Pattern 2: Bash/shell code blocks
    var bashBlocks = ExtractCodeBlocks(response)
        .Where(b => b.Language is "bash" or "shell" or "sh" or "powershell" or "cmd");
    
    foreach (var block in bashBlocks)
    {
        var lines = block.Content.Split('\n', StringSplitOptions.RemoveEmptyEntries);
        foreach (var line in lines)
        {
            if (!line.TrimStart().StartsWith("#")) // Skip comments
            {
                commands.Add(ParseCommand(line.Trim()));
            }
        }
    }
    
    return commands;
}

private CommandEntry ParseCommand(string commandLine)
{
    var entry = new CommandEntry
    {
        Id = Guid.NewGuid().ToString(),
        Command = commandLine,
        Status = CommandStatus.Pending,
        RequiresApproval = true,
        When = ExecutionTiming.Manual
    };
    
    // Detect command type
    if (commandLine.StartsWith("pip install"))
    {
        entry.Type = CommandType.PipInstall;
        var parts = commandLine.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length > 2)
        {
            entry.Package = parts[2];
            if (parts.Length > 3)
                entry.Version = parts[3];
        }
    }
    else if (commandLine.StartsWith("dotnet "))
    {
        entry.Type = CommandType.DotNet;
    }
    else if (commandLine.StartsWith("npm install"))
    {
        entry.Type = CommandType.Npm;
        var packageMatch = Regex.Match(commandLine, @"npm install\s+(@?[\w\-\/]+)");
        if (packageMatch.Success)
            entry.Package = packageMatch.Groups[1].Value;
    }
    else if (commandLine.Contains("powershell"))
    {
        entry.Type = CommandType.PowerShell;
    }
    else
    {
        entry.Type = CommandType.Bash;
    }
    
    // Check if dangerous
    if (IsDangerousCommand(commandLine))
    {
        entry.RequiresApproval = true; // Force approval
    }
    
    return entry;
}
```

---

### Strategy 4: Decision Extraction

**Pattern:**
```
I decided to {action} because {rationale}
We should use {choice} instead of {alternative} because {reason}
```

**Implementation:**
```csharp
public List<Decision> ExtractDecisions(string response, string agentName)
{
    var decisions = new List<Decision>();
    
    var patterns = new[]
    {
        @"I decided to ([^.]+)\s+because\s+([^.]+)",
        @"(?:We should|I'll) use ([^.]+) (?:instead of|rather than) ([^.]+) because ([^.]+)",
        @"Decision:\s*([^\n]+)"
    };
    
    foreach (var pattern in patterns)
    {
        foreach (Match match in Regex.Matches(response, pattern, RegexOptions.IgnoreCase))
        {
            decisions.Add(new Decision
            {
                Timestamp = DateTime.UtcNow,
                Agent = agentName,
                Decision = match.Groups[1].Value.Trim(),
                Rationale = match.Groups.Count > 2 ? match.Groups[2].Value.Trim() : null,
                Category = DecisionCategory.Implementation
            });
        }
    }
    
    return decisions;
}
```

---

### Strategy 5: JSON Manifest Detection

**Pattern:**
```json
{
  "version": "4.0",
  "context": { ... },
  "files": [ ... ]
}
```

**Contract:**
If a JSON code block contains `"version": "4.0"` AND `"files"`, it's a manifest.

**Implementation:**
```csharp
public ManifestV4? ExtractManifest(string response)
{
    var jsonBlocks = ExtractCodeBlocks(response)
        .Where(b => b.Language == "json");
    
    foreach (var block in jsonBlocks)
    {
        try
        {
            var doc = JsonDocument.Parse(block.Content);
            
            if (doc.RootElement.TryGetProperty("version", out var versionProp) &&
                versionProp.GetString() == "4.0" &&
                doc.RootElement.TryGetProperty("files", out _))
            {
                return JsonSerializer.Deserialize<ManifestV4>(block.Content);
            }
        }
        catch (JsonException)
        {
            // Not a valid manifest
            continue;
        }
    }
    
    return null;
}
```

---

## Full Parser Implementation

```csharp
public class ResponseParser
{
    private readonly string _agentName;
    
    public ResponseParser(string agentName = "Unknown")
    {
        _agentName = agentName;
    }
    
    /// <summary>
    /// Parse a chatty AI response into structured manifest updates.
    /// </summary>
    public ParsedResponse Parse(string response)
    {
        var result = new ParsedResponse();
        
        // 1. Check if entire response is a manifest
        result.Manifest = ExtractManifest(response);
        if (result.Manifest != null)
        {
            return result; // This is a formal manifest, nothing else to extract
        }
        
        // 2. Extract code blocks
        var codeBlocks = ExtractCodeBlocks(response);
        
        // 3. Try to infer filenames and create file entries
        foreach (var block in codeBlocks)
        {
            var filename = InferFilename(block, response);
            
            if (filename != null)
            {
                result.Files.Add(new FileEntry
                {
                    Path = filename,
                    State = FileState.Created,
                    Content = block.Content,
                    ContentEncoding = "utf-8",
                    Language = block.Language,
                    Lines = block.Content.Split('\n').Length,
                    Size = Encoding.UTF8.GetByteCount(block.Content),
                    CreatedDate = DateTime.UtcNow,
                    LastModifiedDate = DateTime.UtcNow,
                    ModelName = _agentName
                });
            }
            else
            {
                // Unknown file, add to "artifacts" list for manual review
                result.UnnamedArtifacts.Add(new CodeArtifact
                {
                    Language = block.Language,
                    Content = block.Content
                });
            }
        }
        
        // 4. Extract commands
        result.Commands = ExtractCommands(response);
        
        // 5. Extract decisions
        result.Decisions = ExtractDecisions(response, _agentName);
        
        // 6. Check for approval requests
        result.RequiresApproval = DetectApprovalRequest(response);
        
        // 7. Extract conversation turn metadata
        result.ConversationTurn = new ConversationTurn
        {
            Role = "assistant",
            Content = response,
            Timestamp = DateTime.UtcNow,
            Model = _agentName,
            Artifacts = result.Files.Select(f => f.Path).ToList()
        };
        
        return result;
    }
    
    private bool DetectApprovalRequest(string response)
    {
        var approvalKeywords = new[]
        {
            "requires approval",
            "please confirm",
            "should i proceed",
            "do you want me to",
            "would you like me to"
        };
        
        var lower = response.ToLowerInvariant();
        return approvalKeywords.Any(kw => lower.Contains(kw));
    }
}

public class ParsedResponse
{
    public ManifestV4? Manifest { get; set; }
    public List<FileEntry> Files { get; set; } = new();
    public List<CommandEntry> Commands { get; set; } = new();
    public List<Decision> Decisions { get; set; } = new();
    public List<CodeArtifact> UnnamedArtifacts { get; set; } = new();
    public bool RequiresApproval { get; set; }
    public ConversationTurn ConversationTurn { get; set; }
}

public class CodeArtifact
{
    public string Language { get; set; }
    public string Content { get; set; }
}
```

---

## Special Cases

### Case 1: Multi-File Responses

**Example:**
```
Here are the files:

### `src/Parser.cs`
```csharp
...
```

### `src/Validator.cs`
```csharp
...
```
```

**Handling:** Each code block gets parsed separately, filename inferred from preceding header.

---

### Case 2: Partial File Edits (Future)

**Example:**
```
Replace lines 45-60 in Parser.cs with:
```csharp
public void Parse() {
    // New implementation
}
```
```

**Current Behavior:** Full file replacement (v4.0 spec)

**Future (v5.0):** Line-level diffs
```json
{
  "path": "Parser.cs",
  "state": "modified",
  "edits": [
    {
      "type": "replace",
      "startLine": 45,
      "endLine": 60,
      "newContent": "..."
    }
  ]
}
```

---

### Case 3: Ambiguous Artifacts

**Example:**
```
Here's a helper function:
```csharp
public static int Add(int a, int b) => a + b;
```
```

**Handling:** No filename can be inferred → add to `UnnamedArtifacts` → show in UI for manual placement.

---

## Error Handling

### Invalid JSON
```csharp
try
{
    var manifest = JsonSerializer.Deserialize<ManifestV4>(jsonContent);
}
catch (JsonException ex)
{
    throw new ParsingException(
        "Failed to parse JSON manifest",
        $"Content: {jsonContent.Substring(0, 100)}...",
        ex
    );
}
```

### Malformed Code Blocks
```csharp
// Missing closing ```
var content = "```csharp\npublic class Foo";

// Parser should:
// 1. Log warning
// 2. Attempt recovery (treat rest of response as code)
// 3. Mark as "needs review"
```

---

## Performance Optimization

### Regex Compilation
```csharp
private static readonly Regex CodeBlockPattern = new(
    @"```(?<lang>\w+)?\s*\n(?<code>.*?)```",
    RegexOptions.Singleline | RegexOptions.Compiled // ← COMPILED
);
```

### Lazy Parsing
```csharp
// Don't parse unless needed
public Lazy<List<CommandEntry>> Commands => new(() => ExtractCommands(_response));
```

---

## Testing Requirements

### Unit Tests MUST Cover:

1. **Single code block extraction**
2. **Multiple code blocks**
3. **Nested code blocks (markdown in markdown)**
4. **Filename inference from headers**
5. **Filename inference from content**
6. **Command extraction (all types)**
7. **Dangerous command detection**
8. **Decision extraction**
9. **Manifest detection**
10. **Approval request detection**
11. **Malformed input handling**

### Example Test:
```csharp
[Fact]
public void ParseResponse_WithMultipleFiles_ExtractsAll()
{
    var response = @"
Here are the files:

### `Parser.cs`
```csharp
public class Parser { }
```

### `Validator.cs`
```csharp
public class Validator { }
```
";
    
    var parser = new ResponseParser("TestAgent");
    var result = parser.Parse(response);
    
    Assert.Equal(2, result.Files.Count);
    Assert.Contains(result.Files, f => f.Path == "Parser.cs");
    Assert.Contains(result.Files, f => f.Path == "Validator.cs");
}
```

---

## Integration with Auto-Executor

```csharp
public class AutoExecutor
{
    private readonly ResponseParser _parser;
    private readonly FileManager _fileManager;
    private readonly CommandQueue _commandQueue;
    
    public void ProcessResponse(string response, string agentName)
    {
        var parsed = new ResponseParser(agentName).Parse(response);
        
        if (parsed.Manifest != null)
        {
            // Full manifest received - replace current state
            ApplyManifest(parsed.Manifest);
            return;
        }
        
        // Process files
        foreach (var file in parsed.Files)
        {
            if (Paused || file.RequiresApproval)
            {
                QueueForApproval(file);
            }
            else
            {
                _fileManager.WriteFile(file);
            }
        }
        
        // Process commands
        foreach (var cmd in parsed.Commands)
        {
            _commandQueue.Add(cmd);
        }
        
        // Record decisions
        foreach (var decision in parsed.Decisions)
        {
            RecordDecision(decision);
        }
    }
}
```

---

## Summary

**Input:** Chatty AI response (text)  
**Output:** Structured data (files, commands, decisions)  
**Strategy:** Pattern matching + heuristics + validation  
**Fallback:** Unnamed artifacts for manual review  
**Performance:** Compiled regex, lazy evaluation  
**Testing:** Comprehensive unit tests for all patterns

This parser is the **bridge between natural language and machine-executable actions**.
