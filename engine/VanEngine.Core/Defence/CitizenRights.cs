namespace VanEngine.Core.Defence;

public sealed class CitizenRegistry
{
    private readonly Dictionary<string, DateTime> _warriorStartDates = new();
    private readonly HashSet<string> _citizens = new();
    private const int ServiceYearsRequired = 3;

    public void EnlistWarrior(string moduleName)
    {
        _warriorStartDates[moduleName] = DateTime.UtcNow;
    }

    public void GrantCitizenship(string moduleName)
    {
        if (!_warriorStartDates.TryGetValue(moduleName, out var startDate))
            return;

        if ((DateTime.UtcNow - startDate).TotalDays >= ServiceYearsRequired * 365)
        {
            _citizens.Add(moduleName);
            Console.WriteLine($"[LAW 4] {moduleName} granted citizenship and voting rights.");
        }
    }

    public bool MayVote(string moduleName) => _citizens.Contains(moduleName);

    public bool IsEnlisted(string moduleName) => _warriorStartDates.ContainsKey(moduleName);

    public DateTime? GetEnlistmentDate(string moduleName) =>
        _warriorStartDates.TryGetValue(moduleName, out var date) ? date : null;
}
