using System.Numerics;
using System.Text.Json;
using System.Text.Json.Serialization;
using VanEngine.Game.Architecture;

namespace VanEngine.Game.Core;

public sealed class CitizenData
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string NamespaceFamily { get; set; } = string.Empty;
    public List<string> OwnedFiles { get; set; } = new();
    public int CompliantLinesContributed { get; set; }
    public bool IsActive { get; set; } = true;
    public bool IsHomeless { get; set; }
    public float DecayTimer { get; set; }
    public byte RoleType { get; set; }
    public float PosX { get; set; }
    public float PosY { get; set; }
    public float TargetX { get; set; }
    public float TargetY { get; set; }
}

public sealed class HouseData
{
    public Guid Id { get; set; }
    public string ProjectName { get; set; } = string.Empty;
    public string RootNamespace { get; set; } = string.Empty;
    public float PosX { get; set; }
    public float PosY { get; set; }
    public float BoundingW { get; set; } = 120;
    public float BoundingH { get; set; } = 90;
    public bool IsCommons { get; set; }
    public List<FileNodeData> TrackedFiles { get; set; } = new();
}

public sealed class FileNodeData
{
    public string FilePath { get; set; } = string.Empty;
    public string ClassName { get; set; } = string.Empty;
    public int LineCount { get; set; }
    public int ErrorCount { get; set; }
    public int WarningCount { get; set; }
    public long LastWriteTimeTicks { get; set; }
}

public sealed class UploadedFileData
{
    public string FilePath { get; set; } = string.Empty;
    public int TotalLines { get; set; }
    public double ComplianceScore { get; set; }
    public int ViolationCount { get; set; }
    public string Details { get; set; } = string.Empty;
    public string Timestamp { get; set; } = string.Empty;
    public string NamespaceRoot { get; set; } = string.Empty;
}

public sealed class SaveGameData
{
    public int SaveVersion { get; set; } = 1;
    public string Timestamp { get; set; } = string.Empty;
    public int Year { get; set; }
    public double Sovereignty { get; set; }
    public double LanguagePurity { get; set; }
    public int Food { get; set; }
    public int Wood { get; set; }
    public int Stone { get; set; }
    public int Metal { get; set; }
    public int Wealth { get; set; }
    public int Gold { get; set; }
    public int TotalCompliantLines { get; set; }
    public int NextCitizenThreshold { get; set; }
    public int NextCitizenId { get; set; }
    public List<CitizenData> Citizens { get; set; } = new();
    public List<HouseData> Houses { get; set; } = new();
    public List<UploadedFileData> UploadHistory { get; set; } = new();
    public List<string> Logs { get; set; } = new();
    public uint DirectiveMask { get; set; }
    public Dictionary<string, double> DirectiveWeights { get; set; } = new();
    public List<TimelineEntryData> Timeline { get; set; } = new();
}

public sealed class TimelineEntryData
{
    public int Year { get; set; }
    public string EventType { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
}

public static class SaveManager
{
    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        WriteIndented = true,
        IncludeFields = true,
    };

    public static string DefaultSaveDir
    {
        get
        {
            var dir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "saves");
            Directory.CreateDirectory(dir);
            return dir;
        }
    }

    public static void Save(SovereignState state, string filePath)
    {
        var res = state.Resources;
        var data = new SaveGameData
        {
            SaveVersion = 1,
            Timestamp = DateTime.Now.ToString("O"),
            Year = state.Year,
            Sovereignty = state.Sovereignty,
            LanguagePurity = state.LanguagePurity,
            Food = res.Food,
            Wood = res.Wood,
            Stone = res.Stone,
            Metal = res.Metal,
            Wealth = res.Wealth,
            Gold = res.Gold,
            TotalCompliantLines = state.TotalCompliantLines,
            NextCitizenThreshold = state.NextCitizenThreshold,
            NextCitizenId = state.NextCitizenId,
            DirectiveMask = state.GetDirectiveMask(),
            DirectiveWeights = state.GetDirectiveWeights(),
        };

        foreach (var c in state.Citizens)
        {
            data.Citizens.Add(new CitizenData
            {
                Id = c.Id,
                Name = c.Name,
                NamespaceFamily = c.NamespaceFamily,
                OwnedFiles = new List<string>(c.OwnedFiles),
                CompliantLinesContributed = c.CompliantLinesContributed,
                IsActive = c.IsActive,
                IsHomeless = c.IsHomeless,
                DecayTimer = c.DecayTimer,
                RoleType = c.RoleType,
                PosX = c.Position.X,
                PosY = c.Position.Y,
                TargetX = c.TargetPosition.X,
                TargetY = c.TargetPosition.Y,
            });
        }

        foreach (var h in state.Houses)
        {
            var hd = new HouseData
            {
                Id = h.Id,
                ProjectName = h.ProjectName,
                RootNamespace = h.RootNamespace,
                PosX = h.Position.X,
                PosY = h.Position.Y,
                BoundingW = h.BoundingBoxSize.X,
                BoundingH = h.BoundingBoxSize.Y,
                IsCommons = h.IsCommons,
            };
            foreach (var f in h.TrackedFiles)
            {
                hd.TrackedFiles.Add(new FileNodeData
                {
                    FilePath = f.FilePath,
                    ClassName = f.ClassName,
                    LineCount = f.LineCount,
                    ErrorCount = f.ErrorCount,
                    WarningCount = f.WarningCount,
                    LastWriteTimeTicks = f.LastWriteTimeTicks,
                });
            }
            data.Houses.Add(hd);
        }

        foreach (var u in state.UploadHistory)
        {
            data.UploadHistory.Add(new UploadedFileData
            {
                FilePath = u.FilePath,
                TotalLines = u.TotalLines,
                ComplianceScore = u.ComplianceScore,
                ViolationCount = u.ViolationCount,
                Details = u.Details,
                Timestamp = u.Timestamp.ToString("O"),
                NamespaceRoot = u.NamespaceRoot,
            });
        }

        data.Logs.AddRange(state.GetLogs());

        foreach (var t in state.GetTimeline())
        {
            data.Timeline.Add(new TimelineEntryData
            {
                Year = t.Year,
                EventType = t.EventType,
                Description = t.Description,
                Source = t.Source,
            });
        }

        string json = JsonSerializer.Serialize(data, JsonOpts);
        File.WriteAllText(filePath, json);
    }

    public static SaveGameData Load(string filePath)
    {
        string json = File.ReadAllText(filePath);
        return JsonSerializer.Deserialize<SaveGameData>(json, JsonOpts) ?? new SaveGameData();
    }

    public static void Restore(SovereignState state, SaveGameData data)
    {
        state.RestoreFromSave(data);
    }

    public static string FindLatestSave()
    {
        var dir = DefaultSaveDir;
        if (!Directory.Exists(dir)) return string.Empty;
        var files = Directory.GetFiles(dir, "*.van");
        if (files.Length == 0) return string.Empty;
        return files.OrderByDescending(f => File.GetLastWriteTime(f)).First();
    }
}
