using System.Drawing;
using System.Drawing.Imaging;
using System.Diagnostics;

namespace ScreenClipOCR;

internal static class OcrService
{
    private const string TesseractPath = @"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe";

    public static async Task<string?> TryExtractTextAsync(Bitmap bitmap)
    {
        if (!File.Exists(TesseractPath))
        {
            throw new FileNotFoundException("Local Tesseract installation was not found.", TesseractPath);
        }

        var tempRoot = Path.Combine(Path.GetTempPath(), "ScreenClipOCR");
        Directory.CreateDirectory(tempRoot);

        var fileToken = Guid.NewGuid().ToString("N");
        var imagePath = Path.Combine(tempRoot, $"{fileToken}.png");
        var outputBase = Path.Combine(tempRoot, $"{fileToken}_ocr");
        var outputPath = outputBase + ".txt";

        try
        {
            bitmap.Save(imagePath, ImageFormat.Png);

            var startInfo = new ProcessStartInfo
            {
                FileName = TesseractPath,
                Arguments = $"\"{imagePath}\" \"{outputBase}\" -psm 6",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = new Process { StartInfo = startInfo };
            process.Start();

            var stdOut = await process.StandardOutput.ReadToEndAsync();
            var stdErr = await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();

            if (process.ExitCode != 0)
            {
                var message = string.IsNullOrWhiteSpace(stdErr) ? stdOut : stdErr;
                throw new InvalidOperationException($"Tesseract OCR failed: {message.Trim()}");
            }

            if (!File.Exists(outputPath))
            {
                return null;
            }

            var text = await File.ReadAllTextAsync(outputPath);
            return string.IsNullOrWhiteSpace(text) ? null : text.Trim();
        }
        finally
        {
            TryDelete(imagePath);
            TryDelete(outputPath);
        }
    }

    private static void TryDelete(string path)
    {
        try
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
        catch
        {
        }
    }
}
