using System.Numerics;
using Raylib_CsLo;
using VanEngine.Game.Architecture;
using VanEngine.Game.Core;
using VanEngine.Game.Forensics;
using VanEngine.Game.Infrastructure;
using VanEngine.Game.Simulation;
using static Raylib_CsLo.Raylib;
using RlVec2 = System.Numerics.Vector2;

namespace VanEngine.Game.UI;

public sealed class DashboardView : IDisposable
{
    private readonly SovereignState _state;
    private readonly TimePhaseController _timeController;
    private readonly SpatialEcosystemManager _ecoManager;
    private readonly WorkspaceManager _workspaceManager;
    private readonly CameraSystem _camera;
    private readonly InspectorPanel _inspector;
    private readonly HistoryTimeline _timeline;
    private readonly int _screenWidth;
    private readonly int _screenHeight;
    private readonly Dictionary<string, string> _cachedLogLines = new();
    private ReviewResult? _lastReview;
    private bool _showTribunal;
    private float _tribunalTimer;
    private bool _processingFile;
    private Citizen? _selectedCitizen;
    private bool _showCitizenFiles;
    private (int fromId, int toId, float similarity)? _hoveredLink;
    private float _timeSinceLastParticleEmit;
    private ProjectHouse? _contextHouse;
    private Citizen? _contextCitizen;
    private bool _showContextMenu;
    private string _saveStatus = string.Empty;
    private float _saveStatusTimer;
    private bool _showHelp;

    private struct Particle { public float X, Y; public float Life; public Color Color; }
    private readonly List<Particle> _particles = new();

    private int _previousFood, _previousWood, _previousStone, _previousMetal, _previousWealth;
    private float _trendTimer;

    private static Color C(byte r, byte g, byte b, byte a = 255) => new(r, g, b, a);

    public FileWatcherService? FileWatcher { get; set; }
    public ThreatController? ThreatCtrl { get; set; }
    public EventWebhook? Webhook { get; set; }
    public GitIntegrationEngine? GitEngine { get; set; }
    public ModLoader? ModLoader { get; set; }
    private string _gitStatus = string.Empty;
    private float _gitStatusTimer;

    public DashboardView(
        SovereignState state,
        TimePhaseController timeController,
        SpatialEcosystemManager ecoManager,
        WorkspaceManager workspaceManager,
        CameraSystem camera,
        InspectorPanel inspector,
        HistoryTimeline timeline,
        int width,
        int height)
    {
        _state = state;
        _timeController = timeController;
        _ecoManager = ecoManager;
        _workspaceManager = workspaceManager;
        _camera = camera;
        _inspector = inspector;
        _timeline = timeline;
        _screenWidth = width;
        _screenHeight = height;
        var res = _state.Resources;
        _previousFood = res.Food; _previousWood = res.Wood; _previousStone = res.Stone;
        _previousMetal = res.Metal; _previousWealth = res.Wealth;
    }

    public void HandlePhaseToggle()
    {
        if (IsKeyPressed(KeyboardKey.KEY_TAB))
        {
            _timeController.TogglePhase();
            bool isNight = _timeController.CurrentPhase == SimulationPhase.Nighttime;
            _timeline.AddEntry(_state.Year, "event", isNight ? "Night phase engaged" : "Day phase resumed", "system");
            _state.EnqueueLog(isNight
                ? "Night phase engaged \u2013 refactoring mode active."
                : "Day phase resumed \u2013 simulation clock running.");
        }
    }

    private AnalysisResult? _pendingAnalysis;
    private string _pendingFilePath = string.Empty;

    public void UpdateFileDrop()
    {
        if (!IsFileDropped() || _processingFile) return;

        var dropped = GetDroppedFilesAndClear();
        if (dropped.Length == 0) return;

        _processingFile = true;
        string path = dropped[0];
        if (!File.Exists(path)) { _processingFile = false; return; }

        _ = System.Threading.Tasks.Task.Run(() =>
        {
            string lang = TexStaticAnalyzer.DetectLanguageFromExtension(path);
            var analysis = lang != "unknown" && lang != "csharp"
                ? TexStaticAnalyzer.AnalyzeSourceFileMultiLang(path)
                : TexStaticAnalyzer.AnalyzeSourceFile(path);

            var review = new ReviewResult
            {
                TotalLines = analysis.TotalLines,
                ErrorCount = analysis.ErrorCount,
                WarningCount = analysis.WarningCount,
                ComplianceScore = analysis.ErrorCount == 0
                    ? 100.0
                    : Math.Max(0, 100.0 - analysis.ErrorCount * 20.0),
                ViolationCount = analysis.ErrorCount + analysis.WarningCount,
                Details = $"[{analysis.DiscoveredNamespace}] {analysis.DiscoveredClassName} ({lang}): " +
                          $"{analysis.ErrorCount} errors, {analysis.WarningCount} warnings",
            };

            _pendingAnalysis = analysis;
            _pendingFilePath = path;
            _lastReview = review;
            _showTribunal = true;
            _tribunalTimer = 0f;
            _processingFile = false;
        });
    }

    public void Update(float deltaTime)
    {
        _camera.Update();
        _inspector.Update(deltaTime);
        _timeline.Update();
        _timeController.UpdateTransition(deltaTime);

        if (_timeController.CurrentPhase == SimulationPhase.Nighttime && !_timeController.IsTransitioning)
        {
            foreach (var citizen in _state.Citizens)
            {
                if (!citizen.IsActive) continue;
                var house = _state.Houses.FirstOrDefault(h => h.RootNamespace == citizen.NamespaceFamily);
                if (house != null)
                    citizen.TargetPosition = house.Position + new Vector2(house.BoundingBoxSize.X / 2, house.BoundingBoxSize.Y / 2);
                var dir = citizen.TargetPosition - citizen.Position;
                if (dir.Length() > 0.1f)
                    citizen.Position += dir * 0.03f;
            }
        }

        if (_showTribunal && _lastReview != null)
        {
            _tribunalTimer += deltaTime;
            if (_tribunalTimer > 20f)
            {
                _showTribunal = false;
                _lastReview = null;
            }
        }

        _trendTimer += deltaTime;
        if (_trendTimer >= 1.0f)
        {
            _trendTimer = 0f;
            var res = _state.Resources;
            _previousFood = res.Food; _previousWood = res.Wood; _previousStone = res.Stone;
            _previousMetal = res.Metal; _previousWealth = res.Wealth;
        }

        _timeSinceLastParticleEmit += deltaTime;
        for (int i = _particles.Count - 1; i >= 0; i--)
        {
            var p = _particles[i];
            p.Life -= deltaTime;
            if (p.Life <= 0) _particles.RemoveAt(i);
            else _particles[i] = p;
        }

        if (_timeController.CurrentPhase == SimulationPhase.Daytime && _timeSinceLastParticleEmit > 0.1f)
        {
            _timeSinceLastParticleEmit = 0f;
            foreach (var house in _state.Houses)
            {
                if (house.CurrentState == BuildState.Error)
                {
                    for (int i = 0; i < 2; i++)
                        _particles.Add(new Particle { X = house.Position.X + GetRandomValue(0, (int)house.BoundingBoxSize.X), Y = house.Position.Y + GetRandomValue(0, (int)house.BoundingBoxSize.Y), Life = 0.8f, Color = C(80, 80, 80, 200) });
                }
                else if (house.CurrentState == BuildState.Warning)
                {
                    if (GetRandomValue(0, 3) == 0)
                        _particles.Add(new Particle { X = house.Position.X + GetRandomValue(0, (int)house.BoundingBoxSize.X), Y = house.Position.Y + GetRandomValue(0, (int)house.BoundingBoxSize.Y), Life = 0.6f, Color = C(255, 100, 0, 180) });
                }
                else if (house.CurrentState == BuildState.Success && GetRandomValue(0, 100) < 20)
                {
                    _particles.Add(new Particle { X = house.Position.X + GetRandomValue(0, (int)house.BoundingBoxSize.X), Y = house.Position.Y + GetRandomValue(0, (int)house.BoundingBoxSize.Y), Life = 0.4f, Color = C(0, 255, 100, 150) });
                }
            }
        }

        _state.FlushLogs();
        foreach (var log in _state.GetLogs())
            if (!_cachedLogLines.ContainsKey(log))
                _cachedLogLines[log] = WrapText(log, 70);

        if (_saveStatusTimer > 0)
        {
            _saveStatusTimer -= deltaTime;
            if (_saveStatusTimer <= 0) _saveStatus = string.Empty;
        }

        HandleKeyboardInput();
        HandleMouseInput();
        HandleContextMenuInput();
    }

    private void HandleKeyboardInput()
    {
        if (IsKeyPressed(KeyboardKey.KEY_S) && !IsKeyDown(KeyboardKey.KEY_LEFT_CONTROL) && !IsKeyDown(KeyboardKey.KEY_RIGHT_CONTROL))
        {
            string savePath = Path.Combine(SaveManager.DefaultSaveDir, $"frya_tex_save_{DateTime.Now:yyyyMMdd_HHmmss}.van");
            SaveManager.Save(_state, savePath);
            _saveStatus = $"Saved: {Path.GetFileName(savePath)}";
            _saveStatusTimer = 3f;
            _state.EnqueueLog($"Game saved to {Path.GetFileName(savePath)}");
        }

        if (IsKeyPressed(KeyboardKey.KEY_L) && !IsKeyDown(KeyboardKey.KEY_LEFT_CONTROL) && !IsKeyDown(KeyboardKey.KEY_RIGHT_CONTROL))
        {
            string latest = SaveManager.FindLatestSave();
            if (!string.IsNullOrEmpty(latest))
            {
                var data = SaveManager.Load(latest);
                SaveManager.Restore(_state, data);
                _saveStatus = $"Loaded: {Path.GetFileName(latest)}";
                _saveStatusTimer = 3f;
            }
        }

        if (IsKeyPressed(KeyboardKey.KEY_W))
        {
            var names = _workspaceManager.WorkspaceNames.ToList();
            int idx = names.IndexOf(_workspaceManager.ActiveName);
            int next = (idx + 1) % names.Count;
            _workspaceManager.SwitchTo(names[next]);
        }

        if (IsKeyPressed(KeyboardKey.KEY_E) && _timeline.IsExpanded)
        {
            string exportPath = Path.Combine(SaveManager.DefaultSaveDir, $"timeline_{DateTime.Now:yyyyMMdd_HHmmss}.txt");
            File.WriteAllText(exportPath, _timeline.ExportAsText());
            _state.EnqueueLog($"Timeline exported");
        }

        // ── Git Integration Keys ─────────────────────────────────────────
        if (IsKeyPressed(KeyboardKey.KEY_G) && !IsKeyDown(KeyboardKey.KEY_LEFT_CONTROL) && !IsKeyDown(KeyboardKey.KEY_RIGHT_CONTROL))
        {
            if (GitEngine != null)
            {
                if (GitEngine.HasUnresolvedConflicts)
                {
                    _state.AddLog("Cannot commit: resolve conflicts first");
                }
                else
                {
                    var type = GitEngine.PerformCommit();
                    _gitStatus = $"Commit on {GitEngine.CurrentBranch}: Year {_state.Year}";
                    _gitStatusTimer = 3f;
                    if (type == Simulation.GitEventType.Conflict)
                        _state.AddLog("ALERT: Conflict introduced during commit");
                }
            }
        }

        if (IsKeyPressed(KeyboardKey.KEY_B) && IsKeyDown(KeyboardKey.KEY_LEFT_CONTROL))
        {
            if (GitEngine != null)
            {
                string name = $"branch_{GitEngine.Branches.Count}";
                GitEngine.PerformBranch(name);
                _gitStatus = $"Branch '{name}' created";
                _gitStatusTimer = 3f;
            }
        }

        if (IsKeyPressed(KeyboardKey.KEY_M) && IsKeyDown(KeyboardKey.KEY_LEFT_CONTROL))
        {
            if (GitEngine != null)
            {
                var branches = GitEngine.Branches.Where(b => b.Name != GitEngine.CurrentBranch).ToList();
                if (branches.Count > 0)
                {
                    var target = branches[0];
                    GitEngine.PerformMerge(GitEngine.CurrentBranch, target.Name);
                    _gitStatus = $"Merged {GitEngine.CurrentBranch} → {target.Name}";
                    _gitStatusTimer = 3f;
                }
            }
        }

        if (IsKeyPressed(KeyboardKey.KEY_R) && IsKeyDown(KeyboardKey.KEY_LEFT_CONTROL))
        {
            if (GitEngine != null)
            {
                int targetYear = Math.Max(1, _state.Year - 3);
                GitEngine.PerformRebase(GitEngine.CurrentBranch, targetYear);
                _gitStatus = $"Rebase: time-travel to Year {targetYear}";
                _gitStatusTimer = 3f;
            }
        }

        // ── Report / Scoreboard Keys ─────────────────────────────────────
        if (IsKeyPressed(KeyboardKey.KEY_H) && !IsKeyDown(KeyboardKey.KEY_LEFT_CONTROL))
        {
            string path = ReportGenerator.GetDefaultReportPath("html");
            ReportGenerator.SaveHtmlReport(_state, path);
            _saveStatus = $"HTML report: {Path.GetFileName(path)}";
            _saveStatusTimer = 3f;
            _state.AddLog($"Health report exported (HTML): {Path.GetFileName(path)}");
        }

        if (IsKeyPressed(KeyboardKey.KEY_R) && !IsKeyDown(KeyboardKey.KEY_LEFT_CONTROL) && !IsKeyDown(KeyboardKey.KEY_RIGHT_CONTROL))
        {
            string path = ReportGenerator.GetDefaultReportPath("md");
            ReportGenerator.SaveMarkdownReport(_state, path);
            _saveStatus = $"Markdown report: {Path.GetFileName(path)}";
            _saveStatusTimer = 3f;
            _state.AddLog($"Health report exported (MD): {Path.GetFileName(path)}");
        }

        if (IsKeyPressed(KeyboardKey.KEY_F) && IsKeyDown(KeyboardKey.KEY_LEFT_CONTROL))
        {
            string path = Path.Combine(ScoreboardService.GetDefaultScoreDir(),
                $"score_{DateTime.Now:yyyyMMdd_HHmmss}.json");
            ScoreboardService.SaveToken(_state, path);
            _saveStatus = $"Score token: {Path.GetFileName(path)}";
            _saveStatusTimer = 3f;
            _state.AddLog($"Score token exported: {Path.GetFileName(path)}");
        }

        if (IsKeyPressed(KeyboardKey.KEY_SLASH))
            _showHelp = !_showHelp;
    }

    private void HandleMouseInput()
    {
        if (_timeController.CurrentPhase != SimulationPhase.Daytime) return;

        Vector2 mousePos = GetMousePosition();
        var worldMouse = _camera.ScreenToWorld(GetMousePosition());

        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_RIGHT))
        {
            foreach (var house in _state.Houses)
            {
                float wx = house.Position.X, wy = house.Position.Y;
                float ww = house.BoundingBoxSize.X, wh = house.BoundingBoxSize.Y;
                var worldP = worldMouse;
                if (worldP.X >= wx && worldP.X <= wx + ww && worldP.Y >= wy && worldP.Y <= wy + wh)
                {
                    _contextHouse = house;
                    _contextCitizen = null;
                    _showContextMenu = true;
                    return;
                }
            }

            foreach (var citizen in _state.Citizens)
            {
                if (!citizen.IsActive) continue;
                float dx = worldMouse.X - citizen.Position.X;
                float dy = worldMouse.Y - citizen.Position.Y;
                if (dx * dx + dy * dy < 400)
                {
                    _contextCitizen = citizen;
                    _contextHouse = null;
                    _showContextMenu = true;
                    return;
                }
            }
            _showContextMenu = false;
        }

        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            foreach (var house in _state.Houses)
            {
                float wx = house.Position.X, wy = house.Position.Y;
                float ww = house.BoundingBoxSize.X, wh = house.BoundingBoxSize.Y;
                if (worldMouse.X >= wx && worldMouse.X <= wx + ww && worldMouse.Y >= wy && worldMouse.Y <= wy + wh)
                {
                    _inspector.SelectHouse(house);
                    return;
                }
            }

            foreach (var citizen in _state.Citizens)
            {
                if (!citizen.IsActive) continue;
                float dx = worldMouse.X - citizen.Position.X;
                float dy = worldMouse.Y - citizen.Position.Y;
                if (dx * dx + dy * dy < 400)
                {
                    _inspector.SelectCitizen(citizen);
                    return;
                }
            }

            if (_showContextMenu)
            {
                var m = GetMousePosition();
                if (_contextHouse != null)
                {
                    float mx = m.X, my = m.Y;
                    if (!(mx >= _screenWidth - 200 && mx <= _screenWidth && my >= 0 && my <= 200))
                        _showContextMenu = false;
                }
                else
                {
                    _showContextMenu = false;
                }
            }
        }
    }

    private void HandleContextMenuInput()
    {
        if (!_showContextMenu) return;
        if (!IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT)) return;

        var m = GetMousePosition();
        int mx = (int)m.X;

        if (_contextHouse != null)
        {
            if (mx >= _screenWidth - 180 && mx <= _screenWidth)
            {
                if (m.Y >= 0 && m.Y < 25)
                {
                    _state.ModifyResources(new ResourcePack { Wealth = -20 });
                    _contextHouse.ProjectName += "_renamed";
                    _state.EnqueueLog($"Renamed: {_contextHouse.ProjectName}");
                    _showContextMenu = false;
                }
                else if (m.Y >= 30 && m.Y < 55)
                {
                    if (_state.Houses.Count > 1)
                    {
                        _state.ModifyResources(new ResourcePack { Wealth = -30 });
                        var target = _state.Houses.FirstOrDefault(h => h.Id != _contextHouse.Id);
                        if (target != null)
                        {
                            int half = _contextHouse.TrackedFiles.Count / 2;
                            var splitHouse = new ProjectHouse(_contextHouse.ProjectName + "_split", _contextHouse.RootNamespace + ".Split",
                                _contextHouse.Position + new Vector2(150, 0));
                            for (int i = 0; i < half && _contextHouse.TrackedFiles.Count > 0; i++)
                            {
                                var f = _contextHouse.TrackedFiles[^1];
                                splitHouse.TrackedFiles.Add(f);
                                _contextHouse.TrackedFiles.RemoveAt(_contextHouse.TrackedFiles.Count - 1);
                            }
                            splitHouse.EvaluateBuildState();
                            _state.AddHouse(splitHouse);
                            _contextHouse.EvaluateBuildState();
                            _state.EnqueueLog($"Split: {_contextHouse.ProjectName}");
                        }
                    }
                    _showContextMenu = false;
                }
                else if (m.Y >= 60 && m.Y < 85)
                {
                    if (_state.Houses.Count > 1)
                    {
                        _state.ModifyResources(new ResourcePack { Wealth = -10 });
                        var target = _state.Houses.FirstOrDefault(h => h.Id != _contextHouse.Id);
                        if (target != null)
                        {
                            foreach (var f in _contextHouse.TrackedFiles)
                                target.TrackedFiles.Add(f);
                            target.EvaluateBuildState();
                            _state.RemoveHouse(_contextHouse);
                            _state.EnqueueLog($"Merged into: {target.ProjectName}");
                        }
                    }
                    _showContextMenu = false;
                }
                else if (m.Y >= 90 && m.Y < 115)
                {
                    _contextHouse.IsCommons = !_contextHouse.IsCommons;
                    _state.EnqueueLog(_contextHouse.IsCommons ? $"Commons designated: {_contextHouse.ProjectName}" : $"Commons revoked: {_contextHouse.ProjectName}");
                    _showContextMenu = false;
                }
                else if (m.Y >= 120 && m.Y < 145)
                {
                    if (_contextHouse.Tier < UpgradeTier.Citadel)
                    {
                        var next = _contextHouse.Tier + 1;
                        int cost = _contextHouse.UpgradeCost(next);
                        var res = _state.Resources;
                        if (res.Gold >= cost)
                        {
                            _state.ModifyResources(new ResourcePack { Gold = -cost });
                            _contextHouse.Upgrade(next);
                            _state.EnqueueLog($"Upgraded {_contextHouse.ProjectName} to {next}");
                            _state.AddTimelineEntry(_state.Year, "house", $"Upgraded {_contextHouse.ProjectName} to {next}", "upgrade");
                        }
                        else
                            _state.EnqueueLog($"Not enough Gold for upgrade (need {cost})");
                    }
                    _showContextMenu = false;
                }
            }
        }
        else if (_contextCitizen != null)
        {
            if (mx >= _screenWidth - 180 && mx <= _screenWidth)
            {
                if (m.Y >= 0 && m.Y < 25)
                {
                    var target = _state.Citizens.FirstOrDefault(c => c.IsActive && c.Id != _contextCitizen.Id);
                    if (target != null)
                        _ecoManager.GiftHomelessToCitizen(_contextCitizen, target);
                    _showContextMenu = false;
                }
                else if (m.Y >= 30 && m.Y < 55)
                {
                    _contextCitizen.IsActive = false;
                    _state.RemoveCitizen(_contextCitizen);
                    _state.EnqueueLog($"Citizen retired: {_contextCitizen.Name}");
                    _showContextMenu = false;
                }
            }
        }
    }

    public void Draw()
    {
        bool isNight = _timeController.CurrentPhase == SimulationPhase.Nighttime;
        bool transitioning = _timeController.IsTransitioning;

        var dayBg = C(12, 14, 18);
        var nightBg = C(0, 4, 28);
        var bg = transitioning ? _timeController.LerpColor(dayBg, nightBg) : (isNight ? nightBg : dayBg);

        ClearBackground(bg);

        _camera.BeginView();
        DrawWorld(transitioning);
        _camera.EndView();

        DrawUI(transitioning);
        DrawOverlays();
    }

    private void DrawWorld(bool transitioning)
    {
        Vector2 mousePos = GetMousePosition();
        var worldMouse = _camera.ScreenToWorld(GetMousePosition());

        bool isNight = _timeController.CurrentPhase == SimulationPhase.Nighttime;

        if (!isNight || transitioning)
        {
            _hoveredLink = null;
            var links = _ecoManager.ComputeSimilarityLinks();
            foreach (var link in links)
            {
                var c1 = _state.Citizens.FirstOrDefault(c => c.Id == link.Key.Item1);
                var c2 = _state.Citizens.FirstOrDefault(c => c.Id == link.Key.Item2);
                if (c1 != null && c2 != null)
                {
                    var p1 = c1.Position;
                    var p2 = c2.Position;
                    var lineColor = C(200, 200, 255, 100);
                    if (IsPointOnLine(worldMouse, p1, p2, 5))
                    {
                        lineColor = C(255, 255, 100, 200);
                        _hoveredLink = (c1.Id, c2.Id, link.Value);
                    }
                    DrawLine((int)p1.X, (int)p1.Y, (int)p2.X, (int)p2.Y, lineColor);
                }
            }

            DrawCrossWorkspaceDependencyGraph();

            foreach (var link in links.Where(l => l.Value > 0.85f))
            {
                var c1 = _state.Citizens.FirstOrDefault(c => c.Id == link.Key.Item1);
                var c2 = _state.Citizens.FirstOrDefault(c => c.Id == link.Key.Item2);
                if (c1 != null && c2 != null)
                {
                    var mid = (c1.Position + c2.Position) / 2;
                    DrawCircle((int)mid.X, (int)mid.Y, 12, C(255, 100, 100, 200));
                    DrawText("*", (int)mid.X - 6, (int)mid.Y - 8, 14, WHITE);

                    if (_ecoManager.ComputeSimilarityLinks().Any(l => l.Value > 0.85f))
                    {
                        _timeline.AddEntry(_state.Year, "event", "High similarity link detected", "system");
                    }
                }
            }

            foreach (var house in _state.Houses)
            {
                var baseColor = house.CurrentState switch
                {
                    BuildState.Success => C(0, 220, 140),
                    BuildState.Warning => C(240, 200, 50),
                    BuildState.Error => C(240, 70, 70),
                    BuildState.Missing => C(50, 150, 200),
                    _ => C(40, 40, 50),
                };
                int hash = house.RootNamespace?.GetHashCode() ?? 0;
                var tint = C((byte)(hash & 0xFF), (byte)((hash >> 8) & 0xFF), (byte)((hash >> 16) & 0xFF), 30);

                int hx = (int)house.Position.X;
                int hy = (int)house.Position.Y;
                int hw = (int)house.BoundingBoxSize.X;
                int hh = (int)house.BoundingBoxSize.Y;

                if (house.IsCommons)
                {
                    DrawRectangle(hx - 6, hy - 6, hw + 12, hh + 12, C(100, 200, 255, 40));
                    DrawRectangleLinesEx(new Rectangle(hx - 6, hy - 6, hw + 12, hh + 12), 1, C(100, 200, 255, 120));
                }

                DrawRectangle(hx, hy, hw, hh, baseColor);
                DrawRectangle(hx, hy, hw, hh, tint);

                float borderThick = house.CollapseTimerSeconds > 0 ? 4f : (house.IsCommons ? 3f : 2f);
                if (house.HasBackyardTreasure) borderThick = 4f;
                DrawRectangleLinesEx(new Rectangle(hx, hy, hw, hh), borderThick, WHITE);

                DrawText(house.ProjectName, hx + 10, hy + 10, 12, WHITE);

                string tierLabel = house.Tier switch
                {
                    UpgradeTier.Village => "[Village]",
                    UpgradeTier.Town => "[Town]",
                    UpgradeTier.Citadel => "[CITADEL]",
                    _ => "",
                };
                if (tierLabel.Length > 0)
                    DrawText(tierLabel, hx + 10, hy + 68, 8, C(255, 215, 0));

                if (house.IsCommons)
                    DrawText("[COMMONS]", hx + 10, hy + 26, 9, C(100, 200, 255));

                int citizenCount = _state.Citizens.Count(c => !c.IsHomeless && c.NamespaceFamily == house.RootNamespace);
                if (citizenCount > 0)
                {
                    string badge = citizenCount.ToString();
                    DrawCircle(hx + hw - 12, hy + 12, 10, RED);
                    DrawText(badge, hx + hw - 17, hy + 6, 12, WHITE);
                }

                if (house.CurrentState == BuildState.Error && house.CollapseTimerSeconds > 0)
                {
                    float ratio = house.CollapseTimerSeconds / ProjectHouse.MaxRectificationWindow;
                    int barWidth = (int)(hw * ratio);
                    DrawRectangle(hx, hy + hh - 8, barWidth, 6, RED);
                }

                if (house.HasBackyardTreasure)
                {
                    var gold = C(255, 215, 0);
                    DrawRectangle(hx + 80, hy + 60, 24, 24, gold);
                    DrawText("$", hx + 84, hy + 62, 18, BLACK);
                }
            }

            foreach (var citizen in _state.Citizens)
            {
                if (!citizen.IsActive) continue;
                var roleColor = citizen.RoleType switch
                {
                    0 => C(160, 160, 160),
                    1 => C(0, 220, 140),
                    2 => C(0, 160, 255),
                    5 => C(255, 215, 0),
                    _ => C(200, 200, 200),
                };
                int radius = 8;
                if (citizen.DecayTimer > 0)
                    DrawCircleLines((int)citizen.Position.X, (int)citizen.Position.Y, radius + 2, RED);

                DrawCircle((int)citizen.Position.X, (int)citizen.Position.Y, radius, roleColor);
                if (citizen.IsHomeless)
                    DrawCircle((int)citizen.Position.X, (int)citizen.Position.Y, radius, C(0, 100, 200, 200));

                float dx = worldMouse.X - citizen.Position.X;
                float dy = worldMouse.Y - citizen.Position.Y;
                if (dx * dx + dy * dy < 400)
                {
                    DrawText(citizen.Name, (int)citizen.Position.X + 10, (int)citizen.Position.Y - 10, 10, WHITE);
                    DrawCitizenTooltip(citizen);
                }
            }

            foreach (var p in _particles)
                DrawCircle((int)p.X, (int)p.Y, 2, p.Color);

            if (_hoveredLink.HasValue)
            {
                DrawText($"Similarity: {_hoveredLink.Value.similarity * 100:F1}%", 10, _screenHeight - 60, 14, YELLOW);
            }

            if (ThreatCtrl != null)
            {
                var wm = _camera.ScreenToWorld(GetMousePosition());
                ThreatCtrl.DrawThreats(wm.X, wm.Y);
            }

            var tradeRoutes = _state.GetTradeRoutes();
            foreach (var route in tradeRoutes)
            {
                if (!route.IsActive) continue;
                var packets = _workspaceManager.GetWorkspace(route.FromWorkspace)?.State.Houses;
                var toHouses = _workspaceManager.GetWorkspace(route.ToWorkspace)?.State.Houses;
                if (packets == null || packets.Count == 0 || toHouses == null || toHouses.Count == 0) continue;

                var f = packets.First();
                var t = toHouses.First();
                float fx = f.Position.X + f.BoundingBoxSize.X / 2;
                float fy = f.Position.Y + f.BoundingBoxSize.Y / 2;
                float tx = t.Position.X + t.BoundingBoxSize.X / 2;
                float ty = t.Position.Y + t.BoundingBoxSize.Y / 2;

                DrawLine((int)fx, (int)fy, (int)tx, (int)ty, C(100, 200, 255, 60));
                DrawCircleLines((int)route.PacketX, (int)route.PacketY, 5, C(100, 200, 255, 150));
                DrawCircle((int)route.PacketX, (int)route.PacketY, 3, C(100, 200, 255));
            }
        }

        if (isNight && !transitioning)
        {
            DrawBlueprintOverlay();
        }
        else if (transitioning)
        {
            float t = _timeController.TransitionProgress;
            int nightAlpha = (int)(235 * t);
            if (nightAlpha > 0)
            {
                DrawRectangle(0, 0, _screenWidth, _screenHeight, C(0, 4, 28, (byte)nightAlpha));
                if (t > 0.3f)
                {
                    float starAlpha = (t - 0.3f) / 0.7f;
                    DrawStars((byte)(180 * starAlpha));
                }
            }
        }
    }

    private void DrawStars(byte alpha)
    {
        var rng = new Random(42);
        for (int i = 0; i < 60; i++)
        {
            int sx = rng.Next(0, _screenWidth);
            int sy = rng.Next(0, _screenHeight);
            DrawCircle(sx, sy, rng.Next(1, 3), C(255, 255, 200, alpha));
        }
    }

    private void DrawCrossWorkspaceDependencyGraph()
    {
        var crossSim = _workspaceManager.ComputeCrossWorkspaceSimilarity();
        var wsNames = _workspaceManager.WorkspaceNames.ToList();

        if (wsNames.Count < 2) return;

        var centers = new Dictionary<string, Vector2>();

        for (int i = 0; i < wsNames.Count; i++)
        {
            var state_i = _workspaceManager.GetWorkspace(wsNames[i])?.State;
            if (state_i == null) continue;

            var houses = state_i.Houses;
            if (houses.Count > 0)
            {
                float cx = houses.Average(h => h.Position.X + h.BoundingBoxSize.X / 2);
                float cy = houses.Average(h => h.Position.Y + h.BoundingBoxSize.Y / 2);
                centers[wsNames[i]] = new Vector2(cx, cy);
            }
        }

        foreach (var kvp in crossSim)
        {
            if (!centers.TryGetValue(kvp.Key.Item1, out var c1) ||
                !centers.TryGetValue(kvp.Key.Item2, out var c2))
                continue;

            float sim = kvp.Value;
            if (sim < 0.2f) continue;

            var lineColor = sim > 0.7f
                ? C(240, 70, 70, (byte)(150 * sim))
                : C(100, 200, 255, (byte)(100 * sim));

            DrawLine((int)c1.X, (int)c1.Y, (int)c2.X, (int)c2.Y, lineColor);

            if (sim > 0.7f)
            {
                var mid = (c1 + c2) / 2;
                DrawCircle((int)mid.X, (int)mid.Y, 6, C(240, 70, 70, 180));
                DrawText("!", (int)mid.X - 4, (int)mid.Y - 6, 12, WHITE);
            }
        }
    }

    private void DrawUI(bool transitioning)
    {
        bool isNight = _timeController.CurrentPhase == SimulationPhase.Nighttime;

        DrawWorkspaceTabs();

        if (isNight && !transitioning)
        {
            DrawRectangle(20, 63, 300, 57, C(0, 10, 50, 200));
            DrawText("RESOURCES PAUSED", 35, 75, 14, C(60, 120, 255));
            DrawText("No decay | No attack risk | Drag freely", 35, 96, 11, C(40, 90, 200));
        }

        if (!isNight || transitioning)
        {
            DrawRectangle(20, 120, 300, 510, C(22, 26, 34));
            DrawLine(20, 165, 320, 165, C(110, 120, 140));
            DrawText("STATE RESOURCES", 35, 132, 16, C(210, 215, 224));

            var res = _state.Resources;
            DrawResourceMetric("FOOD:", res.Food, _previousFood, 35, 185);
            DrawResourceMetric("WOOD:", res.Wood, _previousWood, 35, 215);
            DrawResourceMetric("STONE:", res.Stone, _previousStone, 35, 245);
            DrawResourceMetric("METAL:", res.Metal, _previousMetal, 35, 275);
            DrawResourceMetric("WEALTH:", res.Wealth, _previousWealth, 35, 305);
            DrawResourceMetric("GOLD:", res.Gold, 0, 35, 335);

            DrawText("CITIZENS", 35, 370, 16, C(210, 215, 224));
            int y = 400;
            foreach (var citizen in _state.Citizens)
            {
                string line = $"{citizen.Name} ({citizen.OwnedFiles.Count} files)";
                DrawText(line, 35, y, 12, C(210, 215, 224));
                y += 18;
                if (y > 550) break;
            }

            DrawRectangle(340, 120, 470, 510, C(22, 26, 34));
            DrawText("SYSTEM CHRONICLES", 355, 135, 16, C(210, 215, 224));
            DrawLine(340, 165, 810, 165, C(110, 120, 140));
            int ly = 180;
            foreach (var log in _state.GetLogs())
            {
                string wrapped = _cachedLogLines.TryGetValue(log, out var w) ? w : log;
                var col = C(210, 215, 224);
                if (log.Contains("Violation") || log.Contains("penalty")) col = C(240, 70, 70);
                else if (log.Contains("Compliant") || log.Contains("reward")) col = C(0, 220, 140);
                else if (log.Contains("ALERT")) col = C(240, 200, 50);
                DrawText(wrapped, 355, ly, 12, col);
                ly += 20;
                if (ly > 570) break;
            }

            DrawRectangle(830, 120, 430, 250, C(22, 26, 34));
            DrawText("CITADEL RADAR", 845, 135, 16, C(210, 215, 224));
            DrawLine(830, 165, 1260, 165, C(110, 120, 140));
            DrawJuulWheel(_screenWidth - 110, 190, 70);
            DrawRadar();

            _timeline.Draw(830, 390, 430, 240);

            DrawSaveLoadButtons();
            DrawWatcherStatus();
            DrawGitControls();
            DrawReportAndScoreButtons();
            DrawGitConflictOverlay();
            DrawContextMenu();
        }

        if (_showContextMenu)
        {
            DrawContextMenu();
        }
    }

    private void DrawWorkspaceTabs()
    {
        int tabX = 340;
        int tabY = 86;
        int tabH = 28;
        int tabW = 100;

        DrawRectangle(tabX - 5, tabY - 5, _workspaceManager.WorkspaceNames.Count() * tabW + 15, tabH + 10, C(22, 26, 34));

        int i = 0;
        foreach (var name in _workspaceManager.WorkspaceNames)
        {
            bool active = name == _workspaceManager.ActiveName;
            var bg = active ? C(60, 100, 180) : C(30, 35, 45);
            DrawRectangle(tabX, tabY, tabW, tabH, bg);
            DrawText(name, tabX + 5, tabY + 6, 12, active ? WHITE : C(110, 120, 140));

            if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
            {
                var m = GetMousePosition();
                if (m.X >= tabX && m.X <= tabX + tabW && m.Y >= tabY && m.Y <= tabY + tabH)
                {
                    if (name != _workspaceManager.ActiveName)
                    {
                        _workspaceManager.SwitchTo(name);
                        _timeline.AddEntry(_state.Year, "event", $"Switched to workspace '{name}'", "system");
                    }
                }
            }

            tabX += tabW + 3;
            i++;
        }

        DrawRectangleLinesEx(new Rectangle(340 - 5, tabY - 5,
            _workspaceManager.WorkspaceNames.Count() * (tabW + 3) + 10, tabH + 10), 1, C(60, 120, 200, 100));
    }

    private void DrawSaveLoadButtons()
    {
        int bx = 20, by = _screenHeight - 40;
        DrawRectangle(bx, by, 80, 28, C(30, 40, 60));
        DrawText("SAVE [S]", bx + 5, by + 5, 12, C(0, 220, 140));
        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X >= bx && m.X <= bx + 80 && m.Y >= by && m.Y <= by + 28)
            {
                string savePath = Path.Combine(SaveManager.DefaultSaveDir, $"quick_save_{DateTime.Now:yyyyMMdd_HHmmss}.van");
                SaveManager.Save(_state, savePath);
                _saveStatus = "Saved!";
                _saveStatusTimer = 2f;
                _state.EnqueueLog("Quick save");
            }
        }

        DrawRectangle(bx + 90, by, 80, 28, C(30, 40, 60));
        DrawText("LOAD [L]", bx + 93, by + 5, 12, C(240, 200, 50));
        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X >= bx + 90 && m.X <= bx + 170 && m.Y >= by && m.Y <= by + 28)
            {
                string latest = SaveManager.FindLatestSave();
                if (!string.IsNullOrEmpty(latest))
                {
                    var data = SaveManager.Load(latest);
                    SaveManager.Restore(_state, data);
                    _saveStatus = "Loaded!";
                    _saveStatusTimer = 2f;
                }
            }
        }

        if (!string.IsNullOrEmpty(_saveStatus))
        {
            DrawText(_saveStatus, bx + 180, by + 5, 11, C(0, 220, 140));
        }
    }

    private void DrawWatcherStatus()
    {
        int wx = 110, wy = _screenHeight - 40;
        bool active = FileWatcher?.IsActive ?? false;
        var col = active ? C(0, 220, 140) : C(110, 120, 140);
        string label = active ? "WATCHER: ON" : "WATCHER: OFF";
        if (FileWatcher != null)
            label += $" ({FileWatcher.WatchedFiles} files)";
        DrawText(label, wx, wy, 11, col);

        bool webhookActive = Webhook?.IsRunning ?? false;
        var whCol = webhookActive ? C(0, 220, 140) : C(110, 120, 140);
        string whLabel = webhookActive ? $"WEBHOOK: :{Webhook!.Port}" : "WEBHOOK: OFF";
        DrawText(whLabel, wx, wy + 14, 11, whCol);
    }

    private void DrawGitControls()
    {
        int y = _screenHeight - 20;
        int x = 260;

        var gitCol = GitEngine != null ? C(0, 220, 140) : C(110, 120, 140);
        string gitLabel = GitEngine != null
            ? $"GIT: {GitEngine.CurrentBranch} ({GitEngine.CommitCount} commits)"
            : "GIT: OFF";
        DrawText(gitLabel, x, y, 11, gitCol);

        if (!string.IsNullOrEmpty(_gitStatus))
        {
            DrawText(_gitStatus, x, y + 14, 11, C(240, 200, 50));
            _gitStatusTimer -= GetFrameTime();
            if (_gitStatusTimer <= 0) _gitStatus = string.Empty;
        }

        if (GitEngine != null && _timeController.CurrentPhase == SimulationPhase.Daytime)
        {
            int bx = x + 200;
            DrawRectangle(bx, y - 3, 50, 16, C(30, 40, 60));
            DrawText("COMMIT", bx + 2, y, 10, C(0, 220, 140));
            if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
            {
                var m = GetMousePosition();
                if (m.X >= bx && m.X <= bx + 50 && m.Y >= y - 3 && m.Y <= y + 13)
                {
                    if (GitEngine.HasUnresolvedConflicts)
                        _state.AddLog("Cannot commit: resolve conflicts first");
                    else
                        GitEngine.PerformCommit();
                }
            }

            DrawRectangle(bx + 55, y - 3, 50, 16, C(40, 30, 60));
            DrawText("BRANCH", bx + 57, y, 10, C(200, 120, 255));
            if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
            {
                var m = GetMousePosition();
                if (m.X >= bx + 55 && m.X <= bx + 105 && m.Y >= y - 3 && m.Y <= y + 13)
                {
                    string name = $"branch_{GitEngine.Branches.Count}";
                    GitEngine.PerformBranch(name);
                }
            }

            DrawRectangle(bx + 110, y - 3, 50, 16, C(60, 40, 40));
            DrawText("MERGE", bx + 112, y, 10, C(240, 200, 50));
            if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
            {
                var m = GetMousePosition();
                if (m.X >= bx + 110 && m.X <= bx + 160 && m.Y >= y - 3 && m.Y <= y + 13)
                {
                    var branches = GitEngine.Branches.Where(b => b.Name != GitEngine.CurrentBranch).ToList();
                    if (branches.Count > 0)
                        GitEngine.PerformMerge(GitEngine.CurrentBranch, branches[0].Name);
                }
            }

            DrawRectangle(bx + 165, y - 3, 50, 16, C(40, 40, 60));
            DrawText("REBASE", bx + 167, y, 10, C(100, 150, 255));
            if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
            {
                var m = GetMousePosition();
                if (m.X >= bx + 165 && m.X <= bx + 215 && m.Y >= y - 3 && m.Y <= y + 13)
                {
                    int targetYear = Math.Max(1, _state.Year - 3);
                    GitEngine.PerformRebase(GitEngine.CurrentBranch, targetYear);
                }
            }
        }

        // Mod status
        int mx = 260, my = _screenHeight - 38;
        string modLine = ModLoader?.GetStatusLine() ?? "MODS: OFF";
        DrawText(modLine, mx, my, 11, ModLoader != null && ModLoader.LoadedCount > 0 ? C(0, 220, 140) : C(110, 120, 140));
    }

    private void DrawReportAndScoreButtons()
    {
        int bx = 680, by = _screenHeight - 40;

        DrawRectangle(bx, by, 70, 28, C(40, 30, 50));
        DrawText("REPORT", bx + 5, by + 5, 12, C(100, 200, 255));
        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X >= bx && m.X <= bx + 70 && m.Y >= by && m.Y <= by + 28)
            {
                string path = ReportGenerator.GetDefaultReportPath("html");
                ReportGenerator.SaveHtmlReport(_state, path);
                _saveStatus = $"HTML report: {Path.GetFileName(path)}";
                _saveStatusTimer = 3f;
                _state.AddLog($"Health report exported (HTML)");
            }
        }

        DrawRectangle(bx + 75, by, 50, 28, C(30, 40, 50));
        DrawText("SCORE", bx + 80, by + 5, 12, C(255, 215, 0));
        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X >= bx + 75 && m.X <= bx + 125 && m.Y >= by && m.Y <= by + 28)
            {
                string path = Path.Combine(ScoreboardService.GetDefaultScoreDir(),
                    $"score_{DateTime.Now:yyyyMMdd_HHmmss}.json");
                ScoreboardService.SaveToken(_state, path);
                _saveStatus = $"Score token: {Path.GetFileName(path)}";
                _saveStatusTimer = 3f;
                _state.AddLog($"Score token exported");
            }
        }

        DrawRectangle(bx + 130, by, 70, 28, C(40, 50, 30));
        DrawText("MD REP", bx + 135, by + 5, 12, C(0, 220, 140));
        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X >= bx + 130 && m.X <= bx + 200 && m.Y >= by && m.Y <= by + 28)
            {
                string path = ReportGenerator.GetDefaultReportPath("md");
                ReportGenerator.SaveMarkdownReport(_state, path);
                _saveStatus = $"Markdown report: {Path.GetFileName(path)}";
                _saveStatusTimer = 3f;
                _state.AddLog($"Health report exported (MD)");
            }
        }
    }

    private void DrawGitConflictOverlay()
    {
        if (GitEngine == null || !GitEngine.HasUnresolvedConflicts) return;

        int y = 88;
        foreach (var conflict in GitEngine.Conflicts)
        {
            if (conflict.IsResolved) continue;
            var col = conflict.DecayTimer < 10f
                ? C(240, 50, 50, 220)
                : C(240, 200, 50, 220);
            string label = $"CONFLICT: {conflict.FilePath} [{conflict.DecayTimer:F0}s]";
            DrawText(label, _screenWidth - 280, y, 10, col);

            string resolveKey = $"[click to resolve]";
            DrawText(resolveKey, _screenWidth - 100, y, 10, C(0, 220, 140));

            if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
            {
                var m = GetMousePosition();
                if (m.X >= _screenWidth - 280 && m.X <= _screenWidth - 60 && m.Y >= y && m.Y <= y + 14)
                {
                    GitEngine.ResolveConflict(conflict.Id);
                    _state.AddLog($"Conflict resolved via click: {conflict.FilePath}");
                }
            }

            y += 14;
            if (y > _screenHeight - 80) break;
        }
    }

    private void DrawHelpOverlay()
    {
        bool isDay = _timeController.CurrentPhase == SimulationPhase.Daytime && !_timeController.IsTransitioning;
        bool isNight = _timeController.CurrentPhase == SimulationPhase.Nighttime && !_timeController.IsTransitioning;
        bool transition = _timeController.IsTransitioning;

        DrawRectangle(0, 0, _screenWidth, _screenHeight, C(5, 7, 14, 230));

        int boxX = 60, boxY = 40, boxW = _screenWidth - 120, boxH = _screenHeight - 80;
        DrawRectangle(boxX, boxY, boxW, boxH, C(16, 20, 28));
        DrawRectangleLinesEx(new Rectangle(boxX, boxY, boxW, boxH), 2, C(60, 120, 200, 180));

        DrawText("KEYBOARD SHORTCUTS", boxX + 30, boxY + 18, 22, C(240, 200, 50));
        DrawText("[/] toggle help  |  Click outside or [/] to close", boxX + 30, boxY + 48, 12, C(110, 120, 140));

        int colX = boxX + 30;
        int colW = (boxW - 80) / 2;
        int y = boxY + 80;

        // ── Group: General (always) ─────────────────────────────────────
        DrawText("GENERAL", colX, y, 14, C(100, 170, 255));
        y += 22;
        DrawText("  TAB           Toggle day/night phase", colX, y, 12, C(210, 215, 224)); y += 17;
        DrawText("  S             Save game", colX, y, 12, C(210, 215, 224)); y += 17;
        DrawText("  L             Load latest save", colX, y, 12, C(210, 215, 224)); y += 17;
        DrawText("  W             Cycle workspaces", colX, y, 12, C(210, 215, 224)); y += 17;
        DrawText("  /             Toggle this help", colX, y, 12, C(210, 215, 224)); y += 17;
        y += 6;

        // ── Reports / Scoreboard (always) ───────────────────────────────
        DrawText("REPORTS & SCOREBOARD", colX, y, 14, C(100, 200, 150));
        y += 22;
        DrawText("  H             Export HTML health report", colX, y, 12, C(210, 215, 224)); y += 17;
        DrawText("  R             Export Markdown health report", colX, y, 12, C(210, 215, 224)); y += 17;
        DrawText("  Ctrl+F        Export signed score token", colX, y, 12, C(210, 215, 224)); y += 17;
        y += 6;

        // ── Git Commands (daytime only) ─────────────────────────────────
        if (GitEngine != null && isDay)
        {
            DrawText("GIT COMMANDS", colX, y, 14, C(200, 120, 255));
            y += 22;
            DrawText("  G             Commit (advances year)", colX, y, 12, C(210, 215, 224)); y += 17;
            DrawText("  Ctrl+B        Create new branch", colX, y, 12, C(210, 215, 224)); y += 17;
            DrawText("  Ctrl+M        Merge to first branch", colX, y, 12, C(210, 215, 224)); y += 17;
            DrawText("  Ctrl+R        Rebase (time-travel -3yr)", colX, y, 12, C(210, 215, 224)); y += 17;
            if (GitEngine.HasUnresolvedConflicts)
                DrawText("  Click label   Resolve merge conflict", colX, y, 12, C(0, 220, 140)); y += 17;
            y += 6;
        }
        else if (GitEngine != null && !isDay)
        {
            DrawText("GIT COMMANDS", colX, y, 14, C(80, 80, 100));
            y += 22;
            DrawText("  (unavailable during nighttime)", colX, y, 12, C(80, 80, 100)); y += 17;
            y += 6;
        }

        // ── Camera (always) ─────────────────────────────────────────────
        y = boxY + 80; // reset to top of right column
        int rightCol = colX + colW + 20;

        DrawText("CAMERA & NAVIGATION", rightCol, y, 14, C(100, 170, 255));
        y += 22;
        DrawText("  Middle-drag    Pan camera", rightCol, y, 12, C(210, 215, 224)); y += 17;
        DrawText("  Scroll         Zoom in/out", rightCol, y, 12, C(210, 215, 224)); y += 17;
        DrawText("  Edge-scroll    Pan to edges", rightCol, y, 12, C(210, 215, 224)); y += 17;
        DrawText("  Left-click     Select house/citizen", rightCol, y, 12, C(210, 215, 224)); y += 17;
        DrawText("  Right-click    Context menu (house/citizen)", rightCol, y, 12, C(210, 215, 224)); y += 17;
        y += 6;

        // ── Tribunal (if active) ────────────────────────────────────────
        if (_showTribunal)
        {
            DrawText("CODE REVIEW TRIBUNAL", rightCol, y, 14, C(240, 200, 50));
            y += 22;
            DrawText("  A             Accept file (apply consequences)", rightCol, y, 12, C(210, 215, 224)); y += 17;
            DrawText("  B             Dismiss / reject file", rightCol, y, 12, C(210, 215, 224)); y += 17;
            y += 6;
        }

        // ── Selected citizen (if any) ───────────────────────────────────
        if (_selectedCitizen != null)
        {
            DrawText("SELECTED CITIZEN", rightCol, y, 14, C(0, 220, 140));
            y += 22;
            DrawText("  Right-click    Gift files / Retire", rightCol, y, 12, C(210, 215, 224)); y += 17;
            DrawText("  Left-click     Inspect citizen details", rightCol, y, 12, C(210, 215, 224)); y += 17;
            if (_selectedCitizen.IsHomeless)
                DrawText("  (homeless — assign to house)", rightCol, y, 12, C(240, 200, 50)); y += 17;
            y += 6;
        }

        // ── Selected / context house (if any) ──────────────────────────
        if (_contextHouse != null || _inspector.SelectedHouse != null)
        {
            DrawText("SELECTED HOUSE", rightCol, y, 14, C(100, 200, 255));
            y += 22;
            DrawText("  Right-click    Rename / Split / Merge", rightCol, y, 12, C(210, 215, 224)); y += 17;
            DrawText("  Right-click    Toggle Commons", rightCol, y, 12, C(210, 215, 224)); y += 17;
            DrawText("  Right-click    Upgrade tier (costs Gold)", rightCol, y, 12, C(210, 215, 224)); y += 17;
            y += 6;
        }

        // ── Nighttime info (if night) ───────────────────────────────────
        if (isNight)
        {
            DrawText("NIGHTTIME MODE", rightCol, y, 14, C(60, 120, 255));
            y += 22;
            DrawText("  Safe refactor — no decay, no threats", rightCol, y, 12, C(210, 215, 224)); y += 17;
            DrawText("  Drag houses freely", rightCol, y, 12, C(210, 215, 224)); y += 17;
            DrawText("  Citizens animate home", rightCol, y, 12, C(210, 215, 224)); y += 17;
            y += 6;
        }

        // ── Timeline export (if expanded) ──────────────────────────────
        if (_timeline.IsExpanded)
        {
            DrawText("TIMELINE", rightCol, y, 14, C(240, 160, 80));
            y += 22;
            DrawText("  E             Export timeline as text", rightCol, y, 12, C(210, 215, 224)); y += 17;
            y += 6;
        }

        // ── Close on click outside or [/] ──────────────────────────────
        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X < boxX || m.X > boxX + boxW || m.Y < boxY || m.Y > boxY + boxH)
                _showHelp = false;
        }
    }

    private void DrawContextMenu()
    {
        if (!_showContextMenu) return;

        int mx = _screenWidth - 180;
        int my = 0;

        DrawRectangle(mx, my, 180, 150, C(22, 26, 34, 240));
        DrawRectangleLinesEx(new Rectangle(mx, my, 180, 150), 1, C(240, 200, 50));

        if (_contextHouse != null)
        {
            DrawText("Rename (-20W)", mx + 5, my + 3, 11, WHITE);
            DrawText("Split (-30W)", mx + 5, my + 33, 11, WHITE);
            DrawText("Merge (-10W)", mx + 5, my + 63, 11, WHITE);
            DrawText("Toggle Commons", mx + 5, my + 93, 11, C(100, 200, 255));
            string upgradeLabel = _contextHouse.Tier < UpgradeTier.Citadel
                ? $"Upgrade to {_contextHouse.Tier + 1} (-{_contextHouse.UpgradeCost(_contextHouse.Tier + 1)}G)"
                : "MAX TIER";
            DrawText(upgradeLabel, mx + 5, my + 123, 11, C(255, 215, 0));
        }
        else if (_contextCitizen != null)
        {
            DrawText("Gift files", mx + 5, my + 3, 11, WHITE);
            DrawText("Retire", mx + 5, my + 33, 11, WHITE);
        }
    }

    private void DrawOverlays()
    {
        if (_showTribunal && _lastReview != null)
        {
            DrawRectangle(0, 0, _screenWidth, _screenHeight, C(5, 7, 10, 210));
            int boxW = 750, boxH = 420;
            int boxX = (_screenWidth - boxW) / 2;
            int boxY = (_screenHeight - boxH) / 2;
            DrawRectangle(boxX, boxY, boxW, boxH, C(22, 26, 34));
            DrawRectangleLinesEx(new Rectangle(boxX, boxY, boxW, boxH), 2, C(240, 200, 50));

            DrawText("CODE REVIEW TRIBUNAL", boxX + 30, boxY + 25, 22, C(240, 200, 50));
            DrawText($"Compliance Score: {_lastReview.ComplianceScore:F1}%", boxX + 30, boxY + 70, 16, C(110, 120, 140));
            DrawText($"Lines scanned: {_lastReview.TotalLines}", boxX + 30, boxY + 100, 14, C(210, 215, 224));
            DrawText($"Violations: {_lastReview.ViolationCount}", boxX + 30, boxY + 130, 14, C(210, 215, 224));
            DrawText(_lastReview.Details, boxX + 30, boxY + 160, 14, C(210, 215, 224));
            DrawText("Press A to ACCEPT (apply consequences), B to DISMISS", boxX + 30, boxY + 350, 16, C(0, 220, 140));
        }

        if (_showCitizenFiles && _selectedCitizen != null)
        {
            DrawRectangle(_screenWidth / 2 - 200, _screenHeight / 2 - 150, 400, 300, C(22, 26, 34));
            DrawRectangleLinesEx(new Rectangle(_screenWidth / 2 - 200, _screenHeight / 2 - 150, 400, 300), 2, C(240, 200, 50));
            DrawText($"Files owned by {_selectedCitizen.Name}", _screenWidth / 2 - 180, _screenHeight / 2 - 130, 14, C(210, 215, 224));
            int fy = _screenHeight / 2 - 100;
            foreach (var file in _selectedCitizen.OwnedFiles.Take(10))
            {
                DrawText(Path.GetFileName(file), _screenWidth / 2 - 180, fy, 11, C(210, 215, 224));
                fy += 18;
            }
            DrawText("Click anywhere to close", _screenWidth / 2 - 180, _screenHeight / 2 + 120, 11, C(110, 120, 140));
            if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
            {
                var m = GetMousePosition();
                if (m.X < _screenWidth / 2 - 200 || m.X > _screenWidth / 2 + 200 ||
                    m.Y < _screenHeight / 2 - 150 || m.Y > _screenHeight / 2 + 150)
                {
                    _showCitizenFiles = false;
                    _selectedCitizen = null;
                }
            }
        }

        if (_inspector.IsOpen)
            _inspector.Draw();

        if (_showHelp)
            DrawHelpOverlay();
    }

    private void DrawBlueprintOverlay()
    {
        DrawRectangle(0, 0, _screenWidth, _screenHeight, C(0, 4, 28, 235));

        const int minor = 20;
        const int major = 100;
        for (int gx = 0; gx < _screenWidth; gx += minor)
        {
            bool isMajor = gx % major == 0;
            byte alpha = isMajor ? (byte)55 : (byte)25;
            DrawLine(gx, 0, gx, _screenHeight, C(80, 140, 255, alpha));
        }
        for (int gy = 0; gy < _screenHeight; gy += minor)
        {
            bool isMajor = gy % major == 0;
            byte alpha = isMajor ? (byte)55 : (byte)25;
            DrawLine(0, gy, _screenWidth, gy, C(80, 140, 255, alpha));
        }

        for (int sy = 0; sy < _screenHeight; sy += 4)
            DrawLine(0, sy, _screenWidth, sy, C(0, 0, 40, 18));

        DrawRectangle(0, 0, _screenWidth, 54, C(0, 10, 50, 220));
        DrawRectangleLinesEx(new Rectangle(0, 0, _screenWidth, 54), 1, C(60, 120, 255, 180));
        DrawText("// NIGHTTIME \u2014 IDE MAINTENANCE GRID", 20, 16, 22, C(100, 170, 255));
        string phaseInfo = $"SAFE REFACTOR MODE  |  YEAR {_state.Year}  |  TAB \u2192 Resume Daytime";
        DrawText(phaseInfo, _screenWidth - 540, 20, 14, C(60, 120, 255));

        foreach (var house in _state.Houses)
        {
            int hx = (int)house.Position.X;
            int hy = (int)house.Position.Y;
            int hw = (int)house.BoundingBoxSize.X;
            int hh = (int)house.BoundingBoxSize.Y;

            DrawRectangle(hx - 8, hy - 8, hw + 16, hh + 16, C(0, 80, 180, 30));
            DrawRectangleLinesEx(new Rectangle(hx - 4, hy - 4, hw + 8, hh + 8), 1, C(60, 140, 255, 100));
            DrawRectangleLinesEx(new Rectangle(hx, hy, hw, hh), 2, C(100, 180, 255, 200));

            int ms = 8;
            DrawLine(hx - ms, hy, hx + ms, hy, C(100, 200, 255, 200));
            DrawLine(hx, hy - ms, hx, hy + ms, C(100, 200, 255, 200));
            DrawLine(hx + hw - ms, hy, hx + hw + ms, hy, C(100, 200, 255, 200));
            DrawLine(hx + hw, hy - ms, hx + hw, hy + ms, C(100, 200, 255, 200));
            DrawLine(hx - ms, hy + hh, hx + ms, hy + hh, C(100, 200, 255, 200));
            DrawLine(hx, hy + hh - ms, hx, hy + hh + ms, C(100, 200, 255, 200));
            DrawLine(hx + hw - ms, hy + hh, hx + hw + ms, hy + hh, C(100, 200, 255, 200));
            DrawLine(hx + hw, hy + hh - ms, hx + hw, hy + hh + ms, C(100, 200, 255, 200));

            DrawText($"[{house.RootNamespace}]", hx + 6, hy + 6, 10, C(80, 160, 255, 200));
            DrawText(house.ProjectName, hx + 6, hy + 20, 12, C(140, 200, 255));
            DrawText($"Files: {house.TrackedFiles.Count}  State: {house.CurrentState}",
                     hx + 6, hy + 36, 10, C(80, 140, 220));
        }
    }

    private void DrawTooltip(ProjectHouse house)
    {
        string text = $"{house.ProjectName}\nNamespace: {house.RootNamespace}\nState: {house.CurrentState}\nFiles: {house.TrackedFiles.Count}";
        if (house.CollapseTimerSeconds > 0)
            text += $"\nCollapse in: {house.CollapseTimerSeconds:F0}s";
        if (house.HasBackyardTreasure)
            text += "\nTreasure ready!";
        if (house.IsCommons)
            text += "\n[COMMONS]";
        DrawText(text, (int)house.Position.X + 10, (int)house.Position.Y - 30, 12, WHITE);
    }

    private void DrawCitizenTooltip(Citizen citizen)
    {
        string role = citizen.RoleType switch { 0 => "Idle", 1 => "Farmer", 2 => "Militia", 5 => "Governor", 6 => "Archivist", 7 => "Sentinel", 8 => "Jurist", _ => "Unknown" };
        string text = $"{citizen.Name}\nRole: {role}";
        if (citizen.DecayTimer > 0)
            text += $"\nDecay: {citizen.DecayTimer:F0}s";
        text += $"\nFiles: {citizen.OwnedFiles.Count}";
        if (citizen.XP > 0)
            text += $"\nXP: {citizen.XP}";
        if (!string.IsNullOrEmpty(citizen.Specialization))
            text += $"\n[{citizen.Specialization}]";
        DrawText(text, (int)citizen.Position.X + 12, (int)citizen.Position.Y - 25, 12, WHITE);
    }

    private void DrawResourceMetric(string label, int current, int previous, int x, int y)
    {
        DrawText(label, x, y, 12, C(110, 120, 140));
        DrawText(current.ToString(), x + 70, y, 14, C(210, 215, 224));
        if (current != previous)
        {
            string arrow = current > previous ? "^" : "v";
            var arrowColor = current > previous ? C(0, 220, 140) : C(240, 70, 70);
            DrawText(arrow, x + 120, y, 14, arrowColor);
        }
    }

    private void DrawJuulWheel(int cx, int cy, int radius)
    {
        var res = _state.Resources;
        float[] lengths = [
            Math.Min(1f, res.Food / 300f) * radius,
            Math.Min(1f, res.Wood / 300f) * radius,
            Math.Min(1f, res.Stone / 300f) * radius,
            Math.Min(1f, res.Metal / 300f) * radius,
            Math.Min(1f, res.Wealth / 300f) * radius,
            Math.Min(1f, res.Gold / 300f) * radius,
        ];

        for (int i = 0; i < 6; i++)
        {
            float angle = i * 60f * MathF.PI / 180f;
            float endX = cx + lengths[i] * MathF.Cos(angle);
            float endY = cy + lengths[i] * MathF.Sin(angle);
            var col = lengths[i] > radius * 0.5f ? C(0, 220, 140) :
                      lengths[i] > radius * 0.2f ? C(240, 200, 50) : C(240, 70, 70);

            float handLen = _timeController.IsTransitioning ? radius : radius;
            DrawLine(cx, cy, (int)endX, (int)endY, col);
        }

        if (_timeController.IsTransitioning)
        {
            float angle = _timeController.ClockHandAngle * MathF.PI / 180f;
            float handX = cx + radius * 0.7f * MathF.Cos(angle);
            float handY = cy + radius * 0.7f * MathF.Sin(angle);
            DrawLine(cx, cy, (int)handX, (int)handY, C(255, 255, 100, 200));
        }

        DrawCircle(cx, cy, 6, C(0, 220, 140));
    }

    private void DrawRadar()
    {
        int cx = 1045, cy = 300;
        DrawCircleLines(cx, cy, 100, C(110, 120, 140));
        DrawCircleLines(cx, cy, 50, C(110, 120, 140));
        DrawLine(cx - 100, cy, cx + 100, cy, C(110, 120, 140));
        DrawLine(cx, cy - 100, cx, cy + 100, C(110, 120, 140));
        DrawRectangle(cx - 8, cy - 8, 16, 16, C(0, 160, 255));

        foreach (var house in _state.Houses)
        {
            float hx = cx + (house.Position.X - 400) * 0.2f;
            float hy = cy + (house.Position.Y - 300) * 0.2f;
            var col = house.CurrentState switch
            {
                BuildState.Success => C(0, 220, 140),
                BuildState.Warning => C(240, 200, 50),
                BuildState.Error => C(240, 70, 70),
                _ => C(100, 100, 100),
            };
            DrawRectangle((int)hx, (int)hy, 8, 8, col);
        }
    }

    private static bool IsPointOnLine(Vector2 point, Vector2 a, Vector2 b, float tolerance)
    {
        float dist = MathF.Abs((b.Y - a.Y) * point.X - (b.X - a.X) * point.Y + b.X * a.Y - b.Y * a.X) /
                     MathF.Sqrt((b.Y - a.Y) * (b.Y - a.Y) + (b.X - a.X) * (b.X - a.X));
        return dist < tolerance;
    }

    private static string WrapText(string text, int maxChars)
    {
        if (text.Length <= maxChars) return text;
        int split = text.LastIndexOf(' ', maxChars);
        if (split == -1) split = maxChars;
        return text[..split] + "\n" + text[(split + 1)..];
    }

    public void ProcessTribunalKey(int key)
    {
        if (!_showTribunal || _lastReview == null) return;

        if (key == (int)KeyboardKey.KEY_A)
        {
            var review = _lastReview;
            var analysis = _pendingAnalysis ?? new AnalysisResult
            {
                TotalLines = review.TotalLines,
                ErrorCount = review.ErrorCount,
                WarningCount = review.WarningCount,
                DiscoveredNamespace = "Unknown",
                DiscoveredClassName = "dropped",
            };

            string filePath = string.IsNullOrEmpty(_pendingFilePath) ? "dropped_file" : _pendingFilePath;
            string namespaceRoot = analysis.DiscoveredNamespace ?? "Unknown";

            var file = new UploadedFile
            {
                FilePath = filePath,
                TotalLines = review.TotalLines,
                ComplianceScore = review.ComplianceScore,
                ViolationCount = review.ViolationCount,
                Details = review.Details,
                Timestamp = DateTime.Now,
                NamespaceRoot = namespaceRoot,
            };

            if (review.ComplianceScore >= 80)
                _state.AddCompliantFile(file, filePath, namespaceRoot, review.TotalLines, analysis);
            else
                _state.AddViolatingFile(file, filePath, review.TotalLines, analysis);

            _timeline.AddEntry(_state.Year, "event", $"Code review: {Path.GetFileName(filePath)} ({review.ComplianceScore:F0}%)", "tribunal");

            _showTribunal = false;
            _lastReview = null;
            _pendingAnalysis = null;
            _pendingFilePath = string.Empty;
        }
        else if (key == (int)KeyboardKey.KEY_B)
        {
            _state.AddLog("Tribunal dismissed; file not applied.");
            _showTribunal = false;
            _lastReview = null;
            _pendingAnalysis = null;
            _pendingFilePath = string.Empty;
        }
    }

    public void Dispose() { }
}
