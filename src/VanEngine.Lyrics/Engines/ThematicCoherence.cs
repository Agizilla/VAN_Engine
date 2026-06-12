namespace VanEngine.Lyrics.Engines;

public class ThematicCoherence
{
    private string _currentTheme = string.Empty;
    private string _pendingRhyme = string.Empty;
    private readonly Dictionary<string, List<string>> _themeKeywords;

    public ThematicCoherence()
    {
        _themeKeywords = new Dictionary<string, List<string>>
        {
            ["chaos"] = new() { "break", "fall", "void", "shadow", "storm", "rage", "burn", "crash" },
            ["order"] = new() { "rise", "build", "light", "code", "truth", "forge", "stand", "crown" },
            ["flow"] = new() { "glide", "move", "ride", "wave", "tide", "stream", "float", "drift" },
            ["pain"] = new() { "hurt", "bleed", "cry", "scar", "loss", "dark", "cold", "alone" },
            ["hope"] = new() { "dream", "light", "rise", "dawn", "heal", "grow", "find", "home" }
        };
    }

    public void SetTheme(string theme) => _currentTheme = theme;

    public string GetThemeKeyword()
    {
        if (string.IsNullOrEmpty(_currentTheme) || !_themeKeywords.ContainsKey(_currentTheme))
            return string.Empty;
        var keywords = _themeKeywords[_currentTheme];
        return keywords[new Random().Next(keywords.Count)];
    }

    public void SetPendingRhyme(string rhymeFamily) => _pendingRhyme = rhymeFamily;

    public string GetPendingRhyme() => _pendingRhyme;

    public void AdvanceTheme(string lyricLine)
    {
        if (lyricLine.Contains("break") || lyricLine.Contains("fall") || lyricLine.Contains("void"))
            _currentTheme = "chaos";
        else if (lyricLine.Contains("rise") || lyricLine.Contains("build") || lyricLine.Contains("light"))
            _currentTheme = "order";
        else if (lyricLine.Contains("hurt") || lyricLine.Contains("bleed") || lyricLine.Contains("alone"))
            _currentTheme = "pain";
        else if (lyricLine.Contains("dream") || lyricLine.Contains("hope") || lyricLine.Contains("dawn"))
            _currentTheme = "hope";
    }
}
