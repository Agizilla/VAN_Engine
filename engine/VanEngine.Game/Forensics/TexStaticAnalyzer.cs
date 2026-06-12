using System.IO;

namespace VanEngine.Game.Forensics;

public class ReviewResult
{
    public int TotalLines;
    public int ErrorCount;
    public int WarningCount;
    public double ComplianceScore;
    public int ViolationCount;
    public string Details = string.Empty;
}

public struct AnalysisResult
{
    public int TotalLines;
    public int ErrorCount;
    public int WarningCount;
    public string DiscoveredNamespace;
    public string DiscoveredClassName;
    public uint TriggeredDirectivesMask;
}

public static class TexStaticAnalyzer
{
    public const uint Directive_ExpelBastards = 1 << 6;
    public const uint Directive_NoDebtSlavery = 1 << 7;

    public static AnalysisResult AnalyzeSourceFile(string filePath)
    {
        var result = new AnalysisResult
        {
            TotalLines = 0,
            ErrorCount = 0,
            WarningCount = 0,
            DiscoveredNamespace = "Unassigned",
            DiscoveredClassName = Path.GetFileNameWithoutExtension(filePath),
            TriggeredDirectivesMask = 0
        };

        if (!File.Exists(filePath))
        {
            result.ErrorCount = 1;
            return result;
        }

        using var reader = new StreamReader(filePath);
        string? line;
        while ((line = reader.ReadLine()) != null)
        {
            result.TotalLines++;
            var span = line.AsSpan().Trim();

            if (span.IsEmpty) continue;

            if (span.StartsWith("namespace ", StringComparison.Ordinal))
            {
                var nsSpan = span.Slice(10).TrimEnd(';').Trim();
                result.DiscoveredNamespace = nsSpan.ToString();
            }

            if (span.Contains("class ".AsSpan(), StringComparison.Ordinal))
            {
                int idx = span.IndexOf("class ".AsSpan(), StringComparison.Ordinal);
                var remainder = span.Slice(idx + 6).Trim();
                int space = remainder.IndexOf(' ');
                if (space > 0) remainder = remainder.Slice(0, space);
                result.DiscoveredClassName = remainder.ToString();
            }

            if (span.Contains("telemetry".AsSpan(), StringComparison.OrdinalIgnoreCase) ||
                span.Contains("analytics".AsSpan(), StringComparison.OrdinalIgnoreCase) ||
                span.Contains("api.".AsSpan(), StringComparison.OrdinalIgnoreCase))
            {
                result.ErrorCount++;
                result.TriggeredDirectivesMask |= Directive_ExpelBastards;
            }

            if (span.Contains("license".AsSpan(), StringComparison.OrdinalIgnoreCase) ||
                span.Contains("proprietary".AsSpan(), StringComparison.OrdinalIgnoreCase) ||
                span.Contains("expires".AsSpan(), StringComparison.OrdinalIgnoreCase))
            {
                result.WarningCount++;
                result.TriggeredDirectivesMask |= Directive_NoDebtSlavery;
            }

            if (span.Contains("Console.WriteLine".AsSpan(), StringComparison.Ordinal))
                result.WarningCount++;
        }

        return result;
    }

    public static async System.Threading.Tasks.Task<ReviewResult> AnalyzeFileAsync(string filePath)
    {
        var analysis = await System.Threading.Tasks.Task.Run(() => AnalyzeSourceFile(filePath));
        return new ReviewResult
        {
            TotalLines = analysis.TotalLines,
            ErrorCount = analysis.ErrorCount,
            WarningCount = analysis.WarningCount,
            ComplianceScore = analysis.ErrorCount == 0
                ? 100.0
                : Math.Max(0, 100.0 - analysis.ErrorCount * 20.0),
            ViolationCount = analysis.ErrorCount + analysis.WarningCount,
            Details = $"[{analysis.DiscoveredNamespace}] {analysis.DiscoveredClassName}: {analysis.ErrorCount} errors, {analysis.WarningCount} warnings",
        };
    }

    public static byte DetermineCharacterTypeFromComplexity(int lineCount)
    {
        if (lineCount < 50) return 0;
        if (lineCount < 250) return 1;
        if (lineCount < 750) return 2;
        return 5;
    }

    // ── Multi-language support ────────────────────────────────────────────
    public static readonly Dictionary<string, string> ExtensionToLanguage = new()
    {
        [".cs"] = "csharp",
        [".py"] = "python",
        [".rs"] = "rust",
        [".js"] = "javascript",
        [".ts"] = "typescript",
        [".go"] = "go",
        [".c"] = "c",
        [".cpp"] = "cpp",
        [".cc"] = "cpp",
        [".h"] = "c_header",
        [".hpp"] = "cpp_header",
        [".java"] = "java",
    };

    public static string DetectLanguageFromExtension(string filePath)
    {
        string ext = Path.GetExtension(filePath)?.ToLowerInvariant() ?? string.Empty;
        return ExtensionToLanguage.TryGetValue(ext, out var lang) ? lang : "unknown";
    }

    public static AnalysisResult AnalyzeSourceFileMultiLang(string filePath)
    {
        var result = AnalyzeSourceFile(filePath);
        string lang = DetectLanguageFromExtension(filePath);

        if (!File.Exists(filePath)) return result;

        using var reader = new StreamReader(filePath);
        string? line;
        while ((line = reader.ReadLine()) != null)
        {
            result.TotalLines++;
            var span = line.AsSpan().Trim();
            if (span.IsEmpty) continue;

            switch (lang)
            {
                case "python":
                    if (span.Contains("print(".AsSpan(), StringComparison.Ordinal) ||
                        span.Contains("eval(".AsSpan(), StringComparison.Ordinal))
                        result.WarningCount++;
                    if (span.Contains("telemetry".AsSpan(), StringComparison.OrdinalIgnoreCase) ||
                        span.Contains("analytics".AsSpan(), StringComparison.OrdinalIgnoreCase))
                        result.ErrorCount++;
                    break;

                case "rust":
                    if (span.Contains("unsafe ".AsSpan(), StringComparison.Ordinal))
                        result.WarningCount++;
                    if (span.Contains("telemetry".AsSpan(), StringComparison.OrdinalIgnoreCase))
                        result.ErrorCount++;
                    break;

                case "javascript":
                case "typescript":
                    if (span.Contains("eval(".AsSpan(), StringComparison.Ordinal) ||
                        span.Contains("Function(".AsSpan(), StringComparison.Ordinal))
                        result.WarningCount++;
                    if (span.Contains("analytics".AsSpan(), StringComparison.OrdinalIgnoreCase) ||
                        span.Contains("telemetry".AsSpan(), StringComparison.OrdinalIgnoreCase))
                        result.ErrorCount++;
                    break;

                case "go":
                    if (span.Contains("telnet".AsSpan(), StringComparison.OrdinalIgnoreCase) ||
                        span.Contains("telemetry".AsSpan(), StringComparison.OrdinalIgnoreCase))
                        result.ErrorCount++;
                    break;

                case "c":
                case "cpp":
                case "c_header":
                case "cpp_header":
                    if (span.Contains("system(".AsSpan(), StringComparison.Ordinal) ||
                        span.Contains("exec(".AsSpan(), StringComparison.Ordinal))
                        result.WarningCount++;
                    break;

                case "java":
                    if (span.Contains("Runtime.getRuntime().exec".AsSpan(), StringComparison.Ordinal) ||
                        span.Contains("telemetry".AsSpan(), StringComparison.OrdinalIgnoreCase))
                        result.ErrorCount++;
                    break;
            }
        }
        return result;
    }
}
