namespace VanEngine.Core.Governance;

public record Dependent(string Name, string Relationship);

public sealed class WidowsOrphansSupport
{
    private readonly Dictionary<string, List<Dependent>> _dependents = new();

    public void RegisterDependent(string deceasedModule, Dependent dependent)
    {
        if (!_dependents.ContainsKey(deceasedModule))
            _dependents[deceasedModule] = new List<Dependent>();

        _dependents[deceasedModule].Add(dependent);
        Console.WriteLine($"[LAW 4] Dependent {dependent.Name} of {deceasedModule} registered for public maintenance.");
    }

    public IReadOnlyList<Dependent> GetDependents(string deceasedModule) =>
        _dependents.TryGetValue(deceasedModule, out var deps) ? deps.AsReadOnly() : new List<Dependent>().AsReadOnly();

    public void AllowInheritance(string childModule, string parentModule)
    {
        Console.WriteLine($"[LAW 4] {childModule} may inscribe {parentModule}'s name on shield.");
    }
}
