namespace VanEngine.Game.UI;

public class TooltipSystem
{
    private readonly Dictionary<string, string> _tooltips = new();

    public void Register(string target, string text) => _tooltips[target] = text;

    public string? GetTooltip(string target) =>
        _tooltips.TryGetValue(target, out var text) ? text : null;

    public void RegisterDefaults()
    {
        Register("workspace_tab", "Click to switch workspaces. Each workspace tracks a separate project.");
        Register("save", "Save current game state to a .van file.");
        Register("load", "Load the most recent save file.");
        Register("report", "Export a project health report in HTML format.");
        Register("score", "Export a signed score token for leaderboard submission.");
        Register("commit", "Git commit — advances the game year by 1.");
        Register("branch", "Create a new git branch (workspace fork).");
        Register("merge", "Merge current branch into the first other branch.");
        Register("rebase", "Rebase — time-travel 3 years into the past.");
        Register("threat", "Click on threats to intercept them. Sentinels deal +50% damage.");
        Register("night", "Night phase: resources paused, no decay, safe to reorganise.");
    }
}
