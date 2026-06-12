using Raylib_CsLo;
using VanEngine.Game.Core;
using static Raylib_CsLo.Raylib;

namespace VanEngine.Game.UI;

public sealed class TimelineEntry
{
    public int Year { get; set; }
    public string EventType { get; set; } = "info";
    public string Description { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
}

public sealed class HistoryTimeline
{
    private readonly SovereignState _state;
    private int _scrollOffset;
    private string _filterType = "all";
    private bool _isExpanded;
    private float _sparklineDataSov = 100f;
    private float _sparklineDataFood = 250f;
    private int _sparklineCount;

    private static Color C(byte r, byte g, byte b, byte a = 255) => new(r, g, b, a);

    public HistoryTimeline(SovereignState state)
    {
        _state = state;
    }

    public void AddEntry(int year, string eventType, string description, string source)
    {
        _state.AddTimelineEntry(year, eventType, description, source);
    }

    public void Update()
    {
        _sparklineCount++;

        var res = _state.Resources;
        _sparklineDataSov = _sparklineDataSov * 0.9f + (float)_state.Sovereignty * 0.1f;
        _sparklineDataFood = _sparklineDataFood * 0.9f + res.Food * 0.1f;

        int wheel = (int)GetMouseWheelMove();
        if (wheel != 0 && _isExpanded)
        {
            _scrollOffset -= wheel * 40;
            _scrollOffset = Math.Max(0, _scrollOffset);
        }
    }

    public void ToggleExpanded() => _isExpanded = !_isExpanded;
    public bool IsExpanded => _isExpanded;

    public string ExportAsText()
    {
        var sb = new System.Text.StringBuilder();
        sb.AppendLine("=== Oera Linda Timeline ===");
        sb.AppendLine($"Exported: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
        sb.AppendLine();

        var entries = _state.GetTimeline();
        foreach (var e in entries)
        {
            sb.AppendLine($"Year {e.Year} [{e.EventType}] {e.Description} (source: {e.Source})");
        }
        return sb.ToString();
    }

    public void Draw(int x, int y, int width, int height)
    {
        DrawRectangle(x, y, width, height, C(22, 26, 34, 230));
        DrawRectangleLinesEx(new Rectangle(x, y, width, height), 1, C(60, 120, 200, 150));
        DrawText("HISTORY TIMELINE", x + 10, y + 8, 14, C(210, 215, 224));

        string expandLabel = _isExpanded ? "[-]" : "[+]";
        DrawText(expandLabel, x + width - 30, y + 8, 14, WHITE);

        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X >= x + width - 35 && m.X <= x + width - 5 && m.Y >= y + 5 && m.Y <= y + 25)
                ToggleExpanded();
        }

        if (!_isExpanded) return;

        DrawLine(x + 10, y + 30, x + width - 10, y + 30, C(60, 60, 70));

        int filterY = y + 35;
        DrawFilterButton(x + 10, filterY, "all", ref _filterType);
        DrawFilterButton(x + 60, filterY, "citizen", ref _filterType);
        DrawFilterButton(x + 125, filterY, "house", ref _filterType);
        DrawFilterButton(x + 185, filterY, "event", ref _filterType);
        DrawFilterButton(x + 245, filterY, "crime", ref _filterType);

        int graphY = filterY + 30;
        DrawSparklines(x + 10, graphY, width - 20, 40);

        int listY = graphY + 50 - _scrollOffset;
        var entries = _state.GetTimeline();
        int visibleHeight = height - (listY - y);

        foreach (var e in entries)
        {
            if (_filterType != "all" && e.EventType != _filterType) continue;

            if (listY > y && listY < y + height - 10)
            {
                var col = e.EventType switch
                {
                    "citizen" => C(0, 220, 140),
                    "house" => C(0, 160, 255),
                    "event" => C(240, 200, 50),
                    "crime" => C(240, 70, 70),
                    _ => C(210, 215, 224),
                };
                string line = $"Y{e.Year} [{e.EventType}] {e.Description}";
                DrawText(line, x + 12, listY, 10, col);
            }
            listY += 16;
            if (listY > y + height) break;
        }

        DrawRectangle(x + 10, y + height - 28, width - 20, 22, C(30, 35, 45));
        DrawText("Export as text [E]", x + 15, y + height - 24, 11, C(110, 120, 140));

        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X >= x + 10 && m.X <= x + width - 10 && m.Y >= y + height - 28 && m.Y <= y + height - 6)
            {
                string exportPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, $"timeline_export_{DateTime.Now:yyyyMMdd_HHmmss}.txt");
                File.WriteAllText(exportPath, ExportAsText());
                _state.EnqueueLog($"Timeline exported to {Path.GetFileName(exportPath)}");
            }
        }
    }

    private void DrawFilterButton(int x, int y, string label, ref string current)
    {
        bool selected = current == label;
        var bg = selected ? C(60, 100, 180) : C(30, 35, 45);
        DrawRectangle(x, y, 45, 22, bg);
        DrawText(label, x + 5, y + 4, 10, selected ? WHITE : C(110, 120, 140));

        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_LEFT))
        {
            var m = GetMousePosition();
            if (m.X >= x && m.X <= x + 45 && m.Y >= y && m.Y <= y + 22)
                current = label;
        }
    }

    private void DrawSparklines(int x, int y, int width, int height)
    {
        DrawText("Sovereignty", x, y, 9, C(110, 120, 140));
        float sovRatio = _sparklineDataSov / 100f;
        DrawRectangle(x + 60, y, (int)(width - 80) / 2, 4, C(0, 220, 140, 100));
        DrawRectangle(x + 60, y, (int)((width - 80) / 2 * sovRatio), 4, C(0, 220, 140));

        DrawText("Food", x + 60 + (width - 80) / 2 + 10, y, 9, C(110, 120, 140));
        float foodRatio = Math.Min(1f, _sparklineDataFood / 500f);
        DrawRectangle(x + 60 + (width - 80) / 2 + 40, y, (int)(width - 80) / 3, 4, C(0, 160, 255, 100));
        DrawRectangle(x + 60 + (width - 80) / 2 + 40, y, (int)((width - 80) / 3 * foodRatio), 4, C(0, 160, 255));
    }
}
