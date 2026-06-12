using VanEngine.Lyrics.Models;

namespace VanEngine.Lyrics.Engines;

public class RhymeEngine
{
    private readonly Dictionary<string, List<PhoneticWord>> _rhymeFamilies;

    public RhymeEngine(List<PhoneticWord> lexicon)
    {
        _rhymeFamilies = lexicon
            .GroupBy(w => w.RhymeFamily)
            .ToDictionary(g => g.Key, g => g.ToList());
    }

    public PhoneticWord? FindRhyme(PhoneticWord word, List<PhoneticWord> lexicon)
    {
        if (!_rhymeFamilies.ContainsKey(word.RhymeFamily))
            return null;

        var rhymes = _rhymeFamilies[word.RhymeFamily]
            .Where(w => w.Token != word.Token)
            .ToList();

        return rhymes.Any() ? rhymes[new Random().Next(rhymes.Count)] : null;
    }

    public List<List<PhoneticWord>> EnforceRhymeScheme(
        List<List<PhoneticWord>> bars,
        string rhymeScheme)
    {
        var result = new List<List<PhoneticWord>>();
        var rhymeTargets = new Dictionary<char, PhoneticWord>();

        for (int i = 0; i < bars.Count && i < rhymeScheme.Length; i++)
        {
            var schemeChar = rhymeScheme[i];
            var bar = bars[i];
            if (!bar.Any()) continue;

            var lastWord = bar.Last();

            if (rhymeTargets.ContainsKey(schemeChar))
            {
                var rhymeWord = FindRhyme(rhymeTargets[schemeChar], bar);
                if (rhymeWord != null)
                {
                    bar.RemoveAt(bar.Count - 1);
                    bar.Add(rhymeWord);
                }
            }
            else
            {
                rhymeTargets[schemeChar] = lastWord;
            }

            result.Add(bar);
        }

        return result;
    }
}
