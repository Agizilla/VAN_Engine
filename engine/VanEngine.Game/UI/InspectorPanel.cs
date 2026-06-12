using Raylib_CsLo;
using VanEngine.Game.Architecture;
using VanEngine.Game.Core;
using static Raylib_CsLo.Raylib;
using RlVec2 = System.Numerics.Vector2;

namespace VanEngine.Game.UI;

public enum InspectorTargetType { None, House, Citizen }

public sealed class InspectorPanel
{
    private readonly SovereignState _state;
    public InspectorTargetType TargetType { get; private set; } = InspectorTargetType.None;
    public ProjectHouse? SelectedHouse { get; private set; }
    public Citizen? SelectedCitizen { get; private set; }
    public bool IsOpen { get; set; }
    public int PanelWidth { get; set; } = 320;
    private int _scrollOffset;
    private string? _actionFeedback;
    private float _feedbackTimer;

    private static Color C(byte r, byte g, byte b, byte a = 255) => new(r, g, b, a);

    public InspectorPanel(SovereignState state)
    {
        _state = state;
    }

    public void SelectHouse(ProjectHouse house)
    {
        SelectedHouse = house;
        SelectedCitizen = null;
        TargetType = InspectorTargetType.House;
        IsOpen = true;
        _scrollOffset = 0;
    }

    public void SelectCitizen(Citizen citizen)
    {
        SelectedCitizen = citizen;
        SelectedHouse = null;
        TargetType = InspectorTargetType.Citizen;
        IsOpen = true;
        _scrollOffset = 0;
    }

    public void Close()
    {
        IsOpen = false;
        TargetType = InspectorTargetType.None;
        SelectedHouse = null;
        SelectedCitizen = null;
    }

    public void Update(float dt)
    {
        if (_feedbackTimer > 0)
        {
            _feedbackTimer -= dt;
            if (_feedbackTimer <= 0) _actionFeedback = null;
        }

        if (!IsOpen) return;

        int panelX = GetScreenWidth() - PanelWidth;
        int panelY = 0;

        int mouseWheel = (int)GetMouseWheelMove();
        if (mouseWheel != 0)
        {
            _scrollOffset -= mouseWheel * 30;
            _scrollOffset = Math.Max(0, _scrollOffset);
        }

        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X > panelX)
            {
                if (TargetType == InspectorTargetType.House && SelectedHouse != null)
                    HandleHouseClick(m, panelX, panelY);
                else if (TargetType == InspectorTargetType.Citizen && SelectedCitizen != null)
                    HandleCitizenClick(m, panelX, panelY);
            }
        }
    }

    private void HandleHouseClick(RlVec2 m, int panelX, int panelY)
    {
        int y = panelY + 60 - _scrollOffset;

        if (_state.Houses.Count > 1 && m.Y >= y && m.Y <= y + 25)
        {
            _state.ModifyResources(new ResourcePack { Wealth = -10 });
            MergeHouses();
            _actionFeedback = "Houses merged! (-10 Wealth)";
            _feedbackTimer = 2f;
            return;
        }
        y += 30;

        if (m.Y >= y && m.Y <= y + 25)
        {
            _state.ModifyResources(new ResourcePack { Wealth = -20 });
            SelectedHouse!.ProjectName += " (renamed)";
            _state.EnqueueLog($"Renamed namespace in {SelectedHouse.ProjectName}");
            _actionFeedback = "Namespace renamed! (-20 Wealth)";
            _feedbackTimer = 2f;
            return;
        }
    }

    private void HandleCitizenClick(RlVec2 m, int panelX, int panelY)
    {
        int y = panelY + 60 - _scrollOffset + 30 + Math.Min(SelectedCitizen!.OwnedFiles.Count, 8) * 20 + 20;

        if (m.Y >= y && m.Y <= y + 25)
        {
            _state.AddLog($"Citizen {SelectedCitizen.Name} files gifted to state.");
            foreach (var f in SelectedCitizen.OwnedFiles.ToList())
            {
                var h = _state.Houses.FirstOrDefault(hh => hh.RootNamespace == SelectedCitizen.NamespaceFamily);
                if (h != null)
                {
                    h.TrackedFiles.Add(new FileNodeAsset { FilePath = f, ClassName = "gifted", LineCount = 0, LastWriteTimeTicks = DateTime.Now.Ticks });
                    h.EvaluateBuildState();
                }
            }
            SelectedCitizen.OwnedFiles.Clear();
            SelectedCitizen.IsActive = false;
            _state.RemoveCitizen(SelectedCitizen);
            _actionFeedback = "Citizen retired.";
            _feedbackTimer = 2f;
            IsOpen = false;
            return;
        }
    }

    private void MergeHouses()
    {
        if (SelectedHouse == null) return;
        var target = _state.Houses.FirstOrDefault(h => h.Id != SelectedHouse.Id);
        if (target == null) return;

        foreach (var f in SelectedHouse.TrackedFiles)
            target.TrackedFiles.Add(f);

        target.EvaluateBuildState();
        _state.RemoveHouse(SelectedHouse);
        _state.AddLog($"Merged '{SelectedHouse.ProjectName}' into '{target.ProjectName}'");
        SelectedHouse = target;
    }

    public void Draw()
    {
        if (!IsOpen) return;

        int panelX = GetScreenWidth() - PanelWidth;
        int panelY = 0;
        int panelH = GetScreenHeight();

        DrawRectangle(panelX, panelY, PanelWidth, panelH, C(15, 18, 24, 240));
        DrawRectangleLinesEx(new Rectangle(panelX, panelY, PanelWidth, panelH), 1, C(60, 120, 200, 180));

        DrawText("INSPECTOR", panelX + 10, panelY + 10, 16, C(210, 215, 224));

        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X > GetScreenWidth() - 30 && m.X < GetScreenWidth() - 10 && m.Y > 10 && m.Y < 30)
            {
                Close();
                return;
            }
        }

        DrawText("X", GetScreenWidth() - 22, 10, 18, RED);

        int y = panelY + 60 - _scrollOffset;

        if (TargetType == InspectorTargetType.House && SelectedHouse != null)
        {
            DrawHouseInspector(panelX, ref y);
        }
        else if (TargetType == InspectorTargetType.Citizen && SelectedCitizen != null)
        {
            DrawCitizenInspector(panelX, ref y);
        }

        if (_actionFeedback != null)
        {
            DrawText(_actionFeedback, panelX + 10, GetScreenHeight() - 40, 14, C(0, 220, 140));
        }
    }

    private void DrawHouseInspector(int panelX, ref int y)
    {
        var h = SelectedHouse!;
        DrawText(h.ProjectName, panelX + 10, y, 14, WHITE);
        y += 22;
        DrawText($"Namespace: {h.RootNamespace}", panelX + 10, y, 12, C(110, 120, 140));
        y += 20;
        DrawText($"State: {h.CurrentState}", panelX + 10, y, 12, C(110, 120, 140));
        y += 20;
        DrawText($"Files: {h.TrackedFiles.Count}", panelX + 10, y, 12, C(110, 120, 140));
        y += 20;

        DrawRectangle(panelX + 10, y, PanelWidth - 20, 1, C(60, 60, 70));
        y += 10;
        DrawText("TRACKED FILES", panelX + 10, y, 12, C(210, 215, 224));
        y += 20;

        foreach (var f in h.TrackedFiles.Take(10))
        {
            string fn = Path.GetFileName(f.FilePath);
            string stats = $"{f.LineCount}L E:{f.ErrorCount} W:{f.WarningCount}";
            DrawText(fn, panelX + 10, y, 10, WHITE);
            DrawText(stats, panelX + 150, y, 10, C(110, 120, 140));
            y += 18;
            if (y > GetScreenHeight() - 100) break;
        }

        if (h.TrackedFiles.Count > 10)
        {
            DrawText($"... and {h.TrackedFiles.Count - 10} more", panelX + 10, y, 10, C(60, 60, 70));
            y += 18;
        }

        DrawRectangle(panelX + 10, y, PanelWidth - 20, 1, C(60, 60, 70));
        y += 10;
        DrawText("ERROR DRILL-DOWN", panelX + 10, y, 12, C(240, 70, 70));
        y += 20;

        bool hasErrors = false;
        foreach (var f in h.TrackedFiles)
        {
            if (f.ErrorCount > 0)
            {
                DrawText($"  {Path.GetFileName(f.FilePath)}: {f.ErrorCount} errors", panelX + 10, y, 10, C(240, 100, 100));
                y += 16;
                hasErrors = true;
            }
            if (y > GetScreenHeight() - 120) break;
        }
        if (!hasErrors)
        {
            DrawText("  No errors", panelX + 10, y, 10, C(0, 220, 140));
            y += 16;
        }

        DrawRectangle(panelX + 10, y, PanelWidth - 20, 1, C(60, 60, 70));
        y += 10;
        DrawText("CITIZEN ROSTER", panelX + 10, y, 12, C(210, 215, 224));
        y += 20;

        int citizenCount = 0;
        foreach (var c in _state.Citizens)
        {
            if (c.IsActive && c.NamespaceFamily == h.RootNamespace)
            {
                string cRole = c.RoleType switch { 0 => "Idle", 1 => "Farmer", 2 => "Militia", 5 => "Governor", _ => "Unknown" };
                DrawText($"  {c.Name} ({cRole}) [{c.OwnedFiles.Count} files]", panelX + 10, y, 10, WHITE);
                y += 16;
                citizenCount++;
                if (y > GetScreenHeight() - 80) break;
            }
        }
        if (citizenCount == 0)
        {
            DrawText("  No citizens assigned", panelX + 10, y, 10, C(110, 120, 140));
            y += 16;
        }

        DrawRectangle(panelX + 10, y, PanelWidth - 20, 1, C(60, 60, 70));
        y += 10;
        DrawText("DIRECTIVE VIOLATIONS", panelX + 10, y, 12, C(240, 200, 50));
        y += 20;

        int violations = 0;
        foreach (var f in h.TrackedFiles)
        {
            if (f.WarningCount > 0)
            {
                DrawText($"  {Path.GetFileName(f.FilePath)}: {f.WarningCount} warnings", panelX + 10, y, 10, C(240, 200, 50));
                y += 16;
                violations++;
            }
            if (y > GetScreenHeight() - 60) break;
        }
        if (violations == 0)
        {
            DrawText("  No violations", panelX + 10, y, 10, C(0, 220, 140));
            y += 16;
        }

        DrawRectangle(panelX + 10, y, PanelWidth - 20, 1, C(60, 60, 70));
        y += 10;
        DrawText("ACTIONS", panelX + 10, y, 12, C(0, 220, 140));
        y += 22;

        if (_state.Houses.Count > 1)
        {
            DrawRectangle(panelX + 10, y, PanelWidth - 20, 25, C(30, 40, 60));
            DrawText("Merge with next house", panelX + 20, y + 4, 12, C(210, 215, 224));
            y += 30;
        }

        DrawRectangle(panelX + 10, y, PanelWidth - 20, 25, C(30, 40, 60));
        DrawText("Rename namespace (-20W)", panelX + 20, y + 4, 12, C(210, 215, 224));
        y += 30;
    }

    private void DrawCitizenInspector(int panelX, ref int y)
    {
        var c = SelectedCitizen!;
        string role = c.RoleType switch { 0 => "Idle", 1 => "Farmer", 2 => "Militia", 5 => "Governor", _ => "Unknown" };
        DrawText(c.Name, panelX + 10, y, 14, WHITE);
        y += 22;
        DrawText($"Role: {role}", panelX + 10, y, 12, C(110, 120, 140));
        y += 20;
        DrawText($"Namespace: {c.NamespaceFamily}", panelX + 10, y, 12, C(110, 120, 140));
        y += 20;
        DrawText($"Files owned: {c.OwnedFiles.Count}", panelX + 10, y, 12, C(110, 120, 140));
        y += 20;
        DrawText($"Lines contributed: {c.CompliantLinesContributed}", panelX + 10, y, 12, C(110, 120, 140));
        y += 20;
        if (c.IsHomeless) DrawText("HOMELESS", panelX + 10, y, 12, C(240, 200, 50));
        y += 20;

        DrawRectangle(panelX + 10, y, PanelWidth - 20, 1, C(60, 60, 70));
        y += 10;
        DrawText("OWNED FILES", panelX + 10, y, 12, C(210, 215, 224));
        y += 20;

        foreach (var f in c.OwnedFiles.Take(8))
        {
            DrawText($"  {Path.GetFileName(f)}", panelX + 10, y, 10, WHITE);
            y += 18;
            if (y > GetScreenHeight() - 100) break;
        }
        if (c.OwnedFiles.Count > 8)
        {
            DrawText($"  ... and {c.OwnedFiles.Count - 8} more", panelX + 10, y, 10, C(60, 60, 70));
            y += 18;
        }

        DrawRectangle(panelX + 10, y, PanelWidth - 20, 1, C(60, 60, 70));
        y += 10;
        DrawText("ACTIONS", panelX + 10, y, 12, C(0, 220, 140));
        y += 22;

        DrawRectangle(panelX + 10, y, PanelWidth - 20, 25, C(30, 40, 60));
        DrawText("Retire (gift files to state)", panelX + 20, y + 4, 12, C(210, 215, 224));
        y += 30;
    }
}
