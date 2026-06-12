using System.Windows.Forms;

namespace SovereignIDE.UI.Services;

/// <summary>
/// Centralized keyboard shortcut management.
/// 
/// Supports:
/// - Global hotkeys
/// - Context-specific shortcuts
/// - Customizable key bindings
/// - Shortcut discovery (help dialog)
/// </summary>
public class KeyboardShortcutManager
{
    private readonly Dictionary<Keys, Action> _globalShortcuts = new();
    private readonly Dictionary<string, Dictionary<Keys, Action>> _contextShortcuts = new();
    private string _currentContext = "global";

    public event EventHandler<string>? ShortcutExecuted;

    public KeyboardShortcutManager()
    {
        RegisterDefaultShortcuts();
    }

    private void RegisterDefaultShortcuts()
    {
        // Global shortcuts
        RegisterGlobal(Keys.Control | Keys.Space, "TogglePause", "Toggle pause mode");
        RegisterGlobal(Keys.Control | Keys.V, "PasteResponse", "Paste AI response");
        RegisterGlobal(Keys.Control | Keys.S, "SaveManifest", "Save manifest");
        RegisterGlobal(Keys.Control | Keys.O, "OpenProject", "Open project");
        RegisterGlobal(Keys.Control | Keys.Shift | Keys.S, "SaveAs", "Save manifest as...");
        RegisterGlobal(Keys.Control | Keys.Q, "Exit", "Exit application");
        RegisterGlobal(Keys.F1, "ShowHelp", "Show help");
        RegisterGlobal(Keys.F5, "Refresh", "Refresh view");
        RegisterGlobal(Keys.Control | Keys.N, "NewManifest", "New manifest");
        RegisterGlobal(Keys.Control | Keys.Shift | Keys.C, "ClearQueue", "Clear command queue");
        RegisterGlobal(Keys.Control | Keys.E, "ExecuteApproved", "Execute approved commands");
        RegisterGlobal(Keys.Escape, "CancelOperation", "Cancel current operation");

        // File Explorer context
        RegisterContext("FileExplorer", Keys.Delete, "DeleteFile", "Delete selected file");
        RegisterContext("FileExplorer", Keys.F2, "RenameFile", "Rename selected file");
        RegisterContext("FileExplorer", Keys.Enter, "OpenFile", "Open selected file");
        RegisterContext("FileExplorer", Keys.Control | Keys.C, "CopyPath", "Copy file path");

        // Command Queue context
        RegisterContext("CommandQueue", Keys.Enter, "ApproveCommand", "Approve selected command");
        RegisterContext("CommandQueue", Keys.Delete, "RejectCommand", "Reject selected command");
        RegisterContext("CommandQueue", Keys.Control | Keys.A, "ApproveAll", "Approve all pending");
    }

    /// <summary>
    /// Registers a global shortcut.
    /// </summary>
    public void RegisterGlobal(Keys keys, string actionName, string description)
    {
        _globalShortcuts[keys] = () =>
        {
            ShortcutExecuted?.Invoke(this, actionName);
        };
    }

    /// <summary>
    /// Registers a context-specific shortcut.
    /// </summary>
    public void RegisterContext(string context, Keys keys, string actionName, string description)
    {
        if (!_contextShortcuts.ContainsKey(context))
        {
            _contextShortcuts[context] = new Dictionary<Keys, Action>();
        }

        _contextShortcuts[context][keys] = () =>
        {
            ShortcutExecuted?.Invoke(this, actionName);
        };
    }

    /// <summary>
    /// Sets the current context.
    /// </summary>
    public void SetContext(string context)
    {
        _currentContext = context;
    }

    /// <summary>
    /// Processes a key press.
    /// Returns true if handled.
    /// </summary>
    public bool ProcessKey(Keys keyData)
    {
        // Try context-specific first
        if (_contextShortcuts.ContainsKey(_currentContext) &&
            _contextShortcuts[_currentContext].TryGetValue(keyData, out var contextAction))
        {
            contextAction.Invoke();
            return true;
        }

        // Try global
        if (_globalShortcuts.TryGetValue(keyData, out var globalAction))
        {
            globalAction.Invoke();
            return true;
        }

        return false;
    }

    /// <summary>
    /// Gets all registered shortcuts for help display.
    /// </summary>
    public List<ShortcutInfo> GetAllShortcuts()
    {
        var shortcuts = new List<ShortcutInfo>();

        // Add global
        foreach (var kvp in _globalShortcuts)
        {
            shortcuts.Add(new ShortcutInfo
            {
                Keys = kvp.Key,
                Context = "Global",
                Description = GetKeyDescription(kvp.Key)
            });
        }

        // Add context-specific
        foreach (var context in _contextShortcuts)
        {
            foreach (var kvp in context.Value)
            {
                shortcuts.Add(new ShortcutInfo
                {
                    Keys = kvp.Key,
                    Context = context.Key,
                    Description = GetKeyDescription(kvp.Key)
                });
            }
        }

        return shortcuts;
    }

    private string GetKeyDescription(Keys keys)
    {
        var parts = new List<string>();

        if ((keys & Keys.Control) != 0)
            parts.Add("Ctrl");
        if ((keys & Keys.Shift) != 0)
            parts.Add("Shift");
        if ((keys & Keys.Alt) != 0)
            parts.Add("Alt");

        var mainKey = keys & ~(Keys.Control | Keys.Shift | Keys.Alt);
        parts.Add(mainKey.ToString());

        return string.Join(" + ", parts);
    }
}

public class ShortcutInfo
{
    public required Keys Keys { get; init; }
    public required string Context { get; init; }
    public required string Description { get; init; }
}

/// <summary>
/// Dialog showing all available keyboard shortcuts.
/// </summary>
public class ShortcutHelpDialog : Form
{
    private ListView _shortcutList;

    public ShortcutHelpDialog(KeyboardShortcutManager manager)
    {
        InitializeComponent();
        PopulateShortcuts(manager);
    }

    private void InitializeComponent()
    {
        Text = "Keyboard Shortcuts";
        Size = new Size(600, 500);
        StartPosition = FormStartPosition.CenterParent;
        BackColor = Color.FromArgb(21, 21, 21);
        ForeColor = Color.FromArgb(230, 230, 230);

        var titleLabel = new Label
        {
            Text = "⌨️ KEYBOARD SHORTCUTS",
            Dock = DockStyle.Top,
            Height = 50,
            Font = new Font("Segoe UI", 14, FontStyle.Bold),
            TextAlign = ContentAlignment.MiddleCenter,
            BackColor = Color.FromArgb(10, 10, 10)
        };

        _shortcutList = new ListView
        {
            Dock = DockStyle.Fill,
            View = View.Details,
            FullRowSelect = true,
            BackColor = Color.FromArgb(20, 20, 20),
            ForeColor = Color.FromArgb(220, 220, 220),
            BorderStyle = BorderStyle.None,
            Font = new Font("Segoe UI", 10)
        };

        _shortcutList.Columns.Add("Shortcut", 150);
        _shortcutList.Columns.Add("Context", 120);
        _shortcutList.Columns.Add("Description", 300);

        var closeButton = new Button
        {
            Text = "CLOSE",
            Dock = DockStyle.Bottom,
            Height = 40,
            BackColor = Color.FromArgb(60, 60, 60),
            ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat,
            Font = new Font("Segoe UI", 10)
        };
        closeButton.FlatAppearance.BorderSize = 0;
        closeButton.Click += (s, e) => Close();

        Controls.Add(_shortcutList);
        Controls.Add(titleLabel);
        Controls.Add(closeButton);
    }

    private void PopulateShortcuts(KeyboardShortcutManager manager)
    {
        var shortcuts = manager.GetAllShortcuts()
            .OrderBy(s => s.Context)
            .ThenBy(s => s.Description);

        foreach (var shortcut in shortcuts)
        {
            var item = new ListViewItem(GetKeyString(shortcut.Keys));
            item.SubItems.Add(shortcut.Context);
            item.SubItems.Add(shortcut.Description);
            _shortcutList.Items.Add(item);
        }
    }

    private string GetKeyString(Keys keys)
    {
        var parts = new List<string>();

        if ((keys & Keys.Control) != 0)
            parts.Add("Ctrl");
        if ((keys & Keys.Shift) != 0)
            parts.Add("Shift");
        if ((keys & Keys.Alt) != 0)
            parts.Add("Alt");

        var mainKey = keys & ~(Keys.Control | Keys.Shift | Keys.Alt);
        parts.Add(mainKey.ToString());

        return string.Join(" + ", parts);
    }

    public static void Show(KeyboardShortcutManager manager, IWin32Window? owner = null)
    {
        using var dialog = new ShortcutHelpDialog(manager);
        dialog.ShowDialog(owner);
    }
}
