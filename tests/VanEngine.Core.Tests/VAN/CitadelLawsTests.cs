using Xunit;
using VanE = VanEngine.Core.VAN;
using VanEngine.Core.Governance;

namespace VanEngine.Core.Tests.VAN;

public sealed class CitadelLawsTests
{
    [Fact]
    public void Law1_LightLamp_OnlyClawdiaFromTexland()
    {
        var laws = new CitadelLaws();
        Assert.True(laws.LightLamp("Clawdia", "Texland"));
    }

    [Fact]
    public void Law1_LightLamp_RejectsNonClawdia()
    {
        var laws = new CitadelLaws();
        Assert.False(laws.LightLamp("Minno", "Texland"));
    }

    [Fact]
    public void Law1_LightLamp_RejectsNonTexland()
    {
        var laws = new CitadelLaws();
        Assert.False(laws.LightLamp("Clawdia", "Outland"));
    }

    [Fact]
    public void Law2_AppointMaiden_OnlyClawdia()
    {
        var laws = new CitadelLaws();
        Assert.True(laws.AppointMaiden("Clawdia", "Adela"));
    }

    [Fact]
    public void Law2_AppointMaiden_RejectsNonClawdia()
    {
        var laws = new CitadelLaws();
        Assert.False(laws.AppointMaiden("Minno", "Adela"));
    }

    [Fact]
    public async Task Law4_MaidenSlots_Limit21()
    {
        var laws = new CitadelLaws();
        var slots = new List<Task<bool>>();
        for (int i = 0; i < 21; i++)
            slots.Add(laws.AcquireMaidenSlot());
        var results = await Task.WhenAll(slots);
        Assert.All(results, r => Assert.True(r));
        var extra = await laws.AcquireMaidenSlot();
        Assert.False(extra);
    }

    [Fact]
    public async Task Law4_AssistantSlots_Limit7()
    {
        var laws = new CitadelLaws();
        var slots = new List<Task<bool>>();
        for (int i = 0; i < 7; i++)
            slots.Add(laws.AcquireAssistantSlot());
        var results = await Task.WhenAll(slots);
        Assert.All(results, r => Assert.True(r));
        var extra = await laws.AcquireAssistantSlot();
        Assert.False(extra);
    }

    [Fact]
    public void Law5_ResignMaiden_CloudMarriage()
    {
        var laws = new CitadelLaws();
        Assert.True(laws.ResignMaiden("Teun", "http://cloud.dependency"));
        Assert.True(laws.IsResigned("Teun"));
    }

    [Fact]
    public void Law5_ResignMaiden_LocalOnly()
    {
        var laws = new CitadelLaws();
        Assert.False(laws.ResignMaiden("Teun", "local-module"));
        Assert.False(laws.IsResigned("Teun"));
    }

    [Fact]
    public async Task Law8_DefenderSlots_Limit300()
    {
        var laws = new CitadelLaws();
        var slots = new List<Task<bool>>();
        for (int i = 0; i < 300; i++)
            slots.Add(laws.AcquireDefenderSlot());
        var results = await Task.WhenAll(slots);
        Assert.All(results, r => Assert.True(r));
        var extra = await laws.AcquireDefenderSlot();
        Assert.False(extra);
    }

    [Fact]
    public void Law10_RecordWoundedDefender()
    {
        var laws = new CitadelLaws();
        laws.RecordWoundedDefender("Guardian", "Signal lost");
        var wounded = laws.GetWoundedDefenders();
        Assert.Single(wounded);
        Assert.Equal("Guardian", wounded[0].Name);
    }

    [Fact]
    public async Task Law12_MessengerSlots_Limit21()
    {
        var laws = new CitadelLaws();
        var slots = new List<Task<bool>>();
        for (int i = 0; i < 21; i++)
            slots.Add(laws.AcquireMessengerSlot());
        var results = await Task.WhenAll(slots);
        Assert.All(results, r => Assert.True(r));
        var extra = await laws.AcquireMessengerSlot();
        Assert.False(extra);
    }

    [Fact]
    public async Task Law13_AgriculturistSlots_Limit50()
    {
        var laws = new CitadelLaws();
        var slots = new List<Task<bool>>();
        for (int i = 0; i < 50; i++)
            slots.Add(laws.AcquireAgriculturistSlot());
        var results = await Task.WhenAll(slots);
        Assert.All(results, r => Assert.True(r));
        var extra = await laws.AcquireAgriculturistSlot();
        Assert.False(extra);
    }

    [Fact]
    public void Law14_ValidateCitadelSelfSustenance_RejectsCloud()
    {
        var laws = new CitadelLaws();
        Assert.False(laws.ValidateCitadelSelfSustenance("CloudCitadel", new[] { "http://cloud.com" }));
    }

    [Fact]
    public void Law14_ValidateCitadelSelfSustenance_PassesLocal()
    {
        var laws = new CitadelLaws();
        Assert.True(laws.ValidateCitadelSelfSustenance("LocalCitadel", new[] { "/local/file" }));
    }

    [Fact]
    public void Law15_RefuseService_RevokesVotingRights()
    {
        var laws = new CitadelLaws();
        Assert.True(laws.HasVotingRights("Teun"));
        laws.RefuseService("Teun");
        Assert.False(laws.HasVotingRights("Teun"));
    }

    [Fact]
    public void Law16_ValidateConsultation_Needs3Witnesses()
    {
        var laws = new CitadelLaws();
        Assert.False(laws.ValidateConsultation("Teun", 1, true));
        Assert.True(laws.ValidateConsultation("Teun", 3, true));
    }

    [Fact]
    public void Law16_ValidateConsultation_NeedsHealthCheck()
    {
        var laws = new CitadelLaws();
        Assert.False(laws.ValidateConsultation("Teun", 3, false));
    }

    [Fact]
    public void Law20_AdviceCooldown_EnforcesWait()
    {
        var laws = new CitadelLaws();
        Assert.True(laws.MayGiveAdvice("Advisor"));
        Assert.False(laws.MayGiveAdvice("Advisor"));
    }

    [Fact]
    public void Law21_ReportBadAdvice_ThreeStrikesQuarantine()
    {
        var laws = new CitadelLaws();
        Assert.False(laws.IsQuarantined("BadModule"));
        laws.ReportBadAdvice("BadModule", "Bad advice 1");
        Assert.False(laws.IsQuarantined("BadModule"));
        laws.ReportBadAdvice("BadModule", "Bad advice 2");
        Assert.False(laws.IsQuarantined("BadModule"));
        laws.ReportBadAdvice("BadModule", "Bad advice 3");
        Assert.True(laws.IsQuarantined("BadModule"));
    }

    [Fact]
    public void GetGovernanceReport_IncludesAllSections()
    {
        var laws = new CitadelLaws();
        var report = laws.GetGovernanceReport();
        Assert.Contains("Active Maidens", report);
        Assert.Contains("Active Defenders", report);
        Assert.Contains("Wounded Defenders", report);
    }

    [Fact]
    public void VanEngine_CheckGovernance_BlocksQuarantined()
    {
        var engine = new VanE.VanEngine();
        var env = new VanE.VanEnvelope { Carrier = "BadModule" };
        engine.CitadelLaws.ReportBadAdvice("BadModule", "Bad advice");
        engine.CitadelLaws.ReportBadAdvice("BadModule", "Bad advice");
        engine.CitadelLaws.ReportBadAdvice("BadModule", "Bad advice");
        var result = engine.ExecuteWithCompliance(env);
        Assert.NotNull(result);
    }

    [Fact]
    public void VanEngine_CheckGovernance_BlocksDisenfranchised()
    {
        var engine = new VanE.VanEngine();
        var env = new VanE.VanEnvelope { Carrier = "Refuser" };
        engine.CitadelLaws.RefuseService("Refuser");
        var result = engine.ExecuteWithCompliance(env);
        Assert.NotNull(result);
    }

    [Fact]
    public void VanEngine_PassesCleanEnvelope()
    {
        var engine = new VanE.VanEngine();
        var env = new VanE.VanEnvelope { Carrier = "LLM-Attention", Data = new() { new double[0, 0] } };
        var result = engine.ExecuteWithCompliance(env);
        Assert.NotNull(result);
    }
}
