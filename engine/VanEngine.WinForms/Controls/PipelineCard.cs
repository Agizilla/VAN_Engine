using VanEngine.WinForms.Helpers;
using VanEngine.WinForms.Models;

namespace VanEngine.WinForms.Controls;

public partial class PipelineCard : UserControl
{
    private readonly PipelineExecution _execution;
    private Panel? _statusIndicator;
    private Label? _titleLabel;
    private Label? _statusLabel;
    private FlowLayoutPanel? _stepsPanel;

    public PipelineCard(PipelineExecution execution)
    {
        _execution = execution;
        InitializeComponent();
        InitializeCustomComponents();
    }

    private void InitializeComponent()
    {
        this.Size = new Size(300, 80);
        this.BackColor = ColorPalette.Secondary;
        this.Padding = new Padding(12);
    }

    private void InitializeCustomComponents()
    {
        _statusIndicator = new Panel
        {
            Size = new Size(4, this.Height),
            Dock = DockStyle.Left,
            BackColor = _execution.Status switch
            {
                "running" => ColorPalette.Accent,
                "completed" => ColorPalette.Success,
                "failed" => ColorPalette.Error,
                _ => ColorPalette.TextMuted
            }
        };
        this.Controls.Add(_statusIndicator);

        _titleLabel = new Label
        {
            Text = $"{_execution.Pipeline} ({_execution.Agent})",
            Font = new Font("Segoe UI", 10, FontStyle.Bold),
            ForeColor = ColorPalette.TextPrimary,
            Location = new Point(16, 8),
            AutoSize = true
        };
        this.Controls.Add(_titleLabel);

        _statusLabel = new Label
        {
            Text = _execution.Status,
            Font = new Font("Segoe UI", 8),
            ForeColor = ColorPalette.TextSecondary,
            Location = new Point(16, 30),
            AutoSize = true
        };
        this.Controls.Add(_statusLabel);

        _stepsPanel = new FlowLayoutPanel
        {
            Location = new Point(16, 50),
            Size = new Size(this.Width - 24, 24),
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            AutoSize = false
        };

        foreach (var step in _execution.Steps)
        {
            var dot = new Panel
            {
                Size = new Size(8, 8),
                Margin = new Padding(2),
                BackColor = step.Status switch
                {
                    "running" => ColorPalette.Accent,
                    "completed" => ColorPalette.Success,
                    "failed" => ColorPalette.Error,
                    _ => ColorPalette.Border
                }
            };
            _stepsPanel.Controls.Add(dot);
        }
        this.Controls.Add(_stepsPanel);
    }
}
