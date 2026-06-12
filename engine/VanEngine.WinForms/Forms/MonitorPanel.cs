using VanEngine.WinForms.Controls;
using VanEngine.WinForms.Helpers;
using VanEngine.WinForms.Models;
using VanEngine.WinForms.Services;

namespace VanEngine.WinForms.Forms;

public partial class MonitorPanel : UserControl
{
    private readonly PipelineMonitor _monitor;
    private System.Windows.Forms.Timer? _refreshTimer;
    private FlowLayoutPanel? _cardsPanel;
    private Label? _statusLabel;
    private Label? _statsLabel;
    private Button? _refreshButton;

    public MonitorPanel(PipelineMonitor monitor)
    {
        _monitor = monitor;
        InitializeComponent();
        InitializeCustomComponents();
        StartAutoRefresh();
    }

    private void InitializeComponent()
    {
        this.Name = "MonitorPanel";
        this.BackColor = ColorPalette.Primary;
        this.AutoScroll = true;
        this.Padding = new Padding(24);
    }

    private void InitializeCustomComponents()
    {
        var titleLabel = new Label { Text = "Pipeline Monitor", Font = new Font("Segoe UI", 24, FontStyle.Bold), ForeColor = ColorPalette.Accent, AutoSize = true, Location = new Point(0, 0) };
        this.Controls.Add(titleLabel);

        var headerPanel = new Panel { Location = new Point(0, 50), Size = new Size(this.Width - 48, 40), Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right };

        _statusLabel = new Label { Text = "Server: Checking...", Font = new Font("Segoe UI", 10), ForeColor = ColorPalette.TextSecondary, Location = new Point(0, 10), AutoSize = true };
        headerPanel.Controls.Add(_statusLabel);

        _refreshButton = new Button
        {
            Text = "Refresh", Location = new Point(headerPanel.Width - 90, 5), Size = new Size(90, 30),
            Anchor = AnchorStyles.Top | AnchorStyles.Right, BackColor = ColorPalette.Accent,
            ForeColor = ColorPalette.Primary, FlatStyle = FlatStyle.Flat,
            Font = new Font("Segoe UI", 10, FontStyle.Bold), Cursor = Cursors.Hand
        };
        _refreshButton.FlatAppearance.BorderSize = 0;
        _refreshButton.Click += async (s, e) => await RefreshData();
        headerPanel.Controls.Add(_refreshButton);
        this.Controls.Add(headerPanel);

        _statsLabel = new Label { Location = new Point(0, 90), AutoSize = true, Font = new Font("Segoe UI", 10), ForeColor = ColorPalette.TextSecondary };
        this.Controls.Add(_statsLabel);

        _cardsPanel = new FlowLayoutPanel
        {
            Location = new Point(0, 120), Size = new Size(this.Width - 48, this.Height - 120),
            FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoScroll = true,
            Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom
        };
        this.Controls.Add(_cardsPanel);
    }

    private void StartAutoRefresh()
    {
        _refreshTimer = new System.Windows.Forms.Timer { Interval = 5000 };
        _refreshTimer.Tick += async (s, e) => await RefreshData();
        _refreshTimer.Start();
        _ = RefreshData();
    }

    private async Task RefreshData()
    {
        try
        {
            var isHealthy = await _monitor.CheckHealthAsync();
            _statusLabel!.Text = isHealthy ? "Server: Online" : "Server: Offline";
            _statusLabel.ForeColor = isHealthy ? ColorPalette.Success : ColorPalette.Error;

            if (isHealthy)
            {
                var executions = await _monitor.GetExecutionsAsync();
                RenderCards(executions);
            }
        }
        catch { }
    }

    private void RenderCards(List<PipelineExecution> executions)
    {
        if (_cardsPanel == null) return;

        _cardsPanel.SuspendLayout();
        _cardsPanel.Controls.Clear();

        var running = executions.Count(e => e.Status == "running");
        var completed = executions.Count(e => e.Status == "completed");
        var failed = executions.Count(e => e.Status == "failed");
        _statsLabel!.Text = $"Total: {executions.Count} | Running: {running} | Completed: {completed} | Failed: {failed}";

        foreach (var exec in executions)
        {
            var card = new PipelineCard(exec);
            card.Width = _cardsPanel.Width - 8;
            _cardsPanel.Controls.Add(card);
        }

        if (executions.Count == 0)
        {
            _cardsPanel.Controls.Add(new Label
            {
                Text = "No pipeline executions yet.\nStart a pipeline from the API to see it here.",
                ForeColor = ColorPalette.TextMuted, Font = new Font("Segoe UI", 10),
                AutoSize = true, Padding = new Padding(16)
            });
        }

        _cardsPanel.ResumeLayout();
    }

    protected override void OnResize(EventArgs e)
    {
        base.OnResize(e);
        if (_cardsPanel != null) _cardsPanel.Size = new Size(this.Width - 48, this.Height - 120);
    }
}
