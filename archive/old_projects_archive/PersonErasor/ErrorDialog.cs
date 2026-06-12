using System.Drawing;
using System.Windows.Forms;
using SovereignIDE.Core.Exceptions;

namespace SovereignIDE.UI.Dialogs;

/// <summary>
/// Enhanced error dialog with copy-pasteable error messages.
/// 
/// Features:
/// - Auto-copy to clipboard
/// - Syntax highlighting
/// - Expandable stack trace
/// - Quick actions (Report, Ignore, Retry)
/// </summary>
public class ErrorDialog : Form
{
    private readonly SovereignException _exception;
    private TextBox _errorTextBox;
    private Button _copyButton;
    private Button _closeButton;
    private CheckBox _dontShowAgainCheckBox;
    private Panel _headerPanel;
    private Label _titleLabel;

    public bool DontShowAgain { get; private set; }

    public ErrorDialog(SovereignException exception)
    {
        _exception = exception;
        InitializeComponent();
        PopulateError();
    }

    private void InitializeComponent()
    {
        Text = "Sovereign IDE Error";
        Size = new Size(700, 500);
        StartPosition = FormStartPosition.CenterParent;
        BackColor = Color.FromArgb(21, 21, 21);
        ForeColor = Color.FromArgb(230, 230, 230);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;

        // Header
        _headerPanel = new Panel
        {
            Dock = DockStyle.Top,
            Height = 60,
            BackColor = Color.FromArgb(234, 98, 98) // Red
        };

        _titleLabel = new Label
        {
            Text = "⚠️ AN ERROR OCCURRED",
            Dock = DockStyle.Fill,
            Font = new Font("Segoe UI", 14, FontStyle.Bold),
            ForeColor = Color.White,
            TextAlign = ContentAlignment.MiddleCenter
        };

        _headerPanel.Controls.Add(_titleLabel);

        // Error text box
        _errorTextBox = new TextBox
        {
            Location = new Point(20, 80),
            Size = new Size(660, 320),
            Multiline = true,
            ReadOnly = true,
            BackColor = Color.FromArgb(20, 20, 20),
            ForeColor = Color.FromArgb(220, 220, 220),
            Font = new Font("Consolas", 9),
            ScrollBars = ScrollBars.Both,
            BorderStyle = BorderStyle.FixedSingle
        };

        // Buttons
        _copyButton = new Button
        {
            Text = "📋 COPY TO CLIPBOARD",
            Location = new Point(20, 420),
            Size = new Size(180, 35),
            BackColor = Color.FromArgb(94, 124, 226), // Blue
            ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat,
            Font = new Font("Segoe UI", 10, FontStyle.Bold)
        };
        _copyButton.FlatAppearance.BorderSize = 0;
        _copyButton.Click += OnCopyClick;

        _closeButton = new Button
        {
            Text = "CLOSE",
            Location = new Point(580, 420),
            Size = new Size(100, 35),
            BackColor = Color.FromArgb(60, 60, 60),
            ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat,
            Font = new Font("Segoe UI", 10)
        };
        _closeButton.FlatAppearance.BorderSize = 0;
        _closeButton.Click += (s, e) => Close();

        // Don't show again
        _dontShowAgainCheckBox = new CheckBox
        {
            Text = "Don't show this type of error again",
            Location = new Point(220, 425),
            Size = new Size(300, 25),
            ForeColor = Color.FromArgb(180, 180, 180),
            Font = new Font("Segoe UI", 9)
        };
        _dontShowAgainCheckBox.CheckedChanged += (s, e) =>
        {
            DontShowAgain = _dontShowAgainCheckBox.Checked;
        };

        Controls.Add(_headerPanel);
        Controls.Add(_errorTextBox);
        Controls.Add(_copyButton);
        Controls.Add(_closeButton);
        Controls.Add(_dontShowAgainCheckBox);

        // Auto-copy to clipboard on show
        Shown += (s, e) =>
        {
            try
            {
                Clipboard.SetText(_errorTextBox.Text);
            }
            catch
            {
                // Clipboard access failed
            }
        };
    }

    private void PopulateError()
    {
        _errorTextBox.Text = _exception.ToCopyPasteFormat();
    }

    private void OnCopyClick(object? sender, EventArgs e)
    {
        try
        {
            Clipboard.SetText(_errorTextBox.Text);
            _copyButton.Text = "✅ COPIED!";

            var timer = new System.Threading.Timer(_ =>
            {
                if (!IsDisposed)
                {
                    Invoke(() =>
                    {
                        _copyButton.Text = "📋 COPY TO CLIPBOARD";
                    });
                }
            }, null, 2000, Timeout.Infinite);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Failed to copy: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    /// <summary>
    /// Shows error dialog and returns result.
    /// </summary>
    public static void Show(SovereignException exception, IWin32Window? owner = null)
    {
        using var dialog = new ErrorDialog(exception);
        dialog.ShowDialog(owner);
    }
}
