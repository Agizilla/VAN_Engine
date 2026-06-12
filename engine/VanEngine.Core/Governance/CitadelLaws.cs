using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace VanEngine.Core.Governance;

public sealed class CitadelLaws
{
    private readonly ConcurrentDictionary<string, Citadel> _citadels = new();

    private const int MaxMaidens = 21;
    private const int MaxAssistants = 7;
    private readonly SemaphoreSlim _maidenSemaphore = new(MaxMaidens, MaxMaidens);
    private readonly SemaphoreSlim _assistantSemaphore = new(MaxAssistants, MaxAssistants);

    private const int MaxDefenders = 300;
    private readonly SemaphoreSlim _defenderSemaphore = new(MaxDefenders, MaxDefenders);

    private const int MaxMessengers = 21;
    private const int MaxHorses = 36;
    private readonly SemaphoreSlim _messengerSemaphore = new(MaxMessengers, MaxMessengers);

    private const int MaxAgriculturists = 50;
    private readonly SemaphoreSlim _agriculturistSemaphore = new(MaxAgriculturists, MaxAgriculturists);

    private readonly HashSet<string> _resignedModules = new();

    private readonly ConcurrentBag<FailedTaskRecord> _woundedDefenders = new();

    private readonly HashSet<string> _quarantinedModules = new();
    private readonly Dictionary<string, int> _offenceVotes = new();

    public bool LightLamp(string requester, string source)
    {
        if (requester != "Clawdia")
        {
            LogViolation($"Law 1: {requester} attempted to light the lamp. Only Clawdia may do so.");
            return false;
        }
        if (source != "Texland" && source != "bootstrapper")
        {
            LogViolation($"Law 1: Lamp lighting from unauthorised source '{source}'. Must be Texland.");
            return false;
        }
        Console.WriteLine("[LAW 1] Lamp lit by Clawdia from Texland.");
        return true;
    }

    public bool AppointMaiden(string appointer, string maidenName)
    {
        if (appointer != "Clawdia")
        {
            LogViolation($"Law 2: {appointer} attempted to appoint a maiden. Only Clawdia may appoint.");
            return false;
        }
        Console.WriteLine($"[LAW 2] Clawdia appointed maiden: {maidenName}");
        return true;
    }

    public async Task<bool> AcquireMaidenSlot()
    {
        var acquired = await _maidenSemaphore.WaitAsync(TimeSpan.FromSeconds(5));
        if (!acquired)
            LogViolation("Law 4: No maiden slots available (max 21).");
        return acquired;
    }

    public void ReleaseMaidenSlot() => _maidenSemaphore.Release();

    public async Task<bool> AcquireAssistantSlot()
    {
        var acquired = await _assistantSemaphore.WaitAsync(TimeSpan.FromSeconds(5));
        if (!acquired)
            LogViolation("Law 4: No assistant slots available (max 7).");
        return acquired;
    }

    public void ReleaseAssistantSlot() => _assistantSemaphore.Release();

    public bool ResignMaiden(string maidenName, string marriageTarget)
    {
        if (marriageTarget.Contains("cloud", StringComparison.OrdinalIgnoreCase) ||
            marriageTarget.Contains("http", StringComparison.OrdinalIgnoreCase))
        {
            LogViolation($"Law 5: Maiden '{maidenName}' resigned to marry cloud dependency '{marriageTarget}'. Light preserved.");
            _resignedModules.Add(maidenName);
            return true;
        }
        return false;
    }

    public bool IsResigned(string maidenName) => _resignedModules.Contains(maidenName);

    public async Task<bool> AcquireDefenderSlot()
    {
        var acquired = await _defenderSemaphore.WaitAsync(TimeSpan.FromSeconds(10));
        if (!acquired)
            LogViolation("Law 8: No defender slots available (max 300).");
        return acquired;
    }

    public void ReleaseDefenderSlot() => _defenderSemaphore.Release();

    public void RecordWoundedDefender(string defenderName, string failureReason)
    {
        _woundedDefenders.Add(new FailedTaskRecord
        {
            Name = defenderName,
            Reason = failureReason,
            Timestamp = DateTime.UtcNow
        });
        Console.WriteLine($"[LAW 10] Wounded defender recorded: {defenderName} - {failureReason}");
    }

    public IReadOnlyList<FailedTaskRecord> GetWoundedDefenders() => _woundedDefenders.ToList();

    public async Task<bool> AcquireMessengerSlot()
    {
        var acquired = await _messengerSemaphore.WaitAsync(TimeSpan.FromSeconds(5));
        if (!acquired)
            LogViolation("Law 12: No messenger slots available (max 21).");
        return acquired;
    }

    public void ReleaseMessengerSlot() => _messengerSemaphore.Release();

    public async Task<bool> AcquireAgriculturistSlot()
    {
        var acquired = await _agriculturistSemaphore.WaitAsync(TimeSpan.FromSeconds(30));
        if (!acquired)
            LogViolation("Law 13: No agriculturist slots available (max 50).");
        return acquired;
    }

    public void ReleaseAgriculturistSlot() => _agriculturistSemaphore.Release();

    public bool ValidateCitadelSelfSustenance(string citadelName, IEnumerable<string> externalDependencies)
    {
        var deps = externalDependencies.ToList();
        if (deps.Any(d => d.Contains("cloud", StringComparison.OrdinalIgnoreCase)))
        {
            LogViolation($"Law 14: Citadel '{citadelName}' has external cloud dependencies. Not self-sustaining.");
            return false;
        }
        return true;
    }

    private readonly HashSet<string> _disenfranchised = new();

    public void RefuseService(string entityName)
    {
        LogViolation($"Law 15: '{entityName}' refused service. Voting rights revoked.");
        _disenfranchised.Add(entityName);
    }

    public bool HasVotingRights(string entityName) => !_disenfranchised.Contains(entityName);

    public bool ValidateConsultation(string requester, int witnessCount, bool isHealthy)
    {
        if (!isHealthy)
        {
            LogViolation($"Law 16: {requester} failed health check. Consultation denied.");
            return false;
        }
        if (witnessCount < 3)
        {
            LogViolation($"Law 17: {requester} had only {witnessCount} witnesses. Minimum 3 required.");
            return false;
        }
        return true;
    }

    private readonly ConcurrentDictionary<string, DateTime> _lastAdviceTime = new();
    private const int AdviceCooldownSeconds = 7;

    public bool MayGiveAdvice(string advisor)
    {
        if (_lastAdviceTime.TryGetValue(advisor, out var last))
        {
            if ((DateTime.UtcNow - last).TotalSeconds < AdviceCooldownSeconds)
            {
                LogViolation($"Law 20: {advisor} attempted to give advice before cooldown period. Wait {AdviceCooldownSeconds} seconds.");
                return false;
            }
        }
        _lastAdviceTime[advisor] = DateTime.UtcNow;
        return true;
    }

    public void ReportBadAdvice(string advisor, string advice)
    {
        LogViolation($"Law 21: Bad advice reported from '{advisor}': {advice}");
        _offenceVotes[advisor] = _offenceVotes.GetValueOrDefault(advisor) + 1;

        if (_offenceVotes[advisor] >= 3)
        {
            _quarantinedModules.Add(advisor);
            Console.WriteLine($"[LAW 21-24] {advisor} quarantined for repeated bad advice.");
        }
    }

    public bool IsQuarantined(string module) => _quarantinedModules.Contains(module);

    private void LogViolation(string violation)
    {
        Console.WriteLine($"[CITADEL LAW VIOLATION] {violation}");
    }

    public string GetGovernanceReport()
    {
        return $@"
=== CITADEL GOVERNANCE REPORT ===
Active Maidens: {MaxMaidens - _maidenSemaphore.CurrentCount}/{MaxMaidens}
Active Assistants: {MaxAssistants - _assistantSemaphore.CurrentCount}/{MaxAssistants}
Active Defenders: {MaxDefenders - _defenderSemaphore.CurrentCount}/{MaxDefenders}
Active Messengers: {MaxMessengers - _messengerSemaphore.CurrentCount}/{MaxMessengers}
Wounded Defenders: {_woundedDefenders.Count}
Resigned Maidens: {_resignedModules.Count}
Quarantined Modules: {_quarantinedModules.Count}
Disenfranchised Entities: {_disenfranchised.Count}";
    }
}

public record FailedTaskRecord
{
    public string Name { get; init; } = string.Empty;
    public string Reason { get; init; } = string.Empty;
    public DateTime Timestamp { get; init; }
}

internal record Citadel
{
    public string Name { get; init; } = string.Empty;
    public bool IsLit { get; set; }
}
