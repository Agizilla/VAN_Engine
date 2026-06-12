using System.Collections.Concurrent;
using System.Numerics;
using VanEngine.Game.Architecture;
using VanEngine.Game.Forensics;

namespace VanEngine.Game.Core;

public class Citizen
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
    public Vector2 Position { get; set; }
    public Vector2 TargetPosition { get; set; }

    public int XP { get; set; }
    public string Specialization { get; set; } = string.Empty;
    public void AddXP(int amount)
    {
        XP += amount;
        if (XP >= 100 && Specialization == string.Empty)
        {
            Specialization = "Archivist";
            RoleType = 6;
        }
        else if (XP >= 250 && Specialization == "Archivist")
        {
            Specialization = "Sentinel";
            RoleType = 7;
        }
        else if (XP >= 500 && Specialization == "Sentinel")
        {
            Specialization = "Jurist";
            RoleType = 8;
        }
    }
}

public class UploadedFile
{
    public string FilePath { get; set; } = string.Empty;
    public int TotalLines { get; set; }
    public double ComplianceScore { get; set; }
    public int ViolationCount { get; set; }
    public string Details { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; }
    public string NamespaceRoot { get; set; } = string.Empty;
}

public struct ResourcePack
{
    public int Food, Wood, Stone, Metal, Wealth, Gold;
}

public sealed class SovereignState
{
    private readonly object _lock = new();
    private int _year;
    private double _sovereignty;
    private double _languagePurity;
    private ResourcePack _resources;
    private readonly List<Citizen> _citizens = new();
    private readonly List<UploadedFile> _uploadHistory = new();
    private readonly List<ProjectHouse> _houses = new();
    private readonly List<TimelineEntry> _timeline = new();
    private int _nextCitizenId = 1;
    private int _totalCompliantLines;
    private int _nextCitizenThreshold = 100;
    private const int ThresholdIncrement = 100;

    private readonly ConcurrentQueue<string> _logQueue = new();
    private readonly List<string> _logs = new();
    private readonly object _logLock = new();

    private const int MaxLogs = 64;
    private const int MaxTimelineEntries = 500;

    private uint _directiveMask = 0xFFFF;
    private Dictionary<string, double> _directiveWeights = new()
    {
        ["telemetry_penalty"] = 5.0,
        ["license_penalty"] = 2.0,
        ["eval_penalty"] = 8.0,
        ["unsafe_penalty"] = 4.0,
    };

    public SovereignState()
    {
        _year = 1;
        _sovereignty = 100.0;
        _languagePurity = 100.0;
        _resources = new ResourcePack { Food = 250, Wood = 150, Stone = 100, Metal = 30, Wealth = 100, Gold = 0 };
    }

    public int Year => _year;
    public double Sovereignty => _sovereignty;
    public double LanguagePurity => _languagePurity;
    public int TotalCompliantLines => _totalCompliantLines;
    public int NextCitizenThreshold => _nextCitizenThreshold;
    public ResourcePack Resources
    {
        get { lock (_lock) return _resources; }
    }
    public IReadOnlyList<Citizen> Citizens => _citizens;
    public IReadOnlyList<UploadedFile> UploadHistory => _uploadHistory;
    public IReadOnlyList<ProjectHouse> Houses => _houses;

    public void IncrementYear() => _year++;

    public void AddSovereignty(double delta, string reason)
    {
        lock (_lock)
        {
            _sovereignty = Math.Clamp(_sovereignty + delta, 0, 100);
            AddLog($"Sovereignty {delta:+0.0;-0.0}%: {reason}");
        }
    }

    public void AddLanguagePurity(double delta, string reason)
    {
        lock (_lock)
        {
            _languagePurity = Math.Clamp(_languagePurity + delta, 0, 100);
            AddLog($"Language Purity {delta:+0.0;-0.0}%: {reason}");
        }
    }

    public void ModifyResources(ResourcePack delta)
    {
        lock (_lock)
        {
            _resources.Food = Math.Max(0, _resources.Food + delta.Food);
            _resources.Wood = Math.Max(0, _resources.Wood + delta.Wood);
            _resources.Stone = Math.Max(0, _resources.Stone + delta.Stone);
            _resources.Metal = Math.Max(0, _resources.Metal + delta.Metal);
            _resources.Wealth = Math.Max(0, _resources.Wealth + delta.Wealth);
            _resources.Gold = Math.Max(0, _resources.Gold + delta.Gold);
        }
    }

    public void AddHouse(ProjectHouse house)
    {
        lock (_lock) _houses.Add(house);
    }

    public void RemoveHouse(ProjectHouse house)
    {
        lock (_lock) _houses.Remove(house);
    }

    public void AddCompliantFile(UploadedFile file, string filePath, string namespaceRoot, int lineCount, AnalysisResult analysis)
    {
        lock (_lock)
        {
            _uploadHistory.Add(file);
            _totalCompliantLines += lineCount;

            double reward = lineCount / 10.0;
            _sovereignty = Math.Clamp(_sovereignty + reward, 0, 100);
            AddLog($"Compliant file '{Path.GetFileName(filePath)}' (+{reward:F1}%)");

            _resources.Food += lineCount / 5;
            _resources.Wood += lineCount / 10;
            _resources.Wealth += lineCount / 20;

            if (_totalCompliantLines >= _nextCitizenThreshold)
            {
                byte role = TexStaticAnalyzer.DetermineCharacterTypeFromComplexity(lineCount);
                var citizen = new Citizen
                {
                    Id = _nextCitizenId++,
                    Name = $"Scribe_{_nextCitizenId}",
                    NamespaceFamily = namespaceRoot,
                    OwnedFiles = new List<string> { filePath },
                    CompliantLinesContributed = lineCount,
                    RoleType = role,
                    Position = new Vector2(100, 100),
                    IsHomeless = true
                };
                _citizens.Add(citizen);
                AddLog($"New citizen '{citizen.Name}' (role {role}) joined! (threshold {_nextCitizenThreshold} lines)");
                _nextCitizenThreshold += ThresholdIncrement;
            }
            else
            {
                var targetCitizen = _citizens.Find(c => c.NamespaceFamily == namespaceRoot);
                if (targetCitizen != null)
                    targetCitizen.OwnedFiles.Add(filePath);
                else if (_citizens.Count > 0)
                    _citizens[^1].OwnedFiles.Add(filePath);
            }

            var house = _houses.Find(h => h.RootNamespace == namespaceRoot);
            if (house != null)
            {
                house.TrackedFiles.Add(new FileNodeAsset
                {
                    FilePath = filePath,
                    ClassName = analysis.DiscoveredClassName,
                    LineCount = lineCount,
                    ErrorCount = analysis.ErrorCount,
                    WarningCount = analysis.WarningCount,
                    LastWriteTimeTicks = DateTime.Now.Ticks
                });
                house.EvaluateBuildState();
            }
        }
    }

    public void AddViolatingFile(UploadedFile file, string filePath, int lineCount, AnalysisResult analysis)
    {
        lock (_lock)
        {
            _uploadHistory.Add(file);

            double penalty = analysis.ErrorCount * 5.0;
            _sovereignty = Math.Clamp(_sovereignty - penalty, 0, 100);
            AddLog($"Violating file '{Path.GetFileName(filePath)}' (-{penalty:F1}%)");

            _resources.Food = Math.Max(0, _resources.Food - lineCount / 10);
            _resources.Wealth = Math.Max(0, _resources.Wealth - lineCount / 20);
            _languagePurity = Math.Clamp(_languagePurity - penalty / 2, 0, 100);
            AddLog($"Language corruption from '{Path.GetFileName(filePath)}'");

            var citizen = _citizens.Find(c => c.OwnedFiles.Contains(filePath));
            if (citizen != null)
                citizen.DecayTimer = 30f;

            var house = _houses.Find(h => h.RootNamespace == analysis.DiscoveredNamespace);
            if (house != null)
            {
                int idx = house.TrackedFiles.FindIndex(f => f.FilePath == filePath);
                if (idx >= 0)
                {
                    house.TrackedFiles[idx] = new FileNodeAsset
                    {
                        FilePath = filePath,
                        ClassName = analysis.DiscoveredClassName,
                        LineCount = lineCount,
                        ErrorCount = analysis.ErrorCount,
                        WarningCount = analysis.WarningCount,
                        LastWriteTimeTicks = DateTime.Now.Ticks
                    };
                }
                else
                {
                    house.TrackedFiles.Add(new FileNodeAsset
                    {
                        FilePath = filePath,
                        ClassName = analysis.DiscoveredClassName,
                        LineCount = lineCount,
                        ErrorCount = analysis.ErrorCount,
                        WarningCount = analysis.WarningCount,
                        LastWriteTimeTicks = DateTime.Now.Ticks
                    });
                }
                house.EvaluateBuildState();
            }
        }
    }

    public void AddLog(string msg)
    {
        _logQueue.Enqueue($"[Year {_year}] {msg}");
        if (_logQueue.Count > MaxLogs)
            _logQueue.TryDequeue(out _);
    }

    public void FlushLogs()
    {
        lock (_logLock)
        {
            _logs.Clear();
            _logs.AddRange(_logQueue);
        }
    }

    public IReadOnlyList<string> GetLogs()
    {
        lock (_logLock) return _logs.ToList();
    }

    public void EnqueueLog(string msg) => AddLog(msg);

    public bool RemoveCitizen(Citizen citizen)
    {
        lock (_lock) return _citizens.Remove(citizen);
    }

    // ── Directive Config ─────────────────────────────────────────────────
    public uint GetDirectiveMask() { lock (_lock) return _directiveMask; }
    public void SetDirectiveBit(int bit, bool enabled)
    {
        lock (_lock)
        {
            if (enabled) _directiveMask |= (1u << bit);
            else _directiveMask &= ~(1u << bit);
        }
    }
    public Dictionary<string, double> GetDirectiveWeights() { lock (_lock) return new Dictionary<string, double>(_directiveWeights); }
    public void SetDirectiveWeight(string key, double value)
    {
        lock (_lock) _directiveWeights[key] = value;
    }
    public double GetWeightedPenalty(string patternType)
    {
        lock (_lock)
        {
            return _directiveWeights.TryGetValue(patternType, out var w) ? w : 5.0;
        }
    }

    // ── Timeline / History ─────────────────────────────────────────────────
    public void AddTimelineEntry(int year, string eventType, string description, string source)
    {
        lock (_lock)
        {
            _timeline.Add(new TimelineEntry { Year = year, EventType = eventType, Description = description, Source = source });
            if (_timeline.Count > MaxTimelineEntries)
                _timeline.RemoveAt(0);
        }
    }
    public IReadOnlyList<TimelineEntry> GetTimeline()
    {
        lock (_lock) return _timeline.ToList();
    }

    // ── Trade Routes ─────────────────────────────────────────────────
    private readonly List<TradeRoute> _tradeRoutes = new();
    public void AddTradeRoute(TradeRoute route)
    {
        lock (_lock) _tradeRoutes.Add(route);
    }
    public IReadOnlyList<TradeRoute> GetTradeRoutes()
    {
        lock (_lock) return _tradeRoutes.ToList();
    }
    public void TickTradeRoutes()
    {
        lock (_lock)
        {
            foreach (var r in _tradeRoutes.ToList())
            {
                r.Progress += 0.05f;
                if (r.Progress >= 1f)
                {
                    int food = Math.Max(1, (int)(r.Efficiency * 3));
                    int wealth = Math.Max(1, (int)(r.Efficiency * 2));
                    _resources.Food += food;
                    _resources.Wealth += wealth;
                    AddLog($"Trade route '{r.Name}' delivered ({food}f, {wealth}w)");
                    r.Progress = 0f;
                }
            }
        }
    }
    public void RemoveTradeRoute(string name)
    {
        lock (_lock) _tradeRoutes.RemoveAll(r => r.Name == name);
    }

    // ── For SaveManager access ─────────────────────────────────────────────────
    public int NextCitizenId { get { lock (_lock) return _nextCitizenId; } set { lock (_lock) _nextCitizenId = value; } }

    public void RestoreFromSave(SaveGameData data)
    {
        lock (_lock)
        {
            _year = data.Year;
            _sovereignty = data.Sovereignty;
            _languagePurity = data.LanguagePurity;
            _resources = new ResourcePack
            {
                Food = data.Food, Wood = data.Wood, Stone = data.Stone,
                Metal = data.Metal, Wealth = data.Wealth, Gold = data.Gold,
            };
            _totalCompliantLines = data.TotalCompliantLines;
            _nextCitizenThreshold = data.NextCitizenThreshold;
            _nextCitizenId = data.NextCitizenId;
            _directiveMask = data.DirectiveMask;
            if (data.DirectiveWeights != null) _directiveWeights = data.DirectiveWeights;

            _citizens.Clear();
            foreach (var cd in data.Citizens)
            {
                _citizens.Add(new Citizen
                {
                    Id = cd.Id,
                    Name = cd.Name,
                    NamespaceFamily = cd.NamespaceFamily,
                    OwnedFiles = cd.OwnedFiles ?? new List<string>(),
                    CompliantLinesContributed = cd.CompliantLinesContributed,
                    IsActive = cd.IsActive,
                    IsHomeless = cd.IsHomeless,
                    DecayTimer = cd.DecayTimer,
                    RoleType = cd.RoleType,
                    Position = new Vector2(cd.PosX, cd.PosY),
                    TargetPosition = new Vector2(cd.TargetX, cd.TargetY),
                });
            }

            _houses.Clear();
            foreach (var hd in data.Houses)
            {
                var house = new ProjectHouse(hd.ProjectName, hd.RootNamespace, new Vector2(hd.PosX, hd.PosY))
                {
                    IsCommons = hd.IsCommons,
                };
                foreach (var fd in hd.TrackedFiles)
                {
                    house.TrackedFiles.Add(new FileNodeAsset
                    {
                        FilePath = fd.FilePath,
                        ClassName = fd.ClassName,
                        LineCount = fd.LineCount,
                        ErrorCount = fd.ErrorCount,
                        WarningCount = fd.WarningCount,
                        LastWriteTimeTicks = fd.LastWriteTimeTicks,
                    });
                }
                house.EvaluateBuildState();
                _houses.Add(house);
            }

            _uploadHistory.Clear();
            foreach (var ud in data.UploadHistory)
            {
                _uploadHistory.Add(new UploadedFile
                {
                    FilePath = ud.FilePath,
                    TotalLines = ud.TotalLines,
                    ComplianceScore = ud.ComplianceScore,
                    ViolationCount = ud.ViolationCount,
                    Details = ud.Details,
                    Timestamp = DateTime.TryParse(ud.Timestamp, out var dt) ? dt : DateTime.Now,
                    NamespaceRoot = ud.NamespaceRoot,
                });
            }

            _timeline.Clear();
            if (data.Timeline != null)
            {
                foreach (var td in data.Timeline)
                {
                    _timeline.Add(new TimelineEntry
                    {
                        Year = td.Year,
                        EventType = td.EventType,
                        Description = td.Description,
                        Source = td.Source,
                    });
                }
            }

            AddLog($"Save restored from Year {data.Year}");
        }
    }
}

public class TimelineEntry
{
    public int Year { get; set; }
    public string EventType { get; set; } = "info";
    public string Description { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
}

public class TradeRoute
{
    public string Name { get; set; } = string.Empty;
    public string FromWorkspace { get; set; } = string.Empty;
    public string ToWorkspace { get; set; } = string.Empty;
    public float Progress { get; set; }
    public float Efficiency { get; set; } = 1f;
    public bool IsActive { get; set; } = true;
    public float PacketX { get; set; }
    public float PacketY { get; set; }
}
