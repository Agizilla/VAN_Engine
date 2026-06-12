using System;
using System.Drawing;
using System.Windows.Forms;

namespace GechoShift.AudioPlayer
{
    // ════════════════════════════════════════════════════════════════════
    // FrmConfigStudio
    //
    //   WinForms layout mirror of ConfigStudio.html.
    //   NO LOGIC — controls are named and positioned for designer editing.
    //
    //   Structure (matches HTML exactly):
    //     pnlHeader           — top bar with logo label + status badge
    //     tabMain             — 5 tabs matching the HTML tabbar:
    //       tabProfiles         Profile Viewer
    //       tabDelta            Delta Composer
    //       tabAdapter          Adapter Builder
    //       tabEq               EQ Presets
    //       tabModels           Model Registry
    //       tabExport           Training Export
    //
    //   Each tab contains:
    //     • A left sidebar panel (pnlSidebar*) where it exists
    //     • A right workspace panel (pnlWork*)
    //     • All named controls for designer access
    //
    //   Colour palette: VmpTheme.CS_* (graphite / copper / cyan)
    // ════════════════════════════════════════════════════════════════════
    public class FrmConfigStudio : Form
    {
        // ── Header ─────────────────────────────────────────────────────
        public Panel    pnlHeader          = null!;
        public Label    lblLogo            = null!;
        public Label    lblDataDir         = null!;
        public Label    lblHostBadge       = null!;

        // ── Tab control ────────────────────────────────────────────────
        public TabControl tabMain          = null!;
        public TabPage    tabProfiles      = null!;
        public TabPage    tabDelta         = null!;
        public TabPage    tabAdapter       = null!;
        public TabPage    tabEq            = null!;
        public TabPage    tabModels        = null!;
        public TabPage    tabExport        = null!;

        // ── Shared sidebar (left panel inside tabMain area) ────────────
        public Panel    pnlSidebar         = null!;
        public Label    lblSidebarHead     = null!;
        public ListBox  lstFiles           = null!;
        public Button   btnLoadFolder      = null!;
        public Button   btnPasteJson       = null!;
        public Button   btnClearAll        = null!;

        // ── Tab: Profile Viewer ────────────────────────────────────────
        public Panel    pnlWorkProfiles    = null!;
        public Label    lblProfileName     = null!;
        // Stat cards row
        public Panel    pnlProfileStats    = null!;
        public Panel    cardNoise          = null!;
        public Label    lblNoiseVal        = null!;
        public Label    lblNoiseCaption    = null!;
        public Panel    cardLength         = null!;
        public Label    lblLengthVal       = null!;
        public Label    lblLengthCaption   = null!;
        public Panel    cardPhonemes       = null!;
        public Label    lblPhonemeCount    = null!;
        public Label    lblPhonemeCaption  = null!;
        public Panel    cardTopKeys        = null!;
        public Label    lblTopKeysVal      = null!;
        public Label    lblTopKeysCaption  = null!;
        // Inference params grid
        public Label    lblInferenceHead   = null!;
        public DataGridView dgvInference   = null!;
        // Phoneme map table
        public Label    lblPhonemeHead     = null!;
        public DataGridView dgvPhonemes    = null!;
        // Actions
        public Button   btnQuickDelta      = null!;
        public Button   btnCopyRaw         = null!;

        // ── Tab: Delta Composer ────────────────────────────────────────
        public Panel    pnlWorkDelta       = null!;
        public Label    lblDeltaDesc       = null!;
        // Profile selectors
        public Label    lblDeltaBaseLabel  = null!;
        public ComboBox cboDeltaBase       = null!;
        public Label    lblDeltaArtistLabel= null!;
        public ComboBox cboDeltaArtist     = null!;
        // Diff grid header
        public Panel    pnlDiffHeader      = null!;
        public Label    lblDiffField       = null!;
        public Label    lblDiffBase        = null!;
        public Label    lblDiffArtist      = null!;
        public Label    lblDiffDelta       = null!;
        // Diff rows
        public DataGridView dgvDeltaDiff   = null!;
        // Phoneme delta
        public Label    lblPhonemeDeltaHead= null!;
        public Label    lblPhonemeDeltaCount= null!;
        public DataGridView dgvPhonemesDelta= null!;
        // Output preview
        public Label    lblDeltaJsonHead   = null!;
        public RichTextBox rtbDeltaJson    = null!;
        public Button   btnSaveDelta       = null!;
        public Button   btnCopyDeltaJson   = null!;

        // ── Tab: Adapter Builder ───────────────────────────────────────
        public Panel    pnlWorkAdapter     = null!;
        public Label    lblAdapterDesc     = null!;
        // Knob cards — 4 panels
        public Panel    cardPitch          = null!;
        public Label    lblPitchCaption    = null!;
        public Label    lblPitchVal        = null!;
        public TrackBar trkPitch           = null!;
        public Panel    cardFormant        = null!;
        public Label    lblFormantCaption  = null!;
        public Label    lblFormantVal      = null!;
        public TrackBar trkFormant         = null!;
        public Panel    cardGrit           = null!;
        public Label    lblGritCaption     = null!;
        public Label    lblGritVal         = null!;
        public TrackBar trkGrit            = null!;
        public Panel    cardBreath         = null!;
        public Label    lblBreathCaption   = null!;
        public Label    lblBreathVal       = null!;
        public TrackBar trkBreath          = null!;
        // Gender + play count
        public Label    lblGenderLabel     = null!;
        public ComboBox cboGender          = null!;
        public Label    lblPlayCountLabel  = null!;
        public NumericUpDown nudPlayCount  = null!;
        // LoRA delta section
        public Label    lblLoraHead        = null!;
        public CheckBox chkHasDelta        = null!;
        public Label    lblDeltaHint       = null!;
        public TextBox  txtDeltaInput      = null!;
        // Binary info grid
        public Label    lblBinaryHead      = null!;
        public DataGridView dgvBinaryInfo  = null!;
        public Button   btnBuildAdapter    = null!;
        public Button   btnParseAdapter    = null!;
        public Label    lblParseB64Label   = null!;
        public TextBox  txtAdapterParseInput = null!;
        public RichTextBox rtbAdapterParsed= null!;

        // ── Tab: EQ Presets ────────────────────────────────────────────
        public Panel    pnlWorkEq          = null!;
        public Label    lblEqDesc          = null!;
        // Preset buttons
        public Button   btnEqFlat          = null!;
        public Button   btnEqVocalBoost    = null!;
        public Button   btnEqBassBoost     = null!;
        public Button   btnEqPresence      = null!;
        public Button   btnEqKaraoke       = null!;
        // 5 band panels
        public Panel    pnlEqBands         = null!;
        public Panel[]  pnlEqBand          = null!;   // [5]
        public Label[]  lblEqBandName      = null!;   // [5]
        public Label[]  lblEqBandHz        = null!;   // [5]
        public TrackBar[] trkEqGain        = null!;   // [5]
        public Label[]  lblEqGainVal       = null!;   // [5]
        // Advanced Q / freq
        public Label    lblEqAdvHead       = null!;
        public DataGridView dgvEqAdvanced  = null!;
        // Output
        public Label    lblEqPayloadHead   = null!;
        public DataGridView dgvEqPayload   = null!;
        public Button   btnBuildEq         = null!;
        public Button   btnParseEq         = null!;
        public TextBox  txtEqParseInput    = null!;
        public RichTextBox rtbEqParsed     = null!;

        // ── Tab: Model Registry ────────────────────────────────────────
        public Panel    pnlWorkModels      = null!;
        public Label    lblModelsDesc      = null!;
        public Panel    pnlModelList       = null!;
        // 5 model rows
        public Panel[]  pnlModelRow        = null!;   // [5]
        public Panel[]  pnlModelDot        = null!;   // [5] — coloured dot
        public Label[]  lblModelName       = null!;   // [5]
        public Label[]  lblModelFile       = null!;   // [5]
        public Label[]  lblModelDesc       = null!;   // [5]
        public Label[]  lblModelBadge      = null!;   // [5]
        // Export instructions
        public Label    lblExportCmdHead   = null!;
        public RichTextBox rtbExportCmd    = null!;

        // ── Tab: Training Export ───────────────────────────────────────
        public Panel    pnlWorkExport      = null!;
        public Label    lblExportDesc      = null!;
        public Label    lblExportDeltaLbl  = null!;
        public ComboBox cboExportDelta     = null!;
        public Label    lblExportAdapterLbl= null!;
        public TextBox  txtExportAdapterB64= null!;
        public Label    lblExportVcLbl     = null!;
        public TextBox  txtExportVcBundle  = null!;
        public Label    lblExportJobLbl    = null!;
        public TextBox  txtExportJobName   = null!;
        public Label    lblExportNotesLbl  = null!;
        public TextBox  txtExportNotes     = null!;
        public Button   btnBuildTraining   = null!;
        public Button   btnPreviewTraining = null!;
        // Preview section
        public Label    lblExportPreviewHead = null!;
        public RichTextBox rtbExportPreview= null!;
        public Button   btnSaveTraining    = null!;
        public Button   btnCopyTraining    = null!;

        // ══════════════════════════════════════════════════════════════
        public FrmConfigStudio()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            SuspendLayout();

            // ── Form ──────────────────────────────────────────────────
            Text            = "VoiceMorphPlayer — Config Studio";
            Size            = new Size(1280, 820);
            MinimumSize     = new Size(1000, 640);
            BackColor       = VmpTheme.CS_Bg0;
            ForeColor       = VmpTheme.CS_Text;
            Font            = VmpTheme.FontSans10;
            StartPosition   = FormStartPosition.CenterScreen;

            // ── Header panel ──────────────────────────────────────────
            pnlHeader = new Panel
            {
                Name      = nameof(pnlHeader),
                Dock      = DockStyle.Top,
                Height    = 44,
                BackColor = VmpTheme.CS_Bg1,
                Padding   = new Padding(16, 0, 16, 0),
            };
            pnlHeader.Paint += (s, e) =>
            {
                using var pen = new Pen(VmpTheme.CS_Border);
                e.Graphics.DrawLine(pen, 0, pnlHeader.Height - 1, pnlHeader.Width, pnlHeader.Height - 1);
            };

            lblLogo = new Label
            {
                Name      = nameof(lblLogo),
                Text      = "● CONFIG STUDIO",
                ForeColor = VmpTheme.CS_Copper,
                BackColor = Color.Transparent,
                Font      = new Font("Consolas", 9.5f, FontStyle.Bold),
                AutoSize  = true,
                Location  = new Point(16, 12),
            };

            lblDataDir = new Label
            {
                Name      = nameof(lblDataDir),
                Text      = "%AppData%\\VoiceMorphPlayer\\voice_deltas",
                ForeColor = VmpTheme.CS_Muted,
                BackColor = Color.Transparent,
                Font      = VmpTheme.FontMono9,
                AutoSize  = true,
            };

            lblHostBadge = new Label
            {
                Name      = nameof(lblHostBadge),
                Text      = "STANDALONE",
                ForeColor = VmpTheme.CS_Amber,
                BackColor = VmpTheme.CS_Bg3,
                Font      = new Font("Consolas", 7.5f, FontStyle.Bold),
                AutoSize  = true,
                Padding   = new Padding(6, 3, 6, 3),
                BorderStyle = BorderStyle.FixedSingle,
            };

            pnlHeader.Controls.AddRange(new Control[] { lblLogo, lblDataDir, lblHostBadge });
            pnlHeader.Layout += (s, e) =>
            {
                lblLogo.Location    = new Point(16, (pnlHeader.Height - lblLogo.Height) / 2);
                lblHostBadge.Location = new Point(pnlHeader.Width - lblHostBadge.Width - 16,
                                                   (pnlHeader.Height - lblHostBadge.Height) / 2);
                lblDataDir.Location = new Point(lblHostBadge.Left - lblDataDir.Width - 12,
                                                 (pnlHeader.Height - lblDataDir.Height) / 2);
            };

            // ── Outer container (sidebar + tab) ───────────────────────
            var pnlOuter = new Panel
            {
                Dock      = DockStyle.Fill,
                BackColor = VmpTheme.CS_Bg0,
            };

            // ── Sidebar ───────────────────────────────────────────────
            pnlSidebar = new Panel
            {
                Name      = nameof(pnlSidebar),
                Dock      = DockStyle.Left,
                Width     = 240,
                BackColor = VmpTheme.CS_Bg1,
            };
            pnlSidebar.Paint += (s, e) =>
            {
                using var pen = new Pen(VmpTheme.CS_Border);
                e.Graphics.DrawLine(pen, pnlSidebar.Width - 1, 0, pnlSidebar.Width - 1, pnlSidebar.Height);
            };

            lblSidebarHead = new Label
            {
                Name      = nameof(lblSidebarHead),
                Text      = "LOADED FILES",
                ForeColor = VmpTheme.CS_Muted,
                BackColor = VmpTheme.CS_Bg1,
                Font      = new Font("Consolas", 7.5f, FontStyle.Bold),
                Dock      = DockStyle.Top,
                Height    = 32,
                Padding   = new Padding(14, 10, 0, 0),
            };

            lstFiles = new ListBox
            {
                Name            = nameof(lstFiles),
                BackColor       = VmpTheme.CS_Bg1,
                ForeColor       = VmpTheme.CS_Text,
                Font            = VmpTheme.FontMono10,
                BorderStyle     = BorderStyle.None,
                Dock            = DockStyle.Fill,
                DrawMode        = DrawMode.OwnerDrawFixed,
                ItemHeight      = 28,
                IntegralHeight  = false,
            };
            // Sample items for designer visibility
            lstFiles.Items.AddRange(new object[]
            {
                "● en_US-amy-medium.onnx.json",
                "● artist-voice.onnx.json",
                "◆ amy_to_artist.json",
            });

            var pnlSidebarBtns = new Panel
            {
                Name      = "pnlSidebarBtns",
                Dock      = DockStyle.Bottom,
                Height    = 114,
                BackColor = VmpTheme.CS_Bg1,
                Padding   = new Padding(10, 8, 10, 8),
            };
            pnlSidebarBtns.Paint += (s, e) =>
            {
                using var pen = new Pen(VmpTheme.CS_Border);
                e.Graphics.DrawLine(pen, 0, 0, pnlSidebarBtns.Width, 0);
            };

            btnLoadFolder = VmpTheme.MakeButton("▶  Load Folder", VmpTheme.CS_Copper, VmpTheme.CS_Bg3, VmpTheme.CS_Copper);
            btnLoadFolder.Name = nameof(btnLoadFolder); btnLoadFolder.Dock = DockStyle.Top; btnLoadFolder.Height = 30; btnLoadFolder.Margin = new Padding(0, 0, 0, 6);

            btnPasteJson = VmpTheme.MakeButton("⊕  Paste JSON", VmpTheme.CS_Text, VmpTheme.CS_Bg3, VmpTheme.CS_Border2);
            btnPasteJson.Name = nameof(btnPasteJson); btnPasteJson.Dock = DockStyle.Top; btnPasteJson.Height = 30; btnPasteJson.Margin = new Padding(0, 0, 0, 6);

            btnClearAll = VmpTheme.MakeButton("✕  Clear All", VmpTheme.CS_Red, VmpTheme.CS_Bg3, VmpTheme.CS_Red);
            btnClearAll.Name = nameof(btnClearAll); btnClearAll.Dock = DockStyle.Top; btnClearAll.Height = 30;

            pnlSidebarBtns.Controls.AddRange(new Control[] { btnClearAll, btnPasteJson, btnLoadFolder });
            pnlSidebar.Controls.AddRange(new Control[] { pnlSidebarBtns, lstFiles, lblSidebarHead });

            // ── Tab control ───────────────────────────────────────────
            tabMain = new TabControl
            {
                Name      = nameof(tabMain),
                Dock      = DockStyle.Fill,
                Font      = new Font("Consolas", 8.5f, FontStyle.Bold),
                DrawMode  = TabDrawMode.OwnerDrawFixed,
                ItemSize  = new Size(120, 34),
                SizeMode  = TabSizeMode.Fixed,
                Appearance = TabAppearance.FlatButtons,
                BackColor = VmpTheme.CS_Bg0,
            };

            // ── Tab pages ─────────────────────────────────────────────
            tabProfiles = MakeTabPage("PROFILE VIEWER",  nameof(tabProfiles));
            tabDelta    = MakeTabPage("DELTA COMPOSER",  nameof(tabDelta));
            tabAdapter  = MakeTabPage("ADAPTER BUILDER", nameof(tabAdapter));
            tabEq       = MakeTabPage("EQ PRESETS",      nameof(tabEq));
            tabModels   = MakeTabPage("MODEL REGISTRY",  nameof(tabModels));
            tabExport   = MakeTabPage("TRAINING EXPORT", nameof(tabExport));

            tabMain.TabPages.AddRange(new[] { tabProfiles, tabDelta, tabAdapter, tabEq, tabModels, tabExport });

            // ── Build each tab content ─────────────────────────────────
            BuildTabProfiles();
            BuildTabDelta();
            BuildTabAdapter();
            BuildTabEq();
            BuildTabModels();
            BuildTabExport();

            pnlOuter.Controls.Add(tabMain);
            pnlOuter.Controls.Add(pnlSidebar);

            Controls.Add(pnlOuter);
            Controls.Add(pnlHeader);

            ResumeLayout(false);
            PerformLayout();
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: PROFILE VIEWER
        // ══════════════════════════════════════════════════════════════
        private void BuildTabProfiles()
        {
            pnlWorkProfiles = MakeWorkPanel(nameof(pnlWorkProfiles));

            lblProfileName = SectionTitle("en_US-amy-medium.onnx.json");
            lblProfileName.Name = nameof(lblProfileName);

            // Stat cards
            pnlProfileStats = new Panel { Name = nameof(pnlProfileStats), Height = 64, Dock = DockStyle.Top, BackColor = Color.Transparent, Padding = new Padding(0, 0, 0, 10) };
            (cardNoise,    lblNoiseVal,   lblNoiseCaption)   = MakeStatCard("1.000",  "noise_scale");
            (cardLength,   lblLengthVal,  lblLengthCaption)  = MakeStatCard("1.000",  "length_scale");
            (cardPhonemes, lblPhonemeCount, lblPhonemeCaption) = MakeStatCard("256",  "phoneme entries");
            (cardTopKeys,  lblTopKeysVal, lblTopKeysCaption) = MakeStatCard("12",    "top-level keys");
            cardNoise.Name = nameof(cardNoise); cardLength.Name = nameof(cardLength);
            cardPhonemes.Name = nameof(cardPhonemes); cardTopKeys.Name = nameof(cardTopKeys);
            LayoutStatCards(pnlProfileStats, cardNoise, cardLength, cardPhonemes, cardTopKeys);

            lblInferenceHead = SectionTitle("Inference parameters");
            lblInferenceHead.Name = nameof(lblInferenceHead);

            dgvInference = MakeDarkGrid(nameof(dgvInference), 120);
            dgvInference.Columns.Add("Key", "FIELD");
            dgvInference.Columns.Add("Value", "VALUE");
            dgvInference.Columns[0].Width = 180;
            dgvInference.Columns[1].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill;
            dgvInference.Rows.Add("noise_scale",  "1.0000");
            dgvInference.Rows.Add("length_scale", "1.0000");
            dgvInference.Rows.Add("model_type",   "\"vits\"");

            lblPhonemeHead = SectionTitle("phoneme_id_map (256 entries)");
            lblPhonemeHead.Name = nameof(lblPhonemeHead);

            dgvPhonemes = MakeDarkGrid(nameof(dgvPhonemes), 140);
            dgvPhonemes.Columns.Add("Id",  "PHONEME ID");
            dgvPhonemes.Columns.Add("Val", "TOKEN ID");
            dgvPhonemes.Columns[0].Width = 120;
            dgvPhonemes.Columns[1].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill;
            for (int i = 0; i < 6; i++) dgvPhonemes.Rows.Add(i.ToString(), (i + 1).ToString());

            var pnlBtns = MakeButtonRow();
            btnQuickDelta = VmpTheme.MakeButton("⊕  Create Delta (Amy baseline)", VmpTheme.CS_Bg0, VmpTheme.CS_Copper, VmpTheme.CS_Copper);
            btnQuickDelta.Name = nameof(btnQuickDelta); btnQuickDelta.Width = 240; btnQuickDelta.Dock = DockStyle.Left;
            btnCopyRaw = VmpTheme.MakeButton("⊡  Copy raw JSON", VmpTheme.CS_Text, VmpTheme.CS_Bg3, VmpTheme.CS_Border2);
            btnCopyRaw.Name = nameof(btnCopyRaw); btnCopyRaw.Width = 150; btnCopyRaw.Dock = DockStyle.Left;
            pnlBtns.Controls.AddRange(new Control[] { btnCopyRaw, btnQuickDelta });

            AddToWorkPanel(pnlWorkProfiles, lblProfileName, pnlProfileStats,
                lblInferenceHead, dgvInference, lblPhonemeHead, dgvPhonemes, pnlBtns);
            tabProfiles.Controls.Add(pnlWorkProfiles);
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: DELTA COMPOSER
        // ══════════════════════════════════════════════════════════════
        private void BuildTabDelta()
        {
            pnlWorkDelta = MakeWorkPanel(nameof(pnlWorkDelta));

            var headLabel = SectionTitle("Delta Composer — VoiceDeltaFactory.Create()");

            lblDeltaDesc = new Label
            {
                Name      = nameof(lblDeltaDesc),
                Text      = "Select a base profile (Amy baseline) and an artist profile.\n" +
                            "Computes noise_scale diff, length_scale diff, and differing phoneme_id_map entries.",
                ForeColor = VmpTheme.CS_Dim,
                BackColor = Color.Transparent,
                Font      = VmpTheme.FontSans9,
                AutoSize  = false,
                Height    = 38,
                Dock      = DockStyle.Top,
            };

            // Profile selector row
            var pnlSelectors = new Panel { Height = 70, Dock = DockStyle.Top, BackColor = Color.Transparent, Padding = new Padding(0, 4, 0, 8) };

            lblDeltaBaseLabel = FieldLabel("BASE PROFILE  [baseline]");
            lblDeltaBaseLabel.Name = nameof(lblDeltaBaseLabel); lblDeltaBaseLabel.ForeColor = VmpTheme.CS_Copper;
            cboDeltaBase = VmpTheme.MakeComboBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text);
            cboDeltaBase.Name = nameof(cboDeltaBase); cboDeltaBase.Items.AddRange(new object[] { "en_US-amy-medium.onnx.json", "en_GB-alan-low.onnx.json" });

            lblDeltaArtistLabel = FieldLabel("ARTIST PROFILE  [artist]");
            lblDeltaArtistLabel.Name = nameof(lblDeltaArtistLabel); lblDeltaArtistLabel.ForeColor = VmpTheme.CS_Cyan;
            cboDeltaArtist = VmpTheme.MakeComboBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text);
            cboDeltaArtist.Name = nameof(cboDeltaArtist); cboDeltaArtist.Items.Add("artist-voice.onnx.json");

            var pnlLeft  = new Panel { Dock = DockStyle.Left, Width = 300, BackColor = Color.Transparent };
            var pnlRight = new Panel { Dock = DockStyle.Fill,              BackColor = Color.Transparent };
            pnlLeft.Controls.AddRange(new Control[]  { cboDeltaBase,   lblDeltaBaseLabel });
            pnlRight.Controls.AddRange(new Control[] { cboDeltaArtist, lblDeltaArtistLabel });
            pnlSelectors.Controls.AddRange(new Control[] { pnlRight, pnlLeft });

            // Diff grid
            var diffHead = SectionTitle("Computed residuals");
            dgvDeltaDiff = MakeDarkGrid(nameof(dgvDeltaDiff), 100);
            dgvDeltaDiff.Columns.Add("Field",  "FIELD");
            dgvDeltaDiff.Columns.Add("Base",   "BASE");
            dgvDeltaDiff.Columns.Add("Artist", "ARTIST");
            dgvDeltaDiff.Columns.Add("Delta",  "Δ DELTA");
            foreach (DataGridViewColumn c in dgvDeltaDiff.Columns) c.Width = 120;
            dgvDeltaDiff.Columns[0].Width = 180;
            dgvDeltaDiff.Rows.Add("noise_scale",  "1.0000", "0.6670", "-0.3330");
            dgvDeltaDiff.Rows.Add("length_scale", "1.0000", "0.8500", "-0.1500");

            // Phoneme delta
            lblPhonemeDeltaHead = SectionTitle("Phoneme map delta");
            lblPhonemeDeltaHead.Name = nameof(lblPhonemeDeltaHead);
            lblPhonemeDeltaCount = new Label { Name = nameof(lblPhonemeDeltaCount), Text = "12 entries differ", ForeColor = VmpTheme.CS_Amber, BackColor = Color.Transparent, Font = VmpTheme.FontMono9, AutoSize = true, Dock = DockStyle.Top };
            dgvPhonemesDelta = MakeDarkGrid(nameof(dgvPhonemesDelta), 110);
            dgvPhonemesDelta.Columns.Add("Id", "PHONEME ID"); dgvPhonemesDelta.Columns.Add("Base", "BASE"); dgvPhonemesDelta.Columns.Add("Artist", "ARTIST"); dgvPhonemesDelta.Columns.Add("Status", "STATUS");
            dgvPhonemesDelta.Rows.Add("3", "4", "7", "changed"); dgvPhonemesDelta.Rows.Add("17", "18", "22", "changed");

            // JSON output
            lblDeltaJsonHead = SectionTitle("Output JSON — voice_delta.json");
            lblDeltaJsonHead.Name = nameof(lblDeltaJsonHead);
            rtbDeltaJson = MakeDarkRtb(nameof(rtbDeltaJson), 130);
            rtbDeltaJson.Text = "{\n  \"BaseProfile\": \"Amy\",\n  \"ArtistProfile\": \"artist-voice\",\n  \"BaseNoiseScale\": 1.0,\n  \"BaseLengthScale\": 1.0,\n  \"ArtistNoiseScale\": 0.667,\n  \"ArtistLengthScale\": 0.85,\n  \"PhonemeMap\": { \"3\": 7 }\n}";

            var pnlBtns = MakeButtonRow();
            btnSaveDelta = VmpTheme.MakeButton("▼  Save voice_delta.json", VmpTheme.CS_Bg0, VmpTheme.CS_Copper, VmpTheme.CS_Copper);
            btnSaveDelta.Name = nameof(btnSaveDelta); btnSaveDelta.Width = 220; btnSaveDelta.Dock = DockStyle.Left;
            btnCopyDeltaJson = VmpTheme.MakeButton("⊡  Copy JSON", VmpTheme.CS_Text, VmpTheme.CS_Bg3, VmpTheme.CS_Border2);
            btnCopyDeltaJson.Name = nameof(btnCopyDeltaJson); btnCopyDeltaJson.Width = 130; btnCopyDeltaJson.Dock = DockStyle.Left;
            pnlBtns.Controls.AddRange(new Control[] { btnCopyDeltaJson, btnSaveDelta });

            AddToWorkPanel(pnlWorkDelta, headLabel, lblDeltaDesc, pnlSelectors,
                diffHead, dgvDeltaDiff, lblPhonemeDeltaHead, lblPhonemeDeltaCount, dgvPhonemesDelta,
                lblDeltaJsonHead, rtbDeltaJson, pnlBtns);
            tabDelta.Controls.Add(pnlWorkDelta);
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: ADAPTER BUILDER
        // ══════════════════════════════════════════════════════════════
        private void BuildTabAdapter()
        {
            pnlWorkAdapter = MakeWorkPanel(nameof(pnlWorkAdapter));

            var headLabel = SectionTitle("VoiceAdapter — DSP Scalar Knobs");

            lblAdapterDesc = new Label
            {
                Name      = nameof(lblAdapterDesc),
                Text      = "Four scalars match AudioEngine.Pitch / .Formant / .Grit / .Breath.\nOutput is Base64 for the X-VOICE-ADAPTER ID3 TXXX tag.",
                ForeColor = VmpTheme.CS_Dim, BackColor = Color.Transparent,
                Font      = VmpTheme.FontSans9, AutoSize = false, Height = 36, Dock = DockStyle.Top,
            };

            // Knob cards
            var pnlKnobs = new Panel { Height = 96, Dock = DockStyle.Top, BackColor = Color.Transparent, Padding = new Padding(0, 0, 0, 8) };
            (cardPitch,   lblPitchCaption,   lblPitchVal,   trkPitch)   = MakeKnobCard("PITCH",   0,   100, 50);
            (cardFormant, lblFormantCaption, lblFormantVal, trkFormant) = MakeKnobCard("FORMANT", 0,   100, 50);
            (cardGrit,    lblGritCaption,    lblGritVal,    trkGrit)    = MakeKnobCard("GRIT",    0,   100, 0);
            (cardBreath,  lblBreathCaption,  lblBreathVal,  trkBreath)  = MakeKnobCard("BREATH",  0,   100, 0);
            cardPitch.Name = nameof(cardPitch); cardFormant.Name = nameof(cardFormant);
            cardGrit.Name  = nameof(cardGrit);  cardBreath.Name  = nameof(cardBreath);
            LayoutKnobCards(pnlKnobs, cardPitch, cardFormant, cardGrit, cardBreath);

            // Gender + play count
            var pnlMeta = new Panel { Height = 52, Dock = DockStyle.Top, BackColor = Color.Transparent, Padding = new Padding(0, 0, 0, 8) };
            lblGenderLabel = FieldLabel("GENDER DETECTED"); lblGenderLabel.Name = nameof(lblGenderLabel);
            cboGender = VmpTheme.MakeComboBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text);
            cboGender.Name = nameof(cboGender); cboGender.Items.AddRange(new object[] { "Unknown", "Male", "Female" }); cboGender.SelectedIndex = 0;
            lblPlayCountLabel = FieldLabel("PLAY COUNT"); lblPlayCountLabel.Name = nameof(lblPlayCountLabel);
            nudPlayCount = new NumericUpDown { Name = nameof(nudPlayCount), BackColor = VmpTheme.CS_Bg2, ForeColor = VmpTheme.CS_Text, Font = VmpTheme.FontMono10, BorderStyle = BorderStyle.FixedSingle, Minimum = 0, Maximum = 9999, Value = 0, Width = 80, Height = 26 };
            var pnlMetaL = new Panel { Dock = DockStyle.Left, Width = 200, BackColor = Color.Transparent };
            var pnlMetaR = new Panel { Dock = DockStyle.Left, Width = 160, BackColor = Color.Transparent, Padding = new Padding(12, 0, 0, 0) };
            pnlMetaL.Controls.AddRange(new Control[] { cboGender, lblGenderLabel });
            pnlMetaR.Controls.AddRange(new Control[] { nudPlayCount, lblPlayCountLabel });
            pnlMeta.Controls.AddRange(new Control[] { pnlMetaL, pnlMetaR });

            // LoRA section
            lblLoraHead = SectionTitle("LoRA Delta (float16 array)");
            lblLoraHead.Name = nameof(lblLoraHead);
            chkHasDelta = new CheckBox { Name = nameof(chkHasDelta), Text = "Include LoRA delta in output", ForeColor = VmpTheme.CS_Text, BackColor = Color.Transparent, Font = VmpTheme.FontSans10, AutoSize = true, Dock = DockStyle.Top };
            lblDeltaHint = new Label { Name = nameof(lblDeltaHint), Text = "Paste 64–4096 float32 values (comma or newline separated).", ForeColor = VmpTheme.CS_Muted, BackColor = Color.Transparent, Font = VmpTheme.FontSans9, AutoSize = false, Height = 20, Dock = DockStyle.Top };
            txtDeltaInput = VmpTheme.MakeTextBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text, VmpTheme.CS_Border2);
            txtDeltaInput.Name = nameof(txtDeltaInput); txtDeltaInput.Height = 60; txtDeltaInput.Multiline = true; txtDeltaInput.Dock = DockStyle.Top;

            // Binary info
            lblBinaryHead = SectionTitle("Binary payload preview (VoiceAdapter.Serialize())");
            lblBinaryHead.Name = nameof(lblBinaryHead);
            dgvBinaryInfo = MakeDarkGrid(nameof(dgvBinaryInfo), 160);
            dgvBinaryInfo.Columns.Add("Field", "FIELD"); dgvBinaryInfo.Columns.Add("Value", "VALUE");
            dgvBinaryInfo.Columns[0].Width = 200; dgvBinaryInfo.Columns[1].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill;
            dgvBinaryInfo.Rows.Add("magic byte",   "0xAD");
            dgvBinaryInfo.Rows.Add("version byte", "0x01");
            dgvBinaryInfo.Rows.Add("pitch (float32)",   "1.0000");
            dgvBinaryInfo.Rows.Add("formant (float32)", "1.0000");
            dgvBinaryInfo.Rows.Add("grit (float32)",    "0.0000");
            dgvBinaryInfo.Rows.Add("breath (float32)",  "0.0000");
            dgvBinaryInfo.Rows.Add("gender (byte)",     "Unknown");
            dgvBinaryInfo.Rows.Add("playCount (int32)", "0");
            dgvBinaryInfo.Rows.Add("total bytes", "24 B");

            var pnlBtns = MakeButtonRow();
            btnBuildAdapter = VmpTheme.MakeButton("⊕  Build & Copy Base64", VmpTheme.CS_Bg0, VmpTheme.CS_Copper, VmpTheme.CS_Copper);
            btnBuildAdapter.Name = nameof(btnBuildAdapter); btnBuildAdapter.Width = 210; btnBuildAdapter.Dock = DockStyle.Left;
            btnParseAdapter = VmpTheme.MakeButton("⊡  Parse existing Base64", VmpTheme.CS_Text, VmpTheme.CS_Bg3, VmpTheme.CS_Border2);
            btnParseAdapter.Name = nameof(btnParseAdapter); btnParseAdapter.Width = 190; btnParseAdapter.Dock = DockStyle.Left;
            pnlBtns.Controls.AddRange(new Control[] { btnParseAdapter, btnBuildAdapter });

            lblParseB64Label = FieldLabel("PARSE: PASTE X-VOICE-ADAPTER BASE64");
            lblParseB64Label.Name = nameof(lblParseB64Label);
            txtAdapterParseInput = VmpTheme.MakeTextBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text, VmpTheme.CS_Border2);
            txtAdapterParseInput.Name = nameof(txtAdapterParseInput); txtAdapterParseInput.Dock = DockStyle.Top;
            rtbAdapterParsed = MakeDarkRtb(nameof(rtbAdapterParsed), 80);

            AddToWorkPanel(pnlWorkAdapter, headLabel, lblAdapterDesc, pnlKnobs, pnlMeta,
                lblLoraHead, chkHasDelta, lblDeltaHint, txtDeltaInput,
                lblBinaryHead, dgvBinaryInfo, pnlBtns, lblParseB64Label, txtAdapterParseInput, rtbAdapterParsed);
            tabAdapter.Controls.Add(pnlWorkAdapter);
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: EQ PRESETS
        // ══════════════════════════════════════════════════════════════
        private void BuildTabEq()
        {
            pnlWorkEq = MakeWorkPanel(nameof(pnlWorkEq));

            var headLabel = SectionTitle("ParametricEq — 5-Band Configuration");

            lblEqDesc = new Label
            {
                Name      = nameof(lblEqDesc),
                Text      = "Bands: 80 Hz sub / 250 Hz bass / 1 kHz mid / 3.5 kHz presence / 10 kHz air.\nOutput: X-EQ-STATE Base64 (60 bytes → 80 chars) for ID3 TXXX tag.",
                ForeColor = VmpTheme.CS_Dim, BackColor = Color.Transparent,
                Font      = VmpTheme.FontSans9, AutoSize = false, Height = 36, Dock = DockStyle.Top,
            };

            // Preset buttons
            var pnlPresetBtns = new Panel { Height = 40, Dock = DockStyle.Top, BackColor = Color.Transparent };
            var presets = new[] { "Flat", "Vocal Boost", "Bass Boost", "Presence", "Karaoke" };
            var presetButtons = new Button[5];
            for (int i = 0; i < 5; i++)
            {
                presetButtons[i] = VmpTheme.MakeButton(presets[i], VmpTheme.CS_Text, VmpTheme.CS_Bg3, VmpTheme.CS_Border2);
                presetButtons[i].Dock = DockStyle.Left; presetButtons[i].Width = 110; presetButtons[i].Height = 30;
            }
            btnEqFlat = presetButtons[0]; btnEqFlat.Name = nameof(btnEqFlat);
            btnEqVocalBoost = presetButtons[1]; btnEqVocalBoost.Name = nameof(btnEqVocalBoost);
            btnEqBassBoost  = presetButtons[2]; btnEqBassBoost.Name  = nameof(btnEqBassBoost);
            btnEqPresence   = presetButtons[3]; btnEqPresence.Name   = nameof(btnEqPresence);
            btnEqKaraoke    = presetButtons[4]; btnEqKaraoke.Name    = nameof(btnEqKaraoke);
            foreach (var b in presetButtons) pnlPresetBtns.Controls.Add(b);

            // 5 EQ band cards
            pnlEqBand    = new Panel[5];
            lblEqBandName= new Label[5];
            lblEqBandHz  = new Label[5];
            trkEqGain    = new TrackBar[5];
            lblEqGainVal = new Label[5];
            var bandLabels = new[] { "SUB",  "BASS", "MID",  "PRES", "AIR" };
            var bandHz     = new[] { "80 Hz","250 Hz","1 kHz","3.5k", "10k" };
            pnlEqBands = new Panel { Name = nameof(pnlEqBands), Height = 130, Dock = DockStyle.Top, BackColor = Color.Transparent, Padding = new Padding(0, 0, 0, 8) };
            for (int i = 0; i < 5; i++)
            {
                pnlEqBand[i] = new Panel { BackColor = VmpTheme.CS_Bg2, Margin = new Padding(0, 0, 6, 0) };
                pnlEqBand[i].Paint += (s, e2) => { using var pen = new Pen(VmpTheme.CS_Border); e2.Graphics.DrawRectangle(pen, 0, 0, ((Panel)s!).Width - 1, ((Panel)s!).Height - 1); };
                lblEqBandName[i] = new Label { Text = bandLabels[i], ForeColor = VmpTheme.CS_Copper, BackColor = Color.Transparent, Font = new Font("Consolas", 8f, FontStyle.Bold), AutoSize = true, Location = new Point(8, 8) };
                lblEqBandHz[i]   = new Label { Text = bandHz[i],     ForeColor = VmpTheme.CS_Muted,  BackColor = Color.Transparent, Font = VmpTheme.FontMono9, AutoSize = true, Location = new Point(8, 24) };
                trkEqGain[i]     = VmpTheme.MakeTrackBar(-18, 18, 0); trkEqGain[i].Location = new Point(6, 44); trkEqGain[i].Width = 70;
                lblEqGainVal[i]  = new Label { Text = "0.0 dB", ForeColor = VmpTheme.CS_Cyan, BackColor = Color.Transparent, Font = new Font("Consolas", 8f, FontStyle.Bold), AutoSize = true, Location = new Point(8, 92) };
                pnlEqBand[i].Controls.AddRange(new Control[] { lblEqBandName[i], lblEqBandHz[i], trkEqGain[i], lblEqGainVal[i] });
            }

            pnlEqBands.Layout += (s, e) =>
            {
                int w = (pnlEqBands.Width - 4 * 6) / 5;
                for (int i = 0; i < 5; i++)
                {
                    pnlEqBand[i].SetBounds(i * (w + 6), 0, w, pnlEqBands.Height - 8);
                    trkEqGain[i].Width = w - 12;
                }
            };
            foreach (var p in pnlEqBand) pnlEqBands.Controls.Add(p);

            lblEqAdvHead = SectionTitle("Q and center frequency per band");
            lblEqAdvHead.Name = nameof(lblEqAdvHead);
            dgvEqAdvanced = MakeDarkGrid(nameof(dgvEqAdvanced), 110);
            dgvEqAdvanced.Columns.Add("Band", "BAND"); dgvEqAdvanced.Columns.Add("Q", "Q"); dgvEqAdvanced.Columns.Add("Freq", "FREQ (Hz)");
            dgvEqAdvanced.Columns[0].Width = 140; dgvEqAdvanced.Columns[1].Width = 80; dgvEqAdvanced.Columns[2].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill;
            var bandFull = new[] { "SUB — 80 Hz (LowShelf)", "BASS — 250 Hz (Peaking)", "MID — 1 kHz (Peaking)", "PRES — 3.5 kHz (Peaking)", "AIR — 10 kHz (HighShelf)" };
            var qs = new[] { "0.707", "1.000", "1.000", "1.000", "0.707" };
            for (int i = 0; i < 5; i++) dgvEqAdvanced.Rows.Add(bandFull[i], qs[i], bandHz[i]);

            lblEqPayloadHead = SectionTitle("X-EQ-STATE payload");
            lblEqPayloadHead.Name = nameof(lblEqPayloadHead);
            dgvEqPayload = MakeDarkGrid(nameof(dgvEqPayload), 100);
            dgvEqPayload.Columns.Add("Band", "BAND"); dgvEqPayload.Columns.Add("Gain", "GAIN"); dgvEqPayload.Columns.Add("Detail", "FREQ / Q");
            dgvEqPayload.Columns[0].Width = 80; dgvEqPayload.Columns[1].Width = 80; dgvEqPayload.Columns[2].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill;
            var gainRows = new[] { "0.0 dB", "0.0 dB", "0.0 dB", "0.0 dB", "0.0 dB" };
            for (int i = 0; i < 5; i++) dgvEqPayload.Rows.Add(bandLabels[i], gainRows[i], $"{bandHz[i]}  Q={qs[i]}");

            var pnlBtns = MakeButtonRow();
            btnBuildEq = VmpTheme.MakeButton("⊕  Build & Copy Base64", VmpTheme.CS_Bg0, VmpTheme.CS_Copper, VmpTheme.CS_Copper);
            btnBuildEq.Name = nameof(btnBuildEq); btnBuildEq.Width = 210; btnBuildEq.Dock = DockStyle.Left;
            btnParseEq = VmpTheme.MakeButton("⊡  Parse existing Base64", VmpTheme.CS_Text, VmpTheme.CS_Bg3, VmpTheme.CS_Border2);
            btnParseEq.Name = nameof(btnParseEq); btnParseEq.Width = 190; btnParseEq.Dock = DockStyle.Left;
            pnlBtns.Controls.AddRange(new Control[] { btnParseEq, btnBuildEq });

            lblEqPayloadHead = SectionTitle("X-EQ-STATE payload");
            var lblEqParseLbl = FieldLabel("PARSE: PASTE X-EQ-STATE BASE64");
            txtEqParseInput = VmpTheme.MakeTextBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text, VmpTheme.CS_Border2);
            txtEqParseInput.Name = nameof(txtEqParseInput); txtEqParseInput.Dock = DockStyle.Top;
            rtbEqParsed = MakeDarkRtb(nameof(rtbEqParsed), 70);

            AddToWorkPanel(pnlWorkEq, headLabel, lblEqDesc, pnlPresetBtns, pnlEqBands,
                lblEqAdvHead, dgvEqAdvanced, lblEqPayloadHead, dgvEqPayload,
                pnlBtns, lblEqParseLbl, txtEqParseInput, rtbEqParsed);
            tabEq.Controls.Add(pnlWorkEq);
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: MODEL REGISTRY
        // ══════════════════════════════════════════════════════════════
        private void BuildTabModels()
        {
            pnlWorkModels = MakeWorkPanel(nameof(pnlWorkModels));
            var headLabel = SectionTitle("ONNX Model Registry — %AppData%\\VoiceMorphPlayer\\models\\");

            lblModelsDesc = new Label
            {
                Name      = nameof(lblModelsDesc),
                Text      = "Models checked by DemucsEngine.ModelAvailable, RvcEngine.ModelAvailable, and GenderFlipEngine at runtime.",
                ForeColor = VmpTheme.CS_Dim, BackColor = Color.Transparent, Font = VmpTheme.FontSans9,
                AutoSize  = false, Height = 24, Dock = DockStyle.Top,
            };

            pnlModelList = new Panel { Name = nameof(pnlModelList), Dock = DockStyle.Top, Height = 280, BackColor = Color.Transparent };
            var modelDefs = new[]
            {
                ("demucs_v4.onnx",   "Demucs v4",     "4-stem separator (~170 MB)",      "DemucsEngine",       true),
                ("hubert_lite.onnx", "HuBERT Lite",   "Content encoder (~25 MB)",        "RvcEngine",          false),
                ("rvc_decoder.onnx", "RVC Decoder",   "Voice conv decoder (~60 MB)",     "RvcEngine",          false),
                ("m2f_voice.onnx",   "M→F Model",     "Male-to-female ONNX model",       "GenderFlipEngine",   false),
                ("f2m_voice.onnx",   "F→M Model",     "Female-to-male ONNX model",       "GenderFlipEngine",   false),
            };

            pnlModelRow   = new Panel[5];
            pnlModelDot   = new Panel[5];
            lblModelName  = new Label[5];
            lblModelFile  = new Label[5];
            lblModelDesc  = new Label[5];
            lblModelBadge = new Label[5];

            for (int i = 0; i < 5; i++)
            {
                int idx = i;   // capture local copy — avoids closure-over-loop-variable bug
                var (file, name, desc, engine, present) = modelDefs[idx];
                pnlModelRow[idx] = new Panel { BackColor = VmpTheme.CS_Bg2, Height = 52, Dock = DockStyle.Top, Margin = new Padding(0, 0, 0, 4) };
                pnlModelRow[idx].Paint += (s, e) => { using var pen = new Pen(VmpTheme.CS_Border); e.Graphics.DrawRectangle(pen, 0, 0, ((Panel)s!).Width-1, ((Panel)s!).Height-1); };

                pnlModelDot[idx] = new Panel { Size = new Size(8, 8), Location = new Point(14, 22), BackColor = present ? VmpTheme.CS_Cyan : VmpTheme.CS_Border2 };

                lblModelName[idx]  = new Label { Text = name,   ForeColor = VmpTheme.CS_Text,  BackColor = Color.Transparent, Font = VmpTheme.FontMonoBold10, AutoSize = true, Location = new Point(32, 8)  };
                lblModelFile[idx]  = new Label { Text = file,   ForeColor = VmpTheme.CS_Muted, BackColor = Color.Transparent, Font = VmpTheme.FontMono9, AutoSize = true, Location = new Point(180, 10) };
                lblModelDesc[idx]  = new Label { Text = $"{desc} — {engine}", ForeColor = VmpTheme.CS_Muted, BackColor = Color.Transparent, Font = VmpTheme.FontSans9, AutoSize = true, Location = new Point(32, 28) };
                lblModelBadge[idx] = new Label { Text = present ? "PRESENT" : "MISSING", ForeColor = present ? VmpTheme.CS_Cyan : VmpTheme.CS_Muted, BackColor = VmpTheme.CS_Bg3, Font = new Font("Consolas", 7.5f, FontStyle.Bold), AutoSize = true, Padding = new Padding(6, 2, 6, 2), BorderStyle = BorderStyle.FixedSingle };
                pnlModelRow[idx].Layout += (s, e2) => lblModelBadge[idx].Location = new Point(((Panel)s!).Width - lblModelBadge[idx].Width - 14, (((Panel)s!).Height - lblModelBadge[idx].Height) / 2);

                pnlModelRow[idx].Controls.AddRange(new Control[] { pnlModelDot[idx], lblModelName[idx], lblModelFile[idx], lblModelDesc[idx], lblModelBadge[idx] });
                pnlModelList.Controls.Add(pnlModelRow[idx]);
            }

            lblExportCmdHead = SectionTitle("Export instructions");
            lblExportCmdHead.Name = nameof(lblExportCmdHead);
            rtbExportCmd = MakeDarkRtb(nameof(rtbExportCmd), 100);
            rtbExportCmd.Text = "pip install demucs torch onnx\n# then run tools/export_hubert.py\n# See: https://huggingface.co/lj1995/VoiceConversionWebUI";

            AddToWorkPanel(pnlWorkModels, headLabel, lblModelsDesc, pnlModelList, lblExportCmdHead, rtbExportCmd);
            tabModels.Controls.Add(pnlWorkModels);
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: TRAINING EXPORT
        // ══════════════════════════════════════════════════════════════
        private void BuildTabExport()
        {
            pnlWorkExport = MakeWorkPanel(nameof(pnlWorkExport));
            var headLabel = SectionTitle("Training Config Export — training_config.json");

            lblExportDesc = new Label
            {
                Name = nameof(lblExportDesc),
                Text = "Merges a VoiceDelta, VoiceAdapter payload, and optional VoiceCentroid bundle metadata\ninto training_config.json for the C# training module.",
                ForeColor = VmpTheme.CS_Dim, BackColor = Color.Transparent, Font = VmpTheme.FontSans9,
                AutoSize = false, Height = 36, Dock = DockStyle.Top,
            };

            // Row 1: delta + adapter
            var row1 = new Panel { Height = 68, Dock = DockStyle.Top, BackColor = Color.Transparent };
            lblExportDeltaLbl  = FieldLabel("DELTA SOURCE");        lblExportDeltaLbl.Name  = nameof(lblExportDeltaLbl);
            cboExportDelta     = VmpTheme.MakeComboBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text); cboExportDelta.Name = nameof(cboExportDelta); cboExportDelta.Items.Add("amy_to_artist.json");
            lblExportAdapterLbl= FieldLabel("ADAPTER BASE64 (OPTIONAL)"); lblExportAdapterLbl.Name = nameof(lblExportAdapterLbl);
            txtExportAdapterB64= VmpTheme.MakeTextBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text, VmpTheme.CS_Border2); txtExportAdapterB64.Name = nameof(txtExportAdapterB64);
            var r1L = new Panel { Dock = DockStyle.Left, Width = 260, BackColor = Color.Transparent }; r1L.Controls.AddRange(new Control[] { cboExportDelta, lblExportDeltaLbl });
            var r1R = new Panel { Dock = DockStyle.Fill, BackColor = Color.Transparent, Padding = new Padding(12, 0, 0, 0) }; r1R.Controls.AddRange(new Control[] { txtExportAdapterB64, lblExportAdapterLbl });
            row1.Controls.AddRange(new Control[] { r1L, r1R });

            // Row 2: vc bundle + job name
            var row2 = new Panel { Height = 68, Dock = DockStyle.Top, BackColor = Color.Transparent };
            lblExportVcLbl  = FieldLabel("VOICECENTROID BUNDLE (OPTIONAL)"); lblExportVcLbl.Name = nameof(lblExportVcLbl);
            txtExportVcBundle = VmpTheme.MakeTextBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text, VmpTheme.CS_Border2); txtExportVcBundle.Name = nameof(txtExportVcBundle);
            lblExportJobLbl = FieldLabel("TRAINING JOB NAME");               lblExportJobLbl.Name = nameof(lblExportJobLbl);
            txtExportJobName  = VmpTheme.MakeTextBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text, VmpTheme.CS_Border2); txtExportJobName.Name = nameof(txtExportJobName); txtExportJobName.Text = "job_001";
            var r2L = new Panel { Dock = DockStyle.Left, Width = 320, BackColor = Color.Transparent }; r2L.Controls.AddRange(new Control[] { txtExportVcBundle, lblExportVcLbl });
            var r2R = new Panel { Dock = DockStyle.Fill, BackColor = Color.Transparent, Padding = new Padding(12, 0, 0, 0) }; r2R.Controls.AddRange(new Control[] { txtExportJobName, lblExportJobLbl });
            row2.Controls.AddRange(new Control[] { r2L, r2R });

            // Notes
            lblExportNotesLbl = FieldLabel("NOTES / DESCRIPTION"); lblExportNotesLbl.Name = nameof(lblExportNotesLbl);
            txtExportNotes = VmpTheme.MakeTextBox(VmpTheme.CS_Bg2, VmpTheme.CS_Text, VmpTheme.CS_Border2);
            txtExportNotes.Name = nameof(txtExportNotes); txtExportNotes.Multiline = true; txtExportNotes.Height = 50; txtExportNotes.Dock = DockStyle.Top;

            var pnlBtns = MakeButtonRow();
            btnBuildTraining = VmpTheme.MakeButton("⊕  Build training_config.json", VmpTheme.CS_Bg0, VmpTheme.CS_Copper, VmpTheme.CS_Copper);
            btnBuildTraining.Name = nameof(btnBuildTraining); btnBuildTraining.Width = 240; btnBuildTraining.Dock = DockStyle.Left;
            btnPreviewTraining = VmpTheme.MakeButton("◈  Preview", VmpTheme.CS_Text, VmpTheme.CS_Bg3, VmpTheme.CS_Border2);
            btnPreviewTraining.Name = nameof(btnPreviewTraining); btnPreviewTraining.Width = 120; btnPreviewTraining.Dock = DockStyle.Left;
            pnlBtns.Controls.AddRange(new Control[] { btnPreviewTraining, btnBuildTraining });

            // Preview output
            lblExportPreviewHead = SectionTitle("Preview — training_config.json"); lblExportPreviewHead.Name = nameof(lblExportPreviewHead);
            rtbExportPreview = MakeDarkRtb(nameof(rtbExportPreview), 160);
            rtbExportPreview.Text = "{\n  \"schema_version\": \"1.0\",\n  \"job_name\": \"job_001\",\n  ...\n}";

            var pnlBtns2 = MakeButtonRow();
            btnSaveTraining = VmpTheme.MakeButton("▼  Save training_config.json", VmpTheme.CS_Bg0, VmpTheme.CS_Cyan2, VmpTheme.CS_Cyan2);
            btnSaveTraining.Name = nameof(btnSaveTraining); btnSaveTraining.Width = 240; btnSaveTraining.Dock = DockStyle.Left;
            btnCopyTraining = VmpTheme.MakeButton("⊡  Copy JSON", VmpTheme.CS_Text, VmpTheme.CS_Bg3, VmpTheme.CS_Border2);
            btnCopyTraining.Name = nameof(btnCopyTraining); btnCopyTraining.Width = 130; btnCopyTraining.Dock = DockStyle.Left;
            pnlBtns2.Controls.AddRange(new Control[] { btnCopyTraining, btnSaveTraining });

            AddToWorkPanel(pnlWorkExport, headLabel, lblExportDesc, row1, row2,
                lblExportNotesLbl, txtExportNotes, pnlBtns,
                lblExportPreviewHead, rtbExportPreview, pnlBtns2);
            tabExport.Controls.Add(pnlWorkExport);
        }

        // ══════════════════════════════════════════════════════════════
        //  LAYOUT HELPERS
        // ══════════════════════════════════════════════════════════════
        private static TabPage MakeTabPage(string text, string name)
            => new TabPage { Text = text, Name = name, BackColor = VmpTheme.CS_Bg0, ForeColor = VmpTheme.CS_Text, Padding = new Padding(0) };

        private static Panel MakeWorkPanel(string name)
            => new Panel { Name = name, Dock = DockStyle.Fill, BackColor = VmpTheme.CS_Bg0,
                           AutoScroll = true, Padding = new Padding(22, 18, 22, 18) };

        private static Label SectionTitle(string text)
            => new Label
            {
                Text        = text,
                ForeColor   = VmpTheme.CS_Copper,
                BackColor   = Color.Transparent,
                Font        = new Font("Consolas", 8f, FontStyle.Bold),
                AutoSize    = false,
                Height      = 28,
                Dock        = DockStyle.Top,
                Padding     = new Padding(0, 10, 0, 4),
            };

        private static Label FieldLabel(string text)
            => new Label
            {
                Text      = text,
                ForeColor = VmpTheme.CS_Muted,
                BackColor = Color.Transparent,
                Font      = new Font("Consolas", 7.5f, FontStyle.Bold),
                AutoSize  = false,
                Height    = 18,
                Dock      = DockStyle.Top,
            };

        private static DataGridView MakeDarkGrid(string name, int height)
        {
            var dgv = new DataGridView
            {
                Name                    = name,
                Dock                    = DockStyle.Top,
                Height                  = height,
                BackgroundColor         = VmpTheme.CS_Bg2,
                ForeColor               = VmpTheme.CS_Text,
                GridColor               = VmpTheme.CS_Border,
                BorderStyle             = BorderStyle.FixedSingle,
                Font                    = VmpTheme.FontMono10,
                RowHeadersVisible       = false,
                AllowUserToAddRows      = false,
                AllowUserToResizeRows   = false,
                AllowUserToDeleteRows   = false,
                SelectionMode           = DataGridViewSelectionMode.FullRowSelect,
                MultiSelect             = false,
                ReadOnly                = true,
                ColumnHeadersHeight     = 26,
                RowTemplate             = { Height = 24 },
                AutoSizeColumnsMode     = DataGridViewAutoSizeColumnsMode.None,
            };
            dgv.ColumnHeadersDefaultCellStyle.BackColor  = VmpTheme.CS_Bg3;
            dgv.ColumnHeadersDefaultCellStyle.ForeColor  = VmpTheme.CS_Muted;
            dgv.ColumnHeadersDefaultCellStyle.Font       = new Font("Consolas", 7.5f, FontStyle.Bold);
            dgv.DefaultCellStyle.BackColor                = VmpTheme.CS_Bg2;
            dgv.DefaultCellStyle.ForeColor                = VmpTheme.CS_Text;
            dgv.DefaultCellStyle.SelectionBackColor       = VmpTheme.CS_Bg3;
            dgv.DefaultCellStyle.SelectionForeColor       = VmpTheme.CS_Copper2;
            dgv.AlternatingRowsDefaultCellStyle.BackColor = VmpTheme.CS_Bg3;
            dgv.EnableHeadersVisualStyles                 = false;
            return dgv;
        }

        private static RichTextBox MakeDarkRtb(string name, int height)
            => new RichTextBox
            {
                Name        = name,
                Dock        = DockStyle.Top,
                Height      = height,
                BackColor   = VmpTheme.CS_Bg2,
                ForeColor   = VmpTheme.CS_Dim,
                Font        = VmpTheme.FontMono9,
                BorderStyle = BorderStyle.FixedSingle,
                ReadOnly    = true,
                ScrollBars  = RichTextBoxScrollBars.Vertical,
                WordWrap    = true,
            };

        private static Panel MakeButtonRow()
            => new Panel { Height = 40, Dock = DockStyle.Top, BackColor = Color.Transparent, Padding = new Padding(0, 4, 0, 4) };

        // Adds controls to a work panel in REVERSE order (Dock=Top stacks bottom-up in WinForms)
        private static void AddToWorkPanel(Panel work, params Control[] controls)
        {
            for (int i = controls.Length - 1; i >= 0; i--)
                work.Controls.Add(controls[i]);
        }

        private static (Panel card, Label val, Label caption) MakeStatCard(string value, string caption)
        {
            var card = new Panel { BackColor = VmpTheme.CS_Bg2, Margin = new Padding(0, 0, 8, 0) };
            card.Paint += (s, e) => { using var pen = new Pen(VmpTheme.CS_Border); e.Graphics.DrawRectangle(pen, 0, 0, card.Width - 1, card.Height - 1); };
            var val = new Label { Text = value, ForeColor = VmpTheme.CS_Copper, BackColor = Color.Transparent, Font = new Font("Consolas", 15f, FontStyle.Bold), AutoSize = true, Location = new Point(12, 8) };
            var cap = new Label { Text = caption.ToUpper(), ForeColor = VmpTheme.CS_Muted, BackColor = Color.Transparent, Font = new Font("Consolas", 7.5f, FontStyle.Bold), AutoSize = true, Location = new Point(12, 38) };
            card.Controls.AddRange(new Control[] { val, cap });
            return (card, val, cap);
        }

        private static void LayoutStatCards(Panel row, params Panel[] cards)
        {
            row.Layout += (s, e) =>
            {
                int w = (row.Width - (cards.Length - 1) * 8) / cards.Length;
                for (int i = 0; i < cards.Length; i++)
                    cards[i].SetBounds(i * (w + 8), 0, w, row.Height - row.Padding.Bottom);
            };
            foreach (var c in cards) row.Controls.Add(c);
        }

        private static (Panel card, Label caption, Label val, TrackBar trk) MakeKnobCard(string label, int min, int max, int def)
        {
            var card = new Panel { BackColor = VmpTheme.CS_Bg2, Margin = new Padding(0, 0, 8, 0) };
            card.Paint += (s, e) => { using var pen = new Pen(VmpTheme.CS_Border); e.Graphics.DrawRectangle(pen, 0, 0, card.Width - 1, card.Height - 1); };
            var cap = new Label { Text = label, ForeColor = VmpTheme.CS_Muted, BackColor = Color.Transparent, Font = new Font("Consolas", 7.5f, FontStyle.Bold), AutoSize = true, Location = new Point(10, 8) };
            var v = new Label   { Text = (def / 100f).ToString("F2"), ForeColor = VmpTheme.CS_Copper, BackColor = Color.Transparent, Font = new Font("Consolas", 14f, FontStyle.Bold), AutoSize = true, Location = new Point(10, 24) };
            var trk = VmpTheme.MakeTrackBar(min, max, def); trk.Location = new Point(6, 58); trk.TickStyle = TickStyle.None;
            card.Controls.AddRange(new Control[] { cap, v, trk });
            card.Layout += (s, e) => { trk.Width = card.Width - 12; };
            return (card, cap, v, trk);
        }

        private static void LayoutKnobCards(Panel row, params Panel[] cards)
        {
            row.Layout += (s, e) =>
            {
                int w = (row.Width - (cards.Length - 1) * 8) / cards.Length;
                for (int i = 0; i < cards.Length; i++)
                    cards[i].SetBounds(i * (w + 8), 0, w, row.Height - 8);
            };
            foreach (var c in cards) row.Controls.Add(c);
        }
    }
}
