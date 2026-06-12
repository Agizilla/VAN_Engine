namespace VanEngine.Core.Governance;

public interface ICouncilMember
{
    bool VoteOnAction(string action);
}

public sealed class CouncilVeto
{
    private readonly List<ICouncilMember> _council = new();
    private readonly List<string> _vetoLog = new();

    public IReadOnlyList<ICouncilMember> Council => _council.AsReadOnly();
    public IReadOnlyList<string> VetoLog => _vetoLog.AsReadOnly();

    public void AddCouncilMember(ICouncilMember member) => _council.Add(member);

    public bool MayProceedWithAction(string action, string proposedBy)
    {
        if (proposedBy != "King")
            return true;

        var votes = _council.Select(m => m.VoteOnAction(action)).ToList();
        var opposed = votes.Count(v => !v);

        if (opposed > _council.Count / 2)
        {
            LogViolation($"Law 6: King's action '{action}' opposed by council. May not persist.");
            _vetoLog.Add($"VETO: {action} opposed by {opposed}/{_council.Count} council members.");
            return false;
        }

        return true;
    }

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[LAW VIOLATION] {violation}");
    }
}
