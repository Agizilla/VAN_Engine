using VanEngine.WinForms.Helpers;
using VanEngine.WinForms.Models;
using VanEngine.WinForms.Services;

namespace VanEngine.WinForms.Forms;

public partial class InferencePanel : UserControl
{
    private readonly InferenceService _inferenceService;

    // Designer controls
    private Label? titleLabel;
    private Label? subtitleLabel;
    private Panel? tierPanel;
    private Label? tierLabel;
    private ComboBox? tierCombo;
    private Label? tierDesc;
    private Label? promptLabel;
    private RichTextBox? promptTextBox;
    private Button? runButton;
    private ProgressBar? progressBar;
    private Label? statusLabel;
    private Panel? resultPanel;
    private Label? resultTitle;
    private RichTextBox? resultTextBox;  // RichTextBox for selectable/copyable results
    private Panel? controlsPanel;

    public InferencePanel(InferenceService inferenceService)
    {
        _inferenceService = inferenceService;
        InitializeComponent();
        InitializeCustomComponents();
    }

    private void InitializeComponent()
    {
        components = new System.ComponentModel.Container();
        this.Name = "InferencePanel";
        this.BackColor = ColorPalette.Primary;
        this.AutoScroll = true;
        this.Padding = new Padding(24);
    }

    private void InitializeCustomComponents()
    {
        int yPos = 0;

        // Title
        this.titleLabel = new Label
        {
            Text = "🎯 Tiered Inference",
            Font = new Font("Segoe UI", 24F, FontStyle.Bold),
            ForeColor = ColorPalette.Accent,
            AutoSize = true,
            Location = new Point(0, yPos)
        };
        this.Controls.Add(titleLabel);
        yPos += 45;

        // Subtitle
        this.subtitleLabel = new Label
        {
            Text = "Fast → Standard → Smart — Choose the right tier for your task",
            Font = new Font("Segoe UI", 12F),
            ForeColor = ColorPalette.TextSecondary,
            AutoSize = true,
            Location = new Point(0, yPos)
        };
        this.Controls.Add(subtitleLabel);
        yPos += 40;

        // Tier panel
        this.tierPanel = new Panel
        {
            Location = new Point(0, yPos),
            Size = new Size(this.Width - 48, 80),
            Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        };

        this.tierLabel = new Label
        {
            Text = "Inference Tier:",
            Font = new Font("Segoe UI", 10F, FontStyle.Bold),
            ForeColor = ColorPalette.TextSecondary,
            Location = new Point(0, 0),
            AutoSize = true
        };
        tierPanel.Controls.Add(tierLabel);

        this.tierCombo = new ComboBox
        {
            Location = new Point(0, 25),
            Size = new Size(200, 30),
            DropDownStyle = ComboBoxStyle.DropDownList,
            BackColor = ColorPalette.Tertiary,
            ForeColor = ColorPalette.TextPrimary,
            FlatStyle = FlatStyle.Flat
        };
        tierCombo.Items.AddRange(new[] {
            "Fast (⚡ Pattern matching & cache)",
            "Standard (🧠 Brain.ExecuteQuery)",
            "Smart (🔮 7-Phase Algorithm)"
        });
        tierCombo.SelectedIndex = 1;
        tierPanel.Controls.Add(tierCombo);

        this.tierDesc = new Label
        {
            Text = "Fast: <1s | Standard: <5s | Smart: <30s (full algorithm)",
            Font = new Font("Segoe UI", 9F),
            ForeColor = ColorPalette.TextMuted,
            Location = new Point(210, 30),
            AutoSize = true
        };
        tierPanel.Controls.Add(tierDesc);

        this.Controls.Add(tierPanel);
        yPos += 90;

        // Prompt label
        this.promptLabel = new Label
        {
            Text = "Prompt:",
            Font = new Font("Segoe UI", 10F, FontStyle.Bold),
            ForeColor = ColorPalette.TextSecondary,
            Location = new Point(0, yPos),
            AutoSize = true
        };
        this.Controls.Add(promptLabel);
        yPos += 25;

        // Prompt text box - READ-WRITE (editable for copying)
        this.promptTextBox = new RichTextBox
        {
            Location = new Point(0, yPos),
            Size = new Size(this.Width - 48, 120),
            BackColor = ColorPalette.Tertiary,
            ForeColor = ColorPalette.TextPrimary,
            BorderStyle = BorderStyle.FixedSingle,
            Font = new Font("Consolas", 10F),
            Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right,
            ReadOnly = false  // Allow editing and copying
        };
        this.Controls.Add(promptTextBox);
        yPos += 130;

        // Controls panel for button and progress
        this.controlsPanel = new Panel
        {
            Location = new Point(0, yPos),
            Size = new Size(this.Width - 48, 50),
            Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        };

        this.runButton = new Button
        {
            Text = "Run Inference",
            Location = new Point(0, 5),
            Size = new Size(150, 40),
            BackColor = ColorPalette.Accent,
            ForeColor = ColorPalette.Primary,
            FlatStyle = FlatStyle.Flat,
            Font = new Font("Segoe UI", 10F, FontStyle.Bold),
            Cursor = Cursors.Hand,
            FlatAppearance = { BorderSize = 0 }
        };
        runButton.Click += RunButton_Click;
        controlsPanel.Controls.Add(runButton);

        this.progressBar = new ProgressBar
        {
            Location = new Point(160, 15),
            Size = new Size(200, 20),
            Visible = false,
            Style = ProgressBarStyle.Marquee
        };
        controlsPanel.Controls.Add(progressBar);

        this.statusLabel = new Label
        {
            Location = new Point(370, 18),
            AutoSize = true,
            ForeColor = ColorPalette.TextSecondary,
            Visible = false
        };
        controlsPanel.Controls.Add(statusLabel);

        this.Controls.Add(controlsPanel);
        yPos += 55;

        // Result panel
        this.resultPanel = new Panel
        {
            Location = new Point(0, yPos),
            Size = new Size(this.Width - 48, 350),
            BackColor = ColorPalette.Secondary,
            BorderStyle = BorderStyle.FixedSingle,
            Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom
        };

        this.resultTitle = new Label
        {
            Text = "Result",
            Font = new Font("Segoe UI", 10F, FontStyle.Bold),
            ForeColor = ColorPalette.Accent,
            Location = new Point(12, 12),
            AutoSize = true
        };
        resultPanel.Controls.Add(resultTitle);

        // Result text box - READ-ONLY but SELECTABLE (for copying)
        this.resultTextBox = new RichTextBox
        {
            Location = new Point(12, 40),
            Size = new Size(resultPanel.Width - 24, resultPanel.Height - 52),
            Font = new Font("Consolas", 9F),
            ForeColor = ColorPalette.TextPrimary,
            BackColor = ColorPalette.Secondary,
            BorderStyle = BorderStyle.None,
            ReadOnly = true,
            DetectUrls = true,
            WordWrap = true
        };
        resultPanel.Controls.Add(resultTextBox);

        this.Controls.Add(resultPanel);
    }

    private async void RunButton_Click(object? sender, EventArgs e)
    {
        if (string.IsNullOrWhiteSpace(promptTextBox?.Text))
        {
            MessageBox.Show("Please enter a prompt.", "Input Required", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        string tier = tierCombo?.SelectedIndex switch
        {
            0 => "fast",
            2 => "smart",
            _ => "standard"
        };

        runButton!.Enabled = false;
        progressBar!.Visible = true;
        statusLabel!.Visible = true;
        statusLabel.Text = $"Running {tier} inference...";
        resultTextBox!.Text = "Processing...";

        try
        {
            var result = await _inferenceService.RunAsync("", promptTextBox.Text, tier, false);

            resultTextBox.Text = result.Success
                ? result.Output
                : $"Error: {result.Error}";

            statusLabel.Text = $"Completed in {result.LatencyMs:F0}ms | Tier: {result.Tier}";
            if (result.FromCache)
                statusLabel.Text += " (cached)";
        }
        catch (Exception ex)
        {
            resultTextBox.Text = $"Error: {ex.Message}";
            statusLabel.Text = "Failed";
        }
        finally
        {
            runButton.Enabled = true;
            progressBar.Visible = false;
        }
    }

    protected override void OnResize(EventArgs e)
    {
        base.OnResize(e);
        if (promptTextBox != null)
            promptTextBox.Width = this.Width - 48;
        if (resultPanel != null && resultTextBox != null)
        {
            resultPanel.Width = this.Width - 48;
            resultTextBox.Width = resultPanel.Width - 24;
            resultTextBox.Height = resultPanel.Height - 52;
        }
        if (controlsPanel != null)
            controlsPanel.Width = this.Width - 48;
    }
}