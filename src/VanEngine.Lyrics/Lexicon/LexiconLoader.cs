using Newtonsoft.Json;
using VanEngine.Lyrics.Models;

namespace VanEngine.Lyrics.Lexicon;

public class LexiconLoader
{
    public List<PhoneticWord> Load(string lexiconPath = "Data/lexicon.json")
    {
        if (!File.Exists(lexiconPath))
        {
            return CreateFallbackLexicon();
        }

        var json = File.ReadAllText(lexiconPath);
        var data = JsonConvert.DeserializeObject<LexiconData>(json);

        if (data?.Lexicon == null || !data.Lexicon.Any())
        {
            return CreateFallbackLexicon();
        }

        return data.Lexicon;
    }

    private static List<PhoneticWord> CreateFallbackLexicon()
    {
        return new List<PhoneticWord>
        {
            new() { Token = "chaos", Syllables = 2, StressPattern = "10", EnergyScore = 0.92, Archetype = "Chaos", RhymeFamily = "aos" },
            new() { Token = "codex", Syllables = 2, StressPattern = "10", EnergyScore = 0.65, Archetype = "Codex", RhymeFamily = "ex" },
            new() { Token = "shadow", Syllables = 2, StressPattern = "10", EnergyScore = 0.45, Archetype = "Chaos", RhymeFamily = "ow" },
            new() { Token = "fire", Syllables = 1, StressPattern = "1", EnergyScore = 0.88, Archetype = "Chaos", RhymeFamily = "ire" },
            new() { Token = "rising", Syllables = 2, StressPattern = "10", EnergyScore = 0.72, Archetype = "Codex", RhymeFamily = "ing" },
            new() { Token = "broken", Syllables = 2, StressPattern = "10", EnergyScore = 0.68, Archetype = "Chaos", RhymeFamily = "en" },
            new() { Token = "healing", Syllables = 2, StressPattern = "10", EnergyScore = 0.55, Archetype = "Butler", RhymeFamily = "ing" },
            new() { Token = "storm", Syllables = 1, StressPattern = "1", EnergyScore = 0.85, Archetype = "Chaos", RhymeFamily = "orm" },
            new() { Token = "light", Syllables = 1, StressPattern = "1", EnergyScore = 0.50, Archetype = "Codex", RhymeFamily = "ight" },
            new() { Token = "pain", Syllables = 1, StressPattern = "1", EnergyScore = 0.70, Archetype = "Chaos", RhymeFamily = "ain" }
        };
    }

    private sealed class LexiconData
    {
        public List<PhoneticWord> Lexicon { get; set; } = new();
        public List<object>? GlueWords { get; set; }
    }
}
