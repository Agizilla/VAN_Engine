namespace VanEngine.Core.Defence;

public interface IResistable
{
    bool Resist(IAssailant assailant);
}

public interface IAssailant
{
    string Name { get; }
    string ThreatDescription { get; }
    int Severity { get; }
}

public sealed class DefenceRegistry
{
    private readonly List<IResistable> _defenders = new();

    public IReadOnlyList<IResistable> Defenders => _defenders;

    public void RegisterDefender(IResistable defender) => _defenders.Add(defender);

    public void SignalAttack(IAssailant assailant)
    {
        foreach (var defender in _defenders)
        {
            if (!defender.Resist(assailant))
            {
                LogViolation($"Defender {defender.GetType().Name} failed to resist assailant {assailant.Name}.");
            }
        }
    }

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[DEFENCE LAW VIOLATION] {violation}");
    }
}
