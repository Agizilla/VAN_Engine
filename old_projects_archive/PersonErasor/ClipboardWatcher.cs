using System.Runtime.InteropServices;
using System.Windows.Forms;
using SovereignIDE.Core.Parsers;

namespace SovereignIDE.Core.Services;

/// <summary>
/// Monitors clipboard for AI responses and triggers parsing.
/// 
/// Contract:
/// - Watches clipboard changes
/// - Detects AI response patterns
/// - Fires event when response detected
/// - Does NOT auto-execute (respects pause button)
/// </summary>
public class ClipboardWatcher : IDisposable
{
    private readonly System.Threading.Timer _pollTimer;
    private string _lastClipboardContent = string.Empty;
    private bool _enabled = true;

    public event EventHandler<string>? ResponseDetected;

    public bool Enabled
    {
        get => _enabled;
        set => _enabled = value;
    }

    public ClipboardWatcher(int pollIntervalMs = 500)
    {
        _pollTimer = new System.Threading.Timer(
            CheckClipboard,
            null,
            TimeSpan.FromMilliseconds(pollIntervalMs),
            TimeSpan.FromMilliseconds(pollIntervalMs)
        );
    }

    private void CheckClipboard(object? state)
    {
        if (!_enabled)
            return;

        try
        {
            // Must access clipboard on STA thread
            var content = GetClipboardText();

            if (string.IsNullOrWhiteSpace(content))
                return;

            // Check if content changed
            if (content == _lastClipboardContent)
                return;

            _lastClipboardContent = content;

            // Detect if this looks like an AI response
            if (IsAIResponse(content))
            {
                ResponseDetected?.Invoke(this, content);
            }
        }
        catch
        {
            // Clipboard access can fail if another app has it locked
            // Silently continue
        }
    }

    private string GetClipboardText()
    {
        string text = string.Empty;

        // Create STA thread to access clipboard
        var thread = new Thread(() =>
        {
            try
            {
                if (Clipboard.ContainsText())
                {
                    text = Clipboard.GetText();
                }
            }
            catch
            {
                // Clipboard locked
            }
        });

        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join(TimeSpan.FromMilliseconds(100)); // Timeout

        return text;
    }

    /// <summary>
    /// Heuristics to detect AI response patterns.
    /// 
    /// Looks for:
    /// - Code blocks (```)
    /// - Common AI phrases
    /// - JSON structures
    /// - File markers
    /// </summary>
    private bool IsAIResponse(string content)
    {
        if (content.Length < 50)
            return false; // Too short

        // Check for code blocks
        if (content.Contains("```"))
            return true;

        // Check for common AI response patterns
        var aiPhrases = new[]
        {
            "Here's the",
            "Here is the",
            "I'll create",
            "I've created",
            "Let me",
            "I can help",
            "Based on",
            "To solve this",
            "First, let's",
            "Here are the files"
        };

        var lower = content.ToLowerInvariant();
        if (aiPhrases.Any(phrase => lower.Contains(phrase.ToLowerInvariant())))
        {
            // Additional validation: must contain some code-like content
            if (content.Contains("class ") ||
                content.Contains("function ") ||
                content.Contains("def ") ||
                content.Contains("public ") ||
                content.Contains("namespace ") ||
                content.Contains("{") && content.Contains("}"))
            {
                return true;
            }
        }

        // Check for JSON manifest
        if (content.Contains("\"version\"") && content.Contains("\"files\""))
            return true;

        return false;
    }

    public void Pause()
    {
        _enabled = false;
    }

    public void Resume()
    {
        _enabled = true;
    }

    public void Dispose()
    {
        _pollTimer?.Dispose();
    }
}
