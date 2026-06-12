using VanEngine.Lyrics.Models;

namespace VanEngine.Lyrics.Engines;

public class LyricalGenerator
{
    private readonly List<PhoneticWord> _lexicon;
    private readonly SyllableMatcher _syllableMatcher;
    private readonly RhymeEngine _rhymeEngine;
    private readonly StressPatternMatcher _stressMatcher;
    private readonly ThematicCoherence _thematicCoherence;
    private readonly TemplateEngine _templateEngine;
    private readonly Random _random = new();

    public LyricalGenerator(List<PhoneticWord> lexicon)
    {
        _lexicon = lexicon;
        _syllableMatcher = new SyllableMatcher();
        _rhymeEngine = new RhymeEngine(lexicon);
        _stressMatcher = new StressPatternMatcher();
        _thematicCoherence = new ThematicCoherence();
        _templateEngine = new TemplateEngine();
    }

    public LyricalResponse Generate(LyricalRequest request)
    {
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();

        var templateType = request.GenerationType.ToLower() switch
        {
            "analysis" or "battleresponse" => "battle",
            "therapy" => "therapy",
            _ => "seed"
        };

        var template = _templateEngine.GetTemplate(templateType);
        var lines = new List<string>();
        var energies = new List<double>();
        var archetypes = new List<string>();

        foreach (var phase in template.Phases)
        {
            var barsInPhase = phase.EndBar - phase.StartBar + 1;
            var archetype = !string.IsNullOrEmpty(phase.RequiredArchetype)
                ? phase.RequiredArchetype
                : request.Archetype;

            for (int bar = 0; bar < barsInPhase; bar++)
            {
                var line = GenerateLine(archetype, request.Spb, phase.MinEnergy, phase.MaxEnergy, request.SeedTokens);
                lines.Add(line);

                var wordsInLine = line.Split(' ').Select(w => _lexicon.FirstOrDefault(l => l.Token == w.ToLower()));
                var avgEnergy = wordsInLine.Where(w => w != null).Average(w => w?.EnergyScore ?? 0.5);
                energies.Add(avgEnergy);
                archetypes.Add(archetype);
                _thematicCoherence.AdvanceTheme(line);
            }
        }

        var rhymeLines = ApplyRhymeScheme(lines, template.RhymeScheme);

        List<string> resonantTokens = new();
        if (request.IsTherapeutic && !string.IsNullOrEmpty(request.InputLyrics))
        {
            resonantTokens = ExtractResonantTokens(request.InputLyrics);
            rhymeLines = InjectTherapeuticLanguage(rhymeLines, resonantTokens, request.EmotionalState);
        }

        if (request.GenerationType == "BattleResponse" && !string.IsNullOrEmpty(request.InputLyrics))
        {
            rhymeLines = GenerateBattleResponse(rhymeLines, request.InputLyrics);
        }

        stopwatch.Stop();

        return new LyricalResponse
        {
            GeneratedVerse = string.Join("\n", rhymeLines),
            Lines = rhymeLines,
            LineEnergies = energies,
            LineArchetypes = archetypes,
            AverageEnergy = energies.Any() ? energies.Average() : 0.5,
            DominantArchetype = archetypes.GroupBy(a => a).OrderByDescending(g => g.Count()).First().Key,
            ProcessingTimeMs = stopwatch.Elapsed.TotalMilliseconds,
            IsTherapeuticOutput = request.IsTherapeutic,
            TherapeuticIntent = request.IsTherapeutic ? "Processing emotional resonance" : null,
            ResonantTokens = resonantTokens,
            Metadata = new Dictionary<string, object>
            {
                ["template"] = template.Name,
                ["seed_tokens"] = request.SeedTokens,
                ["energy_target"] = request.EnergyTarget
            }
        };
    }

    private string GenerateLine(string archetype, double targetSpb, double minEnergy, double maxEnergy, List<string> seedTokens)
    {
        var filteredLexicon = _lexicon
            .Where(w => w.Archetype == archetype || string.IsNullOrEmpty(archetype))
            .Where(w => w.EnergyScore >= minEnergy && w.EnergyScore <= maxEnergy)
            .ToList();

        if (!filteredLexicon.Any())
            filteredLexicon = _lexicon;

        var words = _syllableMatcher.MatchBySyllables(filteredLexicon, (int)targetSpb);

        if (seedTokens.Any())
        {
            foreach (var seed in seedTokens)
            {
                var seedWord = _lexicon.FirstOrDefault(w => w.Token == seed.ToLower());
                if (seedWord != null && !words.Contains(seedWord))
                {
                    if (words.Any())
                        words.Insert(_random.Next(words.Count), seedWord);
                    else
                        words.Add(seedWord);
                }
            }
        }

        var themeKeyword = _thematicCoherence.GetThemeKeyword();
        if (!string.IsNullOrEmpty(themeKeyword))
        {
            var themeWord = _lexicon.FirstOrDefault(w => w.Token == themeKeyword);
            if (themeWord != null && !words.Contains(themeWord))
                words.Add(themeWord);
        }

        if (!words.Any())
            return "[fill]";

        var line = string.Join(" ", words.Select(w => w.Token));
        line = char.ToUpper(line[0]) + line.Substring(1);

        if (!line.EndsWith('.') && !line.EndsWith('!') && !line.EndsWith('?'))
            line += ".";

        return line;
    }

    private List<string> ApplyRhymeScheme(List<string> lines, string scheme)
    {
        var result = new List<string>(lines);
        for (int i = 0; i < result.Count && i < scheme.Length; i++)
        {
            _ = scheme[i];
        }
        return result;
    }

    private List<string> ExtractResonantTokens(string inputLyrics)
    {
        var tokens = inputLyrics.ToLower()
            .Split(new[] { ' ', '\n', '\r', '.', ',', '!', '?' }, StringSplitOptions.RemoveEmptyEntries)
            .Where(w => w.Length > 3)
            .Distinct()
            .ToList();

        return tokens
            .Where(t => _lexicon.Any(w => w.Token == t))
            .Take(5)
            .ToList();
    }

    private List<string> InjectTherapeuticLanguage(List<string> lines, List<string> resonantTokens, string? emotionalState)
    {
        var result = new List<string>(lines);
        if (resonantTokens.Any() && result.Any())
        {
            var tokenToInject = resonantTokens.First();
            result[result.Count - 1] = $"{result.Last()} {tokenToInject}.";
        }
        _ = emotionalState;
        return result;
    }

    private List<string> GenerateBattleResponse(List<string> lines, string opponentLyrics)
    {
        var result = new List<string>(lines);
        var opponentWords = opponentLyrics.ToLower().Split(' ');
        var weakIndicators = new[] { "can't", "won't", "never", "fake", "weak", "sorry" };
        var weaknesses = opponentWords.Where(w => weakIndicators.Contains(w)).ToList();
        if (weaknesses.Any() && result.Any())
        {
            result[0] = $"You said '{weaknesses.First()}'? {result[0]}";
        }
        return result;
    }
}
