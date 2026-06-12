namespace VanEngine.Core.VAN;

public static class FryasAlphabet
{
    public static IReadOnlyDictionary<char, JuulMask> Map => _map;
    private static readonly Dictionary<char, JuulMask> _map = new()
    {
        // ── Vowels (7) ──────────────────────────────────────────
        { 'I', JuulMask.Spoke0 },
        { '—', JuulMask.Spoke180 },
        { 'O', JuulMask.OuterRim },
        { 'Λ', JuulMask.Spoke0 | JuulMask.Spoke60 },
        { 'V', JuulMask.Spoke120 | JuulMask.Spoke180 },
        { '/', JuulMask.Spoke60 },
        { '\\', JuulMask.Spoke300 },

        // ── Core Consonants (16) ────────────────────────────────
        { 'M', JuulMask.Spoke0 | JuulMask.Spoke180 },
        { 'N', JuulMask.Spoke60 | JuulMask.Spoke240 },
        { 'T', JuulMask.Spoke0 | JuulMask.Spoke60 | JuulMask.Spoke120 },
        { 'K', JuulMask.Spoke180 | JuulMask.Spoke240 | JuulMask.Spoke300 },
        { 'F', JuulMask.Spoke0 | JuulMask.Spoke180 | JuulMask.OuterRim },
        { 'S', JuulMask.Spoke0 | JuulMask.Spoke60 | JuulMask.Spoke120 | JuulMask.Spoke180 | JuulMask.Spoke240 | JuulMask.Spoke300 },
        { 'R', JuulMask.Spoke60 | JuulMask.Spoke180 | JuulMask.Spoke300 },
        { 'H', JuulMask.Spoke240 | JuulMask.Spoke300 | JuulMask.Spoke0 },

        // Remaining 8 consonants — awaiting Captain's Oera Linda chart
        { 'B', JuulMask.Spoke0 | JuulMask.Spoke60 | JuulMask.OuterRim },
        { 'D', JuulMask.Spoke60 | JuulMask.Spoke180 | JuulMask.OuterRim },
        { 'G', JuulMask.Spoke120 | JuulMask.Spoke240 | JuulMask.Spoke300 },
        { 'L', JuulMask.Spoke0 | JuulMask.Spoke300 },
        { 'P', JuulMask.Spoke0 | JuulMask.Spoke60 | JuulMask.Spoke180 },
        { 'W', JuulMask.Spoke60 | JuulMask.Spoke120 | JuulMask.Spoke240 },
        { 'J', JuulMask.Spoke120 | JuulMask.Spoke300 },
        { 'Z', JuulMask.Spoke0 | JuulMask.Spoke240 | JuulMask.Spoke300 | JuulMask.OuterRim },

        // ── Numerals (5) — all include OuterRim to distinguish from vowels ──
        { '0', JuulMask.OuterRim | JuulMask.Spoke0 | JuulMask.Spoke120 },
        { '1', JuulMask.OuterRim | JuulMask.Spoke60 | JuulMask.Spoke300 },
        { '2', JuulMask.OuterRim | JuulMask.Spoke0 | JuulMask.Spoke240 },
        { '3', JuulMask.OuterRim | JuulMask.Spoke120 | JuulMask.Spoke300 },
        { '4', JuulMask.OuterRim | JuulMask.Spoke60 | JuulMask.Spoke180 | JuulMask.Spoke240 },

        // ── Extended marks (6) — awaiting Captain's chart ──
        { 'Þ', JuulMask.Spoke0 | JuulMask.Spoke60 | JuulMask.Spoke240 },
        { 'Ð', JuulMask.Spoke60 | JuulMask.Spoke180 | JuulMask.Spoke240 },
        { 'Æ', JuulMask.Spoke0 | JuulMask.Spoke120 | JuulMask.Spoke180 },
        { 'Œ', JuulMask.Spoke60 | JuulMask.Spoke120 | JuulMask.Spoke240 | JuulMask.OuterRim },
        { '×', JuulMask.Spoke0 | JuulMask.Spoke120 | JuulMask.Spoke240 },
        { '†', JuulMask.Spoke60 | JuulMask.Spoke180 | JuulMask.Spoke300 | JuulMask.OuterRim },

        // Total: 7 + 16 + 5 + 6 = 34
    };

    public static JuulMask GetMask(char character)
    {
        if (_map.TryGetValue(character, out var mask))
            return mask;
        throw new ArgumentOutOfRangeException(nameof(character), $"Character '{character}' is not in the Fryas alphabet.");
    }

    public static char? GetCharacter(JuulMask mask)
    {
        foreach (var kv in _map)
            if (kv.Value == mask)
                return kv.Key;
        return null;
    }
}
