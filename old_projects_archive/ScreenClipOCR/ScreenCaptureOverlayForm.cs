using System.Drawing;

namespace ScreenClipOCR;

internal sealed class ScreenCaptureOverlayForm : Form
{
    private readonly Bitmap _screenSnapshot;
    private Point _dragStart;
    private Point _dragCurrent;
    private bool _isDragging;

    public Rectangle Selection { get; private set; }

    public ScreenCaptureOverlayForm()
    {
        DoubleBuffered = true;
        FormBorderStyle = FormBorderStyle.None;
        StartPosition = FormStartPosition.Manual;
        TopMost = true;
        ShowInTaskbar = false;
        Cursor = Cursors.Cross;
        KeyPreview = true;

        Bounds = SystemInformation.VirtualScreen;
        _screenSnapshot = new Bitmap(Bounds.Width, Bounds.Height);

        using var graphics = Graphics.FromImage(_screenSnapshot);
        graphics.CopyFromScreen(Bounds.Location, Point.Empty, Bounds.Size);

        MouseDown += OnMouseDown;
        MouseMove += OnMouseMove;
        MouseUp += OnMouseUp;
        KeyDown += OnKeyDown;
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _screenSnapshot.Dispose();
        }

        base.Dispose(disposing);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.DrawImageUnscaled(_screenSnapshot, 0, 0);

        using var dimBrush = new SolidBrush(Color.FromArgb(120, Color.Black));
        e.Graphics.FillRectangle(dimBrush, ClientRectangle);

        if (Selection.Width <= 0 || Selection.Height <= 0)
        {
            return;
        }

        e.Graphics.DrawImage(
            _screenSnapshot,
            Selection,
            Selection,
            GraphicsUnit.Pixel
        );

        using var borderPen = new Pen(Color.DeepSkyBlue, 2);
        e.Graphics.DrawRectangle(borderPen, Selection);
    }

    private void OnMouseDown(object? sender, MouseEventArgs e)
    {
        if (e.Button != MouseButtons.Left)
        {
            return;
        }

        _isDragging = true;
        _dragStart = e.Location;
        _dragCurrent = e.Location;
        Selection = Rectangle.Empty;
        Invalidate();
    }

    private void OnMouseMove(object? sender, MouseEventArgs e)
    {
        if (!_isDragging)
        {
            return;
        }

        _dragCurrent = e.Location;
        Selection = NormalizeRect(_dragStart, _dragCurrent);
        Invalidate();
    }

    private void OnMouseUp(object? sender, MouseEventArgs e)
    {
        if (!_isDragging)
        {
            return;
        }

        _isDragging = false;
        _dragCurrent = e.Location;
        Selection = NormalizeRect(_dragStart, _dragCurrent);

        if (Selection.Width < 4 || Selection.Height < 4)
        {
            DialogResult = DialogResult.Cancel;
        }
        else
        {
            DialogResult = DialogResult.OK;
        }

        Close();
    }

    private void OnKeyDown(object? sender, KeyEventArgs e)
    {
        if (e.KeyCode == Keys.Escape)
        {
            DialogResult = DialogResult.Cancel;
            Close();
        }
    }

    private static Rectangle NormalizeRect(Point a, Point b)
    {
        var left = Math.Min(a.X, b.X);
        var top = Math.Min(a.Y, b.Y);
        var right = Math.Max(a.X, b.X);
        var bottom = Math.Max(a.Y, b.Y);
        return Rectangle.FromLTRB(left, top, right, bottom);
    }
}
