using System.Runtime.InteropServices;

namespace ScreenClipOCR;

internal sealed class GlobalHotkeyWindow : NativeWindow, IDisposable
{
    private const int HotkeyId = 0x5001;
    private const int WmHotkey = 0x0312;
    private const uint ModControl = 0x0002;
    private const uint ModShift = 0x0004;
    private const uint VkS = 0x53;

    public event EventHandler? HotkeyPressed;
    public bool IsRegistered { get; }
    public string DisplayText => "Ctrl + Shift + S";

    public GlobalHotkeyWindow()
    {
        CreateHandle(new CreateParams());
        IsRegistered = Register();
    }

    public void Dispose()
    {
        UnregisterHotKey(Handle, HotkeyId);
        DestroyHandle();
    }

    protected override void WndProc(ref Message m)
    {
        if (m.Msg == WmHotkey && m.WParam == HotkeyId)
        {
            HotkeyPressed?.Invoke(this, EventArgs.Empty);
        }

        base.WndProc(ref m);
    }

    private bool Register()
    {
        return RegisterHotKey(Handle, HotkeyId, ModControl | ModShift, VkS);
    }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool UnregisterHotKey(IntPtr hWnd, int id);
}
