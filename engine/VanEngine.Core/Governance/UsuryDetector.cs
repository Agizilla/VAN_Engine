namespace VanEngine.Core.Governance;

public sealed class UsuryDetector
{
    private static readonly HashSet<string> UsuryPatterns = new(StringComparer.OrdinalIgnoreCase)
    {
        "interest", "apr", "compound", "fee", "premium", "markup", "surge pricing"
    };

    public bool IsUsurious(string transactionDescription)
    {
        foreach (var pattern in UsuryPatterns)
        {
            if (transactionDescription.Contains(pattern, StringComparison.OrdinalIgnoreCase))
            {
                LogViolation($"Law 11: Usury detected: '{transactionDescription}' (pattern: '{pattern}')");
                return true;
            }
        }
        return false;
    }

    public void RegisterUsuryPattern(string pattern)
    {
        UsuryPatterns.Add(pattern);
    }

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[UNIVERSAL LAW VIOLATION] {violation}");
    }
}
