using VanEngine.Lyrics.Models;

namespace VanEngine.Lyrics.Lexicon;

public class LexiconExpander
{
    private readonly PhoneticAnalyzer _analyzer;

    public LexiconExpander()
    {
        _analyzer = new PhoneticAnalyzer();
    }

    public List<PhoneticWord> ExpandWith(List<PhoneticWord> existing, List<string> newWords, string archetype = "Generic")
    {
        var existingTokens = new HashSet<string>(existing.Select(w => w.Token.ToLower()));
        var additions = new List<PhoneticWord>();

        foreach (var word in newWords)
        {
            var lower = word.ToLower();
            if (existingTokens.Contains(lower)) continue;

            var analyzed = _analyzer.Analyze(word, archetype);
            additions.Add(analyzed);
            existingTokens.Add(lower);
        }

        existing.AddRange(additions);
        return existing;
    }

    public List<PhoneticWord> GenerateRhymeVariants(PhoneticWord source, int count)
    {
        var variants = new List<PhoneticWord>();

        var rhymeEndings = new Dictionary<string, string[]>
        {
            ["ing"] = new[] { "bringing", "singing", "ringing", "flinging", "swinging" },
            ["ight"] = new[] { "night", "fight", "might", "sight", "tight", "bright" },
            ["ain"] = new[] { "rain", "strain", "pain", "gain", "train", "plain" },
            ["ire"] = new[] { "fire", "wire", "tire", "liar", "buyer" },
            ["orm"] = new[] { "storm", "warm", "form", "norm", "swarm" }
        };

        if (rhymeEndings.TryGetValue(source.RhymeFamily, out var rhymes))
        {
            foreach (var r in rhymes.Take(count))
            {
                variants.Add(_analyzer.Analyze(r, source.Archetype));
            }
        }

        return variants;
    }
}
