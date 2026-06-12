using VanEngine.Core.VAN;

namespace VanEngine.Core.Governance;

public sealed class AnnualReelection
{
    private readonly Dictionary<string, DateTime> _lastElectionDates = new();
    private readonly FryasComplianceEngine _compliance;

    public AnnualReelection(FryasComplianceEngine compliance)
    {
        _compliance = compliance;
    }

    public bool IsEligibleForReelection(string officialName)
    {
        if (!_compliance.IsDirectiveActive(FryasDirective.AllDirectives))
            return false;

        if (_lastElectionDates.TryGetValue(officialName, out var lastElection))
        {
            if ((DateTime.UtcNow - lastElection).TotalDays < 365)
                return true;
        }

        Console.WriteLine($"[LAW 6] {officialName} requires annual re-election.");
        return false;
    }

    public void RecordElection(string officialName)
    {
        _lastElectionDates[officialName] = DateTime.UtcNow;
    }
}
