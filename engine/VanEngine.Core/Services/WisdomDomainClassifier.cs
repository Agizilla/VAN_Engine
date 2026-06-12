using System.Text.RegularExpressions;

namespace VanEngine.Core.Services;

public class WisdomDomainClassifier
{
    private readonly List<DomainKeyword> _domains;
    private readonly string _wisdomDirectory;

    public WisdomDomainClassifier(string baseDirectory)
    {
        _wisdomDirectory = Path.Combine(baseDirectory, "MEMORY", "WISDOM", "FRAMES");
        _domains = InitializeDomains();
    }

    private static List<DomainKeyword> InitializeDomains()
    {
        return new List<DomainKeyword>
        {
            new() { Domain = "communication", Primary = new[] { @"response|format|output|verbose|concise|summary|explain", @"tone|voice|style|wording|phrasing", @"greeting|rating|feedback" }, Secondary = new[] { @"short|long|brief|detail", @"say|tell|write|read" } },
            new() { Domain = "development", Primary = new[] { @"code|function|class|module|import|export", @"bug|fix|refactor|implement|build|create|add", @"typescript|javascript|python|bun|csharp|dotnet", @"test|lint|type.?check|compile", @"hook|skill|tool|agent|algorithm" }, Secondary = new[] { @"file|path|directory|folder", @"error|crash|broken|issue" } },
            new() { Domain = "deployment", Primary = new[] { @"deploy|push|ship|release|publish", @"cloudflare|worker|pages|wrangler|vercel|azure|aws", @"production|staging|live|remote", @"git\s+push|git\s+remote" }, Secondary = new[] { @"build|compile|bundle", @"url|domain|dns|ssl" } },
            new() { Domain = "content-creation", Primary = new[] { @"blog|post|article|newsletter|write", @"draft|edit|proofread|publish", @"social|tweet|linkedin", @"video|podcast|youtube" }, Secondary = new[] { @"header|image|thumbnail", @"audience|reader|subscriber" } },
            new() { Domain = "system-architecture", Primary = new[] { @"architecture|design|system|infrastructure", @"memory|state|hook|skill|algorithm", @"pai|framework|platform" }, Secondary = new[] { @"pattern|structure|flow|pipeline", @"integration|component|module" } },
            new() { Domain = "security", Primary = new[] { @"security|vulnerability|exploit|cve", @"auth|authentication|authorization|oauth", @"encryption|crypto|tls|ssl", @"scan|audit|penetration" }, Secondary = new[] { @"secret|key|token|credential", @"firewall|waf|ids|ips" } }
        };
    }

    public List<ClassificationResult> Classify(string text)
    {
        var results = new List<ClassificationResult>();
        var textLower = text.ToLower();

        foreach (var domain in _domains)
        {
            int score = 0, primaryHits = 0, secondaryHits = 0;

            foreach (var pattern in domain.Primary)
            {
                var matches = Regex.Matches(textLower, pattern, RegexOptions.IgnoreCase);
                if (matches.Count > 0) { primaryHits += matches.Count; score += matches.Count * 2; }
            }

            foreach (var pattern in domain.Secondary)
            {
                var matches = Regex.Matches(textLower, pattern, RegexOptions.IgnoreCase);
                if (matches.Count > 0) { secondaryHits += matches.Count; score += matches.Count; }
            }

            if (primaryHits >= 1 || secondaryHits >= 2)
            {
                var framePath = Path.Combine(_wisdomDirectory, $"{domain.Domain}.md");
                results.Add(new ClassificationResult
                {
                    Domain = domain.Domain,
                    Path = File.Exists(framePath) ? framePath : null,
                    Relevance = Math.Min(score / 10.0, 1.0),
                    PrimaryHits = primaryHits,
                    SecondaryHits = secondaryHits
                });
            }
        }

        return results.OrderByDescending(r => r.Relevance).ToList();
    }

    public async Task<List<(string Domain, string Content)>> LoadRelevantFramesAsync(string text, int maxFrames = 3)
    {
        var classified = Classify(text);
        var result = new List<(string, string)>();
        foreach (var c in classified.Take(maxFrames))
        {
            if (!string.IsNullOrEmpty(c.Path) && File.Exists(c.Path))
                result.Add((c.Domain, await File.ReadAllTextAsync(c.Path)));
        }
        return result;
    }

    public List<string> ListFrames()
    {
        if (!Directory.Exists(_wisdomDirectory)) return new List<string>();
        return Directory.GetFiles(_wisdomDirectory, "*.md")
            .Select(f => Path.GetFileNameWithoutExtension(f) ?? "")
            .Where(f => !string.IsNullOrEmpty(f)).ToList();
    }
}

public class DomainKeyword
{
    public string Domain { get; set; } = "";
    public string[] Primary { get; set; } = Array.Empty<string>();
    public string[] Secondary { get; set; } = Array.Empty<string>();
}

public class ClassificationResult
{
    public string Domain { get; set; } = "";
    public string? Path { get; set; }
    public double Relevance { get; set; }
    public int PrimaryHits { get; set; }
    public int SecondaryHits { get; set; }
}
