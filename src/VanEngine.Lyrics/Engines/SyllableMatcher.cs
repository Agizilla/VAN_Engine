using VanEngine.Lyrics.Models;

namespace VanEngine.Lyrics.Engines;

public class SyllableMatcher
{
    private readonly Random _random = new();

    public List<PhoneticWord> MatchBySyllables(
        List<PhoneticWord> lexicon,
        int targetSyllables,
        string? requiredArchetype = null,
        double? minEnergy = null,
        double? maxEnergy = null)
    {
        var candidates = lexicon.Where(w => w.Syllables <= targetSyllables);

        if (!string.IsNullOrEmpty(requiredArchetype))
            candidates = candidates.Where(w => w.Archetype == requiredArchetype);

        if (minEnergy.HasValue)
            candidates = candidates.Where(w => w.EnergyScore >= minEnergy.Value);

        if (maxEnergy.HasValue)
            candidates = candidates.Where(w => w.EnergyScore <= maxEnergy.Value);

        var result = new List<PhoneticWord>();
        var remaining = targetSyllables;

        while (remaining > 0 && candidates.Any())
        {
            var available = candidates.Where(w => w.Syllables <= remaining).ToList();
            if (!available.Any()) break;

            var chosen = available[_random.Next(available.Count)];
            result.Add(chosen);
            remaining -= chosen.Syllables;
            candidates = candidates.Where(w => w.Token != chosen.Token);
        }

        return result;
    }
}
