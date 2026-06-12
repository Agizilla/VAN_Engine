namespace VanEngine.WinForms.Helpers;

public static class ColorPalette
{
    public static readonly Color Primary = Color.FromArgb(10, 14, 23);
    public static readonly Color Secondary = Color.FromArgb(18, 24, 36);
    public static readonly Color Tertiary = Color.FromArgb(26, 35, 51);

    public static readonly Color Border = Color.FromArgb(46, 61, 82);
    public static readonly Color BorderLight = Color.FromArgb(62, 77, 98);

    public static readonly Color Accent = Color.FromArgb(0, 255, 204);
    public static readonly Color AccentDark = Color.FromArgb(0, 200, 160);

    public static readonly Color TextPrimary = Color.FromArgb(226, 232, 240);
    public static readonly Color TextSecondary = Color.FromArgb(148, 163, 184);
    public static readonly Color TextMuted = Color.FromArgb(100, 116, 139);

    public static readonly Color Success = Color.FromArgb(74, 222, 128);
    public static readonly Color Warning = Color.FromArgb(251, 191, 36);
    public static readonly Color Error = Color.FromArgb(248, 113, 113);
    public static readonly Color Info = Color.FromArgb(96, 165, 250);
}

public static class DarkTheme
{
    public static void ApplyToForm(Form form)
    {
        form.BackColor = ColorPalette.Primary;
        form.ForeColor = ColorPalette.TextPrimary;
        ApplyToControls(form.Controls);
    }

    public static void ApplyToControls(Control.ControlCollection controls)
    {
        foreach (Control ctrl in controls)
        {
            if (ctrl is Panel or GroupBox or UserControl)
                ctrl.BackColor = ColorPalette.Secondary;
            else if (ctrl is TextBoxBase)
            {
                ctrl.BackColor = ColorPalette.Tertiary;
                ctrl.ForeColor = ColorPalette.TextPrimary;
            }
            else if (ctrl is Button btn)
            {
                btn.BackColor = ColorPalette.Tertiary;
                btn.ForeColor = ColorPalette.TextPrimary;
                btn.FlatStyle = FlatStyle.Flat;
                btn.FlatAppearance.BorderColor = ColorPalette.Border;
                btn.FlatAppearance.MouseOverBackColor = ColorPalette.BorderLight;
            }
            else if (ctrl is ListBox or ListView or TreeView)
            {
                ctrl.BackColor = ColorPalette.Tertiary;
                ctrl.ForeColor = ColorPalette.TextPrimary;
            }
            else if (ctrl is Label lbl)
                lbl.ForeColor = ColorPalette.TextPrimary;

            if (ctrl.HasChildren)
                ApplyToControls(ctrl.Controls);
        }
    }
}
