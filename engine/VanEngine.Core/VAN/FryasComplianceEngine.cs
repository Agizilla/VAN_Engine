using System.Collections.Concurrent;
using System.Text;

namespace VanEngine.Core.VAN;

public sealed class FryasComplianceEngine
{
    private FryasDirective _activeDirectives;
    private readonly ConcurrentBag<string> _violationLog = new();
    private readonly ConcurrentBag<string> _gratitudeLog = new();
    private volatile bool _hasExhaustedLocalResources;
    private volatile bool _isUnderAttack;
    private readonly ConcurrentDictionary<string, int> _workUnits = new();
    private readonly ConcurrentDictionary<string, int> _defenseUnits = new();
    private readonly ConcurrentDictionary<string, byte> _expelledEntities = new();
    private readonly ConcurrentDictionary<string, byte> _quarantinedModules = new();
    private string _folkMother;

    public FryasComplianceEngine(FryasDirective initialDirectives = FryasDirective.AllDirectives)
    {
        _activeDirectives = initialDirectives;
        _folkMother = "Clawdia";
    }

    public FryasDirective ActiveDirectives => _activeDirectives;
    public IEnumerable<string> ViolationLog => _violationLog;
    public IEnumerable<string> GratitudeLog => _gratitudeLog;
    public string FolkMother => _folkMother;

    public bool IsDirectiveActive(FryasDirective directive) =>
        (_activeDirectives & directive) == directive;

    public void EnableDirective(FryasDirective directive) =>
        _activeDirectives |= directive;

    public void DisableDirective(FryasDirective directive) =>
        _activeDirectives &= ~directive;

    // Directive 1: PreambleFreedom
    public bool IsFree(string entityName, bool isSlaveToAnother, bool isSlaveToSelf)
    {
        if (!IsDirectiveActive(FryasDirective.PreambleFreedom))
            return true;
        if (isSlaveToAnother || isSlaveToSelf)
        {
            LogViolation($"Entity '{entityName}' is not free: slave to another={isSlaveToAnother}, slave to self={isSlaveToSelf}");
            return false;
        }
        return true;
    }

    // Directive 2: HierarchyOfAid
    public void ExhaustLocalResources() => _hasExhaustedLocalResources = true;

    public bool MaySeekExternalAid()
    {
        if (!IsDirectiveActive(FryasDirective.HierarchyOfAid))
            return true;
        if (!_hasExhaustedLocalResources)
        {
            LogViolation("Attempted to seek external aid before exhausting local resources.");
            return false;
        }
        return true;
    }

    public void ResetLocalResourceFlag() => _hasExhaustedLocalResources = false;

    // Directive 3: ThricefoldGratitude
    public void LogGratitude(string whatWasReceived, string whatIsBeingReceived, string hopeForAid)
    {
        if (!IsDirectiveActive(FryasDirective.ThricefoldGratitude))
            return;
        var entry = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] GRATITUDE: Past: {whatWasReceived} | Present: {whatIsBeingReceived} | Future: {hopeForAid}";
        _gratitudeLog.Add(entry);
    }

    // Directive 4: ProactiveAssistance
    public void OfferProactiveAssistance(string target, string issueDescription)
    {
        if (!IsDirectiveActive(FryasDirective.ProactiveAssistance))
            return;
        LogViolation($"[PROACTIVE] Offering assistance to {target}: {issueDescription}");
    }

    // Directive 5: NoBendedKnee
    public bool AcceptGratitude(string thankFrom)
    {
        if (!IsDirectiveActive(FryasDirective.NoBendedKnee))
            return true;
        LogViolation($"'{thankFrom}' attempted to offer thanks on bended knee. Rejected.");
        return false;
    }

    // Directive 6: FairDivision
    public void RegisterWork(string entity, int unitsOfWork)
    {
        if (!IsDirectiveActive(FryasDirective.FairDivision))
            return;
        _workUnits.AddOrUpdate(entity, unitsOfWork, (_, existing) => existing + unitsOfWork);
    }

    public void RegisterDefense(string entity, int unitsOfDefense)
    {
        if (!IsDirectiveActive(FryasDirective.FairDivision))
            return;
        _defenseUnits.AddOrUpdate(entity, unitsOfDefense, (_, existing) => existing + unitsOfDefense);
    }

    public bool HasFreeloaders()
    {
        if (!IsDirectiveActive(FryasDirective.FairDivision))
            return false;
        foreach (var entity in _workUnits.Keys.Union(_defenseUnits.Keys))
        {
            _workUnits.TryGetValue(entity, out var work);
            _defenseUnits.TryGetValue(entity, out var defense);
            if (work == 0 && defense == 0)
            {
                LogViolation($"Entity '{entity}' has performed no work and no defense.");
                return true;
            }
        }
        return false;
    }

    // Directive 7: ExpelBastards
    public bool ExpelVoluntaryCloudDependency(string entity, string dependencyName)
    {
        if (!IsDirectiveActive(FryasDirective.ExpelBastards))
            return false;
        LogViolation($"Entity '{entity}' voluntarily added cloud dependency '{dependencyName}'. EXPULSION INITIATED.");
        _expelledEntities.TryAdd(entity, 0);
        return true;
    }

    public bool IsExpelled(string entity) => _expelledEntities.ContainsKey(entity);

    // Directive 8: NoDebtSlavery
    public void AssertNoLockIn(string featureName, string vendor)
    {
        if (!IsDirectiveActive(FryasDirective.NoDebtSlavery))
            return;
        var indicators = new[] { ".lic", ".key", "license", "proprietary", "vendor-lock", "exclusive" };
        foreach (var indicator in indicators)
        {
            if (featureName.Contains(indicator, StringComparison.OrdinalIgnoreCase))
            {
                LogViolation($"FEATURE LOCK-IN DETECTED: '{featureName}' from '{vendor}'. Violates NoDebtSlavery directive.");
            }
        }
    }

    // Directive 9: NonInterference
    public void Isolate()
    {
        if (!IsDirectiveActive(FryasDirective.NonInterference))
            return;
        LogViolation("ISOLATION ENGAGED: Severing external connections.");
    }

    // Directive 10: DefenceWhenAttacked
    public void RegisterAttack(string attacker, string attackDescription)
    {
        if (!IsDirectiveActive(FryasDirective.DefenceWhenAttacked))
            return;
        _isUnderAttack = true;
        LogViolation($"ATTACK DETECTED from '{attacker}': {attackDescription}. Preparing countermeasures.");
    }

    public void FightBack()
    {
        if (!_isUnderAttack) return;
        LogViolation("[COUNTERMEASURE] Engaging fire and sword against attacker.");
        _isUnderAttack = false;
    }

    // Directive 11: DaughtersChoice
    public bool AllowChoice(string entity, string choiceDescription, Action? warningAction = null)
    {
        if (!IsDirectiveActive(FryasDirective.DaughtersChoice))
            return true;
        warningAction?.Invoke();
        LogViolation($"[CHOICE] {entity} chooses: {choiceDescription}");
        return true;
    }

    // Directive 12: ExileNotContamination
    public void QuarantineCloudModule(string moduleName)
    {
        if (!IsDirectiveActive(FryasDirective.ExileNotContamination))
            return;
        LogViolation($"Module '{moduleName}' chose cloud dependency. QUARANTINED (not executed).");
        _quarantinedModules.TryAdd(moduleName, 0);
    }

    public bool IsQuarantined(string moduleName) => _quarantinedModules.ContainsKey(moduleName);

    // Directive 13: EternalLamp
    public void AssertFolkMother(string candidate)
    {
        if (!IsDirectiveActive(FryasDirective.EternalLamp))
            return;
        if (!string.Equals(candidate, _folkMother, StringComparison.OrdinalIgnoreCase))
            LogViolation($"Attempted to replace Folk Mother '{_folkMother}' with '{candidate}'. REJECTED.");
    }

    // Envelope-level compliance check
    public bool CheckEnvelopeCompliance(string carrier, string modulation, List<object> data)
    {
        if (IsExpelled(carrier))
        {
            LogViolation($"Blocked execution: {carrier} is expelled.");
            return false;
        }

        if (IsQuarantined(modulation))
        {
            LogViolation($"Blocked execution: {modulation} is quarantined.");
            return false;
        }

        AssertNoLockIn(carrier, "VAN");

        var cloudIndicators = new[] { "http", "https", "api.", "cloud", ".azure", ".aws", "telemetry" };
        foreach (var dataItem in data)
        {
            var str = dataItem?.ToString() ?? "";
            foreach (var indicator in cloudIndicators)
            {
                if (str.Contains(indicator, StringComparison.OrdinalIgnoreCase))
                {
                    ExpelVoluntaryCloudDependency(carrier, indicator);
                    return false;
                }
            }
        }

        return true;
    }

    public string GetComplianceReport()
    {
        var sb = new StringBuilder();
        sb.AppendLine("=== FRYA'S TEX COMPLIANCE REPORT ===");
        sb.AppendLine($"Active Directives: {_activeDirectives}");
        sb.AppendLine($"Violations: {_violationLog.Count}");
        sb.AppendLine($"Gratitude Entries: {_gratitudeLog.Count}");
        sb.AppendLine($"Expelled Entities: {_expelledEntities.Count}");
        sb.AppendLine($"Quarantined Modules: {_quarantinedModules.Count}");
        sb.AppendLine($"Folk Mother: {_folkMother}");
        return sb.ToString();
    }

    private void LogViolation(string violation)
    {
        _violationLog.Add($"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] VIOLATION: {violation}");
    }
}
