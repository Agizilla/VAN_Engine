namespace VanEngine.Core.Governance;

public sealed class TermLimits
{
    private readonly Dictionary<string, List<DateTime>> _terms = new();
    private const int MaxTermYears = 3;
    private const int CooldownYears = 7;

    public bool MayServeAsKing(string candidate)
    {
        if (!_terms.TryGetValue(candidate, out var terms))
            return true;

        var lastTerm = terms.Last();
        var yearsSinceLastTerm = (DateTime.UtcNow - lastTerm).TotalDays / 365;

        if (yearsSinceLastTerm < CooldownYears)
        {
            LogViolation($"Law 8-9: {candidate} cannot serve again. {CooldownYears - yearsSinceLastTerm:F1} years remaining in cooldown.");
            return false;
        }

        return true;
    }

    public void RecordTermStart(string kingName)
    {
        if (!_terms.ContainsKey(kingName))
            _terms[kingName] = new List<DateTime>();

        _terms[kingName].Add(DateTime.UtcNow);
    }

    public bool IsTermExpired(string kingName)
    {
        if (!_terms.TryGetValue(kingName, out var terms))
            return false;

        var currentTermStart = terms.Last();
        var yearsInOffice = (DateTime.UtcNow - currentTermStart).TotalDays / 365;

        return yearsInOffice >= MaxTermYears;
    }

    public int TermCount(string kingName) =>
        _terms.TryGetValue(kingName, out var terms) ? terms.Count : 0;

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[LAW VIOLATION] {violation}");
    }
}
