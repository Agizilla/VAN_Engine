using Xunit;
using VanE = VanEngine.Core.VAN;
using VanEngine.Core.Governance;

namespace VanEngine.Core.Tests.VAN;

public sealed class UniversalLawTests
{
    [Fact]
    public void Law1_FairQueue_FirstInFirstServed()
    {
        var law = new UniversalLaw();
        var results = new List<int>();
        law.Enqueue(new WorkItem("A", () => { results.Add(1); return null; }));
        law.Enqueue(new WorkItem("B", () => { results.Add(2); return null; }));
        law.Enqueue(new WorkItem("C", () => { results.Add(3); return null; }));

        while (law.TryDequeue(out var item) && item is not null)
            item.Execute!();

        Assert.Equal(new[] { 1, 2, 3 }, results);
    }

    [Fact]
    public void Law1_FairQueue_EmptyQueue()
    {
        var law = new UniversalLaw();
        Assert.False(law.TryDequeue(out _));
        Assert.Equal(0, law.QueueLength);
    }

    [Fact]
    public void Law2_ValidateFreeChoice_PassesClean()
    {
        var law = new UniversalLaw();
        Assert.True(law.ValidateFreeChoice("ModuleA", "http-lib"));
    }

    [Fact]
    public void Law2_ValidateFreeChoice_BlocksForcedTransitive()
    {
        var law = new UniversalLaw();
        law.RegisterForcedDependency("evil-lib");
        Assert.False(law.ValidateFreeChoice("ModuleA", "evil-lib"));
    }

    [Fact]
    public void Law3_ModuleContext_IsolationByDefault()
    {
        var ctx1 = new ModuleContext("ModuleA");
        var ctx2 = new ModuleContext("ModuleB");

        ctx1.SetPrivateState("key", "value-a");
        ctx2.SetPrivateState("key", "value-b");

        Assert.True(ctx1.TryGetPrivateState("key", out var v1));
        Assert.True(ctx2.TryGetPrivateState("key", out var v2));
        Assert.Equal("value-a", v1);
        Assert.Equal("value-b", v2);
    }

    [Fact]
    public void Law4_CrossVillage_FlagSet()
    {
        var ctx = new ModuleContext("ForeignModule", isCrossVillage: true);
        Assert.True(ctx.IsCrossVillage);
    }

    [Fact]
    public void Law5_PublicServiceAttribute_RequiredForPublicExposure()
    {
        Assert.False(PublicServiceValidator.HasPublicServiceAttribute(typeof(UniversalLawTests)));
    }

    [PublicService("Test service for testing")]
    public sealed class ServiceClass { }

    [Fact]
    public void Law5_PublicServiceAttribute_Present()
    {
        Assert.True(PublicServiceValidator.HasPublicServiceAttribute(typeof(ServiceClass)));
    }

    [Fact]
    public void Law6_CommonsPool_BorrowReturn()
    {
        var pool = new CommonsPool<string>(() => "fresh");
        var item = pool.Borrow();
        Assert.Equal("fresh", item);
        Assert.Equal(1, pool.Borrowed);
        pool.Return(item);
        Assert.Equal(0, pool.Borrowed);
    }

    [Fact]
    public void Law6_CommonsPool_RejectsDamaged()
    {
        int disposed = 0;
        var pool = new CommonsPool<DisposableMock>(
            () => new DisposableMock(() => disposed++),
            integrityCheck: d => d.IsValid,
            maxSize: 5
        );

        var good = pool.Borrow();
        good.IsValid = true;
        pool.Return(good);

        var bad = pool.Borrow();
        bad.IsValid = false;
        pool.Return(bad);

        Assert.Equal(1, disposed);
    }

    private sealed class DisposableMock : IDisposable
    {
        private readonly Action _onDispose;
        public bool IsValid { get; set; }
        public DisposableMock(Action onDispose) => _onDispose = onDispose;
        public void Dispose() => _onDispose();
    }

    [Fact]
    public void Law7_ForestGuardian_AllocatesWithinLimit()
    {
        var forest = new ForestGuardian(1000);
        Assert.True(forest.RequestTreeFelling(500, "ModuleA"));
        Assert.Equal(500, forest.TotalAllocated);
    }

    [Fact]
    public void Law7_ForestGuardian_BlocksOverCapacity()
    {
        var forest = new ForestGuardian(1000);
        Assert.True(forest.RequestTreeFelling(600, "ModuleA"));
        Assert.False(forest.RequestTreeFelling(500, "ModuleB"));
        Assert.Equal(600, forest.TotalAllocated);
    }

    [Fact]
    public void Law7_ForestGuardian_ReleaseFreesMemory()
    {
        var forest = new ForestGuardian(1000);
        forest.RequestTreeFelling(500, "ModuleA");
        forest.Release(200, "ModuleA");
        Assert.Equal(300, forest.TotalAllocated);
    }

    [Fact]
    public void Law8_MarketOverhead_UnderCap()
    {
        var market = new MarketRegulator();
        market.RecordUserWork(1100);
        market.RecordSystemOverhead(100);
        Assert.True(market.IsOverheadCompliant());
    }

    [Fact]
    public void Law8_MarketOverhead_ExceedsCap()
    {
        var market = new MarketRegulator();
        market.RecordUserWork(100);
        market.RecordSystemOverhead(100);
        Assert.False(market.IsOverheadCompliant());
    }

    [Fact]
    public void Law10_Distribution_20Grevetman_10Keeper_5Assistants_1Mother_4Midwife_10Village_50Poor()
    {
        var market = new MarketRegulator();
        var dist = market.DistributeMarketProceeds(10000);
        Assert.Equal(10000, dist.Total);
        Assert.Equal(2000, dist.Grevetman);
        Assert.Equal(1000, dist.Keeper);
        Assert.Equal(500, dist.Assistants);
        Assert.Equal(100, dist.Volksmoeder);
        Assert.Equal(400, dist.Midwife);
        Assert.Equal(1000, dist.Village);
        Assert.Equal(5000, dist.PoorAndInfirm);
    }

    [Fact]
    public void Law11_UsuryDetector_DetectsInterest()
    {
        var detector = new UsuryDetector();
        Assert.True(detector.IsUsurious("loan with 5% interest"));
    }

    [Fact]
    public void Law11_UsuryDetector_PassesClean()
    {
        var detector = new UsuryDetector();
        Assert.False(detector.IsUsurious("fair trade: 10 apples for 10 oranges"));
    }

    [Fact]
    public void Law12_MarketKeeper_RejectsCorruptedGoods()
    {
        var keeper = new MarketKeeper();
        Assert.False(keeper.ValidateGoods("corrupt", s => s == "valid"));
    }

    [Fact]
    public void Law12_MarketKeeper_AcceptsValidGoods()
    {
        var keeper = new MarketKeeper();
        Assert.True(keeper.ValidateGoods("valid", s => s == "valid"));
    }

    [Fact]
    public void Law12_MarketKeeper_ExpelsMerchant()
    {
        var keeper = new MarketKeeper();
        keeper.ExpelMerchant("FraudMerchant");
        Assert.True(keeper.IsExpelled("FraudMerchant"));
    }

    [Fact]
    public void VanEngine_UniversalLawMemory_ForestGuardianWorks()
    {
        var engine = new VanE.VanEngine();
        var env = new VanE.VanEnvelope
        {
            Carrier = "LLM-Attention",
            Data = new() { new double[10, 10] }
        };
        var result = engine.ExecuteWithCompliance(env);
        Assert.NotNull(result);
    }
}
