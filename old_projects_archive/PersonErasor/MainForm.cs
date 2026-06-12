using System.Drawing;
using System.Windows.Forms;
using SovereignIDE.Core.Execution;
using SovereignIDE.Core.Exceptions;
using SovereignIDE.Core.FileSystem;
using SovereignIDE.Core.Models;
using SovereignIDE.Core.Parsers;
using SovereignIDE.Core.Services;
using SovereignIDE.UI.Controls;
using SovereignIDE.UI.Dialogs;
using SovereignIDE.UI.Services;

namespace SovereignIDE.UI;

/// <summary>
/// Main application window with 3-panel layout.
/// Layout: [File Explorer] | [Center Workspace] | [Artifacts/Commands]
/// 
/// Enhanced v1.1 features:
/// - ClipboardWatcher (auto-detect AI responses)
/// - ManifestManager (auto-save with versioning)
/// - ConfigurationManager (persistent settings)
/// - KeyboardShortcuts (comprehensive hotkeys)
/// - ErrorDialog (copy-pasteable errors)
/// </summary>
public partial class MainForm : Form
{
    private readonly string _sessionId;
    private ManifestV4? _currentManifest;

    // Core components
    private FileManager? _fileManager;
    private CommandQueue? _commandQueue;
    private AutoExecutor? _autoExecutor;
    private ManifestManager? _manifestManager;
    private ClipboardWatcher? _clipboardWatcher;
    private ConfigurationManager _configManager;
    private KeyboardShortcutManager _shortcutManager;

    // UI Controls
    private SplitContainer _mainSplit;
    private SplitContainer _rightSplit;
    private FileExplorerControl _fileExplorer;
    private ManifestViewerControl _manifestViewer;
    private CommandQueueControl _commandQueueControl;
    private Button _pauseButton;
    private Label _statusLabel;

    public MainForm()
    {
        _sessionId = Guid.NewGuid().ToString();
        _configManager = new ConfigurationManager();
        _shortcutManager = new KeyboardShortcutManager();

        InitializeComponent();
        SetupUI();
        SetupEventHandlers();
        SetupServices();
        
        // Restore window layout
        RestoreWindowLayout();
    }

    private void InitializeComponent()
    {
        Text = "Sovereign IDE - AI Development Environment";
        Size = new Size(1600, 900);
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Color.FromArgb(21, 21, 21); // Dark theme
        ForeColor = Color.FromArgb(230, 230, 230);
    }

    private void SetupUI()
    {
        // Main layout: 3 columns
        _mainSplit = new SplitContainer
        {
            Dock = DockStyle.Fill,
            SplitterDistance = 320,
            FixedPanel = FixedPanel.Panel1,
            BorderStyle = BorderStyle.None
        };

        _rightSplit = new SplitContainer
        {
            Dock = DockStyle.Fill,
            Orientation = Orientation.Vertical,
            SplitterDistance = 420,
            FixedPanel = FixedPanel.Panel2,
            BorderStyle = BorderStyle.None
        };

        // Left panel: File Explorer
        _fileExplorer = new FileExplorerControl
        {
            Dock = DockStyle.Fill
        };

        // Center panel: Manifest Viewer
        _manifestViewer = new ManifestViewerControl
        {
            Dock = DockStyle.Fill
        };

        // Right panel: Command Queue
        _commandQueueControl = new CommandQueueControl
        {
            Dock = DockStyle.Fill
        };

        // Pause button (top-right)
        _pauseButton = new Button
        {
            Text = "⏸ PAUSED",
            Size = new Size(120, 40),
            Location = new Point(Width - 140, 10),
            Anchor = AnchorStyles.Top | AnchorStyles.Right,
            BackColor = Color.FromArgb(234, 98, 98), // Red
            ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat,
            Font = new Font("Segoe UI", 12, FontStyle.Bold)
        };
        _pauseButton.FlatAppearance.BorderSize = 0;

        // Status bar
        _statusLabel = new Label
        {
            Text = $"Session: {_sessionId.Substring(0, 8)}... | Ready",
            Dock = DockStyle.Bottom,
            Height = 24,
            BackColor = Color.FromArgb(15, 15, 15),
            ForeColor = Color.FromArgb(180, 180, 180),
            Padding = new Padding(10, 0, 0, 0),
            TextAlign = ContentAlignment.MiddleLeft
        };

        // Assemble layout
        _mainSplit.Panel1.Controls.Add(_fileExplorer);
        _rightSplit.Panel1.Controls.Add(_manifestViewer);
        _rightSplit.Panel2.Controls.Add(_commandQueueControl);
        _mainSplit.Panel2.Controls.Add(_rightSplit);

        Controls.Add(_mainSplit);
        Controls.Add(_pauseButton);
        Controls.Add(_statusLabel);

        // Menu bar
        SetupMenuBar();
    }

    private void SetupMenuBar()
    {
        var menuStrip = new MenuStrip
        {
            BackColor = Color.FromArgb(15, 15, 15),
            ForeColor = Color.FromArgb(230, 230, 230)
        };

        // File menu
        var fileMenu = new ToolStripMenuItem("File");
        fileMenu.DropDownItems.Add("Open Project Folder...", null, OnOpenProject);
        fileMenu.DropDownItems.Add("Load Manifest...", null, OnLoadManifest);
        fileMenu.DropDownItems.Add("Save Manifest...", null, OnSaveManifest);
        fileMenu.DropDownItems.Add(new ToolStripSeparator());
        fileMenu.DropDownItems.Add("Exit", null, (s, e) => Close());

        // Edit menu
        var editMenu = new ToolStripMenuItem("Edit");
        editMenu.DropDownItems.Add("Paste Response", null, OnPasteResponse);
        editMenu.DropDownItems.Add(new ToolStripSeparator());
        editMenu.DropDownItems.Add("Clear Command Queue", null, OnClearQueue);

        // View menu
        var viewMenu = new ToolStripMenuItem("View");
        viewMenu.DropDownItems.Add("File Explorer", null, (s, e) => _fileExplorer.Visible = !_fileExplorer.Visible);
        viewMenu.DropDownItems.Add("Manifest Viewer", null, (s, e) => _manifestViewer.Visible = !_manifestViewer.Visible);
        viewMenu.DropDownItems.Add("Command Queue", null, (s, e) => _commandQueueControl.Visible = !_commandQueueControl.Visible);

        menuStrip.Items.Add(fileMenu);
        menuStrip.Items.Add(editMenu);
        menuStrip.Items.Add(viewMenu);

        MainMenuStrip = menuStrip;
        Controls.Add(menuStrip);
    }

    private void SetupEventHandlers()
    {
        _pauseButton.Click += OnPauseButtonClick;
        _fileExplorer.FileSelected += OnFileSelected;
        _commandQueueControl.CommandApproved += OnCommandApproved;
        _commandQueueControl.CommandRejected += OnCommandRejected;
        _commandQueueControl.ExecuteCommand += OnExecuteCommand;
        
        // Keyboard shortcuts
        _shortcutManager.ShortcutExecuted += OnShortcutExecuted;
        
        // Window closing - save layout
        FormClosing += OnFormClosing;
    }

    private void SetupServices()
    {
        // Initialize clipboard watcher if enabled
        if (_configManager.Config.Preferences.ClipboardWatcherEnabled)
        {
            _clipboardWatcher = new ClipboardWatcher();
            _clipboardWatcher.ResponseDetected += OnClipboardResponseDetected;
            UpdateStatus("Clipboard watcher enabled");
        }
    }

    private void RestoreWindowLayout()
    {
        var layout = _configManager.Config.WindowLayout;
        if (layout != null)
        {
            Size = new Size(layout.Width, layout.Height);
            Location = new Point(layout.X, layout.Y);
            
            if (layout.Maximized)
            {
                WindowState = FormWindowState.Maximized;
            }
            
            _mainSplit.SplitterDistance = layout.LeftPanelWidth;
            _rightSplit.SplitterDistance = layout.RightPanelWidth;
        }
    }

    private void OnFormClosing(object? sender, FormClosingEventArgs e)
    {
        // Save window layout
        var layout = WindowState == FormWindowState.Normal
            ? new { Width = Width, Height = Height, X = Location.X, Y = Location.Y }
            : new { Width = RestoreBounds.Width, Height = RestoreBounds.Height, X = RestoreBounds.X, Y = RestoreBounds.Y };
        
        _configManager.UpdateWindowLayout(
            layout.Width,
            layout.Height,
            layout.X,
            layout.Y,
            WindowState == FormWindowState.Maximized,
            _mainSplit.SplitterDistance,
            _rightSplit.SplitterDistance
        );
        
        // Cleanup
        _clipboardWatcher?.Dispose();
        _manifestManager?.Dispose();
    }

    private void OnShortcutExecuted(object? sender, string actionName)
    {
        switch (actionName)
        {
            case "TogglePause":
                OnPauseButtonClick(null, EventArgs.Empty);
                break;
            case "PasteResponse":
                OnPasteResponse(null, EventArgs.Empty);
                break;
            case "SaveManifest":
                OnSaveManifest(null, EventArgs.Empty);
                break;
            case "OpenProject":
                OnOpenProject(null, EventArgs.Empty);
                break;
            case "ShowHelp":
                ShortcutHelpDialog.Show(_shortcutManager, this);
                break;
            case "Exit":
                Close();
                break;
            case "Refresh":
                RefreshView();
                break;
            case "ClearQueue":
                OnClearQueue(null, EventArgs.Empty);
                break;
        }
    }

    private void OnClipboardResponseDetected(object? sender, string response)
    {
        // Invoke on UI thread
        if (InvokeRequired)
        {
            Invoke(() => OnClipboardResponseDetected(sender, response));
            return;
        }
        
        // Show notification
        UpdateStatus($"📋 AI response detected ({response.Length} chars)");
        
        // Ask user if they want to process it
        var result = MessageBox.Show(
            $"AI response detected in clipboard ({response.Length} characters).\n\nProcess now?",
            "Response Detected",
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Question
        );
        
        if (result == DialogResult.Yes)
        {
            ProcessAIResponse(response);
        }
    }

    private void RefreshView()
    {
        if (_currentManifest != null)
        {
            _fileExplorer.LoadFiles(_currentManifest.Files);
            _manifestViewer.LoadManifest(_currentManifest);
        }
    }

    private void OnPauseButtonClick(object? sender, EventArgs e)
    {
        if (_autoExecutor == null)
            return;

        _autoExecutor.Paused = !_autoExecutor.Paused;

        _pauseButton.Text = _autoExecutor.Paused ? "⏸ PAUSED" : "▶ AUTO";
        _pauseButton.BackColor = _autoExecutor.Paused
            ? Color.FromArgb(234, 98, 98)   // Red
            : Color.FromArgb(94, 124, 226); // Blue

        UpdateStatus(_autoExecutor.Paused ? "Paused" : "Auto-executing");
    }

    private void OnOpenProject(object? sender, EventArgs e)
    {
        using var dialog = new FolderBrowserDialog
        {
            Description = "Select project root folder"
        };

        if (dialog.ShowDialog() == DialogResult.OK)
        {
            InitializeProject(dialog.SelectedPath);
        }
    }

    private void InitializeProject(string rootPath)
    {
        try
        {
            _fileManager = new FileManager(rootPath, _sessionId);
            _commandQueue = new CommandQueue(_sessionId);
            _autoExecutor = new AutoExecutor(_commandQueue);

            _autoExecutor.PausedChanged += (s, paused) =>
            {
                UpdateStatus(paused ? "Paused" : "Auto-executing");
            };

            // Initialize manifest manager
            var manifestPath = Path.Combine(rootPath, "manifest.json");
            _manifestManager = new ManifestManager(
                manifestPath,
                _configManager.Config.Preferences.AutoSaveEnabled,
                _configManager.Config.Preferences.AutoSaveIntervalSeconds,
                _configManager.Config.Preferences.MaxBackups
            );

            _manifestManager.ManifestSaved += (s, e) =>
            {
                UpdateStatus("📝 Manifest auto-saved");
            };

            _manifestManager.AutoSaveError += (s, error) =>
            {
                UpdateStatus($"⚠️ Auto-save failed: {error}");
            };

            // Try to load existing manifest, or create new
            if (File.Exists(manifestPath))
            {
                _currentManifest = _manifestManager.Load();
                UpdateStatus("Loaded existing manifest");
            }
            else
            {
                _currentManifest = _manifestManager.CreateNew(rootPath, Environment.UserName);
                _currentManifest = _currentManifest with
                {
                    Files = _fileManager.ScanDirectory()
                };
                _manifestManager.Update(_currentManifest);
                _manifestManager.Save();
            }

            _fileExplorer.LoadFiles(_currentManifest.Files);
            _manifestViewer.LoadManifest(_currentManifest);
            _commandQueueControl.SetCommandQueue(_commandQueue);

            // Add to recent projects
            _configManager.AddRecentProject(rootPath);

            UpdateStatus($"Loaded project: {Path.GetFileName(rootPath)}");
        }
        catch (SovereignException ex)
        {
            ErrorDialog.Show(ex, this);
        }
        catch (Exception ex)
        {
            var wrappedException = new ExecutionException(
                $"Failed to open project: {ex.Message}",
                $"Project path: {rootPath}",
                _sessionId,
                ex
            );
            ErrorDialog.Show(wrappedException, this);
        }
    }

    private void OnLoadManifest(object? sender, EventArgs e)
    {
        using var dialog = new OpenFileDialog
        {
            Filter = "JSON files (*.json)|*.json|All files (*.*)|*.*",
            Title = "Load Manifest"
        };

        if (dialog.ShowDialog() == DialogResult.OK)
        {
            try
            {
                var json = File.ReadAllText(dialog.FileName);
                var manifest = System.Text.Json.JsonSerializer.Deserialize<ManifestV4>(json);

                if (manifest != null)
                {
                    _currentManifest = manifest;
                    _manifestViewer.LoadManifest(manifest);
                    _fileExplorer.LoadFiles(manifest.Files);
                    UpdateStatus("Manifest loaded");
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to load manifest: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }

    private void OnSaveManifest(object? sender, EventArgs e)
    {
        if (_currentManifest == null)
        {
            MessageBox.Show("No manifest to save", "Info", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        using var dialog = new SaveFileDialog
        {
            Filter = "JSON files (*.json)|*.json",
            FileName = "manifest.json"
        };

        if (dialog.ShowDialog() == DialogResult.OK)
        {
            try
            {
                var json = System.Text.Json.JsonSerializer.Serialize(_currentManifest, new System.Text.Json.JsonSerializerOptions
                {
                    WriteIndented = true
                });

                File.WriteAllText(dialog.FileName, json);
                UpdateStatus("Manifest saved");
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to save manifest: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }

    private void OnPasteResponse(object? sender, EventArgs e)
    {
        if (Clipboard.ContainsText())
        {
            var response = Clipboard.GetText();
            ProcessAIResponse(response);
        }
    }

    private void ProcessAIResponse(string response)
    {
        if (_fileManager == null || _commandQueue == null || _autoExecutor == null)
        {
            MessageBox.Show("Please open a project first", "Info", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        try
        {
            var parser = new ResponseParser("PastedResponse");
            var parsed = parser.Parse(response);

            // Handle files
            foreach (var file in parsed.Files)
            {
                _fileManager.WriteFile(file);
                _currentManifest?.Files.Add(file);
            }

            // Handle commands
            foreach (var command in parsed.Commands)
            {
                _commandQueue.Add(command);
            }

            _fileExplorer.LoadFiles(_currentManifest?.Files ?? new List<FileEntry>());
            UpdateStatus($"Processed: {parsed.Files.Count} files, {parsed.Commands.Count} commands");
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to process response: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void OnClearQueue(object? sender, EventArgs e)
    {
        _commandQueue?.ClearCompleted();
        UpdateStatus("Queue cleared");
    }

    private void OnFileSelected(object? sender, FileEntry file)
    {
        _manifestViewer.ShowFilePreview(file);
    }

    private async void OnCommandApproved(object? sender, CommandEntry command)
    {
        if (_autoExecutor == null)
            return;

        _commandQueue?.Approve(command.Id, Environment.UserName);
        await _autoExecutor.ExecuteCommandAsync(command);
    }

    private void OnCommandRejected(object? sender, CommandEntry command)
    {
        _commandQueue?.Reject(command.Id);
    }

    private async void OnExecuteCommand(object? sender, CommandEntry command)
    {
        if (_autoExecutor == null)
            return;

        await _autoExecutor.ExecuteCommandAsync(command);
    }

    private void UpdateStatus(string message)
    {
        _statusLabel.Text = $"Session: {_sessionId.Substring(0, 8)}... | {message}";
    }

    protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
    {
        // Let shortcut manager handle it
        if (_shortcutManager.ProcessKey(keyData))
            return true;

        return base.ProcessCmdKey(ref msg, keyData);
    }
}
