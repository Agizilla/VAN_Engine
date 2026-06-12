using VanEngine.Lyrics.Models;

namespace VanEngine.Lyrics.Lexicon;

public class PhoneticAnalyzer
{
    private readonly HashSet<char> _plosives = new() { 'p', 't', 'k', 'b', 'd', 'g' };
    private readonly HashSet<char> _fricatives = new() { 'f', 'v', 's', 'z', 'h', 'c' };
    private readonly HashSet<char> _vowels = new() { 'a', 'e', 'i', 'o', 'u', 'y' };

    public PhoneticWord Analyze(string word, string archetype = "Generic")
    {
        var lowerWord = word.ToLower();

        var syllables = CountSyllables(lowerWord);
        var stressPattern = GenerateStressPattern(syllables);
        var plosiveCount = lowerWord.Count(c => _plosives.Contains(c));
        var fricativeCount = lowerWord.Count(c => _fricatives.Contains(c));
        var energyScore = CalculateEnergy(lowerWord, plosiveCount, syllables);
        var rhymeFamily = GetRhymeFamily(lowerWord);
        var vowelCore = GetVowelCore(lowerWord);

        return new PhoneticWord
        {
            Token = word,
            Syllables = syllables,
            StressPattern = stressPattern,
            PlosiveCount = plosiveCount,
            FricativeCount = fricativeCount,
            EnergyScore = energyScore,
            Archetype = archetype,
            RhymeFamily = rhymeFamily,
            VowelCore = vowelCore,
            IsFunctionWord = IsFunctionWord(lowerWord),
            Pos = IsFunctionWord(lowerWord) ? "FUNC" : "CONTENT"
        };
    }

    private int CountSyllables(string word)
    {
        var count = 0;
        var wasVowel = false;

        foreach (var c in word)
        {
            var isVowel = _vowels.Contains(c);
            if (isVowel && !wasVowel) count++;
            wasVowel = isVowel;
        }

        if (word.EndsWith("e") && count > 1) count--;
        return Math.Max(1, count);
    }

    private static string GenerateStressPattern(int syllables)
    {
        if (syllables == 1) return "1";
        if (syllables == 2) return "10";
        return "1" + new string('0', syllables - 1);
    }

    private static double CalculateEnergy(string word, int plosives, int syllables)
    {
        var energy = 0.3;
        energy += plosives * 0.08;
        if (syllables == 1) energy += 0.1;
        if (word.Length > 6) energy += 0.05;

        var harshSounds = new[] { "x", "z", "k", "c", "q" };
        energy += harshSounds.Count(word.Contains) * 0.03;

        return Math.Min(1.0, energy);
    }

    private static string GetRhymeFamily(string word)
    {
        var match = System.Text.RegularExpressions.Regex.Match(word, @"[aeiouy][^aeiouy]*$");
        return match.Success ? match.Value : word.Length > 2 ? word.Substring(word.Length - 2) : word;
    }

    private static string GetVowelCore(string word)
    {
        var vowels = word.Where(c => "aeiouy".Contains(c)).ToList();
        return vowels.Any() ? string.Join("-", vowels.Take(3)).ToUpper() : "A";
    }

    private static bool IsFunctionWord(string word)
    {
        var functionWords = new HashSet<string>
        {
            "the", "and", "of", "to", "a", "in", "that", "is", "it", "for",
            "on", "with", "as", "by", "at", "from", "or", "an", "be", "are",
            "was", "were", "have", "has", "had", "not", "but", "so", "if", "then"
        };
        return functionWords.Contains(word);
    }
}
