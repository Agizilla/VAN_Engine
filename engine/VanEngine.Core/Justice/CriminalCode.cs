namespace VanEngine.Core.Justice;

public enum Crime
{
    Robbery,
    Murder,
    Arson,
    Rape,
    DataCorruption,
    ResourceTheft,
    UnauthorisedAccess,
    Treason
}

public static class ModuleManager
{
    private static readonly HashSet<string> _terminated = new();

    public static void Terminate(string moduleName)
    {
        _terminated.Add(moduleName);
        Console.WriteLine($"[MODULE MANAGER] {moduleName} terminated.");
    }

    public static bool IsTerminated(string moduleName) => _terminated.Contains(moduleName);
}

public static class AuditLog
{
    private static readonly List<string> _entries = new();

    public static void RecordExecution(string entity, string action, string reason)
    {
        var entry = $"[{DateTime.UtcNow:O}] {entity} - {action} - {reason}";
        _entries.Add(entry);
        Console.WriteLine($"[AUDIT] {entry}");
    }

    public static IReadOnlyList<string> Entries => _entries.AsReadOnly();
}

public static class NamingRights
{
    private static readonly HashSet<string> _revoked = new();

    public static void RevokeFromLineage(string moduleName)
    {
        _revoked.Add(moduleName);
        Console.WriteLine($"[NAMING] Naming rights revoked from lineage of {moduleName}.");
    }

    public static bool IsRevoked(string moduleName) => _revoked.Contains(moduleName);
}

public static class DamageRepair
{
    public static void MakeGood(Crime committed)
    {
        Console.WriteLine($"[REPAIR] Making good the fault for crime: {committed}");
    }
}

public sealed class CapitalPunishment
{
    public void ExecuteCulprit(string culprit, Crime committed, string victimState)
    {
        AuditLog.RecordExecution(culprit, "EXECUTED", committed.ToString());
        Console.WriteLine($"[MINNO] {culprit} put to death in presence of offended for {committed} against {victimState}.");
        ModuleManager.Terminate(culprit);
    }
}

public sealed class Accountability
{
    public void PunishAuthority(string authorityName, Crime committed)
    {
        Console.WriteLine($"[MINNO] Authority {authorityName} committed {committed}. Making good the fault.");
        DamageRepair.MakeGood(committed);
        var punishment = new CapitalPunishment();
        punishment.ExecuteCulprit(authorityName, committed, "all states");
        NamingRights.RevokeFromLineage(authorityName);
    }
}
