using System.Reflection;
using System.Runtime.Loader;
using VanEngine.Game.Core;
using VanEngine.Game.Forensics;

namespace VanEngine.Game.Infrastructure;

public interface IMod
{
    string Name { get; }
    string Version { get; }
    void OnLoad(SovereignState state);
    void OnYearTick(int year);
    void OnFileAnalyzed(string filePath, AnalysisResult result);
    void OnModifyResources(ref ResourcePack resources);
    void OnSovereigntyChange(ref double delta, string reason);
    void OnDispose();
}

public sealed class ModInfo
{
    public string Name { get; set; } = "Unknown";
    public string Version { get; set; } = "0.0.0";
    public string FilePath { get; set; } = string.Empty;
    public bool IsLoaded { get; set; }
    public string? Error { get; set; }
}

public sealed class ModLoader : IDisposable
{
    private readonly SovereignState _state;
    private readonly string _modsDirectory;
    private readonly List<IMod> _loadedMods = new();
    private readonly List<ModInfo> _modInfos = new();
    private readonly List<AssemblyLoadContext> _loadContexts = new();

    public IReadOnlyList<ModInfo> ModInfos => _modInfos;
    public int LoadedCount => _loadedMods.Count;

    public ModLoader(SovereignState state)
    {
        _state = state;
        _modsDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "mods");
        Directory.CreateDirectory(_modsDirectory);
    }

    public void LoadAllMods()
    {
        Directory.CreateDirectory(_modsDirectory);

        var dllFiles = Directory.GetFiles(_modsDirectory, "*.dll");
        foreach (var dll in dllFiles)
            LoadMod(dll);

        _state.AddLog($"ModLoader: loaded {_loadedMods.Count} mod(s) from {_modsDirectory}");
    }

    public void LoadMod(string dllPath)
    {
        var modInfo = new ModInfo { FilePath = dllPath };

        try
        {
            var context = new AssemblyLoadContext(Path.GetFileNameWithoutExtension(dllPath), isCollectible: true);
            _loadContexts.Add(context);

            var assembly = context.LoadFromAssemblyPath(dllPath);
            var modTypes = assembly.GetExportedTypes()
                .Where(t => typeof(IMod).IsAssignableFrom(t) && !t.IsAbstract && !t.IsInterface)
                .ToList();

            if (modTypes.Count == 0)
            {
                modInfo.Error = "No IMod implementation found";
                modInfo.IsLoaded = false;
                _modInfos.Add(modInfo);
                return;
            }

            foreach (var type in modTypes)
            {
                var mod = (IMod)Activator.CreateInstance(type)!;
                mod.OnLoad(_state);
                _loadedMods.Add(mod);

                modInfo.Name = mod.Name;
                modInfo.Version = mod.Version;
                modInfo.IsLoaded = true;

                _state.AddLog($"Mod loaded: {mod.Name} v{mod.Version}");
            }

            _modInfos.Add(modInfo);
        }
        catch (Exception ex)
        {
            modInfo.Error = ex.Message;
            modInfo.IsLoaded = false;
            _modInfos.Add(modInfo);
            _state.AddLog($"Mod load failed: {Path.GetFileName(dllPath)} - {ex.Message}");
        }
    }

    public void NotifyYearTick(int year)
    {
        foreach (var mod in _loadedMods)
        {
            try { mod.OnYearTick(year); }
            catch { }
        }
    }

    public void NotifyFileAnalyzed(string filePath, AnalysisResult result)
    {
        foreach (var mod in _loadedMods)
        {
            try { mod.OnFileAnalyzed(filePath, result); }
            catch { }
        }
    }

    public ResourcePack ApplyModifiers(ResourcePack resources)
    {
        var modified = resources;
        foreach (var mod in _loadedMods)
        {
            try { mod.OnModifyResources(ref modified); }
            catch { }
        }
        return modified;
    }

    public double ApplySovereigntyModifiers(double delta, string reason)
    {
        double modified = delta;
        foreach (var mod in _loadedMods)
        {
            try { mod.OnSovereigntyChange(ref modified, reason); }
            catch { }
        }
        return modified;
    }

    public void Dispose()
    {
        foreach (var mod in _loadedMods)
        {
            try { mod.OnDispose(); }
            catch { }
        }
        _loadedMods.Clear();

        foreach (var ctx in _loadContexts)
        {
            try { ctx.Unload(); }
            catch { }
        }
        _loadContexts.Clear();
    }

    public string GetStatusLine()
    {
        int ok = _modInfos.Count(m => m.IsLoaded);
        int fail = _modInfos.Count(m => !m.IsLoaded);
        return ok > 0 || fail > 0 ? $"MODS: {ok} ok, {fail} fail" : "MODS: none";
    }
}
