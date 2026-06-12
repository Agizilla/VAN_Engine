using VanEngine.Game.Architecture;
using VanEngine.Game.Core;

namespace VanEngine.Game.Simulation;

public enum ThreatSeverity { Low, Medium, High, Critical }

public sealed class ThreatEntity
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N")[..8];
    public string Name { get; set; } = "CVE-0000";
    public ThreatSeverity Severity { get; set; } = ThreatSeverity.Low;
    public float X { get; set; }
    public float Y { get; set; }
    public float TargetX { get; set; }
    public float TargetY { get; set; }
    public float Speed { get; set; } = 0.5f;
    public float Health { get; set; } = 10f;
    public float Progress { get; set; }
    public bool IsActive { get; set; } = true;
    public ProjectHouse? TargetHouse { get; set; }
    public float DamageDealt { get; set; }
}

public sealed class ThreatController
{
    private readonly SovereignState _state;
    private readonly Random _rand = new();
    private readonly List<ThreatEntity> _threats = new();
    private float _spawnTimer;
    private float _spawnInterval = 12f;
    private int _threatCount;

    private static readonly string[] CveNames = [
        "CVE-2024-3094", "CVE-2024-27198", "CVE-2024-6387", "CVE-2024-4577",
        "CVE-2024-0204", "CVE-2025-1234", "CVE-2025-5678", "CVE-2025-9012"
    ];

    public IReadOnlyList<ThreatEntity> Threats => _threats;

    public ThreatController(SovereignState state)
    {
        _state = state;
    }

    public void Update(float delta)
    {
        if (_state.Year < 2) return;

        _spawnTimer += delta;
        if (_spawnTimer >= _spawnInterval)
        {
            _spawnTimer = 0f;
            _spawnInterval = Math.Max(4f, _spawnInterval - 0.3f);
            SpawnThreat();
        }

        foreach (var t in _threats.ToList())
        {
            if (!t.IsActive) continue;

            t.Progress += delta * t.Speed;
            t.X += (t.TargetX - t.X) * 0.02f;
            t.Y += (t.TargetY - t.Y) * 0.02f;

            if (t.Progress >= 100f)
            {
                ResolveThreat(t);
            }
        }
    }

    private void SpawnThreat()
    {
        _threatCount++;
        var severity = _threatCount switch
        {
            < 3 => ThreatSeverity.Low,
            < 6 => ThreatSeverity.Medium,
            < 10 => ThreatSeverity.High,
            _ => ThreatSeverity.Critical,
        };

        var name = CveNames[_rand.Next(CveNames.Length)];

        float edge = _rand.Next(4);
        float x = 0, y = 0;
        switch (edge)
        {
            case 0: x = _rand.Next(-200, -50); y = _rand.Next(0, 720); break;
            case 1: x = _rand.Next(1480, 1680); y = _rand.Next(0, 720); break;
            case 2: x = _rand.Next(0, 1280); y = _rand.Next(-200, -50); break;
            case 3: x = _rand.Next(0, 1280); y = _rand.Next(770, 920); break;
        }

        var errorHouses = _state.Houses.Where(h => h.CurrentState == BuildState.Error).ToList();
        ProjectHouse? target = null;
        float tx = 640, ty = 360;

        if (errorHouses.Count > 0 && _rand.NextDouble() < 0.6)
        {
            target = errorHouses[_rand.Next(errorHouses.Count)];
            tx = target.Position.X + target.BoundingBoxSize.X / 2;
            ty = target.Position.Y + target.BoundingBoxSize.Y / 2;
        }

        float hp = severity switch
        {
            ThreatSeverity.Low => 5f,
            ThreatSeverity.Medium => 12f,
            ThreatSeverity.High => 25f,
            ThreatSeverity.Critical => 50f,
            _ => 5f,
        };

        float speed = severity switch
        {
            ThreatSeverity.Low => 0.3f,
            ThreatSeverity.Medium => 0.5f,
            ThreatSeverity.High => 0.7f,
            ThreatSeverity.Critical => 1.0f,
            _ => 0.3f,
        };

        _threats.Add(new ThreatEntity
        {
            Name = name,
            Severity = severity,
            X = x, Y = y,
            TargetX = tx, TargetY = ty,
            Speed = speed,
            Health = hp,
            TargetHouse = target,
            IsActive = true,
        });

        _state.EnqueueLog($"Threat detected: {name} ({severity}) approaching!");
        _state.AddTimelineEntry(_state.Year, "event", $"Threat {name} ({severity}) spawned", "threat");
    }

    public bool InterceptThreat(float mouseX, float mouseY, Citizen? sentinel)
    {
        foreach (var t in _threats.ToList())
        {
            if (!t.IsActive) continue;
            float dx = t.X - mouseX, dy = t.Y - mouseY;
            if (dx * dx + dy * dy > 2500) continue;

            float dmg = sentinel?.RoleType == 6 ? 15f : 10f;
            t.Health -= dmg;

            if (t.Health <= 0)
            {
                t.IsActive = false;
                _threats.Remove(t);
                int goldReward = t.Severity switch
                {
                    ThreatSeverity.Low => 5,
                    ThreatSeverity.Medium => 15,
                    ThreatSeverity.High => 30,
                    ThreatSeverity.Critical => 60,
                    _ => 5,
                };
                _state.ModifyResources(new ResourcePack { Gold = goldReward, Wealth = goldReward / 2 });
                string tier = t.Severity.ToString().ToLower();
                _state.AddSovereignty(2, $"Threat {t.Name} intercepted (+{goldReward}g)");
                _state.AddTimelineEntry(_state.Year, "event", $"Threat {t.Name} ({tier}) defeated, +{goldReward}g", "threat");
                return true;
            }
        }
        return false;
    }

    private void ResolveThreat(ThreatEntity t)
    {
        t.IsActive = false;
        _threats.Remove(t);

        int foodLoss = 10 + (int)t.Severity * 5;
        int wealthLoss = 5 + (int)t.Severity * 3;
        _state.ModifyResources(new ResourcePack { Food = -foodLoss, Wealth = -wealthLoss });
        _state.AddSovereignty(-3 - (int)t.Severity, $"Threat {t.Name} breached defenses");

        if (t.TargetHouse != null)
        {
            var file = t.TargetHouse.TrackedFiles.FirstOrDefault();
            if (file.FilePath != null)
            {
                int idx = t.TargetHouse.TrackedFiles.FindIndex(f => f.FilePath == file.FilePath);
                if (idx >= 0)
                {
                    var corrupted = file;
                    corrupted.ErrorCount += 1 + (int)t.Severity;
                    corrupted.WarningCount += 2;
                    t.TargetHouse.TrackedFiles[idx] = corrupted;
                    t.TargetHouse.EvaluateBuildState();
                    _state.EnqueueLog($"File corrupted by {t.Name}: {Path.GetFileName(file.FilePath)}");
                }
            }
        }
        _state.AddTimelineEntry(_state.Year, "crime", $"Threat {t.Name} breached, resources lost", "threat");
    }

    public void DrawThreats(float mouseX, float mouseY)
    {
        foreach (var t in _threats)
        {
            if (!t.IsActive) continue;

            float dx = t.X - mouseX, dy = t.Y - mouseY;
            float dist = MathF.Sqrt(dx * dx + dy * dy);

            var color = t.Severity switch
            {
                ThreatSeverity.Low => new Raylib_CsLo.Color(100, 200, 100, 200),
                ThreatSeverity.Medium => new Raylib_CsLo.Color(240, 200, 50, 200),
                ThreatSeverity.High => new Raylib_CsLo.Color(240, 100, 50, 200),
                ThreatSeverity.Critical => new Raylib_CsLo.Color(240, 50, 50, 200),
                _ => new Raylib_CsLo.Color(200, 200, 200, 200),
            };

            Raylib_CsLo.Raylib.DrawCircle((int)t.X, (int)t.Y, 12 + (int)t.Severity * 3, color);
            Raylib_CsLo.Raylib.DrawCircleLines((int)t.X, (int)t.Y, 14 + (int)t.Severity * 3,
                new Raylib_CsLo.Color(255, 255, 255, 150));

            string label = $"{t.Name}";
            if (dist < 100)
            {
                label += $" [{t.Health:F0}hp]";
                Raylib_CsLo.Raylib.DrawText(label, (int)t.X - 20, (int)t.Y - 22, 9,
                    new Raylib_CsLo.Color(255, 255, 255, 220));
            }

            if (t.TargetHouse != null)
            {
                Raylib_CsLo.Raylib.DrawLine((int)t.X, (int)t.Y,
                    (int)(t.TargetHouse.Position.X + t.TargetHouse.BoundingBoxSize.X / 2),
                    (int)(t.TargetHouse.Position.Y + t.TargetHouse.BoundingBoxSize.Y / 2),
                    new Raylib_CsLo.Color(240, 50, 50, 60));
            }
        }
    }
}
