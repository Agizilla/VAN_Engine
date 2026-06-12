using Xunit;
using VanEngine.Core.Governance;
using VanEngine.Core.Justice;
using VanEngine.Core.Navigation;

namespace VanEngine.Core.Tests.VAN;

public sealed class SecurityRulesTests
{
    [Fact]
    public void Law1_CommonGood_DefaultAllows()
    {
        var validator = new CommonGoodValidator();
        Assert.True(validator.IsForCommonGood("fair scheduling", "Clawdia"));
    }

    [Fact]
    public void Law2_GeneralLevy_AssessesDamage()
    {
        var levy = new GeneralLevy();
        var damage = new DamageReport("War", 3000, "Destroyed citadel");
        levy.AssessLevyForDamage(damage);
        Assert.True(levy.TotalCollected > 0);
    }

    [Fact]
    public void Law3_WoundedWarrior_Registered()
    {
        var registry = new WoundedWarriorRegistry();
        registry.RegisterWounded("Guardian", "Combat injury", true);
        var wounded = registry.GetWounded();
        Assert.Single(wounded);
        Assert.Equal("Guardian", wounded[0].Name);
    }

    [Fact]
    public void Law4_WidowsOrphans_RegisterDependent()
    {
        var support = new WidowsOrphansSupport();
        support.RegisterDependent("FallenModule", new Dependent("ChildModule", "son"));
        var deps = support.GetDependents("FallenModule");
        Assert.Single(deps);
        Assert.Equal("ChildModule", deps[0].Name);
    }

    [Fact]
    public void Law5_QuarantineProtocol_QuarantinesCompromised()
    {
        var quarantine = new QuarantineProtocol();
        quarantine.QuarantineReturnedModule("CompromisedModule", "compromised by attacker");
        Assert.True(quarantine.IsQuarantined("CompromisedModule"));
    }

    [Fact]
    public void Law5_QuarantineProtocol_PassesClean()
    {
        var quarantine = new QuarantineProtocol();
        quarantine.QuarantineReturnedModule("CleanModule", "returned voluntarily");
        Assert.False(quarantine.IsQuarantined("CleanModule"));
    }

    [Fact]
    public void Law5_QuarantineProtocol_ReintegrateAfterValidation()
    {
        var quarantine = new QuarantineProtocol();
        quarantine.QuarantineReturnedModule("ModuleX", "compromised");
        Assert.True(quarantine.MayReintegrate("ModuleX"));
        Assert.False(quarantine.IsQuarantined("ModuleX"));
    }

    [Fact]
    public void Law6_CaptureDependency_IsolatesInSandbox()
    {
        var protocol = new EnemyPrisonerProtocol();
        protocol.CaptureDependency("evil-lib", "1.0.0");
        Assert.True(Sandbox.IsIsolated("evil-lib"));
    }

    [Fact]
    public void Law7_ReleaseWithKindness()
    {
        var protocol = new EnemyPrisonerProtocol();
        protocol.CaptureDependency("foreign-lib", "2.0.0");
        protocol.TeachCustoms("foreign-lib");
        protocol.ReleaseWithKindness("foreign-lib");
        Assert.False(Sandbox.IsIsolated("foreign-lib"));
    }

    [Fact]
    public void Minno_CapitalPunishment_ExecutesCulprit()
    {
        var punishment = new CapitalPunishment();
        punishment.ExecuteCulprit("TraitorModule", Crime.Treason, "CitadelA");
        Assert.True(ModuleManager.IsTerminated("TraitorModule"));
    }

    [Fact]
    public void Minno_Accountability_RevokesLineage()
    {
        var accountability = new Accountability();
        accountability.PunishAuthority("CorruptKing", Crime.Robbery);
        Assert.True(ModuleManager.IsTerminated("CorruptKing"));
        Assert.True(NamingRights.IsRevoked("CorruptKing"));
    }

    [Fact]
    public void NavLaw1_EnlistNavigator()
    {
        var rights = new NavigatorRights();
        Assert.True(rights.EnlistNavigator("ModuleSea"));
        Assert.Single(rights.Navigators);
    }

    [Fact]
    public void NavLaw4_ReplaceKing()
    {
        var vote = new LeadershipVote();
        vote.ReplaceIncompetentKing("BadKing", "GoodKing");
    }

    [Fact]
    public void NavLaw5_ProfitSharing_Distributes()
    {
        var sharing = new ProfitSharing();
        var manifest = new FleetManifest();

        var king = new Navigator { Name = "KingA", Role = "King" };
        var admiral = new Navigator { Name = "AdmiralA", Role = "Admiral" };
        var crew = new Navigator { Name = "SailorA", Role = "Crew" };
        manifest.AddNavigator(king);
        manifest.AddNavigator(admiral);
        manifest.AddNavigator(crew);

        sharing.DistributeProfits(9000, manifest);

        Assert.True(king.ProfitReceived > 0);
        Assert.True(admiral.ProfitReceived > 0);
        Assert.True(crew.ProfitReceived > 0);
        Assert.True(king.ProfitReceived > admiral.ProfitReceived);
    }
}
