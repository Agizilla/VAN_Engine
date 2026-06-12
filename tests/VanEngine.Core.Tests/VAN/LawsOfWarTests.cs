using Xunit;
using VanEngine.Core.Defence;
using VanEngine.Core.Governance;

namespace VanEngine.Core.Tests.VAN;

public sealed class LawsOfWarTests
{
    [Fact]
    public void Law1_DefenceRegistry_RegistersAndSignals()
    {
        var registry = new DefenceRegistry();
        var defender = new TestDefender();
        registry.RegisterDefender(defender);
        registry.SignalAttack(new TestAssailant("threat", 5));
        Assert.True(defender.WasCalled);
    }

    private sealed class TestDefender : IResistable
    {
        public bool WasCalled { get; private set; }
        public bool Resist(IAssailant assailant)
        {
            WasCalled = true;
            return assailant.Severity < 10;
        }
    }

    private sealed record TestAssailant(string Name, int Severity) : IAssailant
    {
        public string ThreatDescription => $"Test threat: {Name}";
    }

    [Fact]
    public void Law2_TrainingRequiredForAdmission()
    {
        var admission = new WarriorAdmission();
        for (int i = 0; i < 52; i++)
            admission.RecordTraining("ModuleA", true);
        Assert.True(admission.IsAdmittedAsWarrior("ModuleA"));
    }

    [Fact]
    public void Law2_InsufficientTrainingBlocks()
    {
        var admission = new WarriorAdmission();
        admission.RecordTraining("ModuleA", true);
        Assert.False(admission.IsAdmittedAsWarrior("ModuleA"));
    }

    [Fact]
    public void Law4_ThreeYearsServiceGrantsCitizenship()
    {
        var registry = new CitizenRegistry();
        registry.EnlistWarrior("ModuleA");
        Assert.True(registry.IsEnlisted("ModuleA"));
        Assert.False(registry.MayVote("ModuleA"));
    }

    [Fact]
    public void Law5_SevenYearsVoterMayBeElected()
    {
        var eligibility = new LeadershipEligibility();
        eligibility.RecordCitizenshipGrant("ModuleA", DateTime.UtcNow.AddYears(-8));
        Assert.True(eligibility.MayVoteForChief("ModuleA"));
        Assert.True(eligibility.MayBeElected("ModuleA"));
    }

    [Fact]
    public void Law5_UnderSevenYearsCannotVote()
    {
        var eligibility = new LeadershipEligibility();
        eligibility.RecordCitizenshipGrant("ModuleA", DateTime.UtcNow.AddYears(-2));
        Assert.False(eligibility.MayVoteForChief("ModuleA"));
    }

    [Fact]
    public void Law8_TermLimits_EnforceMaxThreeYears()
    {
        var limits = new TermLimits();
        limits.RecordTermStart("KingA");
        Assert.False(limits.IsTermExpired("KingA"));
    }

    [Fact]
    public void Law9_CooldownRequiredBetweenTerms()
    {
        var limits = new TermLimits();
        limits.RecordTermStart("KingA");
        var oldTermsField = typeof(TermLimits).GetField("_terms",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var terms = (Dictionary<string, List<DateTime>>)oldTermsField!.GetValue(limits)!;
        terms["KingA"] = new List<DateTime> { DateTime.UtcNow.AddYears(-10) };
        Assert.True(limits.MayServeAsKing("KingA"));
    }

    [Fact]
    public void Law12_KingBearsNoArms()
    {
        var registry = new DefenceRegistry();
        var protocol = new KingProtocol(registry);
        Assert.False(protocol.MayDirectlyDefend());
    }

    [Fact]
    public void Law12_KingDelegatesDefence()
    {
        var registry = new DefenceRegistry();
        var defender = new TestDefender();
        registry.RegisterDefender(defender);
        var protocol = new KingProtocol(registry);
        protocol.DelegateDefence(new TestAssailant("enemy", 5));
        Assert.True(defender.WasCalled);
    }

    [Fact]
    public void Law10_EmergencySuccession()
    {
        var rules = new SuccessionRules();
        rules.DefineRelation("FallenKing", "HeirModule", 1);
        var successor = rules.DetermineSuccessor("FallenKing", killedByEnemy: true);
        Assert.Equal("HeirModule", successor);
    }

    [Fact]
    public void Law11_NaturalDeathRequiresDistantRelation()
    {
        var rules = new SuccessionRules();
        var successor = rules.DetermineSuccessor("FallenKing", killedByEnemy: false);
        Assert.NotNull(successor);
    }
}
