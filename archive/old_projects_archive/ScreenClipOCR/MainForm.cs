using System.Drawing;
using System.ComponentModel;
using System.Text;

namespace ScreenClipOCR;

public partial class MainForm : Form
{
    private static readonly Color AppBackground = Color.FromArgb(243, 238, 230);
    private static readonly Color CardBackground = Color.FromArgb(252, 249, 243);
    private static readonly Color InsetBackground = Color.FromArgb(255, 253, 249);
    private static readonly Color AccentColor = Color.FromArgb(30, 91, 76);
    private static readonly Color AccentSoft = Color.FromArgb(224, 238, 232);
    private static readonly Color BorderColor = Color.FromArgb(210, 201, 189);
    private static readonly Color TextColor = Color.FromArgb(29, 33, 36);
    private static readonly Color MutedColor = Color.FromArgb(93, 98, 104);

    private readonly GlobalHotkeyWindow? _hotkeyWindow;
    private readonly AppOptions _options = new();
    private readonly List<CaptureHistoryItem> _captureHistory = [];
    private readonly NotifyIcon _trayIcon = new();
    private readonly ContextMenuStrip _trayMenu = new();
    private bool _settingsExpanded = true;
    private bool _actionsExpanded = true;
    private bool _allowClose;
    private int _captureCounter;
    private CaptureHistoryItem? _selectedCapture;

    public MainForm()
    {
        InitializeComponent();
        ApplyTheme();
        if (IsDesignerHosted())
        {
            return;
        }

        WireEvents();
        InitializeTray();

        _hotkeyWindow = new GlobalHotkeyWindow();
        _hotkeyWindow.HotkeyPressed += async (_, _) => await RunCaptureAsync();
        hotkeyLabel.Text = _hotkeyWindow.IsRegistered
            ? $"Global hotkey registered: {_hotkeyWindow.DisplayText}"
            : "Global hotkey could not be registered. Manual capture still works.";

        statusLabel.Text = _hotkeyWindow.IsRegistered
            ? "Ready. Captured images will always be copied to the clipboard."
            : "Ready without a global hotkey. Use Start Capture to test the app.";

        saveFolderTextBox.Text = _options.SaveFolder;
        runOcrCheckbox.Checked = _options.RunOcr;
        saveImageCheckbox.Checked = _options.SaveImage;
        RefreshSettingsSummary();
        RefreshActionsSummary();
    }

    private static bool IsDesignerHosted()
    {
        return LicenseManager.UsageMode == LicenseUsageMode.Designtime;
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            foreach (var item in _captureHistory)
            {
                item.Image.Dispose();
                item.Thumbnail.Dispose();
            }

            lastCapturePreview.Image?.Dispose();
            _hotkeyWindow?.Dispose();
            _trayIcon.Dispose();
            _trayMenu.Dispose();
            components?.Dispose();
        }

        base.Dispose(disposing);
    }

    private void ApplyTheme()
    {
        BackColor = AppBackground;
        ForeColor = TextColor;
        Font = new Font("Segoe UI", 10F, FontStyle.Regular, GraphicsUnit.Point);

        titleLabel.ForeColor = TextColor;
        subtitleLabel.ForeColor = MutedColor;
        statusLabel.ForeColor = TextColor;
        extractedTextHintLabel.ForeColor = MutedColor;

        hotkeyLabel.BackColor = AccentSoft;
        hotkeyLabel.ForeColor = AccentColor;

        settingsCardPanel.BackColor = CardBackground;
        leftCardPanel.BackColor = CardBackground;
        rightCardPanel.BackColor = CardBackground;

        lastCapturePanel.BackColor = InsetBackground;
        historyPanel.BackColor = InsetBackground;
        statusPanel.BackColor = InsetBackground;
        extractedTextPanel.BackColor = InsetBackground;

        extractedTextTextBox.BackColor = InsetBackground;
        lastCapturePreview.BackColor = InsetBackground;
        captureHistoryListView.BackColor = InsetBackground;

        ConfigurePrimaryButton(startCaptureButton);
        ConfigureSecondaryButton(browseButton);
        ConfigureSecondaryButton(extractTextButton);
        ConfigureSecondaryButton(btnSaveImagesFolder);
    }

    private void WireEvents()
    {
        browseButton.Click += BrowseButton_Click;
        startCaptureButton.Click += async (_, _) => await RunCaptureAsync();
        extractTextButton.Click += async (_, _) => await RunExtractionAsync();
        btnSaveImagesFolder.Click += BtnSaveImagesFolder_Click;

        saveImageCheckbox.CheckedChanged += (_, _) =>
        {
            _options.SaveImage = saveImageCheckbox.Checked;
            RefreshSettingsSummary();
        };

        runOcrCheckbox.CheckedChanged += (_, _) =>
        {
            _options.RunOcr = runOcrCheckbox.Checked;
            RefreshSettingsSummary();
        };

        saveFolderTextBox.TextChanged += (_, _) =>
        {
            _options.SaveFolder = saveFolderTextBox.Text.Trim();
            RefreshSettingsSummary();
        };

        lastCapturePreview.Click += (_, _) => ShowSelectedCaptureText();
        lastCapturePreview.DoubleClick += (_, _) => ShowSelectedCaptureImage();

        captureHistoryListView.SelectedIndexChanged += HistoryListView_SelectedIndexChanged;
        captureHistoryListView.DoubleClick += (_, _) => ShowSelectedCaptureImage();

        Resize += MainForm_Resize;
        FormClosing += MainForm_FormClosing;
    }

    private void InitializeTray()
    {
        var openItem = new ToolStripMenuItem("Open ScreenClipOCR");
        openItem.Click += (_, _) => RestoreFromTray();

        var captureItem = new ToolStripMenuItem("Start Capture");
        captureItem.Click += async (_, _) =>
        {
            RestoreFromTray();
            await RunCaptureAsync();
        };

        var exitItem = new ToolStripMenuItem("Exit");
        exitItem.Click += (_, _) =>
        {
            _allowClose = true;
            _trayIcon.Visible = false;
            Close();
        };

        _trayMenu.Items.Add(openItem);
        _trayMenu.Items.Add(captureItem);
        _trayMenu.Items.Add(new ToolStripSeparator());
        _trayMenu.Items.Add(exitItem);

        _trayIcon.Text = "ScreenClipOCR";
        _trayIcon.Icon = SystemIcons.Application;
        _trayIcon.ContextMenuStrip = _trayMenu;
        _trayIcon.DoubleClick += (_, _) => RestoreFromTray();
        _trayIcon.Visible = true;
    }

    private void ConfigurePrimaryButton(Button button)
    {
        button.BackColor = AccentColor;
        button.ForeColor = Color.White;
        button.FlatStyle = FlatStyle.Flat;
        button.FlatAppearance.BorderSize = 0;
    }

    private void ConfigureSecondaryButton(Button button)
    {
        button.BackColor = Color.White;
        button.ForeColor = TextColor;
        button.FlatStyle = FlatStyle.Flat;
        button.FlatAppearance.BorderColor = BorderColor;
    }

    private void BrowseButton_Click(object? sender, EventArgs e)
    {
        using var dialog = new FolderBrowserDialog
        {
            InitialDirectory = _options.SaveFolder,
            UseDescriptionForTitle = true,
            Description = "Choose where ScreenClipOCR should save images."
        };

        if (dialog.ShowDialog(this) == DialogResult.OK)
        {
            saveFolderTextBox.Text = dialog.SelectedPath;
        }
    }

    private async void BtnSaveImagesFolder_Click(object? sender, EventArgs e)
    {
        if (_captureHistory.Count == 0)
        {
            statusLabel.Text = "There are no captured images to save yet.";
            return;
        }

        var targetFolder = saveFolderTextBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(targetFolder))
        {
            statusLabel.Text = "Choose a save folder first using Browse.";
            return;
        }

        try
        {
            Directory.CreateDirectory(targetFolder);
            var exportRoot = Path.Combine(targetFolder, $"ScreenClipOCR_Export_{DateTime.Now:yyyyMMdd_HHmmss}");
            Directory.CreateDirectory(exportRoot);

            var manifest = new StringBuilder();
            manifest.AppendLine("ScreenClipOCR Export");
            manifest.AppendLine($"Created: {DateTime.Now:O}");
            manifest.AppendLine();

            foreach (var item in _captureHistory)
            {
                var safeName = GetSafeFileName($"{item.Title}_{item.CreatedAt:yyyyMMdd_HHmmss}");
                var imagePath = Path.Combine(exportRoot, $"{safeName}.png");
                item.Image.Save(imagePath);

                manifest.AppendLine($"{item.Title}");
                manifest.AppendLine($"  Image: {Path.GetFileName(imagePath)}");
                manifest.AppendLine($"  Captured: {item.CreatedAt:O}");

                if (!string.IsNullOrWhiteSpace(item.ExtractedText))
                {
                    var textPath = Path.Combine(exportRoot, $"{safeName}.txt");
                    await File.WriteAllTextAsync(textPath, item.ExtractedText);
                    manifest.AppendLine($"  Text: {Path.GetFileName(textPath)}");
                }

                manifest.AppendLine();
            }

            await File.WriteAllTextAsync(Path.Combine(exportRoot, "manifest.txt"), manifest.ToString());
            statusLabel.Text = $"Saved {_captureHistory.Count} captured image(s) to {exportRoot}.";
        }
        catch (Exception ex)
        {
            statusLabel.Text = $"Save all failed: {ex.Message}";
        }
    }

    private async Task RunCaptureAsync()
    {
        if (!Visible)
        {
            Show();
            WindowState = FormWindowState.Normal;
        }

        startCaptureButton.Enabled = false;
        statusLabel.Text = "Capture mode starting...";
        extractedTextTextBox.Clear();

        try
        {
            Hide();
            await Task.Delay(150);

            var capture = ScreenCaptureService.CaptureRegion(this);
            if (capture is null)
            {
                statusLabel.Text = "Capture cancelled.";
                return;
            }

            using var image = capture.Image;
            Clipboard.SetImage(image);

            string? savedPath = null;
            if (_options.SaveImage)
            {
                savedPath = ScreenCaptureService.SaveCapture(image, _options.SaveFolder);
            }

            string? ocrText = null;
            if (_options.RunOcr)
            {
                ocrText = await ExtractFromBitmapAsync(image);
            }

            var item = AddCaptureToHistory(image, ocrText);
            SelectCapture(item);
            statusLabel.Text = BuildStatusText(savedPath, ocrText);
        }
        catch (Exception ex)
        {
            statusLabel.Text = $"Capture failed: {ex.Message}";
        }
        finally
        {
            Show();
            Activate();
            startCaptureButton.Enabled = true;
            RefreshActionsSummary();
        }
    }

    private async Task RunExtractionAsync()
    {
        if (_selectedCapture is null)
        {
            statusLabel.Text = "Capture an image first, then extract text.";
            return;
        }

        startCaptureButton.Enabled = false;

        try
        {
            using var bitmap = new Bitmap(_selectedCapture.Image);
            var text = await ExtractFromBitmapAsync(bitmap);
            _selectedCapture.ExtractedText = text;
            ShowSelectedCaptureText();
            statusLabel.Text = string.IsNullOrWhiteSpace(text)
                ? "No OCR text extracted from the selected capture."
                : "OCR text copied to clipboard from the selected capture.";
        }
        catch (Exception ex)
        {
            statusLabel.Text = $"Extraction failed: {ex.Message}";
        }
        finally
        {
            startCaptureButton.Enabled = true;
            RefreshActionsSummary();
        }
    }

    private async Task<string?> ExtractFromBitmapAsync(Bitmap bitmap)
    {
        statusLabel.Text = "Running OCR...";
        var ocrText = await OcrService.TryExtractTextAsync(bitmap);
        if (!string.IsNullOrWhiteSpace(ocrText))
        {
            Clipboard.SetText(ocrText);
            extractedTextTextBox.Text = ocrText;
        }

        return ocrText;
    }

    private CaptureHistoryItem AddCaptureToHistory(Bitmap image, string? extractedText)
    {
        _captureCounter += 1;

        var storedImage = new Bitmap(image);
        var thumb = new Bitmap(image, new Size(72, 72));
        var item = new CaptureHistoryItem
        {
            Id = _captureCounter,
            Title = $"Capture {_captureCounter}",
            CreatedAt = DateTime.Now,
            Image = storedImage,
            Thumbnail = thumb,
            ExtractedText = extractedText
        };

        _captureHistory.Add(item);
        captureHistoryImageList.Images.Add(item.Thumbnail);

        var listViewItem = new ListViewItem(item.Title, captureHistoryImageList.Images.Count - 1)
        {
            Tag = item
        };
        captureHistoryListView.Items.Insert(0, listViewItem);

        return item;
    }

    private void HistoryListView_SelectedIndexChanged(object? sender, EventArgs e)
    {
        if (captureHistoryListView.SelectedItems.Count == 0)
        {
            return;
        }

        if (captureHistoryListView.SelectedItems[0].Tag is CaptureHistoryItem item)
        {
            SelectCapture(item);
            ShowSelectedCaptureText();
        }
    }

    private void SelectCapture(CaptureHistoryItem item)
    {
        _selectedCapture = item;

        lastCapturePreview.Image?.Dispose();
        lastCapturePreview.Image = new Bitmap(item.Image);
        RefreshActionsSummary();
    }

    private void ShowSelectedCaptureText()
    {
        if (_selectedCapture is null)
        {
            return;
        }

        extractedTextTextBox.Text = string.IsNullOrWhiteSpace(_selectedCapture.ExtractedText)
            ? "No extracted text stored yet for this capture."
            : _selectedCapture.ExtractedText;
    }

    private void ShowSelectedCaptureImage()
    {
        if (_selectedCapture is null)
        {
            return;
        }

        using var viewer = new CaptureViewerForm(_selectedCapture.Title, _selectedCapture.Image);
        viewer.ShowDialog(this);
    }

    private void ToggleSettings()
    {
        _settingsExpanded = !_settingsExpanded;
        settingsCardPanel.Visible = _settingsExpanded;
    }

    private void ToggleActions()
    {
        _actionsExpanded = !_actionsExpanded;
        startCaptureButton.Visible = _actionsExpanded;
        extractTextButton.Visible = _actionsExpanded;
        btnSaveImagesFolder.Visible = _actionsExpanded;
    }

    private void RefreshSettingsSummary()
    {
        var saveText = _options.SaveImage ? "save image on" : "save image off";
        var ocrText = _options.RunOcr ? "auto OCR on" : "auto OCR off";
        var folderText = string.IsNullOrWhiteSpace(_options.SaveFolder) ? "no folder selected" : _options.SaveFolder;
        Text = $"ScreenClipOCR · {saveText} · {ocrText}";
    }

    private void RefreshActionsSummary()
    {
        var selected = _selectedCapture is null ? "no capture selected" : _selectedCapture.Title;
        statusHeaderLabel.Text = $"Status · {selected} · {_captureHistory.Count} capture(s)";
    }

    private void MainForm_Resize(object? sender, EventArgs e)
    {
        if (WindowState == FormWindowState.Minimized)
        {
            Hide();
            _trayIcon.ShowBalloonTip(1200, "ScreenClipOCR", "Still running in the system tray.", ToolTipIcon.Info);
        }
    }

    private void MainForm_FormClosing(object? sender, FormClosingEventArgs e)
    {
        if (_allowClose || IsDesignerHosted())
        {
            return;
        }

        e.Cancel = true;
        Hide();
        _trayIcon.ShowBalloonTip(1200, "ScreenClipOCR", "Minimized to tray. Use the tray icon to reopen or exit.", ToolTipIcon.Info);
    }

    private void RestoreFromTray()
    {
        Show();
        WindowState = FormWindowState.Normal;
        Activate();
    }

    private static string GetSafeFileName(string value)
    {
        foreach (var invalid in Path.GetInvalidFileNameChars())
        {
            value = value.Replace(invalid, '_');
        }

        return value;
    }

    private static string BuildStatusText(string? savedPath, string? ocrText)
    {
        var parts = new List<string>
        {
            "Image copied to clipboard."
        };

        if (!string.IsNullOrWhiteSpace(savedPath))
        {
            parts.Add($"Saved to {savedPath}.");
        }

        if (!string.IsNullOrWhiteSpace(ocrText))
        {
            parts.Add("OCR text copied to clipboard.");
        }
        else
        {
            parts.Add("No OCR text extracted.");
        }

        return string.Join(" ", parts);
    }

    private sealed class CaptureHistoryItem
    {
        public required int Id { get; init; }
        public required string Title { get; init; }
        public required DateTime CreatedAt { get; init; }
        public required Bitmap Image { get; init; }
        public required Bitmap Thumbnail { get; init; }
        public string? ExtractedText { get; set; }
    }

    private sealed class CaptureViewerForm : Form
    {
        public CaptureViewerForm(string title, Image image)
        {
            Text = title;
            Width = 1000;
            Height = 760;
            StartPosition = FormStartPosition.CenterParent;
            BackColor = Color.Black;

            var picture = new PictureBox
            {
                Dock = DockStyle.Fill,
                Image = new Bitmap(image),
                SizeMode = PictureBoxSizeMode.Zoom,
                BackColor = Color.Black
            };

            Controls.Add(picture);
        }
    }

   
}
