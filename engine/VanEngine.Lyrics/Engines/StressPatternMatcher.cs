using VanEngine.Lyrics.Models;

namespace VanEngine.Lyrics.Engines;

public class StressPatternMatcher
{
    public List<PhoneticWord> FilterByStressPattern(
        List<PhoneticWord> words,
        string targetPattern)
    {
        return words.Where(w => w.StressPattern == targetPattern).ToList();
    }

    public string SuggestStressPattern(int syllables)
    {
        if (syllables == 1) return "1";
        if (syllables == 2) return new Random().Next(2) == 0 ? "10" : "01";
        if (syllables == 3) return "100";
        return "10" + new string('0', syllables - 2);
    }
}
