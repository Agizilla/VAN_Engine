using System.Numerics;
using Raylib_CsLo;
using VanEngine.Game.Architecture;
using VanEngine.Game.Core;
using VanEngine.Game.Forensics;
using VanEngine.Game.Infrastructure;
using VanEngine.Game.Simulation;
using VanEngine.Game.UI;
using static Raylib_CsLo.Raylib;

namespace VanEngine.Game;

public static class Program
{
    private const int ScreenWidth = 1280;
    private const int ScreenHeight = 720;

    private static SovereignState _state = null!;
    private static DashboardView _dashboard = null!;
    private static TimePhaseController _timeController = null!;
    private static SpatialEcosystemManager _ecoManager = null!;
    private static WorkspaceManager _workspaceManager = null!;
    private static CameraSystem _camera = null!;
    private static FileWatcherService _fileWatcher = null!;
    private static InspectorPanel _inspector = null!;
    private static HistoryTimeline _timeline = null!;
    private static ThreatController _threatCtrl = null!;
    private static EventWebhook _webhook = null!;
    private static GitIntegrationEngine _gitEngine = null!;
    private static ModLoader _modLoader = null!;
    private static float _autosaveTimer;
    private const float AutosaveInterval = 40f;

    public static void Main()
    {
        SetConfigFlags(ConfigFlags.FLAG_WINDOW_RESIZABLE);
        InitWindow(ScreenWidth, ScreenHeight, "Oera Linda Simulator - Living Code Ecosystem");
        SetTargetFPS(60);

        _workspaceManager = new WorkspaceManager();
        _workspaceManager.LoadRegistry();

        _state = _workspaceManager.ActiveState;
        _timeController = new TimePhaseController();
        _ecoManager = new SpatialEcosystemManager(_state);
        _camera = new CameraSystem();
        _inspector = new InspectorPanel(_state);
        _timeline = new HistoryTimeline(_state);
        _threatCtrl = new ThreatController(_state);
        _webhook = new EventWebhook(_state);
        _gitEngine = new GitIntegrationEngine(_state, _workspaceManager);
        _gitEngine.SetScreenWidth(ScreenWidth);
        _modLoader = new ModLoader(_state);
        _modLoader.LoadAllMods();

        _dashboard = new DashboardView(_state, _timeController, _ecoManager,
            _workspaceManager, _camera, _inspector, _timeline,
            ScreenWidth, ScreenHeight);

        _dashboard.ThreatCtrl = _threatCtrl;
        _dashboard.Webhook = _webhook;
        _dashboard.GitEngine = _gitEngine;
        _dashboard.ModLoader = _modLoader;

        _fileWatcher = new FileWatcherService(_state, path =>
        {
            string lang = TexStaticAnalyzer.DetectLanguageFromExtension(path);
            var analysis = lang != "unknown" && lang != "csharp"
                ? TexStaticAnalyzer.AnalyzeSourceFileMultiLang(path)
                : TexStaticAnalyzer.AnalyzeSourceFile(path);

            var house = _state.Houses.FirstOrDefault(h =>
                h.TrackedFiles.Any(f => f.FilePath == path));
            if (house != null)
            {
                int idx = house.TrackedFiles.FindIndex(f => f.FilePath == path);
                if (idx >= 0)
                {
                    var assets = house.TrackedFiles.ToList();
                    assets[idx] = new FileNodeAsset
                    {
                        FilePath = path,
                        ClassName = analysis.DiscoveredClassName,
                        LineCount = analysis.TotalLines,
                        ErrorCount = analysis.ErrorCount,
                        WarningCount = analysis.WarningCount,
                        LastWriteTimeTicks = DateTime.Now.Ticks,
                    };
                    house.TrackedFiles.Clear();
                    house.TrackedFiles.AddRange(assets);
                    house.EvaluateBuildState();
                }
            }

            _timeline.AddEntry(_state.Year, "house", $"File changed: {Path.GetFileName(path)}", "watcher");
        });
        _fileWatcher.WatchDirectory(AppDomain.CurrentDomain.BaseDirectory);
        _dashboard.FileWatcher = _fileWatcher;

        _state.AddHouse(new ProjectHouse("Core VAN Engine", "VanEngine.Core", new Vector2(200, 200)));
        _state.AddHouse(new ProjectHouse("Lexicon Service", "VanEngine.Lyrics", new Vector2(500, 150)));
        _state.AddHouse(new ProjectHouse("Voice Module", "VanEngine.Voice", new Vector2(800, 300)));

        // Establish a sample trade route
        if (_workspaceManager.WorkspaceNames.Count() >= 2)
        {
            var names = _workspaceManager.WorkspaceNames.ToList();
            _workspaceManager.EstablishTradeRoute(names[0], names[1]);
        }

        _timeline.AddEntry(_state.Year, "event", "Oera Linda Simulator started", "system");
        _timeline.AddEntry(_state.Year, "citizen", "Initial state: 3 houses, 0 citizens", "system");

        _webhook.Start();

        while (!WindowShouldClose())
        {
            float dt = GetFrameTime();
            Update(dt);
            Draw();
        }

        _modLoader.Dispose();
        _webhook.Dispose();
        _fileWatcher.Dispose();
        _workspaceManager.SaveRegistry();
        CloseWindow();
    }

    private static void Update(float dt)
    {
        _dashboard.HandlePhaseToggle();
        _dashboard.UpdateFileDrop();
        _camera.Update();

        if (_timeController.TickEngineClock(dt, out bool yearChanged))
        {
            if (yearChanged)
            {
                _state.IncrementYear();
                _timeline.AddEntry(_state.Year, "event", $"Year {_state.Year} begins", "system");

                _workspaceManager.CheckTradeRouteStatus();

                _modLoader.NotifyYearTick(_state.Year);

                _autosaveTimer += 1f;
                if (_autosaveTimer >= 5f)
                {
                    _autosaveTimer = 0f;
                    string savePath = Path.Combine(SaveManager.DefaultSaveDir,
                        $"autosave_year_{_state.Year}_{DateTime.Now:yyyyMMdd_HHmmss}.van");
                    SaveManager.Save(_state, savePath);
                    _state.EnqueueLog($"Autosave: Year {_state.Year}");
                }
            }

            foreach (var house in _state.Houses)
            {
                bool collapsed;
                house.UpdateDecayClock(dt, out collapsed);
                if (collapsed)
                {
                    _timeline.AddEntry(_state.Year, "house", $"House collapsed: {house.ProjectName}", "system");
                    foreach (var cit in _state.Citizens.Where(c => c.NamespaceFamily == house.RootNamespace))
                        cit.IsHomeless = true;
                }
            }

            foreach (var citizen in _state.Citizens)
            {
                if (citizen.DecayTimer > 0)
                    citizen.DecayTimer -= dt;
            }
        }

        if (_timeController.CurrentPhase == SimulationPhase.Daytime)
        {
            _ecoManager.UpdateKinClustering(dt, _timeController.CurrentPhase);
            _ecoManager.AttractHomelessCharacters();
            _threatCtrl.Update(dt);
            _workspaceManager.TickTradeRoutes();
            _gitEngine.TickConflicts(dt);
        }

        if (IsKeyPressed(KeyboardKey.KEY_A))
            _dashboard.ProcessTribunalKey((int)KeyboardKey.KEY_A);

        if (IsKeyPressed(KeyboardKey.KEY_B))
            _dashboard.ProcessTribunalKey((int)KeyboardKey.KEY_B);

        _dashboard.Update(dt);
    }

    private static void Draw()
    {
        BeginDrawing();
        _dashboard.Draw();
        EndDrawing();
    }
}
