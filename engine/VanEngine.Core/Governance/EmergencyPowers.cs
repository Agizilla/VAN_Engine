namespace VanEngine.Core.Governance;

public sealed class EmergencyPowers
{
    private bool _emergencyMode;
    private DateTime _emergencyStart;
    private string _declaredBy = string.Empty;
    private string _threatDescription = string.Empty;
    private const int MaxEmergencyDurationSeconds = 300;

    public bool IsEmergencyActive
    {
        get
        {
            if (_emergencyMode && (DateTime.UtcNow - _emergencyStart).TotalSeconds > MaxEmergencyDurationSeconds)
                EndEmergency();
            return _emergencyMode;
        }
    }

    public string DeclaredBy => _declaredBy;
    public string ThreatDescription => _threatDescription;

    public void DeclareEmergency(string declaredBy, string threat)
    {
        if (declaredBy != "King" && declaredBy != "Clawdia")
        {
            LogViolation($"Law 7: {declaredBy} attempted to declare emergency without authority.");
            return;
        }

        _emergencyMode = true;
        _emergencyStart = DateTime.UtcNow;
        _declaredBy = declaredBy;
        _threatDescription = threat;
        Console.WriteLine($"[LAW 7] EMERGENCY DECLARED by {declaredBy} due to {threat}. King's orders are absolute.");
    }

    public void EndEmergency()
    {
        _emergencyMode = false;
        _declaredBy = string.Empty;
        _threatDescription = string.Empty;
        Console.WriteLine("[LAW 7] Emergency ended. Normal governance restored.");
    }

    public bool MustObeyKingOrders(string issuer)
    {
        return IsEmergencyActive && issuer == "King";
    }

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[LAW VIOLATION] {violation}");
    }
}
