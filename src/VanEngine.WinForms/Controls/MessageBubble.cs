using VanEngine.WinForms.Helpers;
using VanEngine.WinForms.Models;

namespace VanEngine.WinForms.Controls;

public partial class MessageBubble : UserControl
{
    private readonly ChatMessage _message;
    private Panel? _bubblePanel;
    private RichTextBox? _contentTextBox;  // Changed from Label to RichTextBox for selectable text
    private Label? _timeLabel;

    public MessageBubble(ChatMessage message)
    {
        _message = message;
        InitializeComponent();
        InitializeCustomComponents();
    }

    private void InitializeComponent()
    {
        this.BackColor = Color.Transparent;
        this.AutoSize = true;
        this.AutoSizeMode = AutoSizeMode.GrowAndShrink;
    }

    private void InitializeCustomComponents()
    {
        int maxWidth = (Parent?.Width ?? 800) * 70 / 100;

        _bubblePanel = new Panel
        {
            AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink,
            Padding = new Padding(12, 8, 12, 8),
            BackColor = _message.IsUser ? ColorPalette.Accent : ColorPalette.Tertiary
        };

        // Use RichTextBox instead of Label for selectable/copyable text
        _contentTextBox = new RichTextBox
        {
            Text = _message.Content,
            ReadOnly = true,          // Can't edit, but CAN select and copy
            BackColor = _bubblePanel.BackColor,
            ForeColor = _message.IsUser ? ColorPalette.Primary : ColorPalette.TextPrimary,
            Font = new Font("Segoe UI", 10F),
            BorderStyle = BorderStyle.None,
            Multiline = true,
            WordWrap = true,
            DetectUrls = true,
            ScrollBars = RichTextBoxScrollBars.None,
            AutoSize = false,
            Width = maxWidth - 24
        };

        // Auto-size height based on content
        using (var graphics = _contentTextBox.CreateGraphics())
        {
            var size = graphics.MeasureString(_message.Content, _contentTextBox.Font, maxWidth - 24);
            _contentTextBox.Height = (int)size.Height + 5;
        }

        _bubblePanel.Controls.Add(_contentTextBox);

        _timeLabel = new Label
        {
            Text = _message.Timestamp.ToString("HH:mm"),
            AutoSize = true,
            Font = new Font("Segoe UI", 7F),
            ForeColor = _message.IsUser ? Color.FromArgb(0, 100, 80) : ColorPalette.TextMuted,
            Location = new Point(_bubblePanel.Width - 30, _bubblePanel.Height - 14)
        };
        _bubblePanel.Controls.Add(_timeLabel);

        if (_message.IsUser)
        {
            _bubblePanel.Location = new Point(this.Width - _bubblePanel.Width - 8, 0);
            _bubblePanel.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        }
        else
        {
            _bubblePanel.Location = new Point(8, 0);
            _bubblePanel.Anchor = AnchorStyles.Top | AnchorStyles.Left;
        }

        this.Controls.Add(_bubblePanel);
        this.Height = _bubblePanel.Height + 8;
        this.Width = _bubblePanel.Width + 16;

        _contentTextBox.TextChanged += (s, e) => UpdateTimePosition();
        this.Resize += (s, e) => UpdateTimePosition();
    }

    private void UpdateTimePosition()
    {
        if (_bubblePanel == null || _timeLabel == null) return;
        _timeLabel.Location = new Point(_bubblePanel.Width - 30, _bubblePanel.Height - 18);
    }

    protected override void OnResize(EventArgs e)
    {
        base.OnResize(e);
        if (_bubblePanel != null)
        {
            if (_message.IsUser)
                _bubblePanel.Location = new Point(this.Width - _bubblePanel.Width - 8, 0);
            else
                _bubblePanel.Location = new Point(8, 0);
        }
    }
}