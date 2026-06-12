using VanEngine.Core.VAN.Compiler;
using VanEngine.Core.VAN.Compiler.Parser;

namespace VanEngine.Core.VAN.Memory;

public sealed class VanMemoryScanner
{
    private readonly string _rootPath;
    private readonly HashSet<string> _extensions;

    public VanMemoryScanner(string rootPath)
    {
        _rootPath = rootPath;
        _extensions = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { ".van" };
    }

    public VanMemoryScanner(string rootPath, string[] extensions)
    {
        _rootPath = rootPath;
        _extensions = new HashSet<string>(extensions, StringComparer.OrdinalIgnoreCase);
    }

    public List<IndexedVanFile> Scan()
    {
        var results = new List<IndexedVanFile>();

        if (!Directory.Exists(_rootPath))
            return results;

        var files = Directory.GetFiles(_rootPath, "*.*", SearchOption.AllDirectories)
            .Where(f => _extensions.Contains(Path.GetExtension(f)))
            .ToArray();

        foreach (var file in files)
        {
            try
            {
                var text = File.ReadAllText(file);
                var parser = new VanParser(text.AsSpan());
                var envelopes = parser.Parse();

                var tags = new HashSet<string>();
                var carriers = new HashSet<string>();
                string firstHeader = string.Empty;

                foreach (var env in envelopes)
                {
                    if (!string.IsNullOrEmpty(env.Carrier))
                    {
                        carriers.Add(env.Carrier);
                        tags.Add(env.Carrier.ToLowerInvariant());
                    }
                    if (!string.IsNullOrEmpty(env.Modulation))
                        tags.Add(env.Modulation.ToLowerInvariant());
                    if (string.IsNullOrEmpty(firstHeader) && !string.IsNullOrEmpty(env.Header))
                        firstHeader = env.Header;
                }

                var contentHash = Convert.ToHexString(
                    System.Security.Cryptography.SHA256.HashData(
                        System.Text.Encoding.UTF8.GetBytes(text)
                    )
                ).ToLowerInvariant()[..12];

                var indexed = new IndexedVanFile
                {
                    Path = file,
                    Hash = contentHash,
                    FirstHeader = firstHeader,
                    Tags = tags.ToArray(),
                    Carriers = carriers.ToArray(),
                    EnvelopeCount = envelopes.Count,
                    FileSize = new FileInfo(file).Length,
                    LastModified = File.GetLastWriteTimeUtc(file),
                    LastIndexed = DateTime.UtcNow
                };

                results.Add(indexed);
            }
            catch
            {
            }
        }

        return results;
    }

    public async Task<List<IndexedVanFile>> ScanAsync(CancellationToken ct = default)
    {
        return await Task.Run(() => Scan(), ct);
    }
}

public sealed class IndexedVanFile
{
    public string Path { get; set; } = string.Empty;
    public string Hash { get; set; } = string.Empty;
    public string FirstHeader { get; set; } = string.Empty;
    public string[] Tags { get; set; } = Array.Empty<string>();
    public string[] Carriers { get; set; } = Array.Empty<string>();
    public int EnvelopeCount { get; set; }
    public long FileSize { get; set; }
    public DateTime LastModified { get; set; }
    public DateTime LastIndexed { get; set; }

    public bool IsModified => LastModified > LastIndexed;
}
