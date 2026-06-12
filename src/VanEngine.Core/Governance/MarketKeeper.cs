namespace VanEngine.Core.Governance;

public sealed class MarketKeeper
{
    private readonly HashSet<string> _expelledMerchants = new();

    public bool ValidateGoods<T>(T goods, Func<T, bool> integrityCheck)
    {
        if (!integrityCheck(goods))
        {
            LogViolation($"Law 12: Attempt to pass corrupted goods of type {typeof(T).Name}");
            return false;
        }
        return true;
    }

    public void ExpelMerchant(string merchantName)
    {
        _expelledMerchants.Add(merchantName);
        Console.WriteLine($"[LAW 12] Merchant '{merchantName}' expelled for attempting to sell damaged goods.");
    }

    public bool IsExpelled(string merchantName) => _expelledMerchants.Contains(merchantName);

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[UNIVERSAL LAW VIOLATION] {violation}");
    }
}
