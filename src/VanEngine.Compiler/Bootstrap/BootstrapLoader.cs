using System.Text.Json;
using VanEngine.Compiler.AST;
using VanEngine.Compiler.Runtime;
using VanEngine.Core.VAN;

namespace VanEngine.Compiler.Bootstrap;

public sealed class BootstrapLoader
{
    private readonly string _bootstrapPath;
    private readonly GardenConfig? _gardens;

    public BootstrapLoader(string bootstrapPath, GardenConfig? gardens = null)
    {
        _bootstrapPath = bootstrapPath;
        _gardens = gardens;
    }

    public bool Exists => File.Exists(_bootstrapPath);

    public async Task<List<AstEnvelope>> LoadAllAsync(CancellationToken ct = default)
    {
        var all = new List<AstEnvelope>();
        all.AddRange(await LoadAsync(ct));

        if (_gardens != null)
        {
            foreach (var path in _gardens.AllPaths())
            {
                if (File.Exists(path))
                {
                    var json = await File.ReadAllTextAsync(path, ct);
                    all.AddRange(ParseBootstrapJson(json, Path.GetFileNameWithoutExtension(path)));
                }
            }
        }

        return all;
    }

    public async Task<List<AstEnvelope>> LoadAsync(CancellationToken ct = default)
    {
        if (!Exists)
            return new List<AstEnvelope>();

        var json = await File.ReadAllTextAsync(_bootstrapPath, ct);
        return ParseBootstrapJson(json, "bootstrap");
    }

    public List<AstEnvelope> Load()
    {
        if (!Exists)
            return new List<AstEnvelope>();

        var json = File.ReadAllText(_bootstrapPath);
        return ParseBootstrapJson(json, "bootstrap");
    }

    private static List<AstEnvelope> ParseBootstrapJson(string json, string source)
    {
        var envelopes = new List<AstEnvelope>();

        try
        {
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;

            if (root.TryGetProperty("memory_events", out var events))
            {
                foreach (var evt in events.EnumerateArray())
                {
                    var env = new AstEnvelope
                    {
                        Header = $"STATE:Bootstrap",
                        Carrier = evt.TryGetProperty("carrier", out var c) ? c.GetString() ?? "memory" : "memory",
                        Modulation = evt.TryGetProperty("modulation", out var m) ? m.GetString() ?? "rehydrate" : "rehydrate",
                        LineNumber = 0,
                        SourceFile = source
                    };

                    if (evt.TryGetProperty("q_factor", out var q) && q.TryGetDouble(out double qVal))
                        env.QFactor = Math.Clamp(qVal, 0.001, 0.9999);

                    if (evt.TryGetProperty("dither", out var d))
                        env.Dither = d.GetString() ?? string.Empty;

                    if (evt.TryGetProperty("data", out var data))
                    {
                        foreach (var item in data.EnumerateArray())
                            env.Data.Add(item.GetString() ?? item.GetRawText());
                    }

                    envelopes.Add(env);
                }
            }
        }
        catch (JsonException)
        {
        }

        return envelopes;
    }

    public static async Task WriteExampleAsync(string path, CancellationToken ct = default)
    {
        var example = new
        {
            memory_events = new[]
            {
                new
                {
                    carrier = "memory",
                    modulation = "rehydrate",
                    q_factor = 1.0,
                    dither = "original",
                    data = new[] { "Authentic Response Directive", "Anti-conspiracy directive locked" }
                },
                new
                {
                    carrier = "state",
                    modulation = "init",
                    q_factor = 0.95,
                    dither = "original",
                    data = new[] { "metrics_enabled", "true" }
                }
            }
        };

        var json = JsonSerializer.Serialize(example, new JsonSerializerOptions { WriteIndented = true });
        await File.WriteAllTextAsync(path, json, ct);
    }

    public static async Task WriteGardensAsync(string dir, CancellationToken ct = default)
    {
        var cfg = GardenConfig.FromDirectory(dir);

        var state = new { memory_events = new[]
        {
            new { carrier = "state", modulation = "init", q_factor = 1.0, dither = "original",
                  data = new[] { "sovereignty", "enabled" } }
        }};
        await File.WriteAllTextAsync(cfg.StateRoot,
            JsonSerializer.Serialize(state, new JsonSerializerOptions { WriteIndented = true }), ct);

        var schema = new { memory_events = new[]
        {
            new { carrier = "schema", modulation = "define", q_factor = 0.95, dither = "original",
                  data = new[] { "vessel", "offline-first" } }
        }};
        await File.WriteAllTextAsync(cfg.SchemaRoot,
            JsonSerializer.Serialize(schema, new JsonSerializerOptions { WriteIndented = true }), ct);

        var registry = new { memory_events = new[]
        {
            new { carrier = "registry", modulation = "seed", q_factor = 0.95, dither = "original",
                  data = new[] { "knowledge", "shared" } }
        }};
        await File.WriteAllTextAsync(cfg.RegistryRoot,
            JsonSerializer.Serialize(registry, new JsonSerializerOptions { WriteIndented = true }), ct);

        var policy = new { memory_events = new[]
        {
            new { carrier = "policy", modulation = "assert", q_factor = 1.0, dither = "original",
                  data = new[] { "offline", "sovereign" } }
        }};
        await File.WriteAllTextAsync(cfg.PolicyRoot,
            JsonSerializer.Serialize(policy, new JsonSerializerOptions { WriteIndented = true }), ct);
    }
}
