namespace VanEngine.Core.Governance;

public sealed class MarketRegulator
{
    private const double MaxOverheadRatio = 1.0 / 12.0;
    private long _userWorkCycles;
    private long _systemOverheadCycles;

    public long UserWorkCycles => _userWorkCycles;
    public long SystemOverheadCycles => _systemOverheadCycles;

    public void RecordUserWork(long cycles) =>
        Interlocked.Add(ref _userWorkCycles, cycles);

    public void RecordSystemOverhead(long cycles) =>
        Interlocked.Add(ref _systemOverheadCycles, cycles);

    public double OverheadRatio
    {
        get
        {
            var total = _userWorkCycles + _systemOverheadCycles;
            return total == 0 ? 0 : (double)_systemOverheadCycles / total;
        }
    }

    public bool IsOverheadCompliant()
    {
        if (OverheadRatio > MaxOverheadRatio)
        {
            LogViolation($"Law 8-10: System overhead {OverheadRatio:P1} exceeds {MaxOverheadRatio:P1} cap.");
            return false;
        }
        return true;
    }

    public MarketDistribution DistributeMarketProceeds(int totalProceeds)
    {
        var hundredth = totalProceeds / 100;
        return new MarketDistribution
        {
            Grevetman = hundredth * 20,
            Keeper = hundredth * 10,
            Assistants = hundredth * 5,
            Volksmoeder = hundredth * 1,
            Midwife = hundredth * 4,
            Village = hundredth * 10,
            PoorAndInfirm = hundredth * 50
        };
    }

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[UNIVERSAL LAW VIOLATION] {violation}");
    }
}

public record MarketDistribution
{
    public int Grevetman { get; init; }
    public int Keeper { get; init; }
    public int Assistants { get; init; }
    public int Volksmoeder { get; init; }
    public int Midwife { get; init; }
    public int Village { get; init; }
    public int PoorAndInfirm { get; init; }

    public int Total => Grevetman + Keeper + Assistants + Volksmoeder + Midwife + Village + PoorAndInfirm;
}
