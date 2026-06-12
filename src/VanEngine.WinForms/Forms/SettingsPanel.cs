using VanEngine.WinForms.Helpers;

namespace VanEngine.WinForms.Forms;

public partial class SettingsPanel : UserControl
{
    private NumericUpDown? _portNumeric;
    private CheckBox? _autoConnectCheck;
    private Button? _testConnectionButton;
    private Label? _connectionResult;

    public SettingsPanel()
    {
        InitializeComponent();
        InitializeCustomComponents();
    }

    private void InitializeComponent()
    {
        this.Name = "SettingsPanel";
        this.BackColor = ColorPalette.Primary;
        this.AutoScroll = true;
        this.Padding = new Padding(24);
    }

    private void InitializeCustomComponents()
    {
        var titleLabel = new Label { Text = "Settings", Font = new Font("Segoe UI", 24, FontStyle.Bold), ForeColor = ColorPalette.Accent, AutoSize = true, Location = new Point(0, 0) };
        this.Controls.Add(titleLabel);

        var groupBox = new GroupBox
        {
            Text = "VAN_Engine Connection", Location = new Point(0, 60),
            Size = new Size(400, 200), BackColor = ColorPalette.Secondary,
            ForeColor = ColorPalette.TextPrimary, Font = new Font("Segoe UI", 10)
        };

        var portLabel = new Label { Text = "API Port:", Location = new Point(16, 35), AutoSize = true, ForeColor = ColorPalette.TextSecondary };
        groupBox.Controls.Add(portLabel);

        _portNumeric = new NumericUpDown
        {
            Location = new Point(100, 32), Size = new Size(100, 25),
            Minimum = 1024, Maximum = 20000, BackColor = ColorPalette.Tertiary,
            ForeColor = ColorPalette.TextPrimary
        };
        groupBox.Controls.Add(_portNumeric);

        _portNumeric.Value = 11434;

        _autoConnectCheck = new CheckBox
        {
            Text = "Auto-connect on startup", Location = new Point(16, 70),
            Size = new Size(200, 25), Checked = true, ForeColor = ColorPalette.TextPrimary
        };
        groupBox.Controls.Add(_autoConnectCheck);

        _testConnectionButton = new Button
        {
            Text = "Test Connection", Location = new Point(16, 110), Size = new Size(150, 35),
            BackColor = ColorPalette.Accent, ForeColor = ColorPalette.Primary,
            FlatStyle = FlatStyle.Flat, Font = new Font("Segoe UI", 10, FontStyle.Bold), Cursor = Cursors.Hand
        };
        _testConnectionButton.FlatAppearance.BorderSize = 0;
        _testConnectionButton.Click += TestConnection_Click;
        groupBox.Controls.Add(_testConnectionButton);

        _connectionResult = new Label { Location = new Point(16, 155), AutoSize = true, ForeColor = ColorPalette.TextSecondary };
        groupBox.Controls.Add(_connectionResult);

        this.Controls.Add(groupBox);
    }

    private async void TestConnection_Click(object? sender, EventArgs e)
    {
        _testConnectionButton!.Enabled = false;
        _testConnectionButton.Text = "Testing...";
        _connectionResult!.Text = "";

        try
        {
            using var httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(5) };
            var port = _portNumeric?.Value ?? 11434;
            var response = await httpClient.GetAsync($"http://localhost:{port}/health");
            _connectionResult.Text = response.IsSuccessStatusCode ? "Connected" : "API responded but not healthy";
            _connectionResult.ForeColor = response.IsSuccessStatusCode ? ColorPalette.Success : ColorPalette.Warning;
        }
        catch (Exception ex)
        {
            _connectionResult.Text = $"Failed: {ex.Message}";
            _connectionResult.ForeColor = ColorPalette.Error;
        }
        finally
        {
            _testConnectionButton.Enabled = true;
            _testConnectionButton.Text = "Test Connection";
        }
    }
}
