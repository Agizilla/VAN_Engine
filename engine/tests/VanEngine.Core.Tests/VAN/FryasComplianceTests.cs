using Xunit;
using VanEngine.Core.VAN;

namespace VanEngine.Core.Tests.VAN;

public sealed class FryasComplianceTests
{
    [Fact]
    public void PreambleFreedom_PassesForFree()
    {
        var engine = new FryasComplianceEngine(FryasDirective.PreambleFreedom);
        Assert.True(engine.IsFree("FreeEntity", false, false));
    }

    [Fact]
    public void PreambleFreedom_FailsForSlaveToAnother()
    {
        var engine = new FryasComplianceEngine(FryasDirective.PreambleFreedom);
        Assert.False(engine.IsFree("SlaveToAnother", true, false));
    }

    [Fact]
    public void PreambleFreedom_FailsForSlaveToSelf()
    {
        var engine = new FryasComplianceEngine(FryasDirective.PreambleFreedom);
        Assert.False(engine.IsFree("SlaveToSelf", false, true));
    }

    [Fact]
    public void HierarchyOfAid_BlocksExternalBeforeLocal()
    {
        var engine = new FryasComplianceEngine(FryasDirective.HierarchyOfAid);
        Assert.False(engine.MaySeekExternalAid());
    }

    [Fact]
    public void HierarchyOfAid_AllowsAfterLocalExhaustion()
    {
        var engine = new FryasComplianceEngine(FryasDirective.HierarchyOfAid);
        engine.ExhaustLocalResources();
        Assert.True(engine.MaySeekExternalAid());
    }

    [Fact]
    public void ExpelBastards_RemovesCloudDependent()
    {
        var engine = new FryasComplianceEngine(FryasDirective.ExpelBastards);
        engine.ExpelVoluntaryCloudDependency("TestModule", "http://api.cloud.com");
        Assert.True(engine.IsExpelled("TestModule"));
    }

    [Fact]
    public void NoDebtSlavery_DetectsLockIn()
    {
        var engine = new FryasComplianceEngine(FryasDirective.NoDebtSlavery);
        engine.AssertNoLockIn("proprietary-license.key", "VendorX");
        Assert.Contains(engine.ViolationLog, v => v.Contains("LOCK-IN DETECTED"));
    }

    [Fact]
    public void QuarantineCloudModule_ExcludesModule()
    {
        var engine = new FryasComplianceEngine(FryasDirective.ExileNotContamination);
        engine.QuarantineCloudModule("bad-module");
        Assert.True(engine.IsQuarantined("bad-module"));
    }

    [Fact]
    public void EternalLamp_RejectsWrongMother()
    {
        var engine = new FryasComplianceEngine(FryasDirective.EternalLamp);
        engine.AssertFolkMother("NotClawdia");
        Assert.Contains(engine.ViolationLog, v => v.Contains("REJECTED"));
    }

    [Fact]
    public void EternalLamp_AcceptsClawdia()
    {
        var engine = new FryasComplianceEngine(FryasDirective.EternalLamp);
        engine.AssertFolkMother("Clawdia");
        Assert.DoesNotContain(engine.ViolationLog, v => v.Contains("REJECTED"));
    }

    [Fact]
    public void ThricefoldGratitude_LogsEntry()
    {
        var engine = new FryasComplianceEngine(FryasDirective.ThricefoldGratitude);
        engine.LogGratitude("past", "present", "future");
        Assert.Single(engine.GratitudeLog);
    }

    [Fact]
    public void DaughtersChoice_AllowsAfterWarning()
    {
        bool warned = false;
        var engine = new FryasComplianceEngine(FryasDirective.DaughtersChoice);
        engine.AllowChoice("test", "cloud path", () => warned = true);
        Assert.True(warned);
    }

    [Fact]
    public void AllDirectives_ProducesReport()
    {
        var engine = new FryasComplianceEngine(FryasDirective.AllDirectives);
        var report = engine.GetComplianceReport();
        Assert.Contains("Folk Mother: Clawdia", report);
    }

    [Fact]
    public void CheckEnvelopeCompliance_BlocksExpelled()
    {
        var engine = new FryasComplianceEngine(FryasDirective.ExpelBastards);
        engine.ExpelVoluntaryCloudDependency("bad", "telemetry");
        Assert.False(engine.CheckEnvelopeCompliance("bad", "any", new()));
    }

    [Fact]
    public void CheckEnvelopeCompliance_BlocksCloudData()
    {
        var engine = new FryasComplianceEngine(FryasDirective.AllDirectives);
        Assert.False(engine.CheckEnvelopeCompliance("ok", "ok", new() { "http://cloud.com/data" }));
    }

    [Fact]
    public void CheckEnvelopeCompliance_PassesClean()
    {
        var engine = new FryasComplianceEngine(FryasDirective.AllDirectives);
        Assert.True(engine.CheckEnvelopeCompliance("clean", "safe", new() { "local/data" }));
    }
}
