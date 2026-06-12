using System.Text.Json;
using VanEngine.WinForms.Models;

namespace VanEngine.WinForms.Services;

public class TranscriptParser
{
    public ParsedTranscript ParseFile(string filePath)
    {
        if (!File.Exists(filePath))
            return new ParsedTranscript { Error = $"File not found: {filePath}" };

        var content = File.ReadAllText(filePath);
        return ParseContent(content);
    }

    public ParsedTranscript ParseContent(string content)
    {
        var result = new ParsedTranscript();
        var lines = content.Split('\n', StringSplitOptions.RemoveEmptyEntries);
        var messages = new List<TranscriptMessage>();
        string lastAssistantMessage = "";

        foreach (var line in lines)
        {
            try
            {
                var entry = JsonSerializer.Deserialize<JsonElement>(line);
                var msgType = entry.GetProperty("type").GetString();

                if (msgType == "assistant")
                {
                    var text = ExtractText(entry);
                    if (!string.IsNullOrEmpty(text))
                    {
                        lastAssistantMessage = text;
                        messages.Add(new TranscriptMessage { Role = "assistant", Content = text });
                    }
                }
                else if (msgType == "user")
                {
                    var text = ExtractText(entry);
                    if (!string.IsNullOrEmpty(text))
                        messages.Add(new TranscriptMessage { Role = "user", Content = text });
                }
            }
            catch { }
        }

        result.LastMessage = lastAssistantMessage;
        result.Messages = messages;
        result.MessageCount = messages.Count;
        result.VoiceCompletion = ExtractVoiceCompletion(lastAssistantMessage);
        result.ResponseState = DetectResponseState(lastAssistantMessage);
        return result;
    }

    private string ExtractText(JsonElement entry)
    {
        if (!entry.TryGetProperty("message", out var msg)) return "";
        if (!msg.TryGetProperty("content", out var content)) return "";

        if (content.ValueKind == JsonValueKind.String)
            return content.GetString() ?? "";

        if (content.ValueKind == JsonValueKind.Array)
        {
            var texts = new List<string>();
            foreach (var block in content.EnumerateArray())
            {
                if (block.TryGetProperty("text", out var textVal))
                    texts.Add(textVal.GetString() ?? "");
                else if (block.TryGetProperty("type", out var typeVal) && typeVal.GetString() == "text")
                {
                    if (block.TryGetProperty("text", out var t))
                        texts.Add(t.GetString() ?? "");
                }
            }
            return string.Join(" ", texts);
        }
        return "";
    }

    private string ExtractVoiceCompletion(string text)
    {
        // Pattern match for voice completion marker (emoji-based)
        var lines = text.Split('\n');
        foreach (var line in lines)
        {
            var trimmed = line.Trim();
            if (trimmed.StartsWith("Assistant:") || trimmed.StartsWith("assistant:"))
                return trimmed[(trimmed.IndexOf(':') + 1)..].Trim();
        }
        return "";
    }

    private string DetectResponseState(string lastMessage)
    {
        if (string.IsNullOrEmpty(lastMessage)) return "completed";
        if (lastMessage.Contains("AskUserQuestion") || lastMessage.Contains("?"))
            return "awaiting_input";
        if (lastMessage.Contains("error", StringComparison.OrdinalIgnoreCase) ||
            lastMessage.Contains("failed", StringComparison.OrdinalIgnoreCase))
            return "error";
        return "completed";
    }
}
