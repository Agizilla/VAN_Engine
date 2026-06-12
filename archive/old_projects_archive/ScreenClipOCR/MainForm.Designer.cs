namespace ScreenClipOCR;

partial class MainForm
{
    private System.ComponentModel.IContainer components = null!;

    private Label titleLabel = null!;
    private Label subtitleLabel = null!;
    private Panel settingsCardPanel = null!;
    private Label settingsHeaderLabel = null!;
    private CheckBox saveImageCheckbox = null!;
    private CheckBox runOcrCheckbox = null!;
    private Label settingsSaveLocationLabel = null!;
    private TextBox saveFolderTextBox = null!;
    private Button browseButton = null!;
    private Label settingsHotkeyHeaderLabel = null!;
    private Label hotkeyLabel = null!;
    private Panel leftCardPanel = null!;
    private Label lastCaptureHeaderLabel = null!;
    private Panel lastCapturePanel = null!;
    private PictureBox lastCapturePreview = null!;
    private Label captureHistoryHeaderLabel = null!;
    private Panel historyPanel = null!;
    private ListView captureHistoryListView = null!;
    private ImageList captureHistoryImageList = null!;
    private Label statusHeaderLabel = null!;
    private Panel statusPanel = null!;
    private Label statusLabel = null!;
    private Panel rightCardPanel = null!;
    private Button startCaptureButton = null!;
    private Button extractTextButton = null!;
    private Label extractedTextHeaderLabel = null!;
    private Label extractedTextHintLabel = null!;
    private Panel extractedTextPanel = null!;
    private TextBox extractedTextTextBox = null!;

    private void InitializeComponent()
    {
        components = new System.ComponentModel.Container();
        titleLabel = new Label();
        subtitleLabel = new Label();
        settingsCardPanel = new Panel();
        browseButton = new Button();
        runOcrCheckbox = new CheckBox();
        hotkeyLabel = new Label();
        saveFolderTextBox = new TextBox();
        settingsSaveLocationLabel = new Label();
        saveImageCheckbox = new CheckBox();
        settingsHotkeyHeaderLabel = new Label();
        settingsHeaderLabel = new Label();
        btnSaveImagesFolder = new Button();
        startCaptureButton = new Button();
        leftCardPanel = new Panel();
        captureHistoryHeaderLabel = new Label();
        historyPanel = new Panel();
        captureHistoryListView = new ListView();
        captureHistoryImageList = new ImageList(components);
        statusPanel = new Panel();
        statusLabel = new Label();
        statusHeaderLabel = new Label();
        lastCaptureHeaderLabel = new Label();
        lastCapturePanel = new Panel();
        lastCapturePreview = new PictureBox();
        rightCardPanel = new Panel();
        extractedTextHeaderLabel = new Label();
        extractedTextHintLabel = new Label();
        extractTextButton = new Button();
        extractedTextPanel = new Panel();
        extractedTextTextBox = new TextBox();
        settingsCardPanel.SuspendLayout();
        leftCardPanel.SuspendLayout();
        historyPanel.SuspendLayout();
        statusPanel.SuspendLayout();
        lastCapturePanel.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)lastCapturePreview).BeginInit();
        rightCardPanel.SuspendLayout();
        extractedTextPanel.SuspendLayout();
        SuspendLayout();
        // 
        // titleLabel
        // 
        titleLabel.AutoSize = true;
        titleLabel.Font = new Font("Segoe UI Semibold", 25F, FontStyle.Bold);
        titleLabel.Location = new Point(24, 15);
        titleLabel.Name = "titleLabel";
        titleLabel.Size = new Size(251, 46);
        titleLabel.TabIndex = 0;
        titleLabel.Text = "ScreenClipOCR";
        // 
        // subtitleLabel
        // 
        subtitleLabel.AutoSize = true;
        subtitleLabel.Location = new Point(281, 30);
        subtitleLabel.MaximumSize = new Size(900, 0);
        subtitleLabel.Name = "subtitleLabel";
        subtitleLabel.Size = new Size(541, 15);
        subtitleLabel.TabIndex = 1;
        subtitleLabel.Text = "Desktop capture, local OCR extraction, and clipboard-first workflows in one compact Windows utility.";
        // 
        // settingsCardPanel
        // 
        settingsCardPanel.BorderStyle = BorderStyle.FixedSingle;
        settingsCardPanel.Controls.Add(browseButton);
        settingsCardPanel.Controls.Add(runOcrCheckbox);
        settingsCardPanel.Controls.Add(hotkeyLabel);
        settingsCardPanel.Controls.Add(saveFolderTextBox);
        settingsCardPanel.Controls.Add(settingsSaveLocationLabel);
        settingsCardPanel.Controls.Add(saveImageCheckbox);
        settingsCardPanel.Controls.Add(settingsHotkeyHeaderLabel);
        settingsCardPanel.Controls.Add(settingsHeaderLabel);
        settingsCardPanel.Location = new Point(24, 73);
        settingsCardPanel.Name = "settingsCardPanel";
        settingsCardPanel.Size = new Size(862, 73);
        settingsCardPanel.TabIndex = 2;
        // 
        // browseButton
        // 
        browseButton.Location = new Point(528, 28);
        browseButton.Name = "browseButton";
        browseButton.Size = new Size(70, 25);
        browseButton.TabIndex = 2;
        browseButton.Text = "Browse";
        // 
        // runOcrCheckbox
        // 
        runOcrCheckbox.AutoSize = true;
        runOcrCheckbox.Location = new Point(169, 4);
        runOcrCheckbox.Name = "runOcrCheckbox";
        runOcrCheckbox.Size = new Size(266, 19);
        runOcrCheckbox.TabIndex = 2;
        runOcrCheckbox.Text = "Run OCR and copy extracted text to clipboard";
        // 
        // hotkeyLabel
        // 
        hotkeyLabel.Location = new Point(689, 5);
        hotkeyLabel.Name = "hotkeyLabel";
        hotkeyLabel.Size = new Size(172, 66);
        hotkeyLabel.TabIndex = 1;
        hotkeyLabel.Text = "hotkey";
        hotkeyLabel.TextAlign = ContentAlignment.MiddleLeft;
        // 
        // saveFolderTextBox
        // 
        saveFolderTextBox.Location = new Point(169, 31);
        saveFolderTextBox.Name = "saveFolderTextBox";
        saveFolderTextBox.Size = new Size(353, 23);
        saveFolderTextBox.TabIndex = 1;
        // 
        // settingsSaveLocationLabel
        // 
        settingsSaveLocationLabel.AutoSize = true;
        settingsSaveLocationLabel.Font = new Font("Segoe UI Semibold", 10F, FontStyle.Bold);
        settingsSaveLocationLabel.Location = new Point(3, 31);
        settingsSaveLocationLabel.Name = "settingsSaveLocationLabel";
        settingsSaveLocationLabel.Size = new Size(96, 19);
        settingsSaveLocationLabel.TabIndex = 0;
        settingsSaveLocationLabel.Text = "Save Location";
        // 
        // saveImageCheckbox
        // 
        saveImageCheckbox.AutoSize = true;
        saveImageCheckbox.Location = new Point(462, 4);
        saveImageCheckbox.Name = "saveImageCheckbox";
        saveImageCheckbox.Size = new Size(136, 19);
        saveImageCheckbox.TabIndex = 1;
        saveImageCheckbox.Text = "Save captured image";
        // 
        // settingsHotkeyHeaderLabel
        // 
        settingsHotkeyHeaderLabel.AutoSize = true;
        settingsHotkeyHeaderLabel.Font = new Font("Segoe UI Semibold", 10F, FontStyle.Bold);
        settingsHotkeyHeaderLabel.Location = new Point(617, 4);
        settingsHotkeyHeaderLabel.Name = "settingsHotkeyHeaderLabel";
        settingsHotkeyHeaderLabel.Size = new Size(53, 19);
        settingsHotkeyHeaderLabel.TabIndex = 0;
        settingsHotkeyHeaderLabel.Text = "Hotkey";
        // 
        // settingsHeaderLabel
        // 
        settingsHeaderLabel.AutoSize = true;
        settingsHeaderLabel.Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold);
        settingsHeaderLabel.Location = new Point(3, 0);
        settingsHeaderLabel.Name = "settingsHeaderLabel";
        settingsHeaderLabel.Size = new Size(143, 21);
        settingsHeaderLabel.TabIndex = 0;
        settingsHeaderLabel.Text = "Options / Settings";
        // 
        // btnSaveImagesFolder
        // 
        btnSaveImagesFolder.Location = new Point(18, 547);
        btnSaveImagesFolder.Name = "btnSaveImagesFolder";
        btnSaveImagesFolder.Size = new Size(144, 29);
        btnSaveImagesFolder.TabIndex = 3;
        btnSaveImagesFolder.Text = "SAVE ALL";
        // 
        // startCaptureButton
        // 
        startCaptureButton.Location = new Point(892, 73);
        startCaptureButton.Name = "startCaptureButton";
        startCaptureButton.Size = new Size(114, 73);
        startCaptureButton.TabIndex = 0;
        startCaptureButton.Text = "Start Capture";
        // 
        // leftCardPanel
        // 
        leftCardPanel.BorderStyle = BorderStyle.FixedSingle;
        leftCardPanel.Controls.Add(btnSaveImagesFolder);
        leftCardPanel.Controls.Add(captureHistoryHeaderLabel);
        leftCardPanel.Controls.Add(historyPanel);
        leftCardPanel.Location = new Point(24, 156);
        leftCardPanel.Name = "leftCardPanel";
        leftCardPanel.Size = new Size(183, 585);
        leftCardPanel.TabIndex = 3;
        // 
        // captureHistoryHeaderLabel
        // 
        captureHistoryHeaderLabel.AutoSize = true;
        captureHistoryHeaderLabel.Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold);
        captureHistoryHeaderLabel.Location = new Point(18, 12);
        captureHistoryHeaderLabel.Name = "captureHistoryHeaderLabel";
        captureHistoryHeaderLabel.Size = new Size(126, 21);
        captureHistoryHeaderLabel.TabIndex = 3;
        captureHistoryHeaderLabel.Text = "Capture History";
        // 
        // historyPanel
        // 
        historyPanel.BorderStyle = BorderStyle.FixedSingle;
        historyPanel.Controls.Add(captureHistoryListView);
        historyPanel.Location = new Point(18, 58);
        historyPanel.Name = "historyPanel";
        historyPanel.Size = new Size(145, 470);
        historyPanel.TabIndex = 4;
        // 
        // captureHistoryListView
        // 
        captureHistoryListView.BorderStyle = BorderStyle.None;
        captureHistoryListView.Dock = DockStyle.Fill;
        captureHistoryListView.LargeImageList = captureHistoryImageList;
        captureHistoryListView.Location = new Point(0, 0);
        captureHistoryListView.MultiSelect = false;
        captureHistoryListView.Name = "captureHistoryListView";
        captureHistoryListView.Size = new Size(143, 468);
        captureHistoryListView.TabIndex = 0;
        captureHistoryListView.UseCompatibleStateImageBehavior = false;
        // 
        // captureHistoryImageList
        // 
        captureHistoryImageList.ColorDepth = ColorDepth.Depth32Bit;
        captureHistoryImageList.ImageSize = new Size(72, 72);
        captureHistoryImageList.TransparentColor = Color.Transparent;
        // 
        // statusPanel
        // 
        statusPanel.BorderStyle = BorderStyle.FixedSingle;
        statusPanel.Controls.Add(statusLabel);
        statusPanel.Location = new Point(371, 551);
        statusPanel.Name = "statusPanel";
        statusPanel.Size = new Size(543, 26);
        statusPanel.TabIndex = 6;
        // 
        // statusLabel
        // 
        statusLabel.Dock = DockStyle.Fill;
        statusLabel.Location = new Point(0, 0);
        statusLabel.Name = "statusLabel";
        statusLabel.Size = new Size(541, 24);
        statusLabel.TabIndex = 0;
        statusLabel.Text = "status";
        // 
        // statusHeaderLabel
        // 
        statusHeaderLabel.Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold);
        statusHeaderLabel.Location = new Point(14, 552);
        statusHeaderLabel.Name = "statusHeaderLabel";
        statusHeaderLabel.Size = new Size(337, 21);
        statusHeaderLabel.TabIndex = 5;
        statusHeaderLabel.Text = "Status";
        // 
        // lastCaptureHeaderLabel
        // 
        lastCaptureHeaderLabel.AutoSize = true;
        lastCaptureHeaderLabel.Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold);
        lastCaptureHeaderLabel.Location = new Point(905, 24);
        lastCaptureHeaderLabel.Name = "lastCaptureHeaderLabel";
        lastCaptureHeaderLabel.Size = new Size(101, 21);
        lastCaptureHeaderLabel.TabIndex = 0;
        lastCaptureHeaderLabel.Text = "Last Capture";
        // 
        // lastCapturePanel
        // 
        lastCapturePanel.BorderStyle = BorderStyle.FixedSingle;
        lastCapturePanel.Controls.Add(lastCapturePreview);
        lastCapturePanel.Location = new Point(1012, 24);
        lastCapturePanel.Name = "lastCapturePanel";
        lastCapturePanel.Size = new Size(145, 123);
        lastCapturePanel.TabIndex = 1;
        // 
        // lastCapturePreview
        // 
        lastCapturePreview.Dock = DockStyle.Fill;
        lastCapturePreview.Location = new Point(0, 0);
        lastCapturePreview.Name = "lastCapturePreview";
        lastCapturePreview.Size = new Size(143, 121);
        lastCapturePreview.SizeMode = PictureBoxSizeMode.Zoom;
        lastCapturePreview.TabIndex = 0;
        lastCapturePreview.TabStop = false;
        // 
        // rightCardPanel
        // 
        rightCardPanel.BorderStyle = BorderStyle.FixedSingle;
        rightCardPanel.Controls.Add(extractedTextHeaderLabel);
        rightCardPanel.Controls.Add(extractedTextHintLabel);
        rightCardPanel.Controls.Add(extractTextButton);
        rightCardPanel.Controls.Add(statusHeaderLabel);
        rightCardPanel.Controls.Add(statusPanel);
        rightCardPanel.Controls.Add(extractedTextPanel);
        rightCardPanel.Location = new Point(225, 156);
        rightCardPanel.Name = "rightCardPanel";
        rightCardPanel.Size = new Size(932, 585);
        rightCardPanel.TabIndex = 4;
        // 
        // extractedTextHeaderLabel
        // 
        extractedTextHeaderLabel.AutoSize = true;
        extractedTextHeaderLabel.Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold);
        extractedTextHeaderLabel.Location = new Point(3, 13);
        extractedTextHeaderLabel.Name = "extractedTextHeaderLabel";
        extractedTextHeaderLabel.Size = new Size(113, 21);
        extractedTextHeaderLabel.TabIndex = 4;
        extractedTextHeaderLabel.Text = "Extracted Text";
        // 
        // extractedTextHintLabel
        // 
        extractedTextHintLabel.AutoSize = true;
        extractedTextHintLabel.Location = new Point(151, 18);
        extractedTextHintLabel.MaximumSize = new Size(730, 0);
        extractedTextHintLabel.Name = "extractedTextHintLabel";
        extractedTextHintLabel.Size = new Size(509, 15);
        extractedTextHintLabel.TabIndex = 5;
        extractedTextHintLabel.Text = "Single-click a capture to view its extracted text. Double-click a thumbnail to view the full image.";
        // 
        // extractTextButton
        // 
        extractTextButton.Location = new Point(798, 13);
        extractTextButton.Name = "extractTextButton";
        extractTextButton.Size = new Size(117, 39);
        extractTextButton.TabIndex = 3;
        extractTextButton.Text = "Extract Text";
        // 
        // extractedTextPanel
        // 
        extractedTextPanel.BorderStyle = BorderStyle.FixedSingle;
        extractedTextPanel.Controls.Add(extractedTextTextBox);
        extractedTextPanel.Location = new Point(13, 58);
        extractedTextPanel.Name = "extractedTextPanel";
        extractedTextPanel.Size = new Size(902, 470);
        extractedTextPanel.TabIndex = 6;
        // 
        // extractedTextTextBox
        // 
        extractedTextTextBox.BorderStyle = BorderStyle.None;
        extractedTextTextBox.Dock = DockStyle.Fill;
        extractedTextTextBox.Location = new Point(0, 0);
        extractedTextTextBox.Multiline = true;
        extractedTextTextBox.Name = "extractedTextTextBox";
        extractedTextTextBox.ScrollBars = ScrollBars.Vertical;
        extractedTextTextBox.Size = new Size(900, 468);
        extractedTextTextBox.TabIndex = 0;
        // 
        // MainForm
        // 
        AutoScaleDimensions = new SizeF(7F, 15F);
        AutoScaleMode = AutoScaleMode.Font;
        ClientSize = new Size(1184, 761);
        Controls.Add(lastCapturePanel);
        Controls.Add(lastCaptureHeaderLabel);
        Controls.Add(startCaptureButton);
        Controls.Add(rightCardPanel);
        Controls.Add(leftCardPanel);
        Controls.Add(settingsCardPanel);
        Controls.Add(subtitleLabel);
        Controls.Add(titleLabel);
        Name = "MainForm";
        Padding = new Padding(24);
        StartPosition = FormStartPosition.CenterScreen;
        Text = "ScreenClipOCR";
        settingsCardPanel.ResumeLayout(false);
        settingsCardPanel.PerformLayout();
        leftCardPanel.ResumeLayout(false);
        leftCardPanel.PerformLayout();
        historyPanel.ResumeLayout(false);
        statusPanel.ResumeLayout(false);
        lastCapturePanel.ResumeLayout(false);
        ((System.ComponentModel.ISupportInitialize)lastCapturePreview).EndInit();
        rightCardPanel.ResumeLayout(false);
        rightCardPanel.PerformLayout();
        extractedTextPanel.ResumeLayout(false);
        extractedTextPanel.PerformLayout();
        ResumeLayout(false);
        PerformLayout();
    }

    private Button btnSaveImagesFolder;
}
