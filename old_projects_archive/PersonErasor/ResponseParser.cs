using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using SovereignIDE.Core.Exceptions;
using SovereignIDE.Core.Models;

namespace SovereignIDE.Core.Parsers;

/// <summary>
/// Extracts structured data from chatty AI model responses.
/// Handles: code blocks, filenames, commands, decisions, manifests.
/// </summary>
public class ResponseParser
{
    private readonly string _agentName;

    private static readonly Regex CodeBlockPattern = new(
        @"```(?<lang>\w+)?\s*\n(?<code>.*?)```",
        RegexOptions.Singleline | RegexOptions.Compiled
    );

    private static readonly Regex FileMarkerPattern = new(
        @"(?:File:|Filename:|Path:)\s*([^\n]+)",
        RegexOptions.IgnoreCase | RegexOptions.Compiled
    );

    private static readonly Regex HeaderPattern = new(
        @"###?\s+`?([^`\n]+)`?",
        RegexOptions.Compiled
    );

    private static readonly Regex CommandMarkerPattern = new(
        @"(?:Run|Execute|Install|Command):\s*([^\n]+)",
        RegexOptions.IgnoreCase | RegexOptions.Compiled
    );

    public ResponseParser(string agentName = "Unknown")
    {
        _agentName = agentName;
    }

    /// <summary>
    /// Parse a chatty AI response into structured manifest updates.
    /// 
    /// Contract:
    /// - Extracts code blocks with language tags
    /// - Infers filenames from context
    /// - Extracts commands (pip, dotnet, npm, bash)
    /// - Extracts decisions
    /// - Detects full manifests
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
                    Language = block.Language ?? "unknown",
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

    private List<CodeBlock> ExtractCodeBlocks(string response)
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

    private string? InferFilename(CodeBlock block, string surroundingContext)
    {
        // Check for explicit file marker
        var contextBefore = surroundingContext.Substring(
            Math.Max(0, block.StartIndex - 200),
            Math.Min(200, block.StartIndex)
        );

        var match = FileMarkerPattern.Match(contextBefore);
        if (match.Success)
        {
            return match.Groups[1].Value.Trim().Trim('`', '"', '\'');
        }

        // Check for markdown header
        match = HeaderPattern.Match(contextBefore);
        if (match.Success && match.Groups[1].Value.Contains("."))
        {
            return match.Groups[1].Value.Trim();
        }

        // Infer from language and content
        return block.Language switch
        {
            "csharp" when block.Content.Contains("namespace") => InferCSharpFilename(block.Content),
            "json" when block.Content.Contains("\"version\"") => "manifest.json",
            "markdown" when block.Content.StartsWith("#") => "README.md",
            "xml" when block.Content.Contains("<Project") => InferProjectFilename(block.Content),
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

        // Extract interface name
        var interfaceMatch = Regex.Match(content, @"interface\s+(\w+)");
        if (interfaceMatch.Success)
        {
            return $"{interfaceMatch.Groups[1].Value}.cs";
        }

        return null;
    }

    private string? InferProjectFilename(string content)
    {
        // Try to extract project name from TargetFramework or AssemblyName
        var match = Regex.Match(content, @"<AssemblyName>(.*?)</AssemblyName>");
        if (match.Success)
        {
            return $"{match.Groups[1].Value}.csproj";
        }

        return "Project.csproj";
    }

    private List<CommandEntry> ExtractCommands(string response)
    {
        var commands = new List<CommandEntry>();

        // Pattern 1: Explicit command markers
        foreach (Match match in CommandMarkerPattern.Matches(response))
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
                var trimmed = line.Trim();
                if (!trimmed.StartsWith("#") && !string.IsNullOrWhiteSpace(trimmed)) // Skip comments
                {
                    commands.Add(ParseCommand(trimmed));
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
            Type = CommandType.Bash, // Default
            Status = CommandStatus.Pending,
            RequiresApproval = true,
            When = ExecutionTiming.Manual
        };

        // Detect command type
        if (commandLine.StartsWith("pip install"))
        {
            entry = entry with { Type = CommandType.PipInstall };
            var parts = commandLine.Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length > 2)
            {
                entry = entry with { Package = parts[2] };
                if (parts.Length > 3)
                    entry = entry with { Version = parts[3] };
            }
        }
        else if (commandLine.StartsWith("dotnet "))
        {
            entry = entry with { Type = CommandType.DotNet };
        }
        else if (commandLine.StartsWith("npm install"))
        {
            entry = entry with { Type = CommandType.Npm };
            var packageMatch = Regex.Match(commandLine, @"npm install\s+(@?[\w\-\/]+)");
            if (packageMatch.Success)
                entry = entry with { Package = packageMatch.Groups[1].Value };
        }
        else if (commandLine.Contains("powershell"))
        {
            entry = entry with { Type = CommandType.PowerShell };
        }
        else if (commandLine.StartsWith("nuget install") || commandLine.Contains("NuGet"))
        {
            entry = entry with { Type = CommandType.NuGet };
        }

        // Check if dangerous (force approval)
        if (Validation.CommandValidator.IsDangerousCommand(commandLine))
        {
            entry = entry with { RequiresApproval = true };
        }

        return entry;
    }

    private List<Decision> ExtractDecisions(string response, string agentName)
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
                var decisionText = match.Groups[1].Value.Trim();
                var rationale = match.Groups.Count > 2 ? match.Groups[2].Value.Trim() : null;

                decisions.Add(new Decision
                {
                    Timestamp = DateTime.UtcNow,
                    Agent = agentName,
                    DecisionText = decisionText,
                    Rationale = rationale,
                    Category = DecisionCategory.Implementation
                });
            }
        }

        return decisions;
    }

    private ManifestV4? ExtractManifest(string response)
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

    private bool DetectApprovalRequest(string response)
    {
        var approvalKeywords = new[]
        {
            "requires approval",
            "please confirm",
            "should i proceed",
            "do you want me to",
            "would you like me to",
            "shall i"
        };

        var lower = response.ToLowerInvariant();
        return approvalKeywords.Any(kw => lower.Contains(kw));
    }
}

/// <summary>
/// Result of parsing an AI response.
/// </summary>
public class ParsedResponse
{
    public ManifestV4? Manifest { get; set; }
    public List<FileEntry> Files { get; set; } = new();
    public List<CommandEntry> Commands { get; set; } = new();
    public List<Decision> Decisions { get; set; } = new();
    public List<CodeArtifact> UnnamedArtifacts { get; set; } = new();
    public bool RequiresApproval { get; set; }
    public ConversationTurn? ConversationTurn { get; set; }
}

/// <summary>
/// Code artifact with unknown filename.
/// </summary>
public class CodeArtifact
{
    public required string Language { get; set; }
    public required string Content { get; set; }
}

/// <summary>
/// Extracted code block with metadata.
/// </summary>
internal class CodeBlock
{
    public string? Language { get; set; }
    public required string Content { get; set; }
    public int StartIndex { get; set; }
}
