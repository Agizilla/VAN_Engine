using Microsoft.Extensions.DependencyInjection;
using VanEngine.WinForms.Helpers;
using VanEngine.WinForms.Services;

namespace VanEngine.WinForms.Forms;

public partial class MainForm : Form
{
    private readonly BrainBridge _brainBridge;

    // Designer controls
    private TableLayoutPanel? mainLayout;
    private Panel? sidebarPanel;
    private Panel? contentPanel;
    private Label? logoLabel;
    private Panel? separator;
    private FlowLayoutPanel? navPanel;
    private Panel? statusBar;
    private Panel? statusIndicator;
    private Label? statusLabel;
    private System.Windows.Forms.Timer? statusTimer;

    // Navigation
    private readonly Dictionary<string, UserControl> _panels = new();
    private Button? _activeNavButton;

    public MainForm(BrainBridge brainBridge)
    {
        _brainBridge = brainBridge;
        InitializeComponent();
        DarkTheme.ApplyToForm(this);
        LoadPanels();
        StartStatusMonitoring();
    }

    private void InitializeComponent()
    {
        // Form properties
        this.Text = "VAN_Engine - Conversation IDE";
        this.Size = new Size(1400, 900);
        this.MinimumSize = new Size(1000, 700);
        this.StartPosition = FormStartPosition.CenterScreen;
        this.BackColor = ColorPalette.Primary;
        this.Name = "MainForm";

        // Main layout - TableLayoutPanel
        this.mainLayout = new TableLayoutPanel();
        this.mainLayout.SuspendLayout();
        // 
        // mainLayout
        // 
        this.mainLayout.ColumnCount = 2;
        this.mainLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 250F));
        this.mainLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));
       
        this.mainLayout.Dock = DockStyle.Fill;
        this.mainLayout.Location = new Point(0, 0);
        this.mainLayout.Name = "mainLayout";
        this.mainLayout.RowCount = 1;
        this.mainLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
        this.mainLayout.Size = new Size(1400, 900);
        this.mainLayout.TabIndex = 0;

        // 
        // sidebarPanel
        // 
        this.sidebarPanel = new Panel();
        this.sidebarPanel.BackColor = ColorPalette.Secondary;
        this.sidebarPanel.Controls.Add(this.logoLabel);
        this.sidebarPanel.Controls.Add(this.separator);
        this.sidebarPanel.Controls.Add(this.navPanel);
        this.sidebarPanel.Controls.Add(this.statusBar);
        this.sidebarPanel.Dock = DockStyle.Fill;
        this.sidebarPanel.Name = "sidebarPanel";
        this.sidebarPanel.Size = new Size(250, 900);
        this.sidebarPanel.TabIndex = 0;

        // 
        // logoLabel
        // 
        this.logoLabel = new Label();
        this.logoLabel.Dock = DockStyle.Top;
        this.logoLabel.Font = new Font("Segoe UI", 16F, FontStyle.Bold);
        this.logoLabel.ForeColor = ColorPalette.Accent;
        this.logoLabel.Height = 60;
        this.logoLabel.Name = "logoLabel";
        this.logoLabel.Padding = new Padding(16, 0, 0, 0);
        this.logoLabel.Text = "⚡ VAN_Engine";
        this.logoLabel.TextAlign = ContentAlignment.MiddleLeft;

        // 
        // separator
        // 
        this.separator = new Panel();
        this.separator.BackColor = ColorPalette.Border;
        this.separator.Dock = DockStyle.Top;
        this.separator.Height = 1;
        this.separator.Name = "separator";

        // 
        // navPanel
        // 
        this.navPanel = new FlowLayoutPanel();
        this.navPanel.AutoSize = true;
        this.navPanel.BackColor = ColorPalette.Secondary;
        this.navPanel.Dock = DockStyle.Top;
        this.navPanel.FlowDirection = FlowDirection.TopDown;
        this.navPanel.Name = "navPanel";
        this.navPanel.Padding = new Padding(8, 12, 8, 12);
        this.navPanel.WrapContents = false;

        // Create navigation buttons
        CreateNavButtons();

        // 
        // statusBar
        // 
        this.statusBar = new Panel();
        this.statusBar.BackColor = ColorPalette.Tertiary;
        this.statusBar.Controls.Add(this.statusIndicator);
        this.statusBar.Controls.Add(this.statusLabel);
        this.statusBar.Dock = DockStyle.Bottom;
        this.statusBar.Height = 40;
        this.statusBar.Name = "statusBar";

        // 
        // statusIndicator
        // 
        this.statusIndicator = new Panel();
        this.statusIndicator.BackColor = ColorPalette.Warning;
        this.statusIndicator.Location = new Point(12, 16);
        this.statusIndicator.Name = "statusIndicator";
        this.statusIndicator.Size = new Size(8, 8);

        // 
        // statusLabel
        // 
        this.statusLabel = new Label();
        this.statusLabel.AutoSize = true;
        this.statusLabel.Font = new Font("Segoe UI", 9F);
        this.statusLabel.ForeColor = ColorPalette.TextSecondary;
        this.statusLabel.Location = new Point(28, 10);
        this.statusLabel.Name = "statusLabel";
        this.statusLabel.Text = "Connecting...";

        // 
        // contentPanel
        // 
        this.contentPanel = new Panel();
        this.contentPanel.AutoScroll = true;
        this.contentPanel.BackColor = ColorPalette.Primary;
        this.contentPanel.Dock = DockStyle.Fill;
        this.contentPanel.Name = "contentPanel";
        this.contentPanel.Size = new Size(1150, 900);
        this.contentPanel.TabIndex = 1;

        // Finalize

        this.mainLayout.Controls.Add(this.sidebarPanel, 0, 0);
        this.mainLayout.Controls.Add(this.contentPanel, 1, 0);
        this.mainLayout.ResumeLayout(false);
        this.mainLayout.PerformLayout();
        this.Controls.Add(this.mainLayout);

        // Resize handler for content panel
        this.contentPanel.Resize += (s, e) =>
        {
            if (contentPanel.Controls.Count > 0)
                contentPanel.Controls[0].Size = contentPanel.Size;
        };
    }

    private void CreateNavButtons()
    {
        var navItems = new[]
        {
            ("chat", "💬 Chat"),
            ("inference", "🎯 Inference"),
            ("transcript", "📝 Transcript"),
            ("monitor", "📊 Monitor"),
            ("settings", "⚙️ Settings")
        };

        foreach (var (id, text) in navItems)
        {
            var btn = new Button();
            btn.Name = $"nav_{id}";
            btn.Tag = id;
            btn.Text = text;
            btn.Font = new Font("Segoe UI", 11F);
            btn.TextAlign = ContentAlignment.MiddleLeft;
            btn.Padding = new Padding(12, 10, 12, 10);
            btn.Height = 44;
            btn.Width = navPanel!.Width - 16;
            btn.FlatStyle = FlatStyle.Flat;
            btn.BackColor = ColorPalette.Secondary;
            btn.ForeColor = ColorPalette.TextSecondary;
            btn.Cursor = Cursors.Hand;
            btn.FlatAppearance.BorderSize = 0;
            btn.Click += NavButton_Click;
            btn.TextImageRelation = TextImageRelation.ImageBeforeText;

            navPanel!.Controls.Add(btn);
        }

        // Add spacer
        navPanel.Controls.Add(new Panel { Height = 20 });

        // Handle resize to adjust button width
        navPanel.Resize += (s, e) =>
        {
            foreach (Button btn in navPanel.Controls)
            {
                if (btn is Button && btn.Name?.StartsWith("nav_") == true)
                    btn.Width = navPanel.Width - 16;
            }
        };
    }

    private void LoadPanels()
    {
        var chatPanel = Program.ServiceProvider.GetRequiredService<ChatPanel>();
        chatPanel.Dock = DockStyle.Fill;
        _panels["chat"] = chatPanel;

        var inferencePanel = Program.ServiceProvider.GetRequiredService<InferencePanel>();
        inferencePanel.Dock = DockStyle.Fill;
        _panels["inference"] = inferencePanel;

        var transcriptPanel = Program.ServiceProvider.GetRequiredService<TranscriptPanel>();
        transcriptPanel.Dock = DockStyle.Fill;
        _panels["transcript"] = transcriptPanel;

        var monitorPanel = Program.ServiceProvider.GetRequiredService<MonitorPanel>();
        monitorPanel.Dock = DockStyle.Fill;
        _panels["monitor"] = monitorPanel;

        var settingsPanel = Program.ServiceProvider.GetRequiredService<SettingsPanel>();
        settingsPanel.Dock = DockStyle.Fill;
        _panels["settings"] = settingsPanel;

        ShowPanel("chat");
    }

    private void NavButton_Click(object? sender, EventArgs e)
    {
        if (sender is Button btn && btn.Tag is string panelId)
        {
            ShowPanel(panelId);

            if (_activeNavButton != null)
            {
                _activeNavButton.BackColor = ColorPalette.Secondary;
                _activeNavButton.ForeColor = ColorPalette.TextSecondary;
            }
            _activeNavButton = btn;
            btn.BackColor = Color.FromArgb(32, 45, 65);
            btn.ForeColor = ColorPalette.Accent;
        }
    }

    private void ShowPanel(string panelId)
    {
        if (contentPanel == null) return;
        contentPanel.Controls.Clear();

        if (_panels.TryGetValue(panelId, out var panel))
        {
            panel.Location = new Point(0, 0);
            panel.Size = contentPanel.Size;
            contentPanel.Controls.Add(panel);
        }
    }

    private void StartStatusMonitoring()
    {
        statusTimer = new System.Windows.Forms.Timer();
        statusTimer.Interval = 5000;
        statusTimer.Tick += async (s, e) => await UpdateStatus();
        statusTimer.Start();
        _ = UpdateStatus();
    }

    private async Task UpdateStatus()
    {
        try
        {
            var status = await _brainBridge.GetStatusAsync();
            if (statusLabel != null && statusIndicator != null)
            {
                if (status.Available)
                {
                    statusLabel.Text = $"Online | {status.TokenCount} tokens";
                    statusIndicator.BackColor = ColorPalette.Success;
                }
                else
                {
                    statusLabel.Text = "Offline";
                    statusIndicator.BackColor = ColorPalette.Error;
                }
            }
        }
        catch
        {
            if (statusLabel != null && statusIndicator != null)
            {
                statusLabel.Text = "Error";
                statusIndicator.BackColor = ColorPalette.Error;
            }
        }
    }
}