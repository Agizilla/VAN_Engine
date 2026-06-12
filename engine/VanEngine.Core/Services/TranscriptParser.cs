using System.Text.Json;
using System.Text.RegularExpressions;

namespace VanEngine.Core.Services;

public class TranscriptParser
{
    private readonly string _transcriptPath;
    private readonly string _daName;

    public TranscriptParser(string transcriptPath, string daName = "Assistant")
    {
        _transcriptPath = transcriptPath;
        _daName = daName;
    }

    public async Task<ParsedTranscript> ParseAsync()
    {
        if (!File.Exists(_transcriptPath))
            return new ParsedTranscript { Raw = "", Error = "Transcript file not found" };

        var raw = await File.ReadAllTextAsync(_transcriptPath);
        var lines = raw.Split('\n', StringSplitOptions.RemoveEmptyEntries);

        var messages = new List<TranscriptMessage>();
        var lastAssistantMessage = "";
        var currentResponseParts = new List<string>();
        var lastHumanIndex = -1;

        for (int i = 0; i < lines.Length; i++)
        {
            try
            {
                var entry = JsonSerializer.Deserialize<TranscriptEntry>(lines[i]);
                if (entry == null) continue;

                if (entry.Type == "user" && IsRealUserMessage(entry.Message?.Content))
                {
                    lastHumanIndex = i;
                    messages.Add(new TranscriptMessage { Role = "user", Content = ExtractText(entry.Message?.Content), Timestamp = entry.Timestamp });
                }
                else if (entry.Type == "assistant")
                {
                    var text = ExtractText(entry.Message?.Content);
                    if (!string.IsNullOrEmpty(text))
                    {
                        lastAssistantMessage = text;
                        messages.Add(new TranscriptMessage { Role = "assistant", Content = text, Timestamp = entry.Timestamp });
                    }
                }
            }
            catch { }
        }

        for (int i = lastHumanIndex + 1; i < lines.Length; i++)
        {
            try
            {
                var entry = JsonSerializer.Deserialize<TranscriptEntry>(lines[i]);
                if (entry?.Type == "assistant")
                {
                    var text = ExtractText(entry.Message?.Content);
                    if (!string.IsNullOrEmpty(text))
                        currentResponseParts.Add(text);
                }
            }
            catch { }
        }

        var currentResponseText = string.Join("\n", currentResponseParts);
        var voiceCompletion = ExtractVoiceCompletion(currentResponseText, _daName);
        var plainCompletion = ExtractPlainCompletion(currentResponseText, _daName);
        var structured = ExtractStructuredSections(currentResponseText);
        var responseState = DetectResponseState(lastAssistantMessage);

        return new ParsedTranscript
        {
            Raw = raw,
            LastMessage = lastAssistantMessage,
            CurrentResponseText = currentResponseText,
            VoiceCompletion = voiceCompletion,
            PlainCompletion = plainCompletion,
            Structured = structured,
            ResponseState = responseState,
            Messages = messages,
            MessageCount = messages.Count
        };
    }

    private static bool IsRealUserMessage(object? content)
    {
        if (content == null) return false;
        if (content is string str) return !string.IsNullOrWhiteSpace(str);
        if (content is JsonElement elem)
        {
            if (elem.ValueKind == JsonValueKind.String)
                return !string.IsNullOrWhiteSpace(elem.GetString());
            if (elem.ValueKind == JsonValueKind.Array)
            {
                foreach (var item in elem.EnumerateArray())
                {
                    if (item.TryGetProperty("type", out var type) && type.GetString() == "text")
                        return true;
                }
            }
        }
        return false;
    }

    private static string ExtractText(object? content)
    {
        if (content == null) return "";
        if (content is string str) return str;
        if (content is JsonElement elem)
        {
            if (elem.ValueKind == JsonValueKind.String)
                return elem.GetString() ?? "";
            if (elem.ValueKind == JsonValueKind.Array)
            {
                var texts = new List<string>();
                foreach (var item in elem.EnumerateArray())
                {
                    if (item.TryGetProperty("type", out var type))
                    {
                        if (type.GetString() == "text" && item.TryGetProperty("text", out var text))
                            texts.Add(text.GetString() ?? "");
                        else if (item.TryGetProperty("text", out var directText))
                            texts.Add(directText.GetString() ?? "");
                    }
                }
                return string.Join(" ", texts);
            }
        }
        return "";
    }

    private static string ExtractVoiceCompletion(string text, string daName)
    {
        text = RemoveSystemReminders(text);

        var patterns = new[]
        {
            new Regex(@"[\u{1f5e3}\u{fe0f}]\s*\*?" + Regex.Escape(daName) + @":?\*?\s*(.+?)(?:\n|$)", RegexOptions.IgnoreCase),
            new Regex(@"\u{1f3af}\s*\*?COMPLETED:?\*?\s*(.+?)(?:\n|$)", RegexOptions.IgnoreCase)
        };

        foreach (var pattern in patterns)
        {
            var matches = pattern.Matches(text);
            if (matches.Count > 0)
            {
                var lastMatch = matches[^1];
                if (lastMatch.Success)
                {
                    var result = lastMatch.Groups[1].Value.Trim();
                    result = Regex.Replace(result, @"^\[AGENT:\w+\]\s*", "");
                    return result;
                }
            }
        }
        return "";
    }

    private static string ExtractPlainCompletion(string text, string daName)
    {
        var voice = ExtractVoiceCompletion(text, daName);
        if (!string.IsNullOrEmpty(voice))
        {
            voice = Regex.Replace(voice, @"\[.*?\]", "");
            voice = Regex.Replace(voice, @"\*\*?", "");
            voice = Regex.Replace(voice, @"\p{So}", "");
            voice = Regex.Replace(voice, @"\s+", " ").Trim();
            return voice;
        }

        var summaryMatch = Regex.Match(text, @"\u{1f4cb}\s*\*?SUMMARY:?\*?\s*(.+?)(?:\n|$)", RegexOptions.IgnoreCase);
        if (summaryMatch.Success)
        {
            var summary = summaryMatch.Groups[1].Value.Trim();
            return summary.Length > 30 ? summary[..27] + "..." : summary;
        }
        return "";
    }

    private static StructuredResponse ExtractStructuredSections(string text)
    {
        text = RemoveSystemReminders(text);
        return new StructuredResponse
        {
            Date = ExtractSection(text, @"\u{1f4c5}\s*(.+?)(?:\n|$)"),
            Summary = ExtractSection(text, @"\u{1f4cb}\s*SUMMARY:\s*(.+?)(?:\n|$)", true),
            Analysis = ExtractSection(text, @"\u{1f50d}\s*ANALYSIS:\s*(.+?)(?:\n|$)", true),
            Actions = ExtractSection(text, @"\u{26a1}\s*ACTIONS:\s*(.+?)(?:\n|$)", true),
            Results = ExtractSection(text, @"\u{2705}\s*RESULTS:\s*(.+?)(?:\n|$)", true),
            Status = ExtractSection(text, @"\u{1f4ca}\s*STATUS:\s*(.+?)(?:\n|$)", true),
            Next = ExtractSection(text, @"\u{27a1}\u{fe0f}\s*NEXT:\s*(.+?)(?:\n|$)", true)
        };
    }

    private static string ExtractSection(string text, string pattern, bool multiline = false)
    {
        var options = multiline ? RegexOptions.Multiline : RegexOptions.None;
        var match = Regex.Match(text, pattern, options);
        return match.Success ? match.Groups[1].Value.Trim() : "";
    }

    private static string RemoveSystemReminders(string text)
    {
        return Regex.Replace(text, @"<system-reminder>[\s\S]*?<\/system-reminder>", "");
    }

    private static ResponseState DetectResponseState(string lastMessage)
    {
        if (string.IsNullOrEmpty(lastMessage))
            return ResponseState.Completed;

        if (lastMessage.Contains("AskUserQuestion") || (lastMessage.Contains("?") && !lastMessage.Contains("COMPLETED")))
            return ResponseState.AwaitingInput;

        if (Regex.IsMatch(lastMessage, @"error|failed|exception|\u{274c}|\u{1f6a8}", RegexOptions.IgnoreCase))
            return ResponseState.Error;

        return ResponseState.Completed;
    }
}

public enum ResponseState { AwaitingInput, Completed, Error }

public class ParsedTranscript
{
    public string Raw { get; set; } = "";
    public string LastMessage { get; set; } = "";
    public string CurrentResponseText { get; set; } = "";
    public string VoiceCompletion { get; set; } = "";
    public string PlainCompletion { get; set; } = "";
    public StructuredResponse Structured { get; set; } = new();
    public ResponseState ResponseState { get; set; }
    public List<TranscriptMessage> Messages { get; set; } = new();
    public int MessageCount { get; set; }
    public string? Error { get; set; }
}

public class StructuredResponse
{
    public string Date { get; set; } = "";
    public string Summary { get; set; } = "";
    public string Analysis { get; set; } = "";
    public string Actions { get; set; } = "";
    public string Results { get; set; } = "";
    public string Status { get; set; } = "";
    public string Next { get; set; } = "";
}

public class TranscriptMessage
{
    public string Role { get; set; } = "";
    public string Content { get; set; } = "";
    public string? Timestamp { get; set; }
}

public class TranscriptEntry
{
    public string? Type { get; set; }
    public MessageContent? Message { get; set; }
    public string? Timestamp { get; set; }
}

public class MessageContent
{
    public object? Content { get; set; }
    public string? Role { get; set; }
}
