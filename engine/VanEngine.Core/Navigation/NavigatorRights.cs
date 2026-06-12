namespace VanEngine.Core.Navigation;

public sealed class Navigator
{
    public string Name { get; set; } = string.Empty;
    public string Role { get; set; } = "Crew";
    public bool IsActive { get; set; } = true;
    public long ProfitReceived { get; set; }

    public void ReceiveProfit(long amount)
    {
        ProfitReceived += amount;
    }
}

public sealed class FleetManifest
{
    public List<Navigator> Positions { get; } = new();
    public double UnitMultiplier { get; set; } = 1.0;
    public int TotalProfit { get; set; }

    public void AddNavigator(Navigator nav) => Positions.Add(nav);
}

public sealed class NavigatorRights
{
    private readonly List<Navigator> _navigators = new();

    public IReadOnlyList<Navigator> Navigators => _navigators.AsReadOnly();

    public bool EnlistNavigator(string moduleName)
    {
        if (IsStalwart(moduleName))
        {
            _navigators.Add(new Navigator { Name = moduleName });
            Console.WriteLine($"[NAV LAW 1] {moduleName} enlisted as navigator.");
            return true;
        }
        return false;
    }

    private static bool IsStalwart(string moduleName)
    {
        return !string.IsNullOrWhiteSpace(moduleName);
    }
}

public sealed class LeadershipVote
{
    public void ReplaceIncompetentKing(string currentKing, string replacement)
    {
        Console.WriteLine($"[NAV LAW 4] King {currentKing} replaced by {replacement} during voyage.");
    }
}

public sealed class ProfitSharing
{
    private const double CrewShare = 1.0 / 3.0;

    public void DistributeProfits(int totalProfit, FleetManifest manifest)
    {
        var crewPool = (int)(totalProfit * CrewShare);

        var weights = new Dictionary<string, double>
        {
            ["King"] = 12,
            ["Admiral"] = 7,
            ["Boatswain"] = 2,
            ["Captain"] = 3,
            ["Crew"] = 1,
            ["YoungestBoy"] = 1.0 / 3.0,
            ["SecondBoy"] = 0.5,
            ["EldestBoy"] = 2.0 / 3.0
        };

        var totalShares = manifest.Positions.Sum(p => weights.GetValueOrDefault(p.Role, 0));

        if (totalShares <= 0) return;

        foreach (var position in manifest.Positions)
        {
            var share = weights.GetValueOrDefault(position.Role, 0);
            var portion = (int)(crewPool * share / totalShares);
            position.ReceiveProfit(portion);
            Console.WriteLine($"[NAV LAW 5] {position.Name} ({position.Role}) receives {portion} profit share.");
        }
    }
}
