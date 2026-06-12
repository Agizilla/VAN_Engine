using System.Text.Json;

namespace VanEngine.Game.Core;

public class SettingsManager
{
    public float GameSpeed { get; set; } = 1.0f;
    public float UIScale { get; set; } = 1.0f;
    public Dictionary<string, float> DirectiveWeights { get; set; } = new();
    public Dictionary<string, bool> EnabledDirectives { get; set; } = new();
    public Dictionary<string, int> KeyBindings { get; set; } = new();
    public bool EnableTelemetry { get; set; } = false;

    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        WriteIndented = true,
    };

    public static SettingsManager LoadOrDefault()
    {
        string path = Path.Combine(AppContext.BaseDirectory, "settings.json");
        if (File.Exists(path))
        {
            try
            {
                var json = File.ReadAllText(path);
                return JsonSerializer.Deserialize<SettingsManager>(json) ?? new();
            }
            catch { }
        }
        return new();
    }

    public void Save()
    {
        string path = Path.Combine(AppContext.BaseDirectory, "settings.json");
        var json = JsonSerializer.Serialize(this, JsonOpts);
        File.WriteAllText(path, json);
    }
}
