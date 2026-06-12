using System.Drawing;
using System.Windows.Forms;
using System.Text.Json;
using SovereignIDE.Core.Models;

namespace SovereignIDE.UI.Controls;

public class ManifestViewerControl : UserControl
{
    private TextBox _manifestTextBox;
    private TextBox _previewTextBox;
    private TabControl _tabControl;
    private Label _headerLabel;

    public ManifestViewerControl()
    {
        InitializeComponent();
    }

    private void InitializeComponent()
    {
        BackColor = Color.FromArgb(15, 15, 15);

        // Header
        _headerLabel = new Label
        {
            Text = "MANIFEST & PREVIEW",
            Dock = DockStyle.Top,
            Height = 40,
            BackColor = Color.FromArgb(10, 10, 10),
            ForeColor = Color.FromArgb(180, 180, 180),
            Font = new Font("Segoe UI", 10, FontStyle.Bold),
            Padding = new Padding(10, 0, 0, 0),
            TextAlign = ContentAlignment.MiddleLeft
        };

        // Tab control
        _tabControl = new TabControl
        {
            Dock = DockStyle.Fill,
            BackColor = Color.FromArgb(15, 15, 15),
            ForeColor = Color.FromArgb(220, 220, 220)
        };

        // Manifest tab
        var manifestTab = new TabPage("Manifest");
        _manifestTextBox = new TextBox
        {
            Dock = DockStyle.Fill,
            Multiline = true,
            BackColor = Color.FromArgb(20, 20, 20),
            ForeColor = Color.FromArgb(220, 220, 220),
            Font = new Font("Consolas", 9),
            BorderStyle = BorderStyle.None,
            ScrollBars = ScrollBars.Both,
            ReadOnly = true
        };
        manifestTab.Controls.Add(_manifestTextBox);

        // Preview tab
        var previewTab = new TabPage("Preview");
        _previewTextBox = new TextBox
        {
            Dock = DockStyle.Fill,
            Multiline = true,
            BackColor = Color.FromArgb(20, 20, 20),
            ForeColor = Color.FromArgb(220, 220, 220),
            Font = new Font("Consolas", 9),
            BorderStyle = BorderStyle.None,
            ScrollBars = ScrollBars.Both,
            ReadOnly = true
        };
        previewTab.Controls.Add(_previewTextBox);

        _tabControl.TabPages.Add(manifestTab);
        _tabControl.TabPages.Add(previewTab);

        Controls.Add(_tabControl);
        Controls.Add(_headerLabel);
    }

    public void LoadManifest(ManifestV4 manifest)
    {
        try
        {
            var json = JsonSerializer.Serialize(manifest, new JsonSerializerOptions
            {
                WriteIndented = true
            });

            _manifestTextBox.Text = json;
        }
        catch (Exception ex)
        {
            _manifestTextBox.Text = $"Error loading manifest: {ex.Message}";
        }
    }

    public void ShowFilePreview(FileEntry file)
    {
        _tabControl.SelectedIndex = 1; // Switch to Preview tab

        var preview = $"File: {file.Path}\n";
        preview += $"State: {file.State}\n";
        preview += $"Language: {file.Language ?? "unknown"}\n";
        preview += $"Size: {file.Size ?? 0} bytes\n";
        preview += $"Lines: {file.Lines ?? 0}\n";
        preview += $"Modified: {file.LastModifiedDate?.ToString() ?? "unknown"}\n";
        preview += new string('-', 80) + "\n\n";
        preview += file.Content ?? "(no content)";

        _previewTextBox.Text = preview;
    }
}
