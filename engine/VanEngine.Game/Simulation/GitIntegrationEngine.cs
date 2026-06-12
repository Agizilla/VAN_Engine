using System.Numerics;
using VanEngine.Game.Architecture;
using VanEngine.Game.Core;

namespace VanEngine.Game.Simulation;

public enum GitEventType
{
    Commit,
    Branch,
    Merge,
    Rebase,
    Conflict
}

public sealed class GitBranch
{
    public string Name { get; set; } = "main";
    public int ForkYear { get; set; }
    public string ForkedFrom { get; set; } = "main";
    public int CommitCount { get; set; }
    public bool IsActive { get; set; } = true;
}

public sealed class GitMergeConflict
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N")[..8];
    public string BranchA { get; set; } = string.Empty;
    public string BranchB { get; set; } = string.Empty;
    public Citizen? CitizenA { get; set; }
    public Citizen? CitizenB { get; set; }
    public string FilePath { get; set; } = string.Empty;
    public float DecayTimer { get; set; } = 30f;
    public bool IsResolved { get; set; }
}

public sealed class GitIntegrationEngine
{
    private readonly SovereignState _state;
    private readonly WorkspaceManager _workspaceManager;
    private readonly Random _rand = new();
    private readonly List<GitBranch> _branches = new() { new GitBranch { Name = "main", CommitCount = 0 } };
    private readonly List<GitMergeConflict> _conflicts = new();
    private string _currentBranch = "main";
    private int _commitCount;

    public IReadOnlyList<GitBranch> Branches => _branches;
    public IReadOnlyList<GitMergeConflict> Conflicts => _conflicts;
    public string CurrentBranch => _currentBranch;
    public int CommitCount => _commitCount;
    public bool HasUnresolvedConflicts => _conflicts.Any(c => !c.IsResolved);

    public GitIntegrationEngine(SovereignState state, WorkspaceManager workspaceManager)
    {
        _state = state;
        _workspaceManager = workspaceManager;
    }

    public GitEventType PerformCommit(string? message = null)
    {
        _commitCount++;
        var branch = _branches.Find(b => b.Name == _currentBranch);
        if (branch != null) branch.CommitCount++;

        _state.IncrementYear();

        string msg = message ?? $"Commit #{_commitCount} on {_currentBranch}";
        _state.AddTimelineEntry(_state.Year, "event", $"Git commit: {msg} ({_currentBranch})", "git");
        _state.AddLog($"git commit: {msg}");
        _state.AddSovereignty(1, $"Commit #{_commitCount} advances to Year {_state.Year}");

        if (_currentBranch != "main" && _rand.NextDouble() < 0.15)
        {
            SpawnRandomConflict();
            return GitEventType.Conflict;
        }

        return GitEventType.Commit;
    }

    public void PerformBranch(string branchName)
    {
        if (_branches.Any(b => b.Name == branchName)) return;

        var newBranch = new GitBranch
        {
            Name = branchName,
            ForkYear = _state.Year,
            ForkedFrom = _currentBranch,
            CommitCount = 0,
        };
        _branches.Add(newBranch);
        _currentBranch = branchName;

        _workspaceManager.CreateWorkspace(branchName, AppDomain.CurrentDomain.BaseDirectory);

        _state.AddTimelineEntry(_state.Year, "event", $"Git branch: '{branchName}' forked from {newBranch.ForkedFrom}", "git");
        _state.AddLog($"git branch {branchName}");
    }

    public void PerformMerge(string sourceBranch, string targetBranch)
    {
        var src = _branches.Find(b => b.Name == sourceBranch);
        var tgt = _branches.Find(b => b.Name == targetBranch);
        if (src == null || tgt == null) return;

        int conflictCount = _rand.Next(1, 4);
        for (int i = 0; i < conflictCount; i++)
            SpawnConflictForMerge(sourceBranch, targetBranch);

        if (_conflicts.Count == 0)
        {
            _state.AddLog($"git merge {sourceBranch} -> {targetBranch}: clean merge");
            _state.AddSovereignty(3, $"Clean merge {sourceBranch} -> {targetBranch}");
        }
        else
        {
            _state.AddLog($"git merge {sourceBranch} -> {targetBranch}: {_conflicts.Count} conflict(s)");
            _state.AddSovereignty(-2, $"Merge conflicts in {targetBranch} from {sourceBranch}");
        }

        _state.AddTimelineEntry(_state.Year, "event", $"Git merge: {sourceBranch} -> {targetBranch} ({conflictCount} conflicts)", "git");
    }

    public void PerformRebase(string branch, int targetYear)
    {
        var b = _branches.Find(x => x.Name == branch);
        if (b == null || targetYear < 1) return;

        int yearDiff = Math.Abs(_state.Year - targetYear);
        _state.AddLog($"git rebase {branch} onto Year {targetYear} (time-travel: {yearDiff} years)");

        if (yearDiff > 0)
            _state.AddSovereignty(-yearDiff * 2, $"Rebase time-travel: {yearDiff} year displacement");

        _state.AddTimelineEntry(_state.Year, "event", $"Git rebase: {branch} rewound to Year {targetYear}", "git");

        if (_rand.NextDouble() < 0.3)
            SpawnRandomConflict();
    }

    public void SwitchBranch(string branchName)
    {
        if (!_branches.Any(b => b.Name == branchName)) return;
        _currentBranch = branchName;

        _workspaceManager.SwitchTo(branchName);

        _state.AddLog($"git checkout {branchName}");
        _state.AddTimelineEntry(_state.Year, "event", $"Switched to branch '{branchName}'", "git");
    }

    public void ResolveConflict(string conflictId)
    {
        var conflict = _conflicts.Find(c => c.Id == conflictId);
        if (conflict == null) return;

        conflict.IsResolved = true;
        _state.AddSovereignty(1, $"Merge conflict resolved: {conflict.FilePath}");
        _state.AddLog($"Conflict resolved: {conflict.FilePath}");
    }

    public void TickConflicts(float delta)
    {
        foreach (var c in _conflicts.ToList())
        {
            if (c.IsResolved)
            {
                _conflicts.Remove(c);
                continue;
            }

            c.DecayTimer -= delta;
            if (c.DecayTimer <= 0)
            {
                if (c.CitizenA != null)
                {
                    c.CitizenA.DecayTimer = 60f;
                    c.CitizenA.IsActive = false;
                }
                if (c.CitizenB != null)
                {
                    c.CitizenB.DecayTimer = 60f;
                    c.CitizenB.IsActive = false;
                }
                _state.AddSovereignty(-5, $"Unresolved conflict decay: {c.FilePath}");
                _state.AddLog($"ALERT: Unresolved conflict in '{c.FilePath}' — citizens decayed");
                _state.AddTimelineEntry(_state.Year, "crime", $"Conflict unresolved: {c.FilePath} — citizens lost", "git");
                _conflicts.Remove(c);
            }
        }
    }

    public void DrawConflicts(float mouseX, float mouseY)
    {
        int y = 88;
        foreach (var c in _conflicts)
        {
            if (c.IsResolved) continue;
            var col = c.DecayTimer < 10f
                ? new Raylib_CsLo.Color(240, 50, 50, 220)
                : new Raylib_CsLo.Color(240, 200, 50, 220);
            string label = $"CONFLICT: {c.FilePath} [{c.DecayTimer:F0}s]";
            Raylib_CsLo.Raylib.DrawText(label, _screenWidth - 280, y, 10, col);
            y += 14;
        }
    }

    private int _screenWidth = 1280;

    private void SpawnRandomConflict()
    {
        var citizens = _state.Citizens.Where(c => c.IsActive).ToList();
        if (citizens.Count < 2) return;

        var a = citizens[_rand.Next(citizens.Count)];
        var b = citizens.Where(c => c.Id != a.Id).ElementAt(_rand.Next(citizens.Count - 1));

        var file = a.OwnedFiles.FirstOrDefault() ?? "unknown_file.cs";
        _conflicts.Add(new GitMergeConflict
        {
            BranchA = _currentBranch,
            CitizenA = a,
            CitizenB = b,
            FilePath = file,
            DecayTimer = 30f,
        });
        _state.AddLog($"Merge conflict on {_currentBranch}: {a.Name} vs {b.Name} over {file}");
    }

    private void SpawnConflictForMerge(string source, string target)
    {
        var citizens = _state.Citizens.Where(c => c.IsActive).ToList();
        if (citizens.Count < 2) return;

        var a = citizens[_rand.Next(citizens.Count)];
        var b = citizens.Where(c => c.Id != a.Id).ElementAt(_rand.Next(citizens.Count - 1));
        var file = a.OwnedFiles.FirstOrDefault() ?? "conflicted_file.cs";

        _conflicts.Add(new GitMergeConflict
        {
            BranchA = source,
            BranchB = target,
            CitizenA = a,
            CitizenB = b,
            FilePath = file,
            DecayTimer = 30f,
        });
    }

    public void SetScreenWidth(int w) => _screenWidth = w;
}
