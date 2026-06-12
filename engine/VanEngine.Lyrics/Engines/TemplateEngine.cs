using VanEngine.Lyrics.Models;

namespace VanEngine.Lyrics.Engines;

public class TemplateEngine
{
    private readonly Dictionary<string, VerseTemplate> _templates;

    public TemplateEngine()
    {
        _templates = new Dictionary<string, VerseTemplate>();
        InitializeTemplates();
    }

    private void InitializeTemplates()
    {
        _templates["gat"] = new VerseTemplate
        {
            Name = "Gat Lifecycle",
            BarCount = 8,
            RhymeScheme = "AABCCBDD",
            Phases = new List<Phase>
            {
                new() { Name = "Gatvuller", StartBar = 1, EndBar = 3, Theme = "Problem/Hole", RequiredArchetype = "Chaos", MinEnergy = 0.6 },
                new() { Name = "Gatstamper", StartBar = 4, EndBar = 6, Theme = "Build/Harden", RequiredArchetype = "Codex", MinEnergy = 0.4, MaxEnergy = 0.8 },
                new() { Name = "Gatveer", StartBar = 7, EndBar = 8, Theme = "Polish/Finish", RequiredArchetype = "Butler", MaxEnergy = 0.4 }
            }
        };

        _templates["battle"] = new VerseTemplate
        {
            Name = "Battle Response",
            BarCount = 8,
            RhymeScheme = "AABBCCDD",
            Phases = new List<Phase>
            {
                new() { Name = "Setup", StartBar = 1, EndBar = 4, Theme = "Challenge", RequiredArchetype = "Chaos", MinEnergy = 0.7 },
                new() { Name = "Punch", StartBar = 5, EndBar = 8, Theme = "Destroy", RequiredArchetype = "Chaos", MinEnergy = 0.8 }
            }
        };

        _templates["therapy"] = new VerseTemplate
        {
            Name = "Therapy",
            BarCount = 8,
            RhymeScheme = "ABABABAB",
            Phases = new List<Phase>
            {
                new() { Name = "Acknowledge", StartBar = 1, EndBar = 3, Theme = "Pain", RequiredArchetype = "Chaos", MaxEnergy = 0.5 },
                new() { Name = "Process", StartBar = 4, EndBar = 6, Theme = "Healing", RequiredArchetype = "Butler", MinEnergy = 0.3, MaxEnergy = 0.6 },
                new() { Name = "Release", StartBar = 7, EndBar = 8, Theme = "Hope", RequiredArchetype = "Codex", MinEnergy = 0.2, MaxEnergy = 0.5 }
            }
        };

        _templates["seed"] = new VerseTemplate
        {
            Name = "Seed Token",
            BarCount = 8,
            RhymeScheme = "AABBCCDD",
            Phases = new List<Phase>
            {
                new() { Name = "Introduction", StartBar = 1, EndBar = 8, Theme = "Custom", RequiredArchetype = "" }
            }
        };
    }

    public VerseTemplate GetTemplate(string type) =>
        _templates.GetValueOrDefault(type, _templates["seed"]);

    public List<string> GetAvailableTemplates() => _templates.Keys.ToList();
}
