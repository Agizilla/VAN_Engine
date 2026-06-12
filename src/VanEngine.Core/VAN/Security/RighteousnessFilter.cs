using VanEngine.Core.VAN.Audit;
using VanEngine.Core.VAN.Compiler;

namespace VanEngine.Core.VAN.Security;

public sealed class RighteousnessFilter
{
    private readonly HashSet<string> _forbiddenTerms;
    private readonly AuditLog? _audit;

    public RighteousnessFilter(AuditLog? audit = null)
    {
        _audit = audit;
        _forbiddenTerms = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "upload", "phone home", "analytics", "telemetry",
            "exfiltrate", "call home", "beacon", "ping", "track",
            "surveillance", "callback", "cloud", "spy", "snoop"
        };
    }

    public RighteousnessFilter(string[] extraTerms, AuditLog? audit = null)
    {
        _audit = audit;
        _forbiddenTerms = new HashSet<string>(extraTerms, StringComparer.OrdinalIgnoreCase);
    }

    public bool IsRighteous(AstEnvelope envelope)
    {
        foreach (var item in envelope.Data)
        {
            var str = item?.ToString();
            if (str != null && _forbiddenTerms.Contains(str))
            {
                _audit?.Record("Righteousness",
                    $"Blocked envelope with forbidden term '{str}' in DATA " +
                    $"(Carrier={envelope.Carrier}, Line={envelope.LineNumber})",
                    AuditSeverity.Critical);
                return false;
            }
        }

        if (_forbiddenTerms.Contains(envelope.Carrier))
        {
            _audit?.Record("Righteousness",
                $"Blocked envelope with forbidden CARRIER '{envelope.Carrier}'",
                AuditSeverity.Critical);
            return false;
        }

        if (_forbiddenTerms.Contains(envelope.Modulation))
        {
            _audit?.Record("Righteousness",
                $"Blocked envelope with forbidden MODULATION '{envelope.Modulation}'",
                AuditSeverity.Critical);
            return false;
        }

        return true;
    }

    public bool IsRighteous(VanEnvelope envelope)
    {
        foreach (var item in envelope.Data)
        {
            var str = item?.ToString();
            if (str != null && _forbiddenTerms.Contains(str))
            {
                _audit?.Record("Righteousness",
                    $"Blocked envelope with forbidden term '{str}' in DATA " +
                    $"(Carrier={envelope.Carrier})",
                    AuditSeverity.Critical);
                return false;
            }
        }

        return true;
    }

    public void AddTerm(string term)
    {
        _forbiddenTerms.Add(term);
    }

    public bool RemoveTerm(string term) => _forbiddenTerms.Remove(term);

    public IReadOnlyCollection<string> Terms => _forbiddenTerms;
}
