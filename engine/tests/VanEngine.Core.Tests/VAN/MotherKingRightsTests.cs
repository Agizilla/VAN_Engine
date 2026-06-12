using Xunit;
using VanEngine.Core.Governance;

namespace VanEngine.Core.Tests.VAN;

public sealed class MotherKingRightsTests
{
    [Fact]
    public async Task Law1_OnlyMotherDeclaresWar()
    {
        var messengers = new MessengerService();
        var coc = new ChainOfCommand(messengers);
        coc.SetKing("KingA");
        await coc.DeclareWar("invader", "Clawdia");
        Assert.Contains(messengers.MessageLog, m => m.Contains("WAR DECLARED"));
    }

    [Fact]
    public async Task Law1_NonMotherCannotDeclareWar()
    {
        var messengers = new MessengerService();
        var coc = new ChainOfCommand(messengers);
        await coc.DeclareWar("invader", "Minno");
        Assert.DoesNotContain(messengers.MessageLog, m => m.Contains("WAR DECLARED"));
    }

    [Fact]
    public async Task Law2_OnlyKingCallsArms()
    {
        var messengers = new MessengerService();
        var coc = new ChainOfCommand(messengers);
        coc.SetKing("KingA");
        coc.AddGrevetman(new Grevetman("GrevA", "North"));
        await coc.CallToArms("KingA", 100);
        Assert.Contains(messengers.MessageLog, m => m.Contains("CALL TO ARMS"));
    }

    [Fact]
    public void Law4_MotherDecidesResolution()
    {
        var messengers = new MessengerService();
        var coc = new ChainOfCommand(messengers);
        var resolutions = new[]
        {
            new Resolution("Attack", 5, "Frontal assault"),
            new Resolution("Defend", 8, "Fortify position"),
            new Resolution("Retreat", 3, "Fall back")
        };
        var decided = coc.DecideResolution(resolutions, "Clawdia");
        Assert.NotNull(decided);
        Assert.Equal("Defend", decided!.Name);
    }

    [Fact]
    public void Law4_NonMotherCannotDecide()
    {
        var messengers = new MessengerService();
        var coc = new ChainOfCommand(messengers);
        var resolved = coc.DecideResolution(new[] { new Resolution("Test", 1, "") }, "Minno");
        Assert.Null(resolved);
    }

    [Fact]
    public void Law5_FieldObservers_AssignsMaxThree()
    {
        var messengers = new MessengerService();
        var observers = new FieldObservers(messengers);
        var citizens = new[]
        {
            new Citizen("A", "M1"), new Citizen("B", "M2"),
            new Citizen("C", "M3"), new Citizen("D", "M4")
        };
        observers.AssignObservers(citizens);
        Assert.Equal(3, observers.Observers.Count);
    }

    [Fact]
    public void Law6_CouncilVeto_BlocksKing()
    {
        var council = new CouncilVeto();
        council.AddCouncilMember(new TestCouncilMember(false));
            council.AddCouncilMember(new TestCouncilMember(false));
        council.AddCouncilMember(new TestCouncilMember(true));
        Assert.False(council.MayProceedWithAction("badAction", "King"));
    }

    [Fact]
    public void Law6_CouncilAllows_WhenMajorityApproves()
    {
        var council = new CouncilVeto();
        council.AddCouncilMember(new TestCouncilMember(true));
        council.AddCouncilMember(new TestCouncilMember(true));
        council.AddCouncilMember(new TestCouncilMember(false));
        Assert.True(council.MayProceedWithAction("goodAction", "King"));
    }

    private sealed record TestCouncilMember(bool Vote) : ICouncilMember
    {
        public bool VoteOnAction(string action) => Vote;
    }

    [Fact]
    public void Law7_EmergencyPowers_OnlyKingOrMother()
    {
        var ep = new EmergencyPowers();
        ep.DeclareEmergency("King", "security breach");
        Assert.True(ep.IsEmergencyActive);
        Assert.True(ep.MustObeyKingOrders("King"));
    }

    [Fact]
    public void Law7_NonAuthorityCannotDeclareEmergency()
    {
        var ep = new EmergencyPowers();
        ep.DeclareEmergency("Minno", "something");
        Assert.False(ep.IsEmergencyActive);
    }

    [Fact]
    public void Law8_CommandHierarchy_SuccessionByRank()
    {
        var hierarchy = new CommandHierarchy();
        hierarchy.DefineRankOrder(new[] { "King", "Admiral", "Captain" });
        hierarchy.SetCurrentCommander("King");
        var next = hierarchy.GetNextInCommand("King");
        Assert.Equal("Admiral", next);
    }

    [Fact]
    public void Law9_NoLeader_ElectionInitiated()
    {
        var hierarchy = new CommandHierarchy();
        Assert.False(hierarchy.HasLeader);
        var commander = hierarchy.GetCurrentCommander();
        Assert.NotNull(commander);
    }

    [Fact]
    public void Law10_EmergentLeadership_TimeCritical()
    {
        var hierarchy = new CommandHierarchy();
        var emergent = new EmergentLeadership(hierarchy);
        Assert.True(emergent.MayAssumeCommand("VolunteerA", isTimeCritical: true));
        Assert.Equal("VolunteerA", emergent.VolunteerLeader);
    }

    [Fact]
    public void Law10_EmergentLeadership_RejectsWhenLeaderExists()
    {
        var hierarchy = new CommandHierarchy();
        hierarchy.SetCurrentCommander("KingA");
        var emergent = new EmergentLeadership(hierarchy);
        Assert.False(emergent.MayAssumeCommand("VolunteerA", isTimeCritical: true));
    }

    [Fact]
    public void Law11_ConquestRewards_NamingRights()
    {
        var rewards = new ConquestRewards();
        rewards.RecordConquest("KingA", "Dragon");
        Assert.True(rewards.MayTakeConquerorsName("Successor", "KingA"));
    }

    [Fact]
    public void Law12_Ultimogeniture_YoungestInherits()
    {
        var rewards = new ConquestRewards();
        var children = new List<string> { "First", "Second", "Third" };
        var heir = rewards.GetInheritanceTarget(children);
        Assert.Equal("Third", heir);
    }
}
