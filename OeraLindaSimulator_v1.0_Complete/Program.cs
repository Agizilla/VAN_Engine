using System.Numerics;
using Raylib_CsLo;
using VanEngine.Game.Architecture;
using VanEngine.Game.Core;
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

    public static void Main()
    {
        SetConfigFlags(ConfigFlags.FLAG_WINDOW_RESIZABLE);
        InitWindow(ScreenWidth, ScreenHeight, "Oera Linda Simulator - Living Code Ecosystem");
        SetTargetFPS(60);

        _state = new SovereignState();
        _timeController = new TimePhaseController();
        _ecoManager = new SpatialEcosystemManager(_state);
        _dashboard = new DashboardView(_state, _timeController, _ecoManager, ScreenWidth, ScreenHeight);

        _state.AddHouse(new ProjectHouse("Core VAN Engine", "VanEngine.Core", new Vector2(200, 200)));
        _state.AddHouse(new ProjectHouse("Lexicon Service", "VanEngine.Lyrics", new Vector2(500, 150)));
        _state.AddHouse(new ProjectHouse("Voice Module", "VanEngine.Voice", new Vector2(800, 300)));

        while (!WindowShouldClose())
        {
            float dt = GetFrameTime();
            Update(dt);
            Draw();
        }

        CloseWindow();
    }

    private static void Update(float dt)
    {
        // Sprint 1: Phase toggle is now owned by DashboardView (input + log feedback).
        _dashboard.HandlePhaseToggle();

        _dashboard.UpdateFileDrop();

        if (_timeController.TickEngineClock(dt, out bool yearChanged))
        {
            if (yearChanged) _state.IncrementYear();

            foreach (var house in _state.Houses)
                house.UpdateDecayClock(dt, out _);

            foreach (var citizen in _state.Citizens)
            {
                if (citizen.DecayTimer > 0)
                    citizen.DecayTimer -= dt;
            }
        }

        _ecoManager.UpdateKinClustering(dt, _timeController.CurrentPhase);
        _ecoManager.AttractHomelessCharacters();

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
