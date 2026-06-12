namespace ScreenClipOCR;

internal sealed class AppOptions
{
    public bool SaveImage { get; set; }

    public bool RunOcr { get; set; } = true;

    public string SaveFolder { get; set; } = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.MyPictures),
        "ScreenClipOCR"
    );
}
