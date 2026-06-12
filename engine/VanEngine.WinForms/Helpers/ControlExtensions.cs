using System.Runtime.InteropServices;

namespace VanEngine.WinForms.Helpers;

public static class ControlExtensions
{
    [DllImport("user32.dll")]
    private static extern int SendMessage(IntPtr hWnd, int msg, int wParam, int lParam);

    private const int WM_SETREDRAW = 0x000B;

    public static void SuspendDrawing(this Control control)
    {
        SendMessage(control.Handle, WM_SETREDRAW, 0, 0);
    }

    public static void ResumeDrawing(this Control control)
    {
        SendMessage(control.Handle, WM_SETREDRAW, 1, 0);
        control.Refresh();
    }

    public static void SetRoundedRegion(this Control control, int radius)
    {
        var path = new System.Drawing.Drawing2D.GraphicsPath();
        path.AddArc(0, 0, radius, radius, 180, 90);
        path.AddArc(control.Width - radius, 0, radius, radius, 270, 90);
        path.AddArc(control.Width - radius, control.Height - radius, radius, radius, 0, 90);
        path.AddArc(0, control.Height - radius, radius, radius, 90, 90);
        path.CloseFigure();
        control.Region = new Region(path);
    }
}
