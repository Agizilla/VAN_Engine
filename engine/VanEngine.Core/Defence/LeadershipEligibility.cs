namespace VanEngine.Core.Defence;

public sealed class LeadershipEligibility
{
    private readonly Dictionary<string, DateTime> _citizenGrantDates = new();
    private const int VotingYearsRequired = 7;

    public void RecordCitizenshipGrant(string moduleName, DateTime grantDate)
    {
        _citizenGrantDates[moduleName] = grantDate;
    }

    public bool MayVoteForChief(string moduleName)
    {
        if (!_citizenGrantDates.TryGetValue(moduleName, out var grantDate))
            return false;

        var yearsAsVoter = (DateTime.UtcNow - grantDate).TotalDays / 365;
        return yearsAsVoter >= VotingYearsRequired;
    }

    public bool MayBeElected(string moduleName) => MayVoteForChief(moduleName);
}
