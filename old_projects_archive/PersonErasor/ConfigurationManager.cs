using System.Text.Json;
using System.Text.Json.Serialization;

namespace SovereignIDE.Core.Services;

/// <summary>
/// Application configuration with persistence.
/// 
/// Stores:
/// - API keys (encrypted)
/// - User preferences
/// - Window layout
/// - Recent projects
/// </summary>
public class Configuration
{
    [JsonPropertyName("apiKeys")]
    public ApiKeysConfig ApiKeys { get; set; } = new();

    [JsonPropertyName("preferences")]
    public PreferencesConfig Preferences { get; set; } = new();

    [JsonPropertyName("recentProjects")]
    public List<string> RecentProjects { get; set; } = new();

    [JsonPropertyName("windowLayout")]
    public WindowLayoutConfig? WindowLayout { get; set; }
}

public class ApiKeysConfig
{
    [JsonPropertyName("anthropic")]
    public string? Anthropic { get; set; }

    [JsonPropertyName("openai")]
    public string? OpenAI { get; set; }

    [JsonPropertyName("deepseek")]
    public string? DeepSeek { get; set; }
}

public class PreferencesConfig
{
    [JsonPropertyName("defaultModel")]
    public string DefaultModel { get; set; } = "Claude";

    [JsonPropertyName("autoSaveEnabled")]
    public bool AutoSaveEnabled { get; set; } = true;

    [JsonPropertyName("autoSaveIntervalSeconds")]
    public int AutoSaveIntervalSeconds { get; set; } = 30;

    [JsonPropertyName("clipboardWatcherEnabled")]
    public bool ClipboardWatcherEnabled { get; set; } = true;

    [JsonPropertyName("darkMode")]
    public bool DarkMode { get; set; } = true;

    [JsonPropertyName("confirmDangerousCommands")]
    public bool ConfirmDangerousCommands { get; set; } = true;

    [JsonPropertyName("maxBackups")]
    public int MaxBackups { get; set; } = 10;

    [JsonPropertyName("commandTimeoutSeconds")]
    public int CommandTimeoutSeconds { get; set; } = 60;
}

public class WindowLayoutConfig
{
    [JsonPropertyName("width")]
    public int Width { get; set; } = 1600;

    [JsonPropertyName("height")]
    public int Height { get; set; } = 900;

    [JsonPropertyName("x")]
    public int X { get; set; }

    [JsonPropertyName("y")]
    public int Y { get; set; }

    [JsonPropertyName("maximized")]
    public bool Maximized { get; set; }

    [JsonPropertyName("leftPanelWidth")]
    public int LeftPanelWidth { get; set; } = 320;

    [JsonPropertyName("rightPanelWidth")]
    public int RightPanelWidth { get; set; } = 420;
}

/// <summary>
/// Manages configuration persistence.
/// </summary>
public class ConfigurationManager
{
    private readonly string _configPath;
    private Configuration _config;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    public Configuration Config => _config;

    public ConfigurationManager(string? configPath = null)
    {
        _configPath = configPath ?? GetDefaultConfigPath();
        _config = Load();
    }

    private static string GetDefaultConfigPath()
    {
        var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        var appDir = Path.Combine(appData, "SovereignIDE");
        Directory.CreateDirectory(appDir);
        return Path.Combine(appDir, "config.json");
    }

    /// <summary>
    /// Loads configuration from disk.
    /// Creates default if not exists.
    /// </summary>
    public Configuration Load()
    {
        try
        {
            if (!File.Exists(_configPath))
            {
                var defaultConfig = new Configuration();
                Save(defaultConfig);
                return defaultConfig;
            }

            var json = File.ReadAllText(_configPath);
            var config = JsonSerializer.Deserialize<Configuration>(json, JsonOptions);

            return config ?? new Configuration();
        }
        catch
        {
            // Corrupted config, use defaults
            return new Configuration();
        }
    }

    /// <summary>
    /// Saves configuration to disk.
    /// </summary>
    public void Save(Configuration? config = null)
    {
        try
        {
            var toSave = config ?? _config;
            var json = JsonSerializer.Serialize(toSave, JsonOptions);
            File.WriteAllText(_configPath, json);
            _config = toSave;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"⚠️ Failed to save config: {ex.Message}");
        }
    }

    /// <summary>
    /// Adds project to recent list.
    /// </summary>
    public void AddRecentProject(string projectPath)
    {
        // Remove if already exists
        _config.RecentProjects.Remove(projectPath);

        // Add to front
        _config.RecentProjects.Insert(0, projectPath);

        // Keep max 10
        if (_config.RecentProjects.Count > 10)
        {
            _config.RecentProjects = _config.RecentProjects.Take(10).ToList();
        }

        Save();
    }

    /// <summary>
    /// Sets API key for a model.
    /// 
    /// Note: This stores in plaintext for now.
    /// TODO: Implement encryption using DPAPI.
    /// </summary>
    public void SetApiKey(string model, string apiKey)
    {
        switch (model.ToLowerInvariant())
        {
            case "anthropic":
            case "claude":
                _config.ApiKeys.Anthropic = apiKey;
                break;
            case "openai":
            case "gpt":
                _config.ApiKeys.OpenAI = apiKey;
                break;
            case "deepseek":
                _config.ApiKeys.DeepSeek = apiKey;
                break;
        }

        Save();
    }

    /// <summary>
    /// Gets API key for a model.
    /// </summary>
    public string? GetApiKey(string model)
    {
        return model.ToLowerInvariant() switch
        {
            "anthropic" or "claude" => _config.ApiKeys.Anthropic,
            "openai" or "gpt" => _config.ApiKeys.OpenAI,
            "deepseek" => _config.ApiKeys.DeepSeek,
            _ => null
        };
    }

    /// <summary>
    /// Updates window layout from current form state.
    /// </summary>
    public void UpdateWindowLayout(int width, int height, int x, int y, bool maximized, int leftPanelWidth, int rightPanelWidth)
    {
        _config.WindowLayout = new WindowLayoutConfig
        {
            Width = width,
            Height = height,
            X = x,
            Y = y,
            Maximized = maximized,
            LeftPanelWidth = leftPanelWidth,
            RightPanelWidth = rightPanelWidth
        };

        Save();
    }
}
