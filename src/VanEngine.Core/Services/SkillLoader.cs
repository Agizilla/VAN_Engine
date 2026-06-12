using System.Text.Json;

namespace VanEngine.Core.Services;

public class SkillLoader
{
    private readonly string _skillsDirectory;
    private readonly string _customizationsDirectory;
    private readonly Dictionary<string, ExtendManifest> _manifests = new();

    public SkillLoader(string baseDirectory)
    {
        _skillsDirectory = Path.Combine(baseDirectory, "skills");
        _customizationsDirectory = Path.Combine(baseDirectory, "USER", "SKILLCUSTOMIZATIONS");
        LoadManifests();
    }

    private void LoadManifests()
    {
        if (!Directory.Exists(_customizationsDirectory)) return;

        foreach (var skillDir in Directory.GetDirectories(_customizationsDirectory))
        {
            var skillName = Path.GetFileName(skillDir);
            var manifestPath = Path.Combine(skillDir, "EXTEND.yaml");

            if (File.Exists(manifestPath))
            {
                try
                {
                    var content = File.ReadAllText(manifestPath);
                    var manifest = ParseExtendManifest(content);
                    if (manifest != null && manifest.Enabled)
                        _manifests[skillName] = manifest;
                }
                catch { }
            }
        }
    }

    private static ExtendManifest? ParseExtendManifest(string yaml)
    {
        var result = new ExtendManifest();
        foreach (var line in yaml.Split('\n'))
        {
            if (line.StartsWith("skill:"))
                result.Skill = line[6..].Trim();
            else if (line.StartsWith("extends:"))
            {
                var extends = line[8..].Trim();
                result.Extends = extends.Split(',').Select(e => e.Trim().Trim('\'').Trim('"')).ToList();
            }
            else if (line.StartsWith("merge_strategy:"))
                result.MergeStrategy = line[15..].Trim();
            else if (line.StartsWith("enabled:"))
                result.Enabled = line[8..].Trim().Equals("true", StringComparison.OrdinalIgnoreCase);
            else if (line.StartsWith("description:"))
                result.Description = line[12..].Trim();
        }
        return string.IsNullOrEmpty(result.Skill) ? null : result;
    }

    public async Task<T> LoadConfigAsync<T>(string skillName, string configFileName) where T : new()
    {
        var baseConfigPath = Path.Combine(_skillsDirectory, skillName, configFileName);
        T baseConfig;

        if (File.Exists(baseConfigPath))
        {
            var json = await File.ReadAllTextAsync(baseConfigPath);
            baseConfig = JsonSerializer.Deserialize<T>(json) ?? new T();
        }
        else
        {
            baseConfig = new T();
        }

        if (!_manifests.TryGetValue(skillName, out var manifest))
            return baseConfig;

        if (!manifest.Extends.Contains(configFileName))
            return baseConfig;

        var customConfigPath = Path.Combine(_customizationsDirectory, skillName, configFileName);
        if (!File.Exists(customConfigPath))
            return baseConfig;

        var customJson = await File.ReadAllTextAsync(customConfigPath);
        var customConfig = JsonSerializer.Deserialize<T>(customJson);
        if (customConfig == null) return baseConfig;

        return manifest.MergeStrategy switch
        {
            "override" => customConfig,
            "deep_merge" => DeepMerge(baseConfig, customConfig),
            _ => customConfig
        };
    }

    private static T DeepMerge<T>(T base_, T custom) where T : new()
    {
        return JsonSerializer.Deserialize<T>(JsonSerializer.Serialize(custom)) ?? base_;
    }

    public bool HasCustomizations(string skillName) => _manifests.ContainsKey(skillName);

    public List<string> ListCustomizedSkills() => _manifests.Keys.ToList();

    public string GetCustomizationPath(string skillName) => Path.Combine(_customizationsDirectory, skillName);
}

public class ExtendManifest
{
    public string Skill { get; set; } = "";
    public List<string> Extends { get; set; } = new();
    public string MergeStrategy { get; set; } = "append";
    public bool Enabled { get; set; } = true;
    public string Description { get; set; } = "";
}
