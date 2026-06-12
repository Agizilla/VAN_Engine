using VanEngine.WinForms.Controls;
using VanEngine.WinForms.Helpers;
using VanEngine.WinForms.Models;
using VanEngine.WinForms.Services;

namespace VanEngine.WinForms.Forms;

public partial class ChatPanel : UserControl
{
    private readonly BrainBridge _brainBridge;

    // Designer controls
    private Panel? messageContainer;
    private FlowLayoutPanel? messagePanel;
    private Panel? inputPanel;
    private RichTextBox? inputTextBox;
    private Button? sendButton;

    private readonly List<ChatMessage> _messages = new();

    public ChatPanel(BrainBridge brainBridge)
    {
        _brainBridge = brainBridge;
        InitializeComponent();
        InitializeCustomComponents();
    }

    private void InitializeComponent()
    {
        SuspendLayout();
        // 
        // ChatPanel
        // 
        BackColor = Color.FromArgb(10, 14, 23);
        Name = "ChatPanel";
        Size = new Size(577, 218);
        ResumeLayout(false);
    }

    private void InitializeCustomComponents()
    {
        // Message container (scrollable)
        this.messageContainer = new Panel();
        this.messageContainer.AutoScroll = true;
        this.messageContainer.BackColor = ColorPalette.Primary;
        this.messageContainer.Dock = DockStyle.Fill;
        this.messageContainer.Name = "messageContainer";

        // Message flow panel
        this.messagePanel = new FlowLayoutPanel();
        this.messagePanel.AutoSize = true;
        this.messagePanel.BackColor = ColorPalette.Primary;
        this.messagePanel.Dock = DockStyle.Top;
        this.messagePanel.FlowDirection = FlowDirection.TopDown;
        this.messagePanel.Padding = new Padding(16);
        this.messagePanel.WrapContents = false;
        this.messageContainer.Controls.Add(this.messagePanel);

        // Input panel
        this.inputPanel = new Panel();
        this.inputPanel.BackColor = ColorPalette.Secondary;
        this.inputPanel.Dock = DockStyle.Bottom;
        this.inputPanel.Height = 80;
        this.inputPanel.Padding = new Padding(12);

        // Input text box - READ-WRITE (editable for copying)
        this.inputTextBox = new RichTextBox();
        this.inputTextBox.BackColor = ColorPalette.Tertiary;
        this.inputTextBox.ForeColor = ColorPalette.TextPrimary;
        this.inputTextBox.BorderStyle = BorderStyle.FixedSingle;
        this.inputTextBox.Font = new Font("Segoe UI", 11F);
        this.inputTextBox.Multiline = true;
        this.inputTextBox.Height = 56;
        this.inputTextBox.Width = 900;
        this.inputTextBox.Location = new Point(12, 12);
        this.inputTextBox.Name = "inputTextBox";
        this.inputTextBox.ReadOnly = false;  // Allow editing and copying
        this.inputTextBox.KeyDown += InputTextBox_KeyDown;

        // Send button
        this.sendButton = new Button();
        this.sendButton.Text = "Send";
        this.sendButton.Size = new Size(80, 40);
        this.sendButton.Location = new Point(930, 20);
        this.sendButton.BackColor = ColorPalette.Accent;
        this.sendButton.ForeColor = ColorPalette.Primary;
        this.sendButton.FlatStyle = FlatStyle.Flat;
        this.sendButton.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
        this.sendButton.Cursor = Cursors.Hand;
        this.sendButton.FlatAppearance.BorderSize = 0;
        this.sendButton.Click += SendButton_Click;

        this.inputPanel.Controls.Add(this.inputTextBox);
        this.inputPanel.Controls.Add(this.sendButton);

        // Add to control
        this.Controls.Add(this.messageContainer);
        this.Controls.Add(this.inputPanel);

        // Resize handler for input box
        this.Resize += (s, e) =>
        {
            if (inputTextBox != null && sendButton != null)
            {
                inputTextBox.Width = this.Width - 110;
                sendButton.Location = new Point(this.Width - 90, 20);
            }
        };

        // Welcome message
        AddMessage(new ChatMessage
        {
            Content = "👋 Welcome to VAN_Engine! How can I help you today?\n\nYou can copy text from any message by selecting it with your mouse.",
            IsUser = false,
            Timestamp = DateTime.Now
        });
    }

    private void InputTextBox_KeyDown(object? sender, KeyEventArgs e)
    {
        if (e.Control && e.KeyCode == Keys.Enter)
        {
            e.SuppressKeyPress = true;
            _ = SendMessage();
        }
    }

    private async void SendButton_Click(object? sender, EventArgs e)
    {
        await SendMessage();
    }

    private async Task SendMessage()
    {
        if (inputTextBox == null || string.IsNullOrWhiteSpace(inputTextBox.Text))
            return;

        var userMessage = inputTextBox.Text;
        inputTextBox.Clear();

        AddMessage(new ChatMessage
        {
            Content = userMessage,
            IsUser = true,
            Timestamp = DateTime.Now
        });

        var typingIndicator = AddTypingIndicator();

        var response = await _brainBridge.QueryAsync(userMessage);

        RemoveTypingIndicator(typingIndicator);

        AddMessage(new ChatMessage
        {
            Content = response.Message,
            IsUser = false,
            Timestamp = DateTime.Now,
            Metadata = new { response.Action, response.Confidence }
        });
    }

    private MessageBubble AddMessage(ChatMessage message)
    {
        if (messagePanel == null) return null!;

        var bubble = new MessageBubble(message);
        messagePanel.Controls.Add(bubble);

        if (messageContainer != null)
            messageContainer.ScrollControlIntoView(bubble);

        return bubble;
    }

    private Panel AddTypingIndicator()
    {
        if (messagePanel == null) return null!;

        var indicator = new Panel { Height = 40, Width = 80, Margin = new Padding(0, 4, 0, 4) };
        var dots = new Label
        {
            Text = "● ● ●",
            ForeColor = ColorPalette.TextSecondary,
            Font = new Font("Segoe UI", 12F),
            TextAlign = ContentAlignment.MiddleCenter,
            Dock = DockStyle.Fill
        };
        indicator.Controls.Add(dots);
        messagePanel.Controls.Add(indicator);

        var timer = new System.Windows.Forms.Timer { Interval = 500 };
        int dotCount = 1;
        timer.Tick += (s, e) =>
        {
            dots.Text = new string('●', dotCount) + new string(' ', 3 - dotCount);
            dotCount = dotCount % 3 + 1;
        };
        timer.Start();
        indicator.Tag = timer;

        return indicator;
    }

    private void RemoveTypingIndicator(Panel? indicator)
    {
        if (indicator == null || messagePanel == null) return;

        if (indicator.Tag is System.Windows.Forms.Timer timer)
        {
            timer.Stop();
            timer.Dispose();
        }

        messagePanel.Controls.Remove(indicator);
        indicator.Dispose();
    }
}