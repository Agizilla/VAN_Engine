namespace VanEngine.Core.Governance;

public sealed class SuccessionRules
{
    private readonly Dictionary<string, List<string>> _moduleRelations = new();

    public void DefineRelation(string module, string relatedModule, int degree)
    {
        if (!_moduleRelations.ContainsKey(module))
            _moduleRelations[module] = new List<string>();
        _moduleRelations[module].Add(relatedModule);
    }

    public string DetermineSuccessor(string fallenKing, bool killedByEnemy)
    {
        if (killedByEnemy)
        {
            if (_moduleRelations.TryGetValue(fallenKing, out var relatives) && relatives.Count > 0)
                return relatives.First();
            return FindNearestByDistance(fallenKing);
        }
        else
        {
            if (_moduleRelations.TryGetValue(fallenKing, out var relatives))
            {
                var distantRelatives = relatives.Where(r => GetRelationDegree(fallenKing, r) >= 4);
                var first = distantRelatives.FirstOrDefault();
                if (first != null)
                    return first;
            }
            return FindByElection();
        }
    }

    public IReadOnlyList<string> GetRelations(string module) =>
        _moduleRelations.TryGetValue(module, out var rels) ? rels.AsReadOnly() : new List<string>().AsReadOnly();

    private static int GetRelationDegree(string a, string b) => 1;
    private static string FindNearestByDistance(string module) => "FolkMother";
    private static string FindByElection() => "ElectedSuccessor";
}
