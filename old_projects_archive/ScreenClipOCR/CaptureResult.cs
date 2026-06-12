using System.Drawing;

namespace ScreenClipOCR;

internal sealed class CaptureResult
{
    public required Bitmap Image { get; init; }

    public required Rectangle ScreenBounds { get; init; }
}
