namespace VanEngine.Core.Defence;

public sealed class WarriorAdmission
{
    private const int TrainingDaysRequired = 52;
    private readonly Dictionary<string, int> _trainingProgress = new();
    private readonly HashSet<string> _admittedWarriors = new();

    public void RecordTraining(string moduleName, bool passedTest)
    {
        if (passedTest)
        {
            _trainingProgress[moduleName] = _trainingProgress.GetValueOrDefault(moduleName) + 1;
        }
    }

    public bool IsAdmittedAsWarrior(string moduleName)
    {
        var progress = _trainingProgress.GetValueOrDefault(moduleName);
        if (progress >= TrainingDaysRequired)
        {
            _admittedWarriors.Add(moduleName);
            Console.WriteLine($"[LAW 2-3] {moduleName} admitted as warrior.");
            return true;
        }
        return false;
    }

    public int GetTrainingProgress(string moduleName) =>
        _trainingProgress.GetValueOrDefault(moduleName);

    public void GrantWeapons(string moduleName)
    {
        if (IsAdmittedAsWarrior(moduleName))
        {
            Console.WriteLine($"[LAW 2-3] Weapons granted to {moduleName}.");
        }
    }

    private static void EnableDefensiveFeatures(string moduleName)
    {
        Console.WriteLine($"[DEFENCE] Defensive features enabled for {moduleName}.");
    }
}
