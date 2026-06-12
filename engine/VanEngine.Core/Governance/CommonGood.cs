namespace VanEngine.Core.Governance;

public sealed class ImpactAnalysis
{
    public double IndividualBenefit { get; set; }
    public double CommonBenefit { get; set; }
}

public sealed class CommonGoodValidator
{
    public bool IsForCommonGood(string regulation, string proposedBy)
    {
        var impact = AnalyzeImpact(regulation);

        if (impact.IndividualBenefit > impact.CommonBenefit * 1.5)
        {
            LogViolation($"Law 1: Regulation '{regulation}' favours individual over common good. Rejected.");
            return false;
        }

        Console.WriteLine($"[LAW 1] Regulation '{regulation}' approved for common good.");
        return true;
    }

    private static ImpactAnalysis AnalyzeImpact(string regulation)
    {
        return new ImpactAnalysis();
    }

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[LAW VIOLATION] {violation}");
    }
}
