using VanEngine.Lyrics.Models;
using VanEngine.Lyrics.Engines;
using VanEngine.Lyrics.Lexicon;

namespace VanEngine.Lyrics.Processors;

public class LyricalVanProcessor
{
    private readonly LyricalGenerator _generator;
    private readonly LexiconLoader _lexiconLoader;
    private readonly PhoneticAnalyzer _analyzer;

    public LyricalVanProcessor(string lexiconPath = "Data/lexicon.json")
    {
        _lexiconLoader = new LexiconLoader();
        var lexicon = _lexiconLoader.Load(lexiconPath);
        _generator = new LyricalGenerator(lexicon);
        _analyzer = new PhoneticAnalyzer();
    }

    public LyricalResponse ProcessVanRequest(VanLyricalRequest request)
    {
        var lyricalRequest = new LyricalRequest
        {
            GenerationType = request.GenerationType,
            InputLyrics = request.InputLyrics,
            SeedTokens = request.SeedTokens,
            Archetype = request.Archetype,
            BarCount = request.BarCount,
            Spb = request.Spb,
            EnergyTarget = request.EnergyTarget,
            UseGlueWords = request.UseGlueWords,
            IsTherapeutic = request.IsTherapeutic,
            EmotionalState = request.EmotionalState
        };

        return _generator.Generate(lyricalRequest);
    }

    public void ExpandLexicon(List<string> newWords, string archetype = "Generic")
    {
    }

    public LyricAnalysis AnalyzeLyrics(string lyrics)
    {
        var words = lyrics.ToLower().Split(new[] { ' ', '\n', '\r', '.', ',', '!', '?' }, StringSplitOptions.RemoveEmptyEntries);

        var analysis = new LyricAnalysis
        {
            WordCount = words.Length,
            UniqueWordCount = words.Distinct().Count(),
            AverageWordLength = words.Average(w => w.Length)
        };

        var energies = words
            .Select(w => _analyzer.Analyze(w).EnergyScore)
            .ToList();
        analysis.AverageEnergy = energies.Any() ? energies.Average() : 0.5;

        var themeKeywords = new Dictionary<string, string[]>
        {
            ["chaos"] = new[] { "break", "fall", "void", "shadow", "storm", "rage", "burn", "crash", "pain", "hurt" },
            ["order"] = new[] { "rise", "build", "light", "code", "truth", "forge", "stand", "crown", "hope", "heal" },
            ["flow"] = new[] { "glide", "move", "ride", "wave", "tide", "stream", "float", "drift" }
        };

        var themeScores = new Dictionary<string, int>();
        foreach (var theme in themeKeywords)
        {
            var score = words.Count(w => theme.Value.Contains(w));
            themeScores[theme.Key] = score;
        }

        analysis.DominantTheme = themeScores.OrderByDescending(kv => kv.Value).First().Key;

        return analysis;
    }
}

public class VanLyricalRequest
{
    public string GenerationType { get; set; } = "SeedTokens";
    public string? InputLyrics { get; set; }
    public List<string> SeedTokens { get; set; } = new();
    public string Archetype { get; set; } = "Chaos";
    public int BarCount { get; set; } = 8;
    public double Spb { get; set; } = 14.0;
    public double EnergyTarget { get; set; } = 0.6;
    public bool UseGlueWords { get; set; } = true;
    public bool IsTherapeutic { get; set; }
    public string? EmotionalState { get; set; }
}

public class LyricAnalysis
{
    public int WordCount { get; set; }
    public int UniqueWordCount { get; set; }
    public double AverageWordLength { get; set; }
    public double AverageEnergy { get; set; }
    public string DominantTheme { get; set; } = string.Empty;
}
