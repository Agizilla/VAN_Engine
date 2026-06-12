using System.Numerics;
using Raylib_CsLo;
using VanEngine.Game.Architecture;
using VanEngine.Game.Core;
using VanEngine.Game.Forensics;
using VanEngine.Game.Simulation;
using static Raylib_CsLo.Raylib;
using RlVec2 = Raylib_CsLo.Vector2;

namespace VanEngine.Game.UI;

public sealed class DashboardView : IDisposable
{
    private readonly SovereignState _state;
    private readonly TimePhaseController _timeController;
    private readonly SpatialEcosystemManager _ecoManager;
    private readonly int _screenWidth;
    private readonly int _screenHeight;
    private readonly Dictionary<string, string> _cachedLogLines = new();
    private ReviewResult? _lastReview;
    private bool _showTribunal;
    private float _tribunalTimer;
    private bool _processingFile;
    private Citizen? _selectedCitizen;
    private bool _showCitizenFiles;
    private ProjectHouse? _draggedHouse;
    private Vector2 _dragOffset;
    private (int fromId, int toId, float similarity)? _hoveredLink;
    private float _timeSinceLastParticleEmit;

    private struct Particle { public float X, Y; public float Life; public Color Color; }
    private readonly List<Particle> _particles = new();

    private int _previousFood, _previousWood, _previousStone, _previousMetal, _previousWealth;
    private float _trendTimer;

    private static Color C(byte r, byte g, byte b, byte a = 255) => new(r, g, b, a);

    public DashboardView(SovereignState state, TimePhaseController timeController, SpatialEcosystemManager ecoManager, int width, int height)
    {
        _state = state;
        _timeController = timeController;
        _ecoManager = ecoManager;
        _screenWidth = width;
        _screenHeight = height;
        var res = _state.Resources;
        _previousFood = res.Food; _previousWood = res.Wood; _previousStone = res.Stone;
        _previousMetal = res.Metal; _previousWealth = res.Wealth;
    }

    // ── Sprint 1 ──────────────────────────────────────────────────────────────
    // TAB key binding owned by DashboardView so the UI layer can respond to the
    // phase transition independently (e.g. triggering the blueprint overlay) without
    // relying solely on the Program.cs polling loop.
    public void HandlePhaseToggle()
    {
        if (IsKeyPressed(KeyboardKey.KEY_TAB))
        {
            _timeController.TogglePhase();
            bool isNight = _timeController.CurrentPhase == SimulationPhase.Nighttime;
            _state.EnqueueLog(isNight
                ? "Night phase engaged – refactoring mode active."
                : "Day phase resumed – simulation clock running.");
        }
    }

    // ── Sprint 3 ──────────────────────────────────────────────────────────────
    // File-drop callback now runs AnalyzeSourceFile synchronously on the worker
    // thread so that the full AnalysisResult (namespace, class name, directives)
    // is available when ProcessTribunalKey applies consequences.
    private AnalysisResult? _pendingAnalysis;
    private string _pendingFilePath = string.Empty;

    public void UpdateFileDrop()
    {
        if (!IsFileDropped() || _processingFile) return;

        var dropped = GetDroppedFilesAndClear();
        if (dropped.Length == 0) return;

        _processingFile = true;
        string path = dropped[0];

        _ = System.Threading.Tasks.Task.Run(() =>
        {
            // Run the full static analysis (namespace + class extraction + directive scan).
            var analysis = TexStaticAnalyzer.AnalyzeSourceFile(path);

            // Build the ReviewResult summary that the Tribunal UI will display.
            var review = new ReviewResult
            {
                TotalLines    = analysis.TotalLines,
                ErrorCount    = analysis.ErrorCount,
                WarningCount  = analysis.WarningCount,
                ComplianceScore = analysis.ErrorCount == 0
                    ? 100.0
                    : Math.Max(0, 100.0 - analysis.ErrorCount * 20.0),
                ViolationCount = analysis.ErrorCount + analysis.WarningCount,
                Details = $"[{analysis.DiscoveredNamespace}] {analysis.DiscoveredClassName}: " +
                          $"{analysis.ErrorCount} errors, {analysis.WarningCount} warnings",
            };

            // Stash the rich AnalysisResult so ProcessTribunalKey can use it.
            _pendingAnalysis   = analysis;
            _pendingFilePath   = path;
            _lastReview        = review;
            _showTribunal      = true;
            _tribunalTimer     = 0f;
            _processingFile    = false;
        });
    }

    public void Update(float deltaTime)
    {
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
            if (p.Life <= 0)
                _particles.RemoveAt(i);
            else
                _particles[i] = p;
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
    }

    // ── Sprint 2 ──────────────────────────────────────────────────────────────
    // Blueprint shader overlay for Nighttime phase.
    // Draws a dark midnight-blue background, a fine grid reminiscent of a CAD/
    // blueprint canvas, subtle scanlines, a header status bar, and highlights
    // every house with a blueprint-style outline so the player can safely drag
    // and re-arrange elements without any resource loss or attack risk.
    private void DrawBlueprintOverlay()
    {
        // --- Background tint (deep midnight blue) ---
        DrawRectangle(0, 0, _screenWidth, _screenHeight, C(0, 4, 28, 235));

        // --- Fine grid (minor lines every 20px, major every 100px) ---
        const int minor = 20;
        const int major = 100;
        for (int gx = 0; gx < _screenWidth; gx += minor)
        {
            bool isMajor = gx % major == 0;
            byte alpha   = isMajor ? (byte)55 : (byte)25;
            DrawLine(gx, 0, gx, _screenHeight, C(80, 140, 255, alpha));
        }
        for (int gy = 0; gy < _screenHeight; gy += minor)
        {
            bool isMajor = gy % major == 0;
            byte alpha   = isMajor ? (byte)55 : (byte)25;
            DrawLine(0, gy, _screenWidth, gy, C(80, 140, 255, alpha));
        }

        // --- Scanlines (subtle horizontal bands for CRT / blueprint feel) ---
        for (int sy = 0; sy < _screenHeight; sy += 4)
            DrawLine(0, sy, _screenWidth, sy, C(0, 0, 40, 18));

        // --- Top header bar ---
        DrawRectangle(0, 0, _screenWidth, 54, C(0, 10, 50, 220));
        DrawRectangleLinesEx(new Rectangle(0, 0, _screenWidth, 54), 1, C(60, 120, 255, 180));
        DrawText("// NIGHTTIME — IDE MAINTENANCE GRID", 20, 16, 22, C(100, 170, 255));
        string phaseInfo = $"SAFE REFACTOR MODE  |  YEAR {_state.Year}  |  TAB → Resume Daytime";
        DrawText(phaseInfo, _screenWidth - 540, 20, 14, C(60, 120, 255));

        // --- Blueprint ghost outlines around every ProjectHouse ---
        foreach (var house in _state.Houses)
        {
            int hx = (int)house.Position.X;
            int hy = (int)house.Position.Y;
            int hw = (int)house.BoundingBoxSize.X;
            int hh = (int)house.BoundingBoxSize.Y;

            // Larger glow halo
            DrawRectangle(hx - 8, hy - 8, hw + 16, hh + 16, C(0, 80, 180, 30));
            // Blueprint border
            DrawRectangleLinesEx(new Rectangle(hx - 4, hy - 4, hw + 8, hh + 8), 1, C(60, 140, 255, 100));
            // Bright inner outline
            DrawRectangleLinesEx(new Rectangle(hx, hy, hw, hh), 2, C(100, 180, 255, 200));

            // Corner cross-hair markers
            int ms = 8;
            DrawLine(hx - ms, hy, hx + ms, hy, C(100, 200, 255, 200));
            DrawLine(hx, hy - ms, hx, hy + ms, C(100, 200, 255, 200));
            DrawLine(hx + hw - ms, hy, hx + hw + ms, hy, C(100, 200, 255, 200));
            DrawLine(hx + hw, hy - ms, hx + hw, hy + ms, C(100, 200, 255, 200));
            DrawLine(hx - ms, hy + hh, hx + ms, hy + hh, C(100, 200, 255, 200));
            DrawLine(hx, hy + hh - ms, hx, hy + hh + ms, C(100, 200, 255, 200));
            DrawLine(hx + hw - ms, hy + hh, hx + hw + ms, hy + hh, C(100, 200, 255, 200));
            DrawLine(hx + hw, hy + hh - ms, hx + hw, hy + hh + ms, C(100, 200, 255, 200));

            // House label in blueprint style
            DrawText($"[{house.RootNamespace}]", hx + 6, hy + 6, 10, C(80, 160, 255, 200));
            DrawText(house.ProjectName,           hx + 6, hy + 20, 12, C(140, 200, 255));
            DrawText($"Files: {house.TrackedFiles.Count}  State: {house.CurrentState}",
                     hx + 6, hy + 36, 10, C(80, 140, 220));
        }
    }

    public void Draw()
    {
        bool isNight = _timeController.CurrentPhase == SimulationPhase.Nighttime;

        ClearBackground(isNight ? C(0, 4, 28) : C(12, 14, 18));

        if (isNight)
        {
            DrawBlueprintOverlay();
            // In night mode skip the regular simulation rendering and return early;
            // only the blueprint canvas and UI panels are drawn.
            DrawRectangle(20, 63, 300, 57, C(0, 10, 50, 200));
            DrawText("RESOURCES PAUSED", 35, 75, 14, C(60, 120, 255));
            DrawText("No decay | No attack risk | Drag freely", 35, 96, 11, C(40, 90, 200));
            return;
        }

        var rlMouse = GetMousePosition();
        Vector2 mousePos = new(rlMouse.x, rlMouse.y);

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
                if (IsPointOnLine(mousePos, p1, p2, 5))
                {
                    lineColor = C(255, 255, 100, 200);
                    _hoveredLink = (c1.Id, c2.Id, link.Value);
                }
                DrawLine((int)p1.X, (int)p1.Y, (int)p2.X, (int)p2.Y, lineColor);
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

            DrawRectangle(hx, hy, hw, hh, baseColor);
            DrawRectangle(hx, hy, hw, hh, tint);

            float borderThick = house.CollapseTimerSeconds > 0 ? 4f : 2f;
            if (house.HasBackyardTreasure) borderThick = 4f;
            DrawRectangleLinesEx(new Rectangle(hx, hy, hw, hh), borderThick, WHITE);

            DrawText(house.ProjectName, hx + 10, hy + 10, 12, WHITE);

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

            if (mousePos.X >= house.Position.X && mousePos.X <= house.Position.X + house.BoundingBoxSize.X &&
                mousePos.Y >= house.Position.Y && mousePos.Y <= house.Position.Y + house.BoundingBoxSize.Y)
            {
                DrawTooltip(house);
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

            float dx = mousePos.X - citizen.Position.X;
            float dy = mousePos.Y - citizen.Position.Y;
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
            DrawRectangle(10, _screenHeight - 60, 250, 30, C(0, 0, 0, 180));
            DrawText($"Similarity: {_hoveredLink.Value.similarity * 100:F1}%", 15, _screenHeight - 55, 14, YELLOW);
        }

        DrawRectangle(20, 90, 300, 540, C(22, 26, 34));
        DrawLine(20, 135, 320, 135, C(110, 120, 140));
        DrawText("STATE RESOURCES", 35, 105, 16, C(210, 215, 224));

        var res = _state.Resources;
        DrawResourceMetric("FOOD:", res.Food, _previousFood, 35, 160);
        DrawResourceMetric("WOOD:", res.Wood, _previousWood, 35, 190);
        DrawResourceMetric("STONE:", res.Stone, _previousStone, 35, 220);
        DrawResourceMetric("METAL:", res.Metal, _previousMetal, 35, 250);
        DrawResourceMetric("WEALTH:", res.Wealth, _previousWealth, 35, 280);
        DrawResourceMetric("GOLD:", res.Gold, 0, 35, 310);

        DrawText("CITIZENS", 35, 350, 16, C(210, 215, 224));
        int y = 380;
        foreach (var citizen in _state.Citizens)
        {
            string line = $"{citizen.Name} (owned: {citizen.OwnedFiles.Count} files)";
            DrawText(line, 35, y, 14, C(210, 215, 224));
            if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
            {
                var m = GetMousePosition();
                if (m.x >= 35 && m.x <= 300 && m.y >= y && m.y <= y + 18)
                {
                    _selectedCitizen = citizen;
                    _showCitizenFiles = true;
                }
            }
            y += 22;
            if (y > 590) break;
        }

        foreach (var link in links.Where(l => l.Value > 0.85f))
        {
            var c1 = _state.Citizens.FirstOrDefault(c => c.Id == link.Key.Item1);
            var c2 = _state.Citizens.FirstOrDefault(c => c.Id == link.Key.Item2);
            if (c1 != null && c2 != null)
            {
                var mid = (c1.Position + c2.Position) / 2;
                DrawCircle((int)mid.X, (int)mid.Y, 12, C(255, 100, 100, 200));
                DrawText("*", (int)mid.X - 6, (int)mid.Y - 8, 14, WHITE);
            }
        }

        DrawRectangle(340, 90, 470, 540, C(22, 26, 34));
        DrawText("SYSTEM CHRONICLES", 355, 105, 16, C(210, 215, 224));
        DrawLine(340, 135, 810, 135, C(110, 120, 140));
        int ly = 150;
        foreach (var log in _state.GetLogs())
        {
            string wrapped = _cachedLogLines.TryGetValue(log, out var w) ? w : log;
            var col = C(210, 215, 224);
            if (log.Contains("Violation") || log.Contains("penalty")) col = C(240, 70, 70);
            else if (log.Contains("Compliant") || log.Contains("reward")) col = C(0, 220, 140);
            else if (log.Contains("ALERT")) col = C(240, 200, 50);
            DrawText(wrapped, 355, ly, 14, col);
            ly += 22;
            if (ly > 570) break;
        }

        DrawRectangle(830, 90, 430, 540, C(22, 26, 34));
        DrawText("CITADEL RADAR", 845, 105, 16, C(210, 215, 224));
        DrawLine(830, 135, 1260, 135, C(110, 120, 140));
        DrawJuulWheel(_screenWidth - 110, 160, 70);
        DrawRadar();

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
            DrawText($"Files owned by {_selectedCitizen.Name}", _screenWidth / 2 - 180, _screenHeight / 2 - 130, 16, C(210, 215, 224));
            int fy = _screenHeight / 2 - 100;
            foreach (var file in _selectedCitizen.OwnedFiles.Take(10))
            {
                DrawText(Path.GetFileName(file), _screenWidth / 2 - 180, fy, 12, C(210, 215, 224));
                fy += 20;
            }
            DrawText("Click anywhere to close", _screenWidth / 2 - 180, _screenHeight / 2 + 120, 12, C(110, 120, 140));
            if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
            {
                var m = GetMousePosition();
                if (m.x < _screenWidth / 2 - 200 || m.x > _screenWidth / 2 + 200 ||
                    m.y < _screenHeight / 2 - 150 || m.y > _screenHeight / 2 + 150)
                {
                    _showCitizenFiles = false;
                    _selectedCitizen = null;
                }
            }
        }

        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            foreach (var house in _state.Houses)
            {
                if (m.x >= house.Position.X && m.x <= house.Position.X + house.BoundingBoxSize.X &&
                    m.y >= house.Position.Y && m.y <= house.Position.Y + house.BoundingBoxSize.Y)
                {
                    _draggedHouse = house;
                    _dragOffset = new Vector2(m.x - house.Position.X, m.y - house.Position.Y);
                    break;
                }
            }
        }
        if (IsMouseButtonDown(MouseButton.MOUSE_BUTTON_LEFT) && _draggedHouse != null)
        {
            var m = GetMousePosition();
            _draggedHouse.Position = new Vector2(m.x - _dragOffset.X, m.y - _dragOffset.Y);
        }
        if (IsMouseButtonReleased(MouseButton.MOUSE_BUTTON_LEFT))
            _draggedHouse = null;

        if (IsFileDropped())
            DrawRectangle(0, 0, _screenWidth, _screenHeight, C(100, 200, 255, 80));
    }

    private void DrawTooltip(ProjectHouse house)
    {
        string text = $"{house.ProjectName}\nNamespace: {house.RootNamespace}\nState: {house.CurrentState}\nFiles: {house.TrackedFiles.Count}";
        if (house.CollapseTimerSeconds > 0)
            text += $"\nCollapse in: {house.CollapseTimerSeconds:F0}s";
        if (house.HasBackyardTreasure)
            text += "\nTreasure ready!";
        DrawText(text, (int)house.Position.X + 10, (int)house.Position.Y - 30, 12, WHITE);
    }

    private void DrawCitizenTooltip(Citizen citizen)
    {
        string role = citizen.RoleType switch { 0 => "Idle", 1 => "Farmer", 2 => "Militia", 5 => "Governor", _ => "Unknown" };
        string text = $"{citizen.Name}\nRole: {role}";
        if (citizen.DecayTimer > 0)
            text += $"\nDecay: {citizen.DecayTimer:F0}s";
        text += $"\nFiles: {citizen.OwnedFiles.Count}";
        DrawText(text, (int)citizen.Position.X + 12, (int)citizen.Position.Y - 25, 12, WHITE);
    }

    private void DrawResourceMetric(string label, int current, int previous, int x, int y)
    {
        DrawText(label, x, y, 14, C(110, 120, 140));
        DrawText(current.ToString(), x + 80, y, 16, C(210, 215, 224));
        if (current != previous)
        {
            string arrow = current > previous ? "^" : "v";
            var arrowColor = current > previous ? C(0, 220, 140) : C(240, 70, 70);
            DrawText(arrow, x + 130, y, 16, arrowColor);
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
            DrawLine(cx, cy, (int)endX, (int)endY, col);
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
            var review   = _lastReview;
            // ── Sprint 3 ──────────────────────────────────────────────────────
            // Use the rich AnalysisResult captured during the file-drop async
            // scan so that the correct namespace, class name, and directive mask
            // are forwarded to SovereignState rather than placeholder strings.
            var analysis = _pendingAnalysis ?? new AnalysisResult
            {
                TotalLines          = review.TotalLines,
                ErrorCount          = review.ErrorCount,
                WarningCount        = review.WarningCount,
                DiscoveredNamespace = "Unknown",
                DiscoveredClassName = "dropped",
            };

            string filePath      = string.IsNullOrEmpty(_pendingFilePath) ? "dropped_file" : _pendingFilePath;
            string namespaceRoot = analysis.DiscoveredNamespace ?? "Unknown";

            var file = new UploadedFile
            {
                FilePath        = filePath,
                TotalLines      = review.TotalLines,
                ComplianceScore = review.ComplianceScore,
                ViolationCount  = review.ViolationCount,
                Details         = review.Details,
                Timestamp       = DateTime.Now,
                NamespaceRoot   = namespaceRoot,
            };

            if (review.ComplianceScore >= 80)
                _state.AddCompliantFile(file, filePath, namespaceRoot, review.TotalLines, analysis);
            else
                _state.AddViolatingFile(file, filePath, review.TotalLines, analysis);

            _showTribunal    = false;
            _lastReview      = null;
            _pendingAnalysis = null;
            _pendingFilePath = string.Empty;
        }
        else if (key == (int)KeyboardKey.KEY_B)
        {
            _state.AddLog("Tribunal dismissed; file not applied.");
            _showTribunal    = false;
            _lastReview      = null;
            _pendingAnalysis = null;
            _pendingFilePath = string.Empty;
        }
    }

    public void Dispose() { }
}
