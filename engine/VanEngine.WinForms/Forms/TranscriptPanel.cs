using VanEngine.WinForms.Helpers;
using VanEngine.WinForms.Services;

namespace VanEngine.WinForms.Forms;

public partial class TranscriptPanel : UserControl
{
    private readonly TranscriptParser _parser;
    private TextBox? _pathTextBox;
    private Button? _loadButton;
    private Label? _voiceLabel;
    private Label? _stateLabel;
    private ListBox? _messagesList;

    public TranscriptPanel(TranscriptParser parser)
    {
        _parser = parser;
        InitializeComponent();
        InitializeCustomComponents();
    }

    private void InitializeComponent()
    {
        this.Name = "TranscriptPanel";
        this.BackColor = ColorPalette.Primary;
        this.AutoScroll = true;
        this.Padding = new Padding(24);
    }

    private void InitializeCustomComponents()
    {
        var titleLabel = new Label { Text = "Transcript Viewer", Font = new Font("Segoe UI", 24, FontStyle.Bold), ForeColor = ColorPalette.Accent, AutoSize = true, Location = new Point(0, 0) };
        this.Controls.Add(titleLabel);

        var inputPanel = new Panel { Location = new Point(0, 50), Size = new Size(this.Width - 48, 40), Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right };

        _pathTextBox = new TextBox
        {
            Location = new Point(0, 0), Size = new Size(inputPanel.Width - 100, 30),
            BackColor = ColorPalette.Tertiary, ForeColor = ColorPalette.TextPrimary,
            BorderStyle = BorderStyle.FixedSingle, Font = new Font("Consolas", 10),
            Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        };
        inputPanel.Controls.Add(_pathTextBox);

        _loadButton = new Button
        {
            Text = "Parse", Location = new Point(inputPanel.Width - 90, 0), Size = new Size(90, 30),
            Anchor = AnchorStyles.Top | AnchorStyles.Right, BackColor = ColorPalette.Accent,
            ForeColor = ColorPalette.Primary, FlatStyle = FlatStyle.Flat,
            Font = new Font("Segoe UI", 10, FontStyle.Bold), Cursor = Cursors.Hand
        };
        _loadButton.FlatAppearance.BorderSize = 0;
        _loadButton.Click += LoadButton_Click;
        inputPanel.Controls.Add(_loadButton);
        this.Controls.Add(inputPanel);

        _stateLabel = new Label { Location = new Point(0, 100), AutoSize = true, Font = new Font("Segoe UI", 10), ForeColor = ColorPalette.TextSecondary };
        this.Controls.Add(_stateLabel);

        _voiceLabel = new Label { Location = new Point(0, 130), AutoSize = true, Font = new Font("Segoe UI", 10), ForeColor = ColorPalette.Accent, MaximumSize = new Size(this.Width - 48, 0) };
        this.Controls.Add(_voiceLabel);

        var messagesLabel = new Label { Text = "Messages:", Location = new Point(0, 170), AutoSize = true, Font = new Font("Segoe UI", 10, FontStyle.Bold), ForeColor = ColorPalette.TextSecondary };
        this.Controls.Add(messagesLabel);

        _messagesList = new ListBox
        {
            Location = new Point(0, 200), Size = new Size(this.Width - 48, 300),
            BackColor = ColorPalette.Tertiary, ForeColor = ColorPalette.TextPrimary,
            BorderStyle = BorderStyle.FixedSingle, Font = new Font("Consolas", 9),
            Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom
        };
        this.Controls.Add(_messagesList);
    }

    private async void LoadButton_Click(object? sender, EventArgs e)
    {
        if (string.IsNullOrWhiteSpace(_pathTextBox?.Text)) return;

        _loadButton!.Enabled = false;
        _loadButton.Text = "Loading...";

        try
        {
            var result = await Task.Run(() => _parser.ParseFile(_pathTextBox.Text));

            if (!string.IsNullOrEmpty(result.Error))
            {
                _stateLabel!.Text = $"Error: {result.Error}";
                return;
            }

            _stateLabel!.Text = $"Messages: {result.MessageCount} | State: {result.ResponseState}";
            _voiceLabel!.Text = string.IsNullOrEmpty(result.VoiceCompletion) ? "(no voice completion)" : result.VoiceCompletion;

            _messagesList!.Items.Clear();
            foreach (var msg in result.Messages)
            {
                var preview = msg.Content.Length > 100 ? msg.Content[..100] + "..." : msg.Content;
                _messagesList.Items.Add($"[{msg.Role}] {preview}");
            }
        }
        catch (Exception ex)
        {
            _stateLabel!.Text = $"Error: {ex.Message}";
        }
        finally
        {
            _loadButton.Enabled = true;
            _loadButton.Text = "Parse";
        }
    }

    protected override void OnResize(EventArgs e)
    {
        base.OnResize(e);
        if (_pathTextBox != null) _pathTextBox.Width = this.Width - 148;
        if (_messagesList != null) _messagesList.Width = this.Width - 48;
        if (_voiceLabel != null) _voiceLabel.MaximumSize = new Size(this.Width - 48, 0);
    }
}
