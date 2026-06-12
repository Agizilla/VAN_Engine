namespace VanEngine.Core.Governance;

public sealed class ConquestRewards
{
    private readonly Dictionary<string, ConquestRecord> _conquests = new();

    public void RecordConquest(string kingName, string defeatedEnemy)
    {
        _conquests[kingName] = new ConquestRecord
        {
            Victor = kingName,
            Enemy = defeatedEnemy,
            Date = DateTime.UtcNow,
            IsDangerous = true
        };
        Console.WriteLine($"[LAW 11] King {kingName} conquered {defeatedEnemy}. Name may be taken by successors.");
    }

    public bool MayTakeConquerorsName(string successor, string conquerorName)
    {
        return _conquests.ContainsKey(conquerorName);
    }

    public string? GetInheritanceTarget(List<string> children)
    {
        if (children.Count == 0) return null;

        var youngest = children.Last();
        Console.WriteLine($"[LAW 12] Youngest child {youngest} inherits the house and grounds.");
        return youngest;
    }

    public bool HasConquests(string kingName) => _conquests.ContainsKey(kingName);

    public sealed class ConquestRecord
    {
        public string Victor { get; set; } = string.Empty;
        public string Enemy { get; set; } = string.Empty;
        public DateTime Date { get; set; }
        public bool IsDangerous { get; set; }
    }
}
