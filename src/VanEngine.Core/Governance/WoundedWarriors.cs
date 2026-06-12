namespace VanEngine.Core.Governance;

public record WoundedWarrior
{
    public string Name { get; init; } = string.Empty;
    public string Reason { get; init; } = string.Empty;
    public bool IsPermanent { get; init; }
    public DateTime DateWounded { get; init; }
}

public sealed class WoundedWarriorRegistry
{
    private readonly List<WoundedWarrior> _wounded = new();

    public void RegisterWounded(string moduleName, string failureReason, bool isPermanent)
    {
        var warrior = new WoundedWarrior
        {
            Name = moduleName,
            Reason = failureReason,
            IsPermanent = isPermanent,
            DateWounded = DateTime.UtcNow
        };

        _wounded.Add(warrior);
        Console.WriteLine($"[LAW 3] {moduleName} registered as wounded warrior. Maintained at public expense.");
    }

    public IReadOnlyList<WoundedWarrior> GetWounded() => _wounded.AsReadOnly();
}
