using VanEngine.WinForms.Helpers;

namespace VanEngine.WinForms.Controls;

public class RoundedButton : Button
{
    private int _borderRadius = 8;

    public int BorderRadius
    {
        get => _borderRadius;
        set { _borderRadius = value; Invalidate(); }
    }

    public RoundedButton()
    {
        FlatStyle = FlatStyle.Flat;
        FlatAppearance.BorderSize = 0;
        BackColor = ColorPalette.Accent;
        ForeColor = ColorPalette.Primary;
        Font = new Font("Segoe UI", 10, FontStyle.Bold);
        Cursor = Cursors.Hand;
        Size = new Size(120, 40);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;

        using var path = new System.Drawing.Drawing2D.GraphicsPath();
        path.AddArc(0, 0, _borderRadius, _borderRadius, 180, 90);
        path.AddArc(Width - _borderRadius, 0, _borderRadius, _borderRadius, 270, 90);
        path.AddArc(Width - _borderRadius, Height - _borderRadius, _borderRadius, _borderRadius, 0, 90);
        path.AddArc(0, Height - _borderRadius, _borderRadius, _borderRadius, 90, 90);
        path.CloseFigure();

        this.Region = new Region(path);

        using var brush = new SolidBrush(Enabled ? BackColor : ColorPalette.Tertiary);
        e.Graphics.FillPath(brush, path);

        var textBrush = new SolidBrush(Enabled ? ForeColor : ColorPalette.TextMuted);
        var textFormat = new StringFormat
        {
            Alignment = StringAlignment.Center,
            LineAlignment = StringAlignment.Center
        };
        e.Graphics.DrawString(Text, Font, textBrush, ClientRectangle, textFormat);
        textBrush.Dispose();
    }
}
