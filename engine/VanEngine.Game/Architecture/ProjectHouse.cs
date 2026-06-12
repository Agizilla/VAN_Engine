using System.Numerics;

namespace VanEngine.Game.Architecture;

public enum BuildState : byte
{
    Empty = 0,
    Success = 1,
    Warning = 2,
    Error = 3,
    Missing = 4
}

public enum UpgradeTier : byte
{
    Hamlet = 0,
    Village = 1,
    Town = 2,
    Citadel = 3
}

public struct FileNodeAsset
{
    public string FilePath;
    public string ClassName;
    public int LineCount;
    public int ErrorCount;
    public int WarningCount;
    public long LastWriteTimeTicks;
}

public sealed class ProjectHouse
{
    public Guid Id { get; }
    public string ProjectName { get; set; }
    public string RootNamespace { get; set; }
    public Vector2 Position { get; set; }
    public Vector2 BoundingBoxSize { get; set; } = new(120, 90);
    public bool IsBeingDragged { get; set; }

    public BuildState CurrentState { get; private set; } = BuildState.Empty;
    public float CollapseTimerSeconds { get; private set; }
    public const float MaxRectificationWindow = 120f;

    public UpgradeTier Tier { get; set; } = UpgradeTier.Hamlet;
    public int MaxTrackedFiles => Tier switch
    {
        UpgradeTier.Hamlet => 5,
        UpgradeTier.Village => 10,
        UpgradeTier.Town => 20,
        UpgradeTier.Citadel => 50,
        _ => 5,
    };
    public float PassiveResourceBonus => Tier switch
    {
        UpgradeTier.Hamlet => 0f,
        UpgradeTier.Village => 0.1f,
        UpgradeTier.Town => 0.25f,
        UpgradeTier.Citadel => 0.5f,
        _ => 0f,
    };
    public float CollapseTimerMultiplier => Tier switch
    {
        UpgradeTier.Hamlet => 1f,
        UpgradeTier.Village => 1.5f,
        UpgradeTier.Town => 2f,
        UpgradeTier.Citadel => 3f,
        _ => 1f,
    };

    public int UpgradeCost(UpgradeTier to) => to switch
    {
        UpgradeTier.Village => 30,
        UpgradeTier.Town => 75,
        UpgradeTier.Citadel => 150,
        _ => 999,
    };

    public bool IsCommons { get; set; }
    public bool HasBackyardTreasure { get; private set; }
    public string? PendingArtifactPath { get; private set; }
    public string InputRequirementFilter { get; set; } = ".mp3";
    public bool IsTreasureBeingDragged { get; set; }

    public List<FileNodeAsset> TrackedFiles { get; } = new();

    public ProjectHouse(string projectName, string rootNamespace, Vector2 initialPosition)
    {
        Id = Guid.NewGuid();
        ProjectName = projectName;
        RootNamespace = rootNamespace;
        Position = initialPosition;
    }

    public bool Upgrade(UpgradeTier to)
    {
        if ((int)to <= (int)Tier) return false;
        Tier = to;
        var oldSize = BoundingBoxSize;
        BoundingBoxSize = to switch
        {
            UpgradeTier.Village => new Vector2(150, 110),
            UpgradeTier.Town => new Vector2(180, 130),
            UpgradeTier.Citadel => new Vector2(220, 160),
            _ => oldSize,
        };
        return true;
    }

    public void EvaluateBuildState()
    {
        if (TrackedFiles.Count == 0)
        {
            CurrentState = BuildState.Empty;
            CollapseTimerSeconds = 0f;
            return;
        }

        int errors = 0, warnings = 0;
        foreach (var file in TrackedFiles)
        {
            errors += file.ErrorCount;
            warnings += file.WarningCount;
        }

        var previous = CurrentState;

        if (errors > 0)
        {
            CurrentState = BuildState.Error;
            if (previous != BuildState.Error)
                CollapseTimerSeconds = MaxRectificationWindow * CollapseTimerMultiplier;
        }
        else if (warnings > 0)
        {
            CurrentState = BuildState.Warning;
            CollapseTimerSeconds = 0f;
        }
        else
        {
            CurrentState = BuildState.Success;
            CollapseTimerSeconds = 0f;
        }
    }

    public bool UpdateDecayClock(float delta, out bool triggeredCollapse)
    {
        triggeredCollapse = false;
        if (CurrentState != BuildState.Error) return false;

        CollapseTimerSeconds -= delta;
        if (CollapseTimerSeconds <= 0)
        {
            CollapseTimerSeconds = 0;
            triggeredCollapse = true;
            return true;
        }
        return false;
    }

    public void AddArtifact(string artifactPath)
    {
        if (CurrentState == BuildState.Success && Tier >= UpgradeTier.Citadel)
        {
            PendingArtifactPath = artifactPath;
            HasBackyardTreasure = true;
        }
    }

    public void ClearBackyardTreasure()
    {
        HasBackyardTreasure = false;
        PendingArtifactPath = null;
    }
}
