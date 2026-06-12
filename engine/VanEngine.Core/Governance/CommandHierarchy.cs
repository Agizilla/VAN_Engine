namespace VanEngine.Core.Governance;

public sealed class CommandHierarchy
{
    private readonly List<string> _rankOrder = new();
    private string _currentCommander = string.Empty;

    public string CurrentCommander => _currentCommander;
    public IReadOnlyList<string> RankOrder => _rankOrder.AsReadOnly();
    public bool HasLeader => !string.IsNullOrEmpty(_currentCommander);

    public void DefineRankOrder(IEnumerable<string> ranks)
    {
        _rankOrder.Clear();
        _rankOrder.AddRange(ranks);
    }

    public void SetCurrentCommander(string commander)
    {
        _currentCommander = commander;
    }

    public string? GetNextInCommand(string currentLeader)
    {
        var currentIndex = _rankOrder.IndexOf(currentLeader);
        if (currentIndex >= 0 && currentIndex + 1 < _rankOrder.Count)
            return _rankOrder[currentIndex + 1];
        return null;
    }

    public string GetCurrentCommander()
    {
        if (!string.IsNullOrEmpty(_currentCommander))
            return _currentCommander;

        Console.WriteLine("[LAW 9] No leader present. Election initiated.");
        return ElectNewLeader();
    }

    private static string ElectNewLeader()
    {
        Console.WriteLine("[LAW 9] Election process started.");
        return "ElectedCommander";
    }
}
