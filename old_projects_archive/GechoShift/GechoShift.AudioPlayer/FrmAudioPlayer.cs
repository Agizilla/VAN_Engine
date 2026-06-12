using System;
using System.Drawing;
using System.Windows.Forms;
using LibVLCSharp.WinForms;

namespace GechoShift.AudioPlayer
{
    // ════════════════════════════════════════════════════════════════════
    // FrmAudioPlayer  —  Main host window
    //
    //   Layout (top → bottom):
    //     pnlHeader          44px   logo + status badge
    //     pnlVideoSurface    240px  LibVLCSharp VideoView (black)
    //     pnlTransport       56px   Open · Play/Pause · Stop · pos slider
    //     pnlMorphControls   110px  Pitch / Formant / Grit / Breath knobs
    //     pnlBottom          40px   Extract Beat · Extract Vocals · Apply Morph
    //                               + links to Config Studio & VoiceCentroid
    //     pnlStatus          24px   status / log strip
    //
    //   NO LOGIC — all controls public and named for wiring up later.
    // ════════════════════════════════════════════════════════════════════
    public sealed class FrmAudioPlayer : Form
    {
        // ── Header ─────────────────────────────────────────────────────
        public Panel   pnlHeader           = null!;
        public Label   lblLogo             = null!;
        public Label   lblVersion          = null!;
        public Label   lblStatusBadge      = null!;

        // ── Video surface ───────────────────────────────────────────────
        public Panel   pnlVideoSurface     = null!;
        public VideoView videoView         = null!;

        // ── Transport ───────────────────────────────────────────────────
        public Panel   pnlTransport        = null!;
        public Button  btnOpen             = null!;
        public Button  btnPlayPause        = null!;
        public Button  btnStop             = null!;
        public TrackBar trkPosition        = null!;
        public Label   lblPosition         = null!;
        public Label   lblDuration         = null!;
        public TrackBar trkVolume          = null!;
        public Label   lblVolumeIcon       = null!;

        // ── Morph controls ──────────────────────────────────────────────
        public Panel   pnlMorphControls    = null!;
        public Label   lblMorphHead        = null!;
        // Pitch
        public Panel   pnlPitchCard        = null!;
        public Label   lblPitchCaption     = null!;
        public Label   lblPitchVal         = null!;
        public TrackBar trkPitch           = null!;
        // Formant
        public Panel   pnlFormantCard      = null!;
        public Label   lblFormantCaption   = null!;
        public Label   lblFormantVal       = null!;
        public TrackBar trkFormant         = null!;
        // Grit
        public Panel   pnlGritCard         = null!;
        public Label   lblGritCaption      = null!;
        public Label   lblGritVal          = null!;
        public TrackBar trkGrit            = null!;
        // Breath
        public Panel   pnlBreathCard       = null!;
        public Label   lblBreathCaption    = null!;
        public Label   lblBreathVal        = null!;
        public TrackBar trkBreath          = null!;
        // Native bridge toggle
        public CheckBox chkNativeBridge    = null!;
        public Label    lblBridgeStatus    = null!;

        // ── Plugin action buttons ───────────────────────────────────────
        public Panel   pnlBottom           = null!;
        public Button  btnExtractBeat      = null!;
        public Button  btnExtractVocals    = null!;
        public Button  btnApplyMorph       = null!;
        public Button  btnOpenConfigStudio = null!;
        public Button  btnOpenVoiceCentroid= null!;

        // ── Status strip ────────────────────────────────────────────────
        public Panel   pnlStatus           = null!;
        public Label   lblStatusText       = null!;
        public Label   lblTempDir          = null!;

        // ════════════════════════════════════════════════════════════════
        public FrmAudioPlayer()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
           // SuspendLayout();

            // ── Form ─────────────────────────────────────────────────
            Text          = "GechoShift — Audio Player";
            Size          = new Size(960, 640);
            MinimumSize   = new Size(760, 520);
            BackColor     = VmpTheme.CS_Bg0;
            ForeColor     = VmpTheme.CS_Text;
            Font          = VmpTheme.FontSans10;
            StartPosition = FormStartPosition.CenterScreen;

            // ── Status strip ─────────────────────────────────────────
            pnlStatus = new Panel
            {
                Name      = nameof(pnlStatus),
                Dock      = DockStyle.Bottom,
                Height    = 24,
                BackColor = VmpTheme.CS_Bg1,
                Padding   = new Padding(10, 0, 10, 0),
            };
            pnlStatus.Paint += PaintTopBorder(VmpTheme.CS_Border);

            lblStatusText = new Label
            {
                Name      = nameof(lblStatusText),
                Text      = "Ready.",
                ForeColor = VmpTheme.CS_Dim,
                BackColor = Color.Transparent,
                Font      = VmpTheme.FontMono9,
                AutoSize  = true,
                Location  = new Point(10, 4),
            };
            lblTempDir = new Label
            {
                Name        = nameof(lblTempDir),
                Text        = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "VlcMorphPlugin"),
                ForeColor   = VmpTheme.CS_Muted,
                BackColor   = Color.Transparent,
                Font        = VmpTheme.FontMono9,
                AutoSize    = true,
                TextAlign   = ContentAlignment.MiddleRight,
            };
            pnlStatus.Controls.AddRange(new Control[] { lblStatusText, lblTempDir });
            pnlStatus.Layout += (s, e) =>
            {
                lblTempDir.Location = new Point(pnlStatus.Width - lblTempDir.Width - 10, 4);
            };

            // ── Bottom action bar ─────────────────────────────────────
            pnlBottom = new Panel
            {
                Name      = nameof(pnlBottom),
                Dock      = DockStyle.Bottom,
                Height    = 46,
                BackColor = VmpTheme.CS_Bg1,
                Padding   = new Padding(12, 7, 12, 7),
            };
            pnlBottom.Paint += PaintTopBorder(VmpTheme.CS_Border);

            btnExtractBeat = MakeActionButton("⊗  Extract Beat",       VmpTheme.CS_Blue,   VmpTheme.CS_Bg3);
            btnExtractBeat.Name = nameof(btnExtractBeat);
            btnExtractVocals = MakeActionButton("⊗  Extract Vocals",   VmpTheme.CS_Cyan,   VmpTheme.CS_Bg3);
            btnExtractVocals.Name = nameof(btnExtractVocals);
            btnApplyMorph = MakeActionButton("⚡  Apply Morph",          VmpTheme.CS_Bg0,    VmpTheme.CS_Copper);
            btnApplyMorph.Name = nameof(btnApplyMorph);

            // Separator
            var sep = new Panel { Width = 1, Dock = DockStyle.Left, BackColor = VmpTheme.CS_Border, Margin = new Padding(8, 0, 8, 0) };

            btnOpenConfigStudio = MakeActionButton("▣  Config Studio",   VmpTheme.CS_Copper, VmpTheme.CS_Bg3);
            btnOpenConfigStudio.Name = nameof(btnOpenConfigStudio);
            btnOpenConfigStudio.Click += (s, e) => new FrmConfigStudio().Show();

            btnOpenVoiceCentroid = MakeActionButton("⚔  VoiceCentroid",  VmpTheme.VC_Indigo2, VmpTheme.CS_Bg3);
            btnOpenVoiceCentroid.Name = nameof(btnOpenVoiceCentroid);
            btnOpenVoiceCentroid.Click += (s, e) => new FrmVoiceCentroid().Show();

            pnlBottom.Controls.AddRange(new Control[]
            {
                btnExtractBeat, btnExtractVocals, btnApplyMorph,
                sep,
                btnOpenConfigStudio, btnOpenVoiceCentroid,
            });
            foreach (Control c in pnlBottom.Controls)
            {
                c.Dock = DockStyle.Left;
                if (c is Button b) b.Margin = new Padding(0, 0, 6, 0);
            }

            // ── Morph controls panel ──────────────────────────────────
            pnlMorphControls = new Panel
            {
                Name      = nameof(pnlMorphControls),
                Dock      = DockStyle.Bottom,
                Height    = 116,
                BackColor = VmpTheme.CS_Bg1,
                Padding   = new Padding(12, 8, 12, 8),
            };
            pnlMorphControls.Paint += PaintTopBorder(VmpTheme.CS_Border);

            lblMorphHead = new Label
            {
                Name      = nameof(lblMorphHead),
                Text      = "DSP MORPH",
                ForeColor = VmpTheme.CS_Copper,
                BackColor = Color.Transparent,
                Font      = new Font("Consolas", 7.5f, FontStyle.Bold),
                AutoSize  = true,
                Location  = new Point(12, 6),
            };

            // 4 knob cards
            (pnlPitchCard,   lblPitchCaption,   lblPitchVal,   trkPitch)   = MakeKnobCard("PITCH",   50,  200, 100, "1.00");
            (pnlFormantCard, lblFormantCaption, lblFormantVal, trkFormant) = MakeKnobCard("FORMANT", 80,  150, 100, "1.00");
            (pnlGritCard,    lblGritCaption,    lblGritVal,    trkGrit)    = MakeKnobCard("GRIT",    0,   100, 0,   "0.00");
            (pnlBreathCard,  lblBreathCaption,  lblBreathVal,  trkBreath)  = MakeKnobCard("BREATH",  0,   100, 0,   "0.00");
            pnlPitchCard.Name  = nameof(pnlPitchCard);
            pnlFormantCard.Name= nameof(pnlFormantCard);
            pnlGritCard.Name   = nameof(pnlGritCard);
            pnlBreathCard.Name = nameof(pnlBreathCard);

            chkNativeBridge = new CheckBox
            {
                Name      = nameof(chkNativeBridge),
                Text      = "Native bridge",
                ForeColor = VmpTheme.CS_Text,
                BackColor = Color.Transparent,
                Font      = VmpTheme.FontMono9,
                AutoSize  = true,
                Checked   = true,
            };
            lblBridgeStatus = new Label
            {
                Name      = nameof(lblBridgeStatus),
                Text      = "not probed",
                ForeColor = VmpTheme.CS_Muted,
                BackColor = Color.Transparent,
                Font      = VmpTheme.FontMono9,
                AutoSize  = true,
            };

            pnlMorphControls.Controls.AddRange(new Control[]
            {
                lblMorphHead,
                pnlPitchCard, pnlFormantCard, pnlGritCard, pnlBreathCard,
                chkNativeBridge, lblBridgeStatus,
            });
            pnlMorphControls.Layout += (s, e) =>
            {
                var cardW = (pnlMorphControls.Width - 24 - 3 * 8 - 130) / 4;
                var cardH = pnlMorphControls.Height - 28;
                var cards = new Panel[] { pnlPitchCard, pnlFormantCard, pnlGritCard, pnlBreathCard };
                for (int i = 0; i < 4; i++)
                    cards[i].SetBounds(12 + i * (cardW + 8), 22, cardW, cardH);
                int bridgeX = pnlPitchCard.Right + 4 * (cardW + 8) + 8;
                chkNativeBridge.Location  = new Point(bridgeX, 28);
                lblBridgeStatus.Location  = new Point(bridgeX, 50);
                foreach (var card in cards)
                    foreach (Control c in card.Controls)
                        if (c is TrackBar t) t.Width = card.Width - 10;
            };

            // ── Transport ─────────────────────────────────────────────
            pnlTransport = new Panel
            {
                Name      = nameof(pnlTransport),
                Dock      = DockStyle.Bottom,
                Height    = 52,
                BackColor = VmpTheme.CS_Bg1,
                Padding   = new Padding(12, 0, 12, 0),
            };
            pnlTransport.Paint += PaintTopBorder(VmpTheme.CS_Border);

            btnOpen = MakeTransportButton("▶ Open", VmpTheme.CS_Text, VmpTheme.CS_Bg3);
            btnOpen.Name = nameof(btnOpen); btnOpen.Width = 70;

            btnPlayPause = MakeTransportButton("▶ Play", Color.Black, VmpTheme.CS_Copper);
            btnPlayPause.Name = nameof(btnPlayPause); btnPlayPause.Width = 80;

            btnStop = MakeTransportButton("■ Stop", VmpTheme.CS_Text, VmpTheme.CS_Bg3);
            btnStop.Name = nameof(btnStop); btnStop.Width = 70;

            lblPosition = new Label { Name = nameof(lblPosition), Text = "0:00", ForeColor = VmpTheme.CS_Text, BackColor = Color.Transparent, Font = VmpTheme.FontMonoBold10, AutoSize = true };
            lblDuration = new Label { Name = nameof(lblDuration), Text = "0:00", ForeColor = VmpTheme.CS_Muted, BackColor = Color.Transparent, Font = VmpTheme.FontMono10, AutoSize = true };

            trkPosition = new TrackBar
            {
                Name      = nameof(trkPosition),
                Minimum   = 0,
                Maximum   = 1000,
                Value     = 0,
                TickStyle = TickStyle.None,
                BackColor = VmpTheme.CS_Bg1,
                Height    = 22,
            };

            lblVolumeIcon = new Label { Name = nameof(lblVolumeIcon), Text = "♪", ForeColor = VmpTheme.CS_Dim, BackColor = Color.Transparent, Font = new Font("Segoe UI", 11f), AutoSize = true };

            trkVolume = new TrackBar
            {
                Name      = nameof(trkVolume),
                Minimum   = 0,
                Maximum   = 100,
                Value     = 80,
                TickStyle = TickStyle.None,
                BackColor = VmpTheme.CS_Bg1,
                Width     = 90,
                Height    = 22,
            };

            pnlTransport.Controls.AddRange(new Control[]
            {
                btnOpen, btnPlayPause, btnStop,
                lblPosition, trkPosition, lblDuration,
                lblVolumeIcon, trkVolume,
            });
            pnlTransport.Layout += (s, e) =>
            {
                var cy = (pnlTransport.Height - 30) / 2;
                int x  = 12;

                void Place(Control c, int w = -1)
                {
                    c.Width    = w > 0 ? w : c.Width;
                    c.Location = new Point(x, (pnlTransport.Height - c.Height) / 2);
                    x += c.Width + 6;
                }

                Place(btnOpen);
                Place(btnPlayPause);
                Place(btnStop);
                x += 6;
                Place(lblPosition);
                int sliderEnd = pnlTransport.Width - 12 - trkVolume.Width - lblVolumeIcon.Width - lblDuration.Width - 20;
                trkPosition.SetBounds(x, cy, sliderEnd - x, 22);
                x = sliderEnd + 4;
                Place(lblDuration);
                x += 8;
                Place(lblVolumeIcon);
                Place(trkVolume, 90);
            };

            // ── Video surface ─────────────────────────────────────────
            pnlVideoSurface = new Panel
            {
                Name      = nameof(pnlVideoSurface),
                Dock      = DockStyle.Fill,
                BackColor = Color.Black,
            };

            videoView = new VideoView
            {
                Name      = nameof(videoView),
                Dock      = DockStyle.Fill,
                BackColor = Color.Black,
            };
            pnlVideoSurface.Controls.Add(videoView);

            // ── Header ────────────────────────────────────────────────
            pnlHeader = new Panel
            {
                Name      = nameof(pnlHeader),
                Dock      = DockStyle.Top,
                Height    = 44,
                BackColor = VmpTheme.CS_Bg1,
                Padding   = new Padding(14, 0, 14, 0),
            };
            pnlHeader.Paint += (s, e) =>
            {
                using var pen = new Pen(VmpTheme.CS_Border);
                e.Graphics.DrawLine(pen, 0, pnlHeader.Height - 1, pnlHeader.Width, pnlHeader.Height - 1);
            };

            lblLogo = new Label
            {
                Name      = nameof(lblLogo),
                Text      = "● GECHOSHIFT  AUDIO PLAYER",
                ForeColor = VmpTheme.CS_Copper,
                BackColor = Color.Transparent,
                Font      = new Font("Consolas", 10f, FontStyle.Bold),
                AutoSize  = true,
            };
            lblVersion = new Label
            {
                Name      = nameof(lblVersion),
                Text      = "v0.1-layout",
                ForeColor = VmpTheme.CS_Muted,
                BackColor = Color.Transparent,
                Font      = VmpTheme.FontMono9,
                AutoSize  = true,
            };
            lblStatusBadge = new Label
            {
                Name        = nameof(lblStatusBadge),
                Text        = "STOPPED",
                ForeColor   = VmpTheme.CS_Muted,
                BackColor   = VmpTheme.CS_Bg3,
                Font        = new Font("Consolas", 7.5f, FontStyle.Bold),
                AutoSize    = true,
                Padding     = new Padding(7, 3, 7, 3),
                BorderStyle = BorderStyle.FixedSingle,
            };
            pnlHeader.Controls.AddRange(new Control[] { lblLogo, lblVersion, lblStatusBadge });
            pnlHeader.Layout += (s, e) =>
            {
                lblLogo.Location       = new Point(14, (pnlHeader.Height - lblLogo.Height) / 2);
                lblVersion.Location    = new Point(lblLogo.Right + 8, (pnlHeader.Height - lblVersion.Height) / 2 + 2);
                lblStatusBadge.Location= new Point(pnlHeader.Width - lblStatusBadge.Width - 14,
                                                    (pnlHeader.Height - lblStatusBadge.Height) / 2);
            };

            // ── Assemble ──────────────────────────────────────────────
            Controls.Add(pnlVideoSurface);
            Controls.Add(pnlTransport);
            Controls.Add(pnlMorphControls);
            Controls.Add(pnlBottom);
            Controls.Add(pnlStatus);
            Controls.Add(pnlHeader);

            ResumeLayout(false);
            PerformLayout();
        }

        // ── Helpers ───────────────────────────────────────────────────
        private static Button MakeActionButton(string text, Color fg, Color bg)
        {
            var b = VmpTheme.MakeButton(text, fg, bg, fg);
            b.Height = 30;
            b.Font   = new Font("Consolas", 8f, FontStyle.Bold);
            return b;
        }

        private static Button MakeTransportButton(string text, Color fg, Color bg)
        {
            var b = VmpTheme.MakeButton(text, fg, bg, VmpTheme.CS_Border2);
            b.Height = 30;
            b.Font   = new Font("Consolas", 8.5f, FontStyle.Bold);
            return b;
        }

        private static (Panel card, Label caption, Label val, TrackBar trk)
            MakeKnobCard(string label, int min, int max, int def, string display)
        {
            var card = new Panel { BackColor = VmpTheme.CS_Bg2 };
            card.Paint += (s, e) =>
            {
                using var pen = new Pen(VmpTheme.CS_Border);
                e.Graphics.DrawRectangle(pen, 0, 0, card.Width - 1, card.Height - 1);
            };
            var cap = new Label { Text = label, ForeColor = VmpTheme.CS_Muted, BackColor = Color.Transparent, Font = new Font("Consolas", 7.5f, FontStyle.Bold), AutoSize = true, Location = new Point(8, 6) };
            var val = new Label { Text = display, ForeColor = VmpTheme.CS_Copper, BackColor = Color.Transparent, Font = new Font("Consolas", 12f, FontStyle.Bold), AutoSize = true, Location = new Point(8, 20) };
            var trk = VmpTheme.MakeTrackBar(min, max, def);
            trk.Location = new Point(5, 50);
            card.Controls.AddRange(new Control[] { cap, val, trk });
            return (card, cap, val, trk);
        }

        // Paints a 1px top border on the panel
        private static PaintEventHandler PaintTopBorder(Color col) =>
            (s, e) =>
            {
                if (s is not Control c) return;
                using var pen = new Pen(col);
                e.Graphics.DrawLine(pen, 0, 0, c.Width, 0);
            };
    }
}
