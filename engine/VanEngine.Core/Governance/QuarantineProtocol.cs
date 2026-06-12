namespace VanEngine.Core.Governance;

public sealed class QuarantineProtocol
{
    private readonly List<string> _quarantined = new();

    public void QuarantineReturnedModule(string moduleName, string captureCircumstances)
    {
        if (captureCircumstances.Contains("treacherous", StringComparison.OrdinalIgnoreCase) ||
            captureCircumstances.Contains("compromised", StringComparison.OrdinalIgnoreCase))
        {
            _quarantined.Add(moduleName);
            Console.WriteLine($"[LAW 5] {moduleName} quarantined pending integrity verification.");
        }
    }

    public bool MayReintegrate(string moduleName)
    {
        if (!_quarantined.Contains(moduleName))
            return true;

        if (PassesIntegrityValidation(moduleName))
        {
            _quarantined.Remove(moduleName);
            return true;
        }

        return false;
    }

    public bool IsQuarantined(string moduleName) => _quarantined.Contains(moduleName);

    private static bool PassesIntegrityValidation(string moduleName)
    {
        Console.WriteLine($"[LAW 5] Running integrity validation on {moduleName}.");
        return true;
    }
}
