using Microsoft.VisualBasic.ApplicationServices;
using Microsoft.VisualBasic.Devices;
using Microsoft.VisualBasic;
using System.Diagnostics.Metrics;
using System.DirectoryServices.ActiveDirectory;
using System.Drawing;
using System.Drawing.Imaging;
using static System.Formats.Asn1.AsnWriter;
using static System.Net.Mime.MediaTypeNames;
using static System.Runtime.InteropServices.JavaScript.JSType;
using static System.Windows.Forms.VisualStyles.VisualStyleElement.TaskbarClock;
using static System.Windows.Forms.VisualStyles.VisualStyleElement.TreeView;
using static System.Windows.Forms.VisualStyles.VisualStyleElement;
using System.Dynamic;
using System.Net.NetworkInformation;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.Intrinsics.X86;
using System.Security.Cryptography;
using System.Security.Policy;
using System.Threading;
using System.Windows.Forms;
using System.Xml.Linq;
using static System.Windows.Forms.VisualStyles.VisualStyleElement.Tab;
using static System.Windows.Forms.VisualStyles.VisualStyleElement.TextBox;
using static System.Windows.Forms.VisualStyles.VisualStyleElement.ToolTip;
using System.ComponentModel;
using System.IO;
using System.Net.Sockets;
using System.Reflection.Emit;
using System.Reflection.Metadata;
using System.Runtime.InteropServices.JavaScript;
using System.Runtime.Intrinsics.Arm;
using System.Windows.Forms.Design.Behavior;
using System;

namespace ScreenClipOCR;

internal static class ScreenCaptureService
{
    public static CaptureResult? CaptureRegion(IWin32Window owner)
    {
        using var overlay = new ScreenCaptureOverlayForm();
        if (overlay.ShowDialog(owner) != DialogResult.OK)
        {
            return null;
        }

        var absoluteBounds = new Rectangle(
            overlay.Selection.X + overlay.Bounds.X,
            overlay.Selection.Y + overlay.Bounds.Y,
            overlay.Selection.Width,
            overlay.Selection.Height
        );

        var bitmap = new Bitmap(absoluteBounds.Width, absoluteBounds.Height);
        using var graphics = Graphics.FromImage(bitmap);
        graphics.CopyFromScreen(absoluteBounds.Location, Point.Empty, absoluteBounds.Size, CopyPixelOperation.SourceCopy);

        return new CaptureResult
        {
            Image = bitmap,
            ScreenBounds = absoluteBounds
        };
    }

    public static string SaveCapture(Bitmap bitmap, string folder)
    {
        Directory.CreateDirectory(folder);
        var filePath = Path.Combine(folder, $"capture_{DateTime.Now:yyyyMMdd_HHmmss}.png");
        bitmap.Save(filePath, ImageFormat.Png);
        return filePath;
    }
}
