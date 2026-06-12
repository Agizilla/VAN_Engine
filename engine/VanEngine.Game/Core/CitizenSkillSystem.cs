namespace VanEngine.Game.Core;

public enum Specialisation
{
    None = 0,
    Archivist = 1,
    Sentinel = 2,
    Jurist = 3
}

public static class CitizenSkillSystem
{
    public static float GetFileAnalysisTimeReduction(string spec) => spec switch
    {
        "Archivist" => 0.5f,
        _ => 1.0f
    };

    public static float GetThreatDetectionRadius(string spec) => spec switch
    {
        "Sentinel" => 150f,
        _ => 60f
    };

    public static float GetDirectiveViolationTolerance(string spec) => spec switch
    {
        "Jurist" => 0.7f,
        _ => 1.0f
    };

    public static float GetXPMultiplier(string spec) => spec switch
    {
        "Archivist" => 1.2f,
        "Sentinel" => 1.1f,
        "Jurist" => 0.9f,
        _ => 1.0f
    };
}
