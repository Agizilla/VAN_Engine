namespace VanEngine.Core.Governance;

public sealed class ExternalDependency
{
    public string Name { get; set; } = string.Empty;
    public string Version { get; set; } = string.Empty;
    public DateTime CaptureDate { get; set; }
    public bool HasLearnedCustoms { get; set; }
}

public static class Sandbox
{
    private static readonly HashSet<string> _isolated = new();

    public static void Isolate(string dependencyName)
    {
        _isolated.Add(dependencyName);
        Console.WriteLine($"[SANDBOX] {dependencyName} isolated for vetting.");
    }

    public static void Release(string dependencyName)
    {
        _isolated.Remove(dependencyName);
        Console.WriteLine($"[SANDBOX] {dependencyName} released from sandbox.");
    }

    public static bool IsIsolated(string dependencyName) => _isolated.Contains(dependencyName);
}

public sealed class EnemyPrisonerProtocol
{
    private readonly List<ExternalDependency> _prisoners = new();

    public void CaptureDependency(string dependencyName, string version)
    {
        var prisoner = new ExternalDependency
        {
            Name = dependencyName,
            Version = version,
            CaptureDate = DateTime.UtcNow
        };

        _prisoners.Add(prisoner);
        Console.WriteLine($"[LAW 6] Dependency {dependencyName} captured. Sent to interior for vetting.");
        Sandbox.Isolate(dependencyName);
    }

    public void TeachCustoms(string dependencyName)
    {
        var prisoner = _prisoners.FirstOrDefault(p => p.Name == dependencyName);
        if (prisoner != null)
        {
            prisoner.HasLearnedCustoms = true;
            Console.WriteLine($"[LAW 6] {dependencyName} has learned our free customs.");
        }
    }

    public void ReleaseWithKindness(string dependencyName)
    {
        var prisoner = _prisoners.FirstOrDefault(p => p.Name == dependencyName);
        if (prisoner != null && prisoner.HasLearnedCustoms)
        {
            Console.WriteLine($"[LAW 7] {dependencyName} released with kindness by the maidens.");
            _prisoners.Remove(prisoner);
            Sandbox.Release(dependencyName);
        }
    }

    public IReadOnlyList<ExternalDependency> GetPrisoners() => _prisoners.AsReadOnly();
}
