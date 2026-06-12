namespace VanEngine.Core.Governance;

public sealed class EmergentLeadership
{
    private readonly CommandHierarchy _hierarchy;
    private string _volunteerLeader = string.Empty;

    public string VolunteerLeader => _volunteerLeader;

    public EmergentLeadership(CommandHierarchy hierarchy)
    {
        _hierarchy = hierarchy;
    }

    public bool MayAssumeCommand(string volunteer, bool isTimeCritical)
    {
        if (!isTimeCritical)
        {
            LogViolation($"Law 10: {volunteer} attempted to assume command without time criticality.");
            return false;
        }

        if (_hierarchy.HasLeader)
        {
            LogViolation($"Law 10: {volunteer} attempted to assume command while a leader exists.");
            return false;
        }

        Console.WriteLine($"[LAW 10] {volunteer} assumes emergency command.");
        _volunteerLeader = volunteer;
        return true;
    }

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[LAW VIOLATION] {violation}");
    }
}
