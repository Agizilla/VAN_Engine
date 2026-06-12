namespace VanEngine.Core.Governance;

public record DamageReport(string Source, long EstimatedRepairCost, string Description);

public sealed class GeneralLevy
{
    private long _totalCollected;
    private readonly List<string> _contributingModules = new();

    public long TotalCollected => _totalCollected;
    public IReadOnlyList<string> ContributingModules => _contributingModules.AsReadOnly();

    public async Task AssessLevyForDamage(DamageReport damage)
    {
        var totalCost = damage.EstimatedRepairCost;
        var activeModules = GetActiveModules();

        if (activeModules.Count == 0) return;

        var levyPerModule = totalCost / activeModules.Count;

        Console.WriteLine($"[LAW 2] War damage assessed: {totalCost} units. Levy of {levyPerModule} per module.");

        foreach (var module in activeModules)
        {
            await CollectContribution(module, levyPerModule);
        }
    }

    private static List<string> GetActiveModules() => new() { "ModuleA", "ModuleB", "ModuleC" };

    private async Task CollectContribution(string module, long amount)
    {
        _contributingModules.Add(module);
        _totalCollected += amount;
        await Task.CompletedTask;
    }

    private static async Task RepairDamage(DamageReport damage)
    {
        Console.WriteLine($"[LAW 2] Repairing damage: {damage.Description}");
        await Task.CompletedTask;
    }
}
