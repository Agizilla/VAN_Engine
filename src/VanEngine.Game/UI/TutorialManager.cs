namespace VanEngine.Game.UI;

public class TutorialManager
{
    public enum TutorialStep
    {
        Welcome = 0,
        FileWatch = 1,
        Refactor = 2,
        Threats = 3,
        Complete = 4
    }

    public TutorialStep CurrentStep { get; set; } = TutorialStep.Welcome;
    public bool IsComplete { get; set; }
    public bool IsActive { get; set; } = true;

    public void Advance()
    {
        if (CurrentStep < TutorialStep.Complete)
        {
            CurrentStep++;
        }
        if (CurrentStep == TutorialStep.Complete)
        {
            IsComplete = true;
            IsActive = false;
        }
    }

    public void Skip()
    {
        CurrentStep = TutorialStep.Complete;
        IsComplete = true;
        IsActive = false;
    }

    public string GetStepDescription() => CurrentStep switch
    {
        TutorialStep.Welcome => "Welcome to Oera Linda Simulator! Drop a .cs file to begin tracking its compliance.",
        TutorialStep.FileWatch => "Files are watched automatically. Watch the log panel for analysis results.",
        TutorialStep.Refactor => "Right-click a house to rename, split, or merge projects.",
        TutorialStep.Threats => "Defend your project from CVEs! Click incoming threats to neutralise them.",
        TutorialStep.Complete => "You've completed the tutorial! Press [/] for help at any time.",
        _ => ""
    };

    public string GetStepHint() => CurrentStep switch
    {
        TutorialStep.Welcome => "Drag and drop a file onto the window.",
        TutorialStep.FileWatch => "Observe the System Chronicles panel.",
        TutorialStep.Refactor => "Try right-clicking the Core VAN Engine house.",
        TutorialStep.Threats => "Stay vigilant — threats get harder each year.",
        TutorialStep.Complete => "",
        _ => ""
    };
}
