using System.Reflection;
using System.Runtime.CompilerServices;

namespace VanEngine.Core.VAN;

[AttributeUsage(AttributeTargets.Assembly)]
public sealed class OfflineOnlyAttribute : Attribute
{
    public string Reason { get; }
    public OfflineOnlyAttribute(string reason) => Reason = reason;
}

public static class TelemetryGuard
{
    private static readonly HashSet<string> BlockedTypes = new(StringComparer.Ordinal)
    {
        "System.Net.Http.HttpClient",
        "System.Net.Dns",
        "System.Net.WebRequest",
        "System.Net.HttpWebRequest",
        "System.Net.WebClient",
        "System.Net.Sockets.TcpClient",
        "System.Net.Sockets.UdpClient"
    };

    private static bool _initialized;
    private static readonly List<string> _warnings = new();

    public static IReadOnlyList<string> Warnings => _warnings.AsReadOnly();
    public static bool HasViolations => _warnings.Count > 0;

    public static void ScanAssembly(Assembly assembly)
    {
        if (_initialized) return;
        _initialized = true;

        foreach (var type in assembly.GetTypes())
        {
            string fullName = type.FullName ?? string.Empty;
            if (BlockedTypes.Contains(fullName))
            {
                var msg = $"Offline violation: {fullName} referenced by {assembly.GetName().Name}";
                _warnings.Add(msg);
            }
        }
    }

    public static void ScanAllLoadedAssemblies()
    {
        foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            ScanAssembly(asm);
    }

    public static void AssertOffline()
    {
        if (HasViolations)
        {
            string msg = $"Offline telemetry violations detected:\n{string.Join("\n", Warnings)}";
            throw new PlatformNotSupportedException(msg);
        }
    }
}
