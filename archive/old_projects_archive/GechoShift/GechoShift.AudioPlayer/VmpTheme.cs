using System.Drawing;
using System.Windows.Forms;

namespace GechoShift.AudioPlayer
{
    // ════════════════════════════════════════════════════════════════════
    // VmpTheme  —  shared colour + font constants for both layout forms.
    //   ConfigStudio  →  CS_*  palette  (graphite / copper / cyan)
    //   VoiceCentroid →  VC_*  palette  (navy / indigo / sky / pink)
    // ════════════════════════════════════════════════════════════════════
    public static class VmpTheme
    {
        // ── Config Studio palette ─────────────────────────────────────
        public static readonly Color CS_Bg0     = Color.FromArgb(0x0D, 0x0E, 0x10);
        public static readonly Color CS_Bg1     = Color.FromArgb(0x13, 0x15, 0x1A);
        public static readonly Color CS_Bg2     = Color.FromArgb(0x1A, 0x1D, 0x24);
        public static readonly Color CS_Bg3     = Color.FromArgb(0x22, 0x26, 0x2F);
        public static readonly Color CS_Border  = Color.FromArgb(0x2E, 0x33, 0x40);
        public static readonly Color CS_Border2 = Color.FromArgb(0x3A, 0x40, 0x50);
        public static readonly Color CS_Muted   = Color.FromArgb(0x55, 0x5E, 0x70);
        public static readonly Color CS_Dim     = Color.FromArgb(0x7A, 0x85, 0x99);
        public static readonly Color CS_Text    = Color.FromArgb(0xC8, 0xD0, 0xE0);
        public static readonly Color CS_Bright  = Color.FromArgb(0xE8, 0xED, 0xF8);
        public static readonly Color CS_Copper  = Color.FromArgb(0xC8, 0x79, 0x41);
        public static readonly Color CS_Copper2 = Color.FromArgb(0xE0, 0x90, 0x50);
        public static readonly Color CS_Cyan    = Color.FromArgb(0x4D, 0xC8, 0xB4);
        public static readonly Color CS_Cyan2   = Color.FromArgb(0x2E, 0xA8, 0x91);
        public static readonly Color CS_Red     = Color.FromArgb(0xD4, 0x50, 0x50);
        public static readonly Color CS_Amber   = Color.FromArgb(0xD4, 0xA0, 0x30);
        public static readonly Color CS_Blue    = Color.FromArgb(0x50, 0x90, 0xD4);

        // ── VoiceCentroid palette ─────────────────────────────────────
        public static readonly Color VC_Bg      = Color.FromArgb(0x05, 0x08, 0x10);
        public static readonly Color VC_Bg2     = Color.FromArgb(0x0A, 0x0F, 0x1E);
        public static readonly Color VC_Bg3     = Color.FromArgb(0x11, 0x18, 0x27);
        public static readonly Color VC_Bg4     = Color.FromArgb(0x1A, 0x22, 0x35);
        public static readonly Color VC_Border  = Color.FromArgb(0x1E, 0x2D, 0x45);
        public static readonly Color VC_Border2 = Color.FromArgb(0x2A, 0x3D, 0x5A);
        public static readonly Color VC_Muted   = Color.FromArgb(0x4A, 0x60, 0x80);
        public static readonly Color VC_Text    = Color.FromArgb(0xC8, 0xD8, 0xF0);
        public static readonly Color VC_Indigo  = Color.FromArgb(0x63, 0x66, 0xF1);
        public static readonly Color VC_Indigo2 = Color.FromArgb(0x81, 0x8C, 0xF8);
        public static readonly Color VC_Sky     = Color.FromArgb(0x38, 0xBD, 0xF8);
        public static readonly Color VC_Pink    = Color.FromArgb(0xF4, 0x72, 0xB6);
        public static readonly Color VC_Green   = Color.FromArgb(0x4A, 0xDE, 0x80);
        public static readonly Color VC_Warn    = Color.FromArgb(0xFB, 0xBF, 0x24);
        public static readonly Color VC_Err     = Color.FromArgb(0xF8, 0x71, 0x71);

        // ── Fonts ─────────────────────────────────────────────────────
        public static readonly Font FontMono10    = new("Consolas", 9f,   FontStyle.Regular, GraphicsUnit.Point);
        public static readonly Font FontMono9     = new("Consolas", 8.5f, FontStyle.Regular, GraphicsUnit.Point);
        public static readonly Font FontMono11    = new("Consolas", 9.5f, FontStyle.Regular, GraphicsUnit.Point);
        public static readonly Font FontMonoBold10= new("Consolas", 9f,   FontStyle.Bold,    GraphicsUnit.Point);
        public static readonly Font FontSans10    = new("Segoe UI", 9f,   FontStyle.Regular, GraphicsUnit.Point);
        public static readonly Font FontSans9     = new("Segoe UI", 8.5f, FontStyle.Regular, GraphicsUnit.Point);
        public static readonly Font FontSansBold11= new("Segoe UI", 9.75f,FontStyle.Bold,    GraphicsUnit.Point);

        // ── Control factories ─────────────────────────────────────────
        public static Button MakeButton(string text, Color fg, Color bg, Color border)
        {
            var btn = new Button
            {
                Text      = text,
                ForeColor = fg,
                BackColor = bg,
                FlatStyle = FlatStyle.Flat,
                Font      = FontMonoBold10,
                Height    = 32,
                Cursor    = Cursors.Hand,
            };
            btn.FlatAppearance.BorderColor        = border;
            btn.FlatAppearance.BorderSize         = 1;
            btn.FlatAppearance.MouseOverBackColor  = ControlPaint.Light(bg, 0.15f);
            btn.FlatAppearance.MouseDownBackColor  = ControlPaint.Dark(bg,  0.1f);
            return btn;
        }

        public static TextBox MakeTextBox(Color bg, Color fg, Color border)
            => new TextBox
            {
                BackColor   = bg,
                ForeColor   = fg,
                Font        = FontMono10,
                BorderStyle = BorderStyle.FixedSingle,
                Height      = 26,
            };

        public static ComboBox MakeComboBox(Color bg, Color fg)
            => new ComboBox
            {
                BackColor     = bg,
                ForeColor     = fg,
                Font          = FontMono10,
                DropDownStyle = ComboBoxStyle.DropDownList,
                FlatStyle     = FlatStyle.Flat,
                Height        = 26,
            };

        public static TrackBar MakeTrackBar(int min, int max, int value)
            => new TrackBar
            {
                Minimum   = min,
                Maximum   = max,
                Value     = value,
                TickStyle = TickStyle.None,
                BackColor = CS_Bg1,
                Height    = 26,
            };

        public static Label MakeLabel(string text, Color fg, Font? font = null)
            => new Label
            {
                Text      = text,
                ForeColor = fg,
                BackColor = Color.Transparent,
                Font      = font ?? FontSans9,
                AutoSize  = true,
            };

        public static Panel MakeCard(Color bg, Color border)
        {
            var p = new Panel { BackColor = bg, Padding = new Padding(12) };
            p.Paint += (s, e) =>
            {
                using var pen = new Pen(border);
                e.Graphics.DrawRectangle(pen, 0, 0, p.Width - 1, p.Height - 1);
            };
            return p;
        }
    }
}
