using System.Text.Json;
using System.Text.RegularExpressions;

namespace VanEngine.Core.Services;

public class ActivityParser
{
    private readonly string _sessionDirectory;
    private readonly string _updatesDirectory;

    public ActivityParser(string baseDirectory)
    {
        _sessionDirectory = Path.Combine(baseDirectory, "sessions");
        _updatesDirectory = Path.Combine(baseDirectory, "MEMORY", "UPDATES");
        Directory.CreateDirectory(_updatesDirectory);
    }

    public async Task<ParsedActivity> ParseTodayActivityAsync(string? sessionFilter = null)
    {
        var sessionFiles = GetSessionFiles(DateTime.Today.AddDays(-1), sessionFilter);
        return await ParseActivity(sessionFiles);
    }

    public async Task<ParsedActivity> ParseSessionAsync(string sessionId)
    {
        var sessionFile = Path.Combine(_sessionDirectory, $"{sessionId}.jsonl");
        if (!File.Exists(sessionFile))
            return new ParsedActivity { Error = $"Session not found: {sessionId}" };
        return await ParseActivity(new[] { sessionFile });
    }

    private string[] GetSessionFiles(DateTime since, string? sessionFilter)
    {
        if (!Directory.Exists(_sessionDirectory)) return Array.Empty<string>();
        var files = Directory.GetFiles(_sessionDirectory, "*.jsonl")
            .Select(f => new { Path = f, Modified = File.GetLastWriteTime(f) })
            .Where(f => f.Modified >= since)
            .OrderByDescending(f => f.Modified)
            .Select(f => f.Path).ToArray();
        if (!string.IsNullOrEmpty(sessionFilter))
            files = files.Where(f => f.Contains(sessionFilter)).ToArray();
        return files;
    }

    private async Task<ParsedActivity> ParseActivity(string[] sessionFiles)
    {
        var activity = new ParsedActivity
        {
            Date = DateTime.Today.ToString("yyyy-MM-dd"),
            Categories = new ActivityCategories()
        };
        var filesModified = new HashSet<string>();
        var filesCreated = new HashSet<string>();

        foreach (var sessionFile in sessionFiles)
        {
            var lines = await File.ReadAllLinesAsync(sessionFile);
            foreach (var line in lines)
            {
                if (string.IsNullOrWhiteSpace(line)) continue;
                try
                {
                    var entry = JsonSerializer.Deserialize<SessionEntry>(line);
                    if (entry?.Type != "assistant" || entry.Message?.Content == null) continue;

                    var content = ExtractToolUse(entry.Message.Content);
                    if (content == null) continue;

                    foreach (var tool in content.Tools)
                    {
                        if (tool.Name == "Write" && tool.Input?.TryGetValue("file_path", out var filePathObj) == true)
                        {
                            var filePath = filePathObj.ToString();
                            if (!string.IsNullOrEmpty(filePath) && filePath.Contains("/.claude/"))
                                filesCreated.Add(filePath);
                        }
                        else if (tool.Name == "Edit" && tool.Input?.TryGetValue("file_path", out filePathObj) == true)
                        {
                            var filePath = filePathObj.ToString();
                            if (!string.IsNullOrEmpty(filePath) && filePath.Contains("/.claude/"))
                                filesModified.Add(filePath);
                        }
                    }
                }
                catch { }
            }
        }

        foreach (var file in filesCreated) filesModified.Remove(file);
        activity.FilesCreated = filesCreated.ToList();
        activity.FilesModified = filesModified.ToList();

        CategorizeChanges(activity.FilesCreated, "created", activity);
        CategorizeChanges(activity.FilesModified, "modified", activity);

        var summaryParts = new List<string>();
        if (activity.SkillsAffected.Count > 0) summaryParts.Add($"{activity.SkillsAffected.Count} skill(s) affected");
        if (activity.Categories.Tools.Count > 0) summaryParts.Add($"{activity.Categories.Tools.Count} tool(s)");
        if (activity.Categories.Hooks.Count > 0) summaryParts.Add($"{activity.Categories.Hooks.Count} hook(s)");
        if (activity.Categories.Workflows.Count > 0) summaryParts.Add($"{activity.Categories.Workflows.Count} workflow(s)");
        if (activity.Categories.Architecture.Count > 0) summaryParts.Add("architecture changes");
        activity.Summary = summaryParts.Count > 0 ? string.Join(", ", summaryParts) : "documentation updates";

        return activity;
    }

    private static ToolUseContent? ExtractToolUse(object? content)
    {
        if (content == null) return null;
        try
        {
            var elements = JsonSerializer.Deserialize<List<ContentBlock>>(content.ToString() ?? "[]");
            if (elements == null) return null;
            var tools = new List<ToolUse>();
            foreach (var block in elements)
            {
                if (block.Type == "tool_use" && !string.IsNullOrEmpty(block.Name))
                    tools.Add(new ToolUse { Name = block.Name, Input = block.Input });
            }
            return new ToolUseContent { Tools = tools };
        }
        catch { return null; }
    }

    private void CategorizeChanges(List<string> files, string action, ParsedActivity activity)
    {
        var skipPatterns = new[] { @"MEMORY\\UPDATES\\", @"MEMORY\\", @"WORK\\.*\\scratch\\", @"\.quote-cache$", @"history\.jsonl$", @"cache\\", @"plans\\" };
        var categoryPatterns = new Dictionary<string, string>
        {
            ["skills"] = @"skills\\[^\\]+\\",
            ["workflows"] = @"Workflows\\",
            ["tools"] = @"skills\\[^\\]+\\Tools\\",
            ["hooks"] = @"hooks\\",
            ["architecture"] = @"(ARCHITECTURE|PAISYSTEMARCHITECTURE|SKILLSYSTEM)\.md$"
        };

        foreach (var file in files)
        {
            if (skipPatterns.Any(p => Regex.IsMatch(file, p, RegexOptions.IgnoreCase))) continue;

            var skillMatch = Regex.Match(file, @"skills\\([^\\]+)\\");
            if (skillMatch.Success) activity.SkillsAffected.Add(skillMatch.Groups[1].Value);

            var category = categoryPatterns.FirstOrDefault(kv => Regex.IsMatch(file, kv.Value, RegexOptions.IgnoreCase)).Key ?? "other";
            var change = new FileChange { Path = file, Action = action, RelativePath = GetRelativePath(file) };

            switch (category)
            {
                case "skills": activity.Categories.Skills.Add(change); break;
                case "workflows": activity.Categories.Workflows.Add(change); break;
                case "tools": activity.Categories.Tools.Add(change); break;
                case "hooks": activity.Categories.Hooks.Add(change); break;
                case "architecture": activity.Categories.Architecture.Add(change); break;
                default: activity.Categories.Other.Add(change); break;
            }
        }
    }

    private static string GetRelativePath(string fullPath)
    {
        var claudeIndex = fullPath.IndexOf("/.claude/", StringComparison.OrdinalIgnoreCase);
        if (claudeIndex == -1) claudeIndex = fullPath.IndexOf("\\.claude\\", StringComparison.OrdinalIgnoreCase);
        return claudeIndex != -1 ? fullPath[(claudeIndex + 9)..] : fullPath;
    }

    public async Task<string> GenerateUpdateFileAsync(ParsedActivity activity)
    {
        var timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");
        var id = $"{activity.Date}-{GenerateSlug(activity.Summary)}";
        var yearMonth = DateTime.Now.ToString("yyyy/MM");
        var updateDir = Path.Combine(_updatesDirectory, yearMonth);
        Directory.CreateDirectory(updateDir);

        var updatePath = Path.Combine(updateDir, $"{activity.Date}_{id}.md");

        var content = $@"---
id: ""{id}""
timestamp: ""{timestamp}""
title: ""System Update: {activity.Summary}""
significance: ""moderate""
change_type: ""multi_area""
files_affected:
{string.Join("\n", activity.FilesCreated.Concat(activity.FilesModified).Take(20).Select(f => $"  - \"{GetRelativePath(f)}\""))}
---

# System Update: {activity.Summary}

**Timestamp:** {timestamp}
**Significance:** Moderate
**Change Type:** Multi-Area

## Summary

{activity.Summary}

## Changes Made

### Skills
{string.Join("\n", activity.Categories.Skills.Select(c => $"- `{c.RelativePath}` - {c.Action}"))}

### Tools
{string.Join("\n", activity.Categories.Tools.Select(c => $"- `{c.RelativePath}` - {c.Action}"))}

### Hooks
{string.Join("\n", activity.Categories.Hooks.Select(c => $"- `{c.RelativePath}` - {c.Action}"))}

## Integrity Check

- **References Found:** 0
- **References Updated:** 0

## Verification

*Auto-generated from session activity.*
---
**Status:** Auto-generated
";
        await File.WriteAllTextAsync(updatePath, content);
        return updatePath;
    }

    private static string GenerateSlug(string text)
    {
        var slug = Regex.Replace(text.ToLower(), @"[^a-z0-9]+", "-");
        return slug.Trim('-');
    }
}

public class ParsedActivity
{
    public string Date { get; set; } = "";
    public string? SessionId { get; set; }
    public ActivityCategories Categories { get; set; } = new();
    public string Summary { get; set; } = "";
    public List<string> FilesModified { get; set; } = new();
    public List<string> FilesCreated { get; set; } = new();
    public HashSet<string> SkillsAffected { get; set; } = new();
    public string? Error { get; set; }
}

public class ActivityCategories
{
    public List<FileChange> Skills { get; set; } = new();
    public List<FileChange> Workflows { get; set; } = new();
    public List<FileChange> Tools { get; set; } = new();
    public List<FileChange> Hooks { get; set; } = new();
    public List<FileChange> Architecture { get; set; } = new();
    public List<FileChange> Documentation { get; set; } = new();
    public List<FileChange> Other { get; set; } = new();
}

public class FileChange
{
    public string Path { get; set; } = "";
    public string Action { get; set; } = "";
    public string RelativePath { get; set; } = "";
}

public class SessionEntry
{
    public string? Type { get; set; }
    public MessageContent? Message { get; set; }
}

public class ContentBlock
{
    public string Type { get; set; } = "";
    public string? Name { get; set; }
    public Dictionary<string, object>? Input { get; set; }
}

public class ToolUse
{
    public string Name { get; set; } = "";
    public Dictionary<string, object>? Input { get; set; }
}

public class ToolUseContent
{
    public List<ToolUse> Tools { get; set; } = new();
}
