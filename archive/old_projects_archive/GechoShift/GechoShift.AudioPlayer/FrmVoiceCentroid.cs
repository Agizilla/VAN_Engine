using System;
using System.Drawing;
using System.Windows.Forms;

namespace GechoShift.AudioPlayer
{
    // ════════════════════════════════════════════════════════════════════
    // FrmVoiceCentroid
    //
    //   WinForms layout mirror of ClaudeVoiceCompare.html (VoiceCentroid).
    //   NO LOGIC — controls are named and positioned for designer editing.
    //
    //   Structure (matches HTML exactly):
    //     pnlHeader             — top bar with logo, status badge, action buttons
    //     tabMain               — 5 tabs:
    //       tabBattle             Battle Generator  (left sidebar + right workspace)
    //       tabRules              Linguistic Rules  (JSON editor)
    //       tabLexicon            Lexicon Viewer    (filterable table)
    //       tabAnalytics          Analytics         (stat cards + bar charts)
    //       tabSaved              Saved Sessions    (list)
    //
    //   Sidebar (tabBattle) contains:
    //     Dataset section: scan + rules buttons, two ComboBoxes (A/B)
    //     Controls section: blend slider, logprob toggle, generate buttons
    //     Stats label
    //
    //   Colour palette: VmpTheme.VC_* (navy / indigo / sky / pink)
    // ════════════════════════════════════════════════════════════════════
    public class FrmVoiceCentroid : Form
    {
        // ── Header ─────────────────────────────────────────────────────
        public Panel   pnlHeader          = null!;
        public Label   lblLogo            = null!;
        public Label   lblStatusBadge     = null!;
        public Button  btnImportBundle    = null!;
        public Button  btnSaveSong        = null!;
        public Button  btnExportBundle    = null!;
        public Button  btnClearLexicon    = null!;

        // ── Tab control ────────────────────────────────────────────────
        public TabControl tabMain         = null!;
        public TabPage    tabBattle       = null!;
        public TabPage    tabRules        = null!;
        public TabPage    tabLexicon      = null!;
        public TabPage    tabAnalytics    = null!;
        public TabPage    tabSaved        = null!;

        // ── Sidebar (lives inside tabBattle) ───────────────────────────
        public Panel   pnlSidebar         = null!;

        // Dataset section
        public Label   lblDatasetHead     = null!;
        public Button  btnScanFolder      = null!;
        public Button  btnLoadRules       = null!;
        public Label   lblArtistALabel    = null!;
        public ComboBox cboArtistA        = null!;
        public Label   lblArtistBLabel    = null!;
        public ComboBox cboArtistB        = null!;

        // Controls section
        public Label   lblControlsHead    = null!;
        public Label   lblBlendLabel      = null!;
        public Panel   pnlBlendRow        = null!;
        public Label   lblBlendA          = null!;
        public TrackBar trkBlend          = null!;
        public Label   lblBlendB          = null!;
        public Label   lblBlendVal        = null!;
        public Panel   pnlLogprobRow      = null!;
        public Label   lblLogprobLabel    = null!;
        public CheckBox chkLogprob        = null!;
        public Button  btnTriBattle       = null!;
        public Button  btnClassicMix      = null!;

        // Stats
        public Label   lblStats           = null!;

        // ── Tab: Battle Generator workspace ────────────────────────────
        public Panel   pnlWorkBattle      = null!;
        // Six verse blocks (rows of 5 lines each)
        public Panel[] pnlVerse           = null!;   // [6]
        public Panel[] pnlVerseHeader     = null!;   // [6]
        public Label[] lblVerseNum        = null!;   // [6]
        // Line rows inside verse 0 (sample — others identical)
        public Panel   pnlLine_0_A1MOD    = null!;
        public Label   lblLine_0_A1MOD    = null!;
        public Panel   pnlLine_0_A2SIM_1  = null!;
        public Label   lblLine_0_A2SIM_1  = null!;
        public Panel   pnlLine_0_A1ORG    = null!;
        public Label   lblLine_0_A1ORG    = null!;
        public Panel   pnlLine_0_A2SIM_2  = null!;
        public Label   lblLine_0_A2SIM_2  = null!;
        public Panel   pnlLine_0_SYNTH    = null!;
        public Label   lblLine_0_SYNTH    = null!;
        public Button  btnRedo_0          = null!;

        // ── Tab: Linguistic Rules ──────────────────────────────────────
        public Panel   pnlWorkRules       = null!;
        public Panel   pnlRulesHeader     = null!;
        public Label   lblRulesTitle      = null!;
        public Label   lblRulesHint       = null!;
        public Button  btnValidateRules   = null!;
        public Label   lblRulesStatus     = null!;
        public RichTextBox rtbRulesEditor = null!;

        // ── Tab: Lexicon Viewer ────────────────────────────────────────
        public Panel   pnlWorkLexicon     = null!;
        public Label   lblLexTitle        = null!;
        public Label   lblLexHint         = null!;
        public Label   lblLexCount        = null!;
        public TextBox txtLexFilter       = null!;
        public DataGridView dgvLexicon    = null!;

        // ── Tab: Analytics ─────────────────────────────────────────────
        public Panel   pnlWorkAnalytics   = null!;
        public Label   lblAnalyticsTitle  = null!;
        // Stat cards
        public Panel   pnlAnalyticsStats  = null!;
        public Panel   cardVocabA         = null!;
        public Label   lblVocabAVal       = null!;
        public Label   lblVocabACap       = null!;
        public Panel   cardVocabB         = null!;
        public Label   lblVocabBVal       = null!;
        public Label   lblVocabBCap       = null!;
        public Panel   cardOverlap        = null!;
        public Label   lblOverlapVal      = null!;
        public Label   lblOverlapCap      = null!;
        public Panel   cardDivergence     = null!;
        public Label   lblDivergenceVal   = null!;
        public Label   lblDivergenceCap   = null!;
        // Logprob bar section
        public Label   lblLogprobHead     = null!;
        public Panel   pnlLogprobBars     = null!;
        public Label   lblLpArtistA       = null!;
        public Panel   pnlLpBarA          = null!;
        public Panel   pnlLpFillA         = null!;
        public Label   lblLpValA          = null!;
        public Label   lblLpArtistB       = null!;
        public Panel   pnlLpBarB          = null!;
        public Panel   pnlLpFillB         = null!;
        public Label   lblLpValB          = null!;
        // Rhyme density bars
        public Label   lblRhymeHead       = null!;
        public Panel   pnlRhymeBars       = null!;
        public Label   lblRhymeA          = null!;
        public Panel   pnlRhymeBarA       = null!;
        public Panel   pnlRhymeFillA      = null!;
        public Label   lblRhymeValA       = null!;
        public Label   lblRhymeB          = null!;
        public Panel   pnlRhymeBarB       = null!;
        public Panel   pnlRhymeFillB      = null!;
        public Label   lblRhymeValB       = null!;
        // Distinctive words
        public Label   lblDistinctHead    = null!;
        public FlowLayoutPanel flpDistinctWords = null!;

        // ── Tab: Saved Sessions ────────────────────────────────────────
        public Panel   pnlWorkSaved       = null!;
        public Label   lblSavedTitle      = null!;
        public Panel   pnlSavedList       = null!;
        // Three sample saved-session rows
        public Panel   pnlSavedRow0       = null!;
        public Label   lblSavedName0      = null!;
        public Label   lblSavedMeta0      = null!;
        public Button  btnSavedLoad0      = null!;
        public Button  btnSavedDel0       = null!;

        // ══════════════════════════════════════════════════════════════
        public FrmVoiceCentroid()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            SuspendLayout();

            // ── Form ──────────────────────────────────────────────────
            Text          = "VoiceCentroid Ultra — Battle Studio";
            Size          = new Size(1280, 820);
            MinimumSize   = new Size(1000, 640);
            BackColor     = VmpTheme.VC_Bg;
            ForeColor     = VmpTheme.VC_Text;
            Font          = VmpTheme.FontSans10;
            StartPosition = FormStartPosition.CenterScreen;

            // ── Header ────────────────────────────────────────────────
            pnlHeader = new Panel
            {
                Name      = nameof(pnlHeader),
                Dock      = DockStyle.Top,
                Height    = 52,
                BackColor = VmpTheme.VC_Bg2,
                Padding   = new Padding(16, 0, 16, 0),
            };
            pnlHeader.Paint += (s, e) =>
            {
                using var pen = new Pen(VmpTheme.VC_Border);
                e.Graphics.DrawLine(pen, 0, pnlHeader.Height - 1, pnlHeader.Width, pnlHeader.Height - 1);
            };

            lblLogo = new Label
            {
                Name      = nameof(lblLogo),
                Text      = "● VOICECENTROID  ULTRA V2",
                ForeColor = VmpTheme.VC_Indigo2,
                BackColor = Color.Transparent,
                Font      = new Font("Consolas", 9.5f, FontStyle.Bold),
                AutoSize  = true,
            };

            lblStatusBadge = new Label
            {
                Name        = nameof(lblStatusBadge),
                Text        = "READY",
                ForeColor   = VmpTheme.VC_Green,
                BackColor   = VmpTheme.VC_Bg3,
                Font        = new Font("Consolas", 7.5f, FontStyle.Bold),
                AutoSize    = true,
                Padding     = new Padding(8, 3, 8, 3),
                BorderStyle = BorderStyle.FixedSingle,
            };

            btnImportBundle = MakeHdrButton("⬇  Import Bundle", VmpTheme.VC_Sky,    VmpTheme.VC_Bg3);
            btnImportBundle.Name = nameof(btnImportBundle);
            btnSaveSong     = MakeHdrButton("★  Save Song",     VmpTheme.VC_Warn,   VmpTheme.VC_Bg3);
            btnSaveSong.Name = nameof(btnSaveSong);
            btnExportBundle = MakeHdrButton("▲  Export Bundle", Color.Black,         VmpTheme.VC_Indigo);
            btnExportBundle.Name = nameof(btnExportBundle);
            btnClearLexicon = MakeHdrButton("✕  Clear Lex",     VmpTheme.VC_Err,    VmpTheme.VC_Bg3);
            btnClearLexicon.Name = nameof(btnClearLexicon);

            pnlHeader.Controls.AddRange(new Control[] { lblLogo, lblStatusBadge, btnImportBundle, btnSaveSong, btnExportBundle, btnClearLexicon });
            pnlHeader.Layout += (s, e) =>
            {
                int cx = pnlHeader.Height / 2;
                lblLogo.Location       = new Point(16, (pnlHeader.Height - lblLogo.Height) / 2);
                int rx = pnlHeader.Width - 12;
                foreach (Button b in new[] { btnClearLexicon, btnExportBundle, btnSaveSong, btnImportBundle })
                {
                    rx -= b.Width + 6;
                    b.Location = new Point(rx, (pnlHeader.Height - b.Height) / 2);
                }
                lblStatusBadge.Location = new Point(rx - lblStatusBadge.Width - 10, (pnlHeader.Height - lblStatusBadge.Height) / 2);
            };

            // ── Tab control ───────────────────────────────────────────
            tabMain = new TabControl
            {
                Name       = nameof(tabMain),
                Dock       = DockStyle.Fill,
                Font       = new Font("Consolas", 8.5f, FontStyle.Bold),
                DrawMode   = TabDrawMode.OwnerDrawFixed,
                ItemSize   = new Size(130, 34),
                SizeMode   = TabSizeMode.Fixed,
                Appearance = TabAppearance.FlatButtons,
                BackColor  = VmpTheme.VC_Bg,
            };

            tabBattle   = MakeTabPage("⚔  BATTLE GENERATOR", nameof(tabBattle));
            tabRules    = MakeTabPage("▣  LINGUISTIC RULES",  nameof(tabRules));
            tabLexicon  = MakeTabPage("◈  LEXICON VIEWER",    nameof(tabLexicon));
            tabAnalytics= MakeTabPage("≋  ANALYTICS",         nameof(tabAnalytics));
            tabSaved    = MakeTabPage("◉  SAVED SESSIONS",    nameof(tabSaved));
            tabMain.TabPages.AddRange(new[] { tabBattle, tabRules, tabLexicon, tabAnalytics, tabSaved });

            BuildTabBattle();
            BuildTabRules();
            BuildTabLexicon();
            BuildTabAnalytics();
            BuildTabSaved();

            Controls.Add(tabMain);
            Controls.Add(pnlHeader);

            ResumeLayout(false);
            PerformLayout();
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: BATTLE GENERATOR
        // ══════════════════════════════════════════════════════════════
        private void BuildTabBattle()
        {
            // ── Sidebar ───────────────────────────────────────────────
            pnlSidebar = new Panel
            {
                Name      = nameof(pnlSidebar),
                Dock      = DockStyle.Left,
                Width     = 300,
                BackColor = VmpTheme.VC_Bg2,
            };
            pnlSidebar.Paint += (s, e) =>
            {
                using var pen = new Pen(VmpTheme.VC_Border);
                e.Graphics.DrawLine(pen, pnlSidebar.Width - 1, 0, pnlSidebar.Width - 1, pnlSidebar.Height);
            };

            // Dataset section
            lblDatasetHead = SidebarSectionHead("Dataset");
            lblDatasetHead.Name = nameof(lblDatasetHead);

            btnScanFolder = MakeSidebarButton("▶  Authorize & Scan Folder", VmpTheme.VC_Indigo2, VmpTheme.VC_Bg3, VmpTheme.VC_Indigo);
            btnScanFolder.Name = nameof(btnScanFolder);
            btnLoadRules  = MakeSidebarButton("▣  Load Lexicon Rules JSON", VmpTheme.VC_Warn, VmpTheme.VC_Bg3, VmpTheme.VC_Warn);
            btnLoadRules.Name = nameof(btnLoadRules);

            lblArtistALabel = SidebarFieldLabel("Artist A — Lead");
            lblArtistALabel.Name = nameof(lblArtistALabel); lblArtistALabel.ForeColor = VmpTheme.VC_Sky;
            cboArtistA = MakeSidebarCombo();
            cboArtistA.Name = nameof(cboArtistA); cboArtistA.Items.Add("artist_a.json");

            lblArtistBLabel = SidebarFieldLabel("Artist B — Sim");
            lblArtistBLabel.Name = nameof(lblArtistBLabel); lblArtistBLabel.ForeColor = VmpTheme.VC_Pink;
            cboArtistB = MakeSidebarCombo();
            cboArtistB.Name = nameof(cboArtistB); cboArtistB.Items.Add("artist_b.json");

            // Controls section
            lblControlsHead = SidebarSectionHead("Controls");
            lblControlsHead.Name = nameof(lblControlsHead);

            lblBlendLabel = SidebarFieldLabel("Style Blend  A ←→ B");
            lblBlendLabel.Name = nameof(lblBlendLabel); lblBlendLabel.ForeColor = VmpTheme.VC_Indigo2;

            pnlBlendRow = new Panel { Name = nameof(pnlBlendRow), Height = 28, Dock = DockStyle.Top, BackColor = Color.Transparent };
            lblBlendA   = new Label { Name = nameof(lblBlendA), Text = "A", ForeColor = VmpTheme.VC_Sky,  BackColor = Color.Transparent, Font = new Font("Consolas", 8f, FontStyle.Bold), AutoSize = true, Location = new Point(0, 6) };
            trkBlend    = VmpTheme.MakeTrackBar(0, 100, 50); trkBlend.Name = nameof(trkBlend); trkBlend.Location = new Point(20, 2); trkBlend.BackColor = VmpTheme.VC_Bg2;
            lblBlendB   = new Label { Name = nameof(lblBlendB), Text = "B", ForeColor = VmpTheme.VC_Pink, BackColor = Color.Transparent, Font = new Font("Consolas", 8f, FontStyle.Bold), AutoSize = true, Location = new Point(0, 6) };
            lblBlendVal = new Label { Name = nameof(lblBlendVal), Text = "50%", ForeColor = VmpTheme.VC_Indigo2, BackColor = Color.Transparent, Font = new Font("Consolas", 8.5f, FontStyle.Bold), AutoSize = true, Location = new Point(0, 6) };
            pnlBlendRow.Layout += (s, e) =>
            {
                lblBlendA.Location  = new Point(2, (pnlBlendRow.Height - lblBlendA.Height) / 2);
                lblBlendB.Location  = new Point(pnlBlendRow.Width - lblBlendVal.Width - lblBlendB.Width - 8, (pnlBlendRow.Height - lblBlendB.Height) / 2);
                lblBlendVal.Location= new Point(pnlBlendRow.Width - lblBlendVal.Width - 2,                    (pnlBlendRow.Height - lblBlendVal.Height) / 2);
                trkBlend.SetBounds(lblBlendA.Right + 4, 2, lblBlendB.Left - lblBlendA.Right - 8, 24);
            };
            pnlBlendRow.Controls.AddRange(new Control[] { lblBlendA, trkBlend, lblBlendB, lblBlendVal });

            pnlLogprobRow = new Panel { Name = nameof(pnlLogprobRow), Height = 26, Dock = DockStyle.Top, BackColor = Color.Transparent };
            lblLogprobLabel = new Label { Name = nameof(lblLogprobLabel), Text = "LOGPROB WEIGHTING", ForeColor = VmpTheme.VC_Indigo2, BackColor = Color.Transparent, Font = new Font("Consolas", 7.5f, FontStyle.Bold), AutoSize = true, Location = new Point(0, 5) };
            chkLogprob = new CheckBox  { Name = nameof(chkLogprob), Text = "", Checked = true, ForeColor = VmpTheme.VC_Text, BackColor = Color.Transparent, AutoSize = true };
            pnlLogprobRow.Layout += (s, e) => { chkLogprob.Location = new Point(pnlLogprobRow.Width - chkLogprob.Width - 4, (pnlLogprobRow.Height - chkLogprob.Height) / 2); };
            pnlLogprobRow.Controls.AddRange(new Control[] { lblLogprobLabel, chkLogprob });

            btnTriBattle  = MakeSidebarButton("⚡  Redo Tri-Battle V2",  Color.White, VmpTheme.VC_Indigo, VmpTheme.VC_Indigo);
            btnTriBattle.Name = nameof(btnTriBattle);
            btnClassicMix = MakeSidebarButton("⟳  Redo Classic Mix",    VmpTheme.VC_Text, VmpTheme.VC_Bg3, VmpTheme.VC_Border2);
            btnClassicMix.Name = nameof(btnClassicMix);

            lblStats = new Label
            {
                Name      = nameof(lblStats),
                Text      = "No dataset loaded.",
                ForeColor = VmpTheme.VC_Muted,
                BackColor = Color.Transparent,
                Font      = VmpTheme.FontMono9,
                Dock      = DockStyle.Bottom,
                Height    = 56,
                Padding   = new Padding(14, 6, 6, 6),
            };
            lblStats.Paint += (s, e) => { using var pen = new Pen(VmpTheme.VC_Border); e.Graphics.DrawLine(pen, 0, 0, lblStats.Width, 0); };

            // Add to sidebar in reverse (Dock=Top stacks)
            var sidebarControls = new Control[]
            {
                btnClassicMix, btnTriBattle, pnlLogprobRow, pnlBlendRow, lblBlendLabel,
                lblControlsHead, cboArtistB, lblArtistBLabel, cboArtistA, lblArtistALabel,
                btnLoadRules, btnScanFolder, lblDatasetHead,
            };
            foreach (var c in sidebarControls) pnlSidebar.Controls.Add(c);
            pnlSidebar.Controls.Add(lblStats);

            // ── Workspace ─────────────────────────────────────────────
            pnlWorkBattle = new Panel
            {
                Name      = nameof(pnlWorkBattle),
                Dock      = DockStyle.Fill,
                BackColor = VmpTheme.VC_Bg,
                AutoScroll= true,
                Padding   = new Padding(28, 20, 28, 20),
            };

            // Build 6 verse blocks
            pnlVerse       = new Panel[6];
            pnlVerseHeader = new Panel[6];
            lblVerseNum    = new Label[6];

            for (int v = 5; v >= 0; v--)   // reverse for Dock=Top
            {
                pnlVerse[v] = MakeVerseBlock(v);
                pnlWorkBattle.Controls.Add(pnlVerse[v]);
            }

            // Wire named controls from verse 0 for designer
            if (pnlVerse[0].Controls.Count > 0)
            {
                // These are already built inside MakeVerseBlock
                // assign public refs from verse block 0
                pnlVerseHeader[0] = (Panel)pnlVerse[0].Controls["pnlVerseHeader_0"]!;
                lblVerseNum[0]    = (Label)pnlVerseHeader[0].Controls["lblVerseNum_0"]!;
                pnlLine_0_A1MOD   = (Panel)pnlVerse[0].Controls["pnlLine_0_A1MOD"]!;
                lblLine_0_A1MOD   = (Label)pnlLine_0_A1MOD.Controls["lblLine_0_A1MOD"]!;
            }

            tabBattle.Controls.Add(pnlWorkBattle);
            tabBattle.Controls.Add(pnlSidebar);
        }

        private Panel MakeVerseBlock(int v)
        {
            var block = new Panel
            {
                Name      = $"pnlVerse_{v}",
                Dock      = DockStyle.Top,
                Height    = 210,
                BackColor = VmpTheme.VC_Bg2,
                Margin    = new Padding(0, 0, 0, 20),
            };
            block.Paint += (s, e) =>
            {
                using var pen = new Pen(VmpTheme.VC_Border);
                e.Graphics.DrawRectangle(pen, 0, 0, block.Width - 1, block.Height - 1);
            };

            // Verse header
            var hdr = new Panel { Name = $"pnlVerseHeader_{v}", Dock = DockStyle.Top, Height = 30, BackColor = VmpTheme.VC_Bg3 };
            hdr.Paint += (s, e) => { using var pen = new Pen(VmpTheme.VC_Border); e.Graphics.DrawLine(pen, 0, hdr.Height - 1, hdr.Width, hdr.Height - 1); };
            var numLbl = new Label { Name = $"lblVerseNum_{v}", Text = $"Verse {v + 1}", ForeColor = VmpTheme.VC_Muted, BackColor = Color.Transparent, Font = new Font("Consolas", 7.5f, FontStyle.Bold), AutoSize = true, Location = new Point(14, 8) };
            hdr.Controls.Add(numLbl);
            block.Controls.Add(hdr);

            // 5 line rows per verse: A1-MOD, A2-SIM, A1-ORG, A2-SIM, SYNTH
            var lineDefs = new[]
            {
                ($"pnlLine_{v}_A1MOD",  $"lblLine_{v}_A1MOD",  "A1-MOD",  VmpTheme.VC_Sky,    false),
                ($"pnlLine_{v}_A2SIM1", $"lblLine_{v}_A2SIM1", "A2-SIM",  VmpTheme.VC_Pink,   false),
                ($"pnlLine_{v}_A1ORG",  $"lblLine_{v}_A1ORG",  "A1-ORG",  VmpTheme.VC_Sky,    false),
                ($"pnlLine_{v}_A2SIM2", $"lblLine_{v}_A2SIM2", "A2-SIM",  VmpTheme.VC_Pink,   false),
                ($"pnlLine_{v}_SYNTH",  $"lblLine_{v}_SYNTH",  "SYNTH",   VmpTheme.VC_Green,  true),
            };
            var sampleLines = new[]
            {
                "I'm the CYBER rapper alive.",
                "No one can touch me on the mic.",
                "I'm the fastest rapper alive.",
                "No one can touch me on the mic.",
                "YEAH FASTEST TOUCH ME ALIVE DRIVE",
            };

            // Add in reverse for Dock=Top
            for (int li = lineDefs.Length - 1; li >= 0; li--)
            {
                var (pName, lName, tag, col, isSynth) = lineDefs[li];
                var lineRow = MakeLineRow(pName, lName, tag, col, isSynth, sampleLines[li], v, li);
                block.Controls.Add(lineRow);
            }

            // Public ref for verse 0 named controls
            if (v == 0)
            {
                pnlVerseHeader[0] = hdr;
                lblVerseNum[0]    = numLbl;
            }

            return block;
        }

        private Panel MakeLineRow(string pName, string lName, string tag, Color accentCol, bool isSynth, string sampleText, int v, int li)
        {
            var row = new Panel
            {
                Name      = pName,
                Dock      = DockStyle.Top,
                Height    = 36,
                BackColor = isSynth ? Color.FromArgb(8, 74, 222, 128) : Color.Transparent,
            };
            row.Paint += (s, e) =>
            {
                using var pen = new Pen(VmpTheme.VC_Border);
                e.Graphics.DrawLine(pen, 0, row.Height - 1, row.Width, row.Height - 1);
                // Left accent bar (4px)
                using var accent = new SolidBrush(accentCol);
                e.Graphics.FillRectangle(accent, 0, 0, 4, row.Height);
            };

            // Tag
            var tagLbl = new Label
            {
                Text      = tag,
                ForeColor = accentCol,
                BackColor = Color.Transparent,
                Font      = new Font("Consolas", 7.5f, FontStyle.Bold),
                AutoSize  = true,
                Location  = new Point(10, (36 - 16) / 2),
            };

            // Line text
            var textLbl = new Label
            {
                Name      = lName,
                Text      = sampleText,
                ForeColor = isSynth ? VmpTheme.VC_Green : VmpTheme.VC_Text,
                BackColor = Color.Transparent,
                Font      = isSynth ? new Font("Consolas", 9f, FontStyle.Bold) : VmpTheme.FontMono10,
                AutoSize  = false,
                AutoEllipsis = true,
                Location  = new Point(80, (36 - 16) / 2),
            };

            // Copy button
            var copyBtn = new Button
            {
                Text      = "copy",
                ForeColor = VmpTheme.VC_Muted,
                BackColor = VmpTheme.VC_Bg3,
                FlatStyle = FlatStyle.Flat,
                Font      = new Font("Consolas", 7.5f),
                Size      = new Size(42, 22),
                Cursor    = Cursors.Hand,
            };
            copyBtn.FlatAppearance.BorderColor = VmpTheme.VC_Border;
            copyBtn.FlatAppearance.BorderSize  = 1;

            Button? redoBtn = null;
            if (isSynth)
            {
                redoBtn = new Button
                {
                    Name      = $"btnRedo_{v}",
                    Text      = "redo",
                    ForeColor = VmpTheme.VC_Green,
                    BackColor = VmpTheme.VC_Bg3,
                    FlatStyle = FlatStyle.Flat,
                    Font      = new Font("Consolas", 7.5f),
                    Size      = new Size(42, 22),
                    Cursor    = Cursors.Hand,
                };
                redoBtn.FlatAppearance.BorderColor = VmpTheme.VC_Green;
                redoBtn.FlatAppearance.BorderSize  = 1;
                if (v == 0) btnRedo_0 = redoBtn;
            }

            row.Layout += (s, e) =>
            {
                int btnX = row.Width - copyBtn.Width - 10;
                copyBtn.Location = new Point(btnX, (row.Height - copyBtn.Height) / 2);
                if (redoBtn != null) { redoBtn.Location = new Point(btnX - redoBtn.Width - 6, (row.Height - redoBtn.Height) / 2); btnX = redoBtn.Left; }
                textLbl.SetBounds(80, (row.Height - textLbl.Font.Height) / 2, btnX - 86, 20);
            };

            row.Controls.Add(tagLbl);
            row.Controls.Add(textLbl);
            row.Controls.Add(copyBtn);
            if (redoBtn != null) row.Controls.Add(redoBtn);

            // Assign public refs for verse 0
            if (v == 0)
            {
                switch (li)
                {
                    case 0: pnlLine_0_A1MOD  = row; lblLine_0_A1MOD  = textLbl; break;
                    case 1: pnlLine_0_A2SIM_1= row; lblLine_0_A2SIM_1= textLbl; break;
                    case 2: pnlLine_0_A1ORG  = row; lblLine_0_A1ORG  = textLbl; break;
                    case 3: pnlLine_0_A2SIM_2= row; lblLine_0_A2SIM_2= textLbl; break;
                    case 4: pnlLine_0_SYNTH  = row; lblLine_0_SYNTH  = textLbl; break;
                }
            }
            return row;
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: LINGUISTIC RULES
        // ══════════════════════════════════════════════════════════════
        private void BuildTabRules()
        {
            pnlWorkRules = new Panel { Name = nameof(pnlWorkRules), Dock = DockStyle.Fill, BackColor = VmpTheme.VC_Bg, Padding = new Padding(24, 16, 24, 16) };

            pnlRulesHeader = new Panel { Name = nameof(pnlRulesHeader), Dock = DockStyle.Top, Height = 44, BackColor = Color.Transparent };
            lblRulesTitle  = new Label { Name = nameof(lblRulesTitle), Text = "Linguistic Rules Editor", ForeColor = VmpTheme.VC_Text, BackColor = Color.Transparent, Font = new Font("Segoe UI", 11f, FontStyle.Bold), AutoSize = true, Location = new Point(0, 2) };
            lblRulesHint   = new Label { Name = nameof(lblRulesHint),  Text = "Edit or paste your lexicon_rules.json. Changes apply on next generation.", ForeColor = VmpTheme.VC_Muted, BackColor = Color.Transparent, Font = VmpTheme.FontSans9, AutoSize = true, Location = new Point(0, 26) };
            btnValidateRules = VmpTheme.MakeButton("✓  Validate & Apply", Color.White, VmpTheme.VC_Indigo, VmpTheme.VC_Indigo);
            btnValidateRules.Name = nameof(btnValidateRules); btnValidateRules.Width = 170; btnValidateRules.Height = 30;
            pnlRulesHeader.Layout += (s, e) => btnValidateRules.Location = new Point(pnlRulesHeader.Width - btnValidateRules.Width, 7);
            pnlRulesHeader.Controls.AddRange(new Control[] { lblRulesTitle, lblRulesHint, btnValidateRules });

            lblRulesStatus = new Label { Name = nameof(lblRulesStatus), Text = "✓ Rules valid and applied.", ForeColor = VmpTheme.VC_Green, BackColor = Color.Transparent, Font = VmpTheme.FontMono9, AutoSize = false, Height = 18, Dock = DockStyle.Top };

            rtbRulesEditor = new RichTextBox
            {
                Name        = nameof(rtbRulesEditor),
                Dock        = DockStyle.Fill,
                BackColor   = VmpTheme.VC_Bg2,
                ForeColor   = VmpTheme.VC_Text,
                Font        = VmpTheme.FontMono10,
                BorderStyle = BorderStyle.FixedSingle,
                ScrollBars  = RichTextBoxScrollBars.Vertical,
                Text        = "{\n  \"categories\": {\n    \"fillers\": [\"yo\",\"yeah\",\"uh\"],\n    \"nouns\":   [\"FIXED\",\"CYBER\",\"GHOST\"]\n  },\n  \"rhyme_map\": {\n    \"ay\": [\"say\",\"day\",\"way\"]\n  },\n  \"flow_rules\": {\n    \"line_length\": 8\n  }\n}",
            };

            pnlWorkRules.Controls.Add(rtbRulesEditor);
            pnlWorkRules.Controls.Add(lblRulesStatus);
            pnlWorkRules.Controls.Add(pnlRulesHeader);
            tabRules.Controls.Add(pnlWorkRules);
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: LEXICON VIEWER
        // ══════════════════════════════════════════════════════════════
        private void BuildTabLexicon()
        {
            pnlWorkLexicon = new Panel { Name = nameof(pnlWorkLexicon), Dock = DockStyle.Fill, BackColor = VmpTheme.VC_Bg, Padding = new Padding(24, 16, 24, 16) };

            lblLexTitle = new Label { Name = nameof(lblLexTitle), Text = "Global Lexicon", ForeColor = VmpTheme.VC_Text, BackColor = Color.Transparent, Font = new Font("Segoe UI", 11f, FontStyle.Bold), AutoSize = false, Height = 26, Dock = DockStyle.Top };
            lblLexHint  = new Label { Name = nameof(lblLexHint),  Text = "Word → Whisper token ID.  Amber = stylistically distinctive (low logprob).", ForeColor = VmpTheme.VC_Muted, BackColor = Color.Transparent, Font = VmpTheme.FontSans9, AutoSize = false, Height = 22, Dock = DockStyle.Top };
            lblLexCount = new Label { Name = nameof(lblLexCount), Text = "1,024 entries", ForeColor = VmpTheme.VC_Indigo2, BackColor = Color.Transparent, Font = new Font("Consolas", 8.5f, FontStyle.Bold), AutoSize = false, Height = 18, Dock = DockStyle.Top };

            txtLexFilter = new TextBox
            {
                Name        = nameof(txtLexFilter),
                Dock        = DockStyle.Top,
                Height      = 28,
                BackColor   = VmpTheme.VC_Bg3,
                ForeColor   = VmpTheme.VC_Text,
                Font        = VmpTheme.FontMono10,
                BorderStyle = BorderStyle.FixedSingle,
                PlaceholderText = "Filter words...",
            };

            dgvLexicon = MakeDarkGrid(nameof(dgvLexicon), VmpTheme.VC_Bg2, VmpTheme.VC_Bg3, VmpTheme.VC_Border);
            dgvLexicon.Dock = DockStyle.Fill;
            dgvLexicon.Columns.Add("Num",     "#");
            dgvLexicon.Columns.Add("Word",    "WORD");
            dgvLexicon.Columns.Add("TokenId", "TOKEN ID");
            dgvLexicon.Columns.Add("Logprob", "AVG LOGPROB");
            dgvLexicon.Columns.Add("Phoneme", "PHONEME");
            dgvLexicon.Columns[0].Width = 50;
            dgvLexicon.Columns[1].Width = 120;
            dgvLexicon.Columns[2].Width = 90;
            dgvLexicon.Columns[3].Width = 100;
            dgvLexicon.Columns[4].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill;
            dgvLexicon.Rows.Add("1", "yeah", "9820",  "-0.421", "JEH");
            dgvLexicon.Rows.Add("2", "mic",  "27820", "-0.312", "MK");
            dgvLexicon.Rows.Add("3", "flow", "12200", "-0.189", "FLO");

            pnlWorkLexicon.Controls.Add(dgvLexicon);
            pnlWorkLexicon.Controls.Add(txtLexFilter);
            pnlWorkLexicon.Controls.Add(lblLexCount);
            pnlWorkLexicon.Controls.Add(lblLexHint);
            pnlWorkLexicon.Controls.Add(lblLexTitle);
            tabLexicon.Controls.Add(pnlWorkLexicon);
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: ANALYTICS
        // ══════════════════════════════════════════════════════════════
        private void BuildTabAnalytics()
        {
            pnlWorkAnalytics = new Panel { Name = nameof(pnlWorkAnalytics), Dock = DockStyle.Fill, BackColor = VmpTheme.VC_Bg, AutoScroll = true, Padding = new Padding(24, 16, 24, 16) };
            lblAnalyticsTitle = new Label { Name = nameof(lblAnalyticsTitle), Text = "Dataset Analytics", ForeColor = VmpTheme.VC_Text, BackColor = Color.Transparent, Font = new Font("Segoe UI", 11f, FontStyle.Bold), AutoSize = false, Height = 28, Dock = DockStyle.Top };

            // Stat cards
            pnlAnalyticsStats = new Panel { Name = nameof(pnlAnalyticsStats), Height = 72, Dock = DockStyle.Top, BackColor = Color.Transparent };
            cardVocabA     = MakeVcCard("1,248", "Artist A vocab",    VmpTheme.VC_Sky);
            cardVocabB     = MakeVcCard("984",   "Artist B vocab",    VmpTheme.VC_Pink);
            cardOverlap    = MakeVcCard("42%",   "Vocab overlap",     VmpTheme.VC_Green);
            cardDivergence = MakeVcCard("71",    "Style divergence",  VmpTheme.VC_Indigo2);
            cardVocabA.Name = nameof(cardVocabA); cardVocabB.Name = nameof(cardVocabB);
            cardOverlap.Name = nameof(cardOverlap); cardDivergence.Name = nameof(cardDivergence);
            pnlAnalyticsStats.Layout += (s, e) =>
            {
                int w = (pnlAnalyticsStats.Width - 3 * 8) / 4;
                var cards = new[] { cardVocabA, cardVocabB, cardOverlap, cardDivergence };
                for (int i = 0; i < 4; i++) cards[i].SetBounds(i * (w + 8), 0, w, pnlAnalyticsStats.Height - 8);
            };
            pnlAnalyticsStats.Controls.AddRange(new Control[] { cardVocabA, cardVocabB, cardOverlap, cardDivergence });

            // Logprob bars
            lblLogprobHead = SectionLabel("Avg logprob (stylistic fingerprint)", VmpTheme.VC_Muted);
            lblLogprobHead.Name = nameof(lblLogprobHead);
            pnlLogprobBars = MakeBarSection(out lblLpArtistA, out pnlLpBarA, out pnlLpFillA, out lblLpValA, "Artist A", VmpTheme.VC_Sky, 65, "-0.28",
                                            out lblLpArtistB, out pnlLpBarB, out pnlLpFillB, out lblLpValB, "Artist B", VmpTheme.VC_Pink, 45, "-0.19");
            pnlLogprobBars.Name = nameof(pnlLogprobBars);

            // Rhyme density
            lblRhymeHead = SectionLabel("Rhyme density (end-rhyme pairs / 100 lines)", VmpTheme.VC_Muted);
            lblRhymeHead.Name = nameof(lblRhymeHead);
            pnlRhymeBars = MakeBarSection(out lblRhymeA, out pnlRhymeBarA, out pnlRhymeFillA, out lblRhymeValA, "Artist A", VmpTheme.VC_Sky,  72, "72%",
                                          out lblRhymeB, out pnlRhymeBarB, out pnlRhymeFillB, out lblRhymeValB, "Artist B", VmpTheme.VC_Pink, 48, "48%");
            pnlRhymeBars.Name = nameof(pnlRhymeBars);

            // Distinctive words
            lblDistinctHead = SectionLabel("Most distinctive words (lowest avg logprob)", VmpTheme.VC_Muted);
            lblDistinctHead.Name = nameof(lblDistinctHead);
            flpDistinctWords = new FlowLayoutPanel
            {
                Name        = nameof(flpDistinctWords),
                Dock        = DockStyle.Top,
                Height      = 52,
                BackColor   = Color.Transparent,
                FlowDirection = FlowDirection.LeftToRight,
                WrapContents= true,
                AutoSize    = false,
            };
            foreach (var word in new[] { "yeah", "mic", "flow", "trap", "hustle", "vibe", "slay", "lit", "drip", "flex" })
            {
                var badge = new Label
                {
                    Text        = word,
                    ForeColor   = VmpTheme.VC_Warn,
                    BackColor   = VmpTheme.VC_Bg3,
                    Font        = VmpTheme.FontMono9,
                    AutoSize    = true,
                    Padding     = new Padding(6, 2, 6, 2),
                    Margin      = new Padding(0, 0, 4, 4),
                    BorderStyle = BorderStyle.FixedSingle,
                };
                flpDistinctWords.Controls.Add(badge);
            }

            var controls = new Control[] { lblAnalyticsTitle, pnlAnalyticsStats, lblLogprobHead, pnlLogprobBars, lblRhymeHead, pnlRhymeBars, lblDistinctHead, flpDistinctWords };
            for (int i = controls.Length - 1; i >= 0; i--) pnlWorkAnalytics.Controls.Add(controls[i]);
            tabAnalytics.Controls.Add(pnlWorkAnalytics);
        }

        // ══════════════════════════════════════════════════════════════
        //  TAB: SAVED SESSIONS
        // ══════════════════════════════════════════════════════════════
        private void BuildTabSaved()
        {
            pnlWorkSaved = new Panel { Name = nameof(pnlWorkSaved), Dock = DockStyle.Fill, BackColor = VmpTheme.VC_Bg, Padding = new Padding(24, 16, 24, 16) };
            lblSavedTitle = new Label { Name = nameof(lblSavedTitle), Text = "Saved Sessions", ForeColor = VmpTheme.VC_Text, BackColor = Color.Transparent, Font = new Font("Segoe UI", 11f, FontStyle.Bold), AutoSize = false, Height = 28, Dock = DockStyle.Top };
            pnlSavedList  = new Panel { Name = nameof(pnlSavedList),  Dock = DockStyle.Fill,  BackColor = Color.Transparent };

            // 3 sample rows
            var sampleSessions = new[] { ("Battle_10:24:30", "12/03/2026  ·  30 lines"), ("Battle_11:05:12", "12/03/2026  ·  30 lines"), ("Classic_Mix_1", "11/03/2026  ·  8 lines") };
            for (int i = sampleSessions.Length - 1; i >= 0; i--)
            {
                var (name, meta) = sampleSessions[i];
                var row = MakeSavedRow(i, name, meta);
                pnlSavedList.Controls.Add(row);
                if (i == 0) { pnlSavedRow0 = row; lblSavedName0 = (Label)row.Controls[$"lblSavedName_{i}"]!; lblSavedMeta0 = (Label)row.Controls[$"lblSavedMeta_{i}"]!; btnSavedLoad0 = (Button)row.Controls[$"btnSavedLoad_{i}"]!; btnSavedDel0 = (Button)row.Controls[$"btnSavedDel_{i}"]!; }
            }

            pnlWorkSaved.Controls.Add(pnlSavedList);
            pnlWorkSaved.Controls.Add(lblSavedTitle);
            tabSaved.Controls.Add(pnlWorkSaved);
        }

        private Panel MakeSavedRow(int i, string name, string meta)
        {
            var row = new Panel { Name = $"pnlSavedRow_{i}", Dock = DockStyle.Top, Height = 52, BackColor = VmpTheme.VC_Bg2, Margin = new Padding(0, 0, 0, 6) };
            row.Paint += (s, e) => { using var pen = new Pen(VmpTheme.VC_Border); e.Graphics.DrawRectangle(pen, 0, 0, row.Width - 1, row.Height - 1); };
            var nameLbl = new Label { Name = $"lblSavedName_{i}", Text = name, ForeColor = VmpTheme.VC_Text, BackColor = Color.Transparent, Font = new Font("Segoe UI", 10f, FontStyle.Bold), AutoSize = true, Location = new Point(14, 10) };
            var metaLbl = new Label { Name = $"lblSavedMeta_{i}", Text = meta, ForeColor = VmpTheme.VC_Muted, BackColor = Color.Transparent, Font = VmpTheme.FontMono9, AutoSize = true, Location = new Point(14, 30) };
            var loadBtn = VmpTheme.MakeButton("load", VmpTheme.VC_Text, VmpTheme.VC_Bg3, VmpTheme.VC_Border2);
            loadBtn.Name = $"btnSavedLoad_{i}"; loadBtn.Width = 60; loadBtn.Height = 26; loadBtn.Font = new Font("Consolas", 8f);
            var delBtn  = VmpTheme.MakeButton("del", VmpTheme.VC_Err, VmpTheme.VC_Bg3, VmpTheme.VC_Err);
            delBtn.Name = $"btnSavedDel_{i}";  delBtn.Width  = 50; delBtn.Height = 26; delBtn.Font = new Font("Consolas", 8f);
            row.Layout += (s, e) =>
            {
                delBtn.Location  = new Point(row.Width - delBtn.Width  - 10, (row.Height - delBtn.Height)  / 2);
                loadBtn.Location = new Point(delBtn.Left  - loadBtn.Width - 6, (row.Height - loadBtn.Height) / 2);
            };
            row.Controls.AddRange(new Control[] { nameLbl, metaLbl, loadBtn, delBtn });
            return row;
        }

        // ══════════════════════════════════════════════════════════════
        //  HELPERS
        // ══════════════════════════════════════════════════════════════
        private static TabPage MakeTabPage(string text, string name)
            => new TabPage { Text = text, Name = name, BackColor = VmpTheme.VC_Bg, ForeColor = VmpTheme.VC_Text, Padding = new Padding(0) };

        private static Label SidebarSectionHead(string text)
            => new Label
            {
                Text      = text.ToUpper(),
                ForeColor = VmpTheme.VC_Muted,
                BackColor = VmpTheme.VC_Bg2,
                Font      = new Font("Consolas", 7.5f, FontStyle.Bold),
                AutoSize  = false, Height = 30,
                Dock      = DockStyle.Top,
                Padding   = new Padding(14, 9, 0, 0),
            };

        private static Label SidebarFieldLabel(string text)
            => new Label
            {
                Text      = text,
                ForeColor = VmpTheme.VC_Muted,
                BackColor = Color.Transparent,
                Font      = new Font("Consolas", 7.5f, FontStyle.Bold),
                AutoSize  = false, Height = 16, Dock = DockStyle.Top,
                Padding   = new Padding(14, 0, 0, 0),
            };

        private static Button MakeSidebarButton(string text, Color fg, Color bg, Color border)
        {
            var b = VmpTheme.MakeButton(text, fg, bg, border);
            b.Dock = DockStyle.Top; b.Height = 32; b.Margin = new Padding(10, 0, 10, 6);
            return b;
        }

        private static ComboBox MakeSidebarCombo()
        {
            var c = VmpTheme.MakeComboBox(VmpTheme.VC_Bg3, VmpTheme.VC_Text);
            c.Dock = DockStyle.Top; c.Margin = new Padding(10, 0, 10, 8);
            return c;
        }

        private static Button MakeHdrButton(string text, Color fg, Color bg)
        {
            var b = new Button { Text = text, ForeColor = fg, BackColor = bg, FlatStyle = FlatStyle.Flat, Font = new Font("Consolas", 8f, FontStyle.Bold), Width = 130, Height = 30, Cursor = Cursors.Hand };
            b.FlatAppearance.BorderColor = fg;
            b.FlatAppearance.BorderSize  = 1;
            return b;
        }

        private static Label SectionLabel(string text, Color fg)
            => new Label { Text = text, ForeColor = fg, BackColor = Color.Transparent, Font = new Font("Consolas", 8f, FontStyle.Bold), AutoSize = false, Height = 26, Dock = DockStyle.Top, Padding = new Padding(0, 10, 0, 2) };

        private static Panel MakeVcCard(string value, string caption, Color accentCol)
        {
            var card = new Panel { BackColor = VmpTheme.VC_Bg3, Margin = new Padding(0, 0, 8, 0) };
            card.Paint += (s, e) => { using var pen = new Pen(VmpTheme.VC_Border); e.Graphics.DrawRectangle(pen, 0, 0, card.Width - 1, card.Height - 1); };
            var val = new Label { Text = value, ForeColor = accentCol, BackColor = Color.Transparent, Font = new Font("Consolas", 14f, FontStyle.Bold), AutoSize = true, Location = new Point(12, 8) };
            var cap = new Label { Text = caption.ToUpper(), ForeColor = VmpTheme.VC_Muted, BackColor = Color.Transparent, Font = new Font("Consolas", 7.5f, FontStyle.Bold), AutoSize = true, Location = new Point(12, 38) };
            card.Controls.AddRange(new Control[] { val, cap });
            return (card);
        }

        private static Panel MakeBarSection(
            out Label lblA, out Panel barA, out Panel fillA, out Label valA, string nameA, Color colA, int pctA, string txtA,
            out Label lblB, out Panel barB, out Panel fillB, out Label valB, string nameB, Color colB, int pctB, string txtB)
        {
            var section = new Panel { Height = 60, Dock = DockStyle.Top, BackColor = Color.Transparent };

            (lblA, barA, fillA, valA) = MakeBar(nameA, colA, pctA, txtA, 0);
            (lblB, barB, fillB, valB) = MakeBar(nameB, colB, pctB, txtB, 26);

            section.Controls.AddRange(new Control[] { lblA, barA, valA, lblB, barB, valB });
            return section;
        }

        private static (Label lbl, Panel bar, Panel fill, Label val) MakeBar(string name, Color col, int pct, string txt, int y)
        {
            var lbl  = new Label { Text = name, ForeColor = col, BackColor = Color.Transparent, Font = new Font("Consolas", 8f, FontStyle.Bold), Size = new Size(70, 20), Location = new Point(0, y + 3) };
            var bar  = new Panel { BackColor = Color.FromArgb(0x0A, 0x0F, 0x1E), Location = new Point(76, y + 6), Height = 8 };
            var fill = new Panel { BackColor = col, Dock = DockStyle.Left, Width = pct };
            bar.Controls.Add(fill);
            var val  = new Label { Text = txt, ForeColor = VmpTheme.VC_Muted, BackColor = Color.Transparent, Font = VmpTheme.FontMono9, AutoSize = true, Location = new Point(0, y + 3) };
            bar.Layout += (s, e) => { fill.Width = (int)(bar.Width * pct / 100f); val.Location = new Point(bar.Right + 6, y + 3); };
            return (lbl, bar, fill, val);
        }

        private static DataGridView MakeDarkGrid(string name, Color bg, Color altBg, Color border)
        {
            var dgv = new DataGridView
            {
                Name                   = name,
                Dock                   = DockStyle.Fill,
                BackgroundColor        = bg,
                ForeColor              = VmpTheme.VC_Text,
                GridColor              = border,
                BorderStyle            = BorderStyle.FixedSingle,
                Font                   = VmpTheme.FontMono10,
                RowHeadersVisible      = false,
                AllowUserToAddRows     = false,
                AllowUserToResizeRows  = false,
                AllowUserToDeleteRows  = false,
                ReadOnly               = true,
                SelectionMode          = DataGridViewSelectionMode.FullRowSelect,
                MultiSelect            = false,
                ColumnHeadersHeight    = 26,
                RowTemplate            = { Height = 24 },
                AutoSizeColumnsMode    = DataGridViewAutoSizeColumnsMode.None,
            };
            dgv.ColumnHeadersDefaultCellStyle.BackColor = altBg;
            dgv.ColumnHeadersDefaultCellStyle.ForeColor = VmpTheme.VC_Muted;
            dgv.ColumnHeadersDefaultCellStyle.Font      = new Font("Consolas", 7.5f, FontStyle.Bold);
            dgv.DefaultCellStyle.BackColor              = bg;
            dgv.DefaultCellStyle.ForeColor              = VmpTheme.VC_Text;
            dgv.DefaultCellStyle.SelectionBackColor     = altBg;
            dgv.DefaultCellStyle.SelectionForeColor     = VmpTheme.VC_Sky;
            dgv.AlternatingRowsDefaultCellStyle.BackColor = altBg;
            dgv.EnableHeadersVisualStyles               = false;
            return dgv;
        }
    }
}
