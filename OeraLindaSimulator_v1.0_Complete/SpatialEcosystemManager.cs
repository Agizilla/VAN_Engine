using VanEngine.Game.Core;

namespace VanEngine.Game.Simulation;

public sealed class SpatialEcosystemManager
{
    private readonly SovereignState _state;
    private readonly Random _rand = new();

    public SpatialEcosystemManager(SovereignState state)
    {
        _state = state;
    }

    public void UpdateKinClustering(float delta, SimulationPhase phase)
    {
        foreach (var citizen in _state.Citizens)
        {
            if (!citizen.IsActive) continue;

            System.Numerics.Vector2 target;
            if (phase == SimulationPhase.Nighttime)
            {
                var house = _state.Houses.FirstOrDefault(h => h.RootNamespace == citizen.NamespaceFamily);
                if (house != null && !citizen.IsHomeless)
                    target = house.Position;
                else
                    target = citizen.Position;
            }
            else
            {
                var house = _state.Houses.FirstOrDefault(h => h.RootNamespace == citizen.NamespaceFamily);
                if (house != null)
                    target = house.Position + new System.Numerics.Vector2(_rand.Next(-40, 40), _rand.Next(-40, 40));
                else
                    target = citizen.Position + new System.Numerics.Vector2(_rand.Next(-20, 20), _rand.Next(-20, 20));
            }

            citizen.TargetPosition = target;
            var dir = citizen.TargetPosition - citizen.Position;
            if (dir.Length() > 0.1f)
                citizen.Position += dir * 0.05f;
        }
    }

    public Dictionary<(int, int), float> ComputeSimilarityLinks()
    {
        var links = new Dictionary<(int, int), float>();
        var files = _state.Citizens
            .SelectMany(c => c.OwnedFiles.Select(f => (c.Id, f)))
            .ToList();

        for (int i = 0; i < files.Count; i++)
        {
            for (int j = i + 1; j < files.Count; j++)
            {
                if (files[i].Id == files[j].Id) continue;
                float similarity = ComputeLevenshteinSimilarity(files[i].f, files[j].f);
                if (similarity > 0.7f)
                    links[(files[i].Id, files[j].Id)] = similarity;
            }
        }
        return links;
    }

    private static float ComputeLevenshteinSimilarity(string a, string b)
    {
        if (string.IsNullOrEmpty(a) || string.IsNullOrEmpty(b)) return 0;
        int distance = LevenshteinDistance(a, b);
        int maxLen = Math.Max(a.Length, b.Length);
        return 1.0f - (float)distance / maxLen;
    }

    private static int LevenshteinDistance(string s, string t)
    {
        int n = s.Length, m = t.Length;
        var d = new int[n + 1, m + 1];
        for (int i = 0; i <= n; i++) d[i, 0] = i;
        for (int j = 0; j <= m; j++) d[0, j] = j;
        for (int i = 1; i <= n; i++)
            for (int j = 1; j <= m; j++)
                d[i, j] = Math.Min(
                    Math.Min(d[i - 1, j] + 1, d[i, j - 1] + 1),
                    d[i - 1, j - 1] + (s[i - 1] == t[j - 1] ? 0 : 1));
        return d[n, m];
    }

    public void PerformMarriage(Citizen a, Citizen b)
    {
        if (a == b) return;

        foreach (var file in b.OwnedFiles)
        {
            if (!a.OwnedFiles.Contains(file))
                a.OwnedFiles.Add(file);
        }
        a.CompliantLinesContributed += b.CompliantLinesContributed;
        a.RoleType = Math.Max(a.RoleType, b.RoleType);

        _state.ModifyResources(new ResourcePack { Wealth = 20 });
        _state.AddLog($"Marriage ceremony: {a.Name} and {b.Name} merged. {b.Name} fades away.");
        b.IsActive = false;
        _state.RemoveCitizen(b);
    }

    // ── Sprint 4 ──────────────────────────────────────────────────────────────
    // Spatial pathfinding for Homeless characters.
    //
    // Each homeless citizen evaluates two complementary weight sources:
    //   1. Namespace string similarity  – direct lexical match of their
    //      NamespaceFamily against each house's RootNamespace.
    //   2. File dependency proximity    – syntactic similarity between every
    //      file the homeless citizen owns and every file already tracked by
    //      each candidate house, sampled from the live similarity matrix so
    //      the pathfinding reacts to merges and re-assignments in real time.
    //
    // The house that scores highest on the combined weight wins; the citizen
    // is set to wander toward it each frame until they arrive (IsHomeless=false).
    public void AttractHomelessCharacters()
    {
        var homeless = _state.Citizens.Where(c => c.IsHomeless && c.IsActive).ToList();
        if (homeless.Count == 0) return;

        // Snapshot the live similarity matrix once per call (O(n²) over files).
        var similarityMatrix = ComputeSimilarityLinks();

        foreach (var h in homeless)
        {
            float bestScore  = -1f;
            ProjectHouse? bestHouse = null;

            foreach (var house in _state.Houses)
            {
                float score = ScoreHouseForCitizen(h, house, similarityMatrix);
                if (score > bestScore)
                {
                    bestScore = score;
                    bestHouse = house;
                }
            }

            if (bestHouse != null)
            {
                h.TargetPosition = bestHouse.Position;
                // Mark as homed only when the citizen has actually arrived
                // (within one bounding-box width of the house centre).
                var centre    = bestHouse.Position + bestHouse.BoundingBoxSize * 0.5f;
                var toHouse   = centre - h.Position;
                if (toHouse.Length() < bestHouse.BoundingBoxSize.X)
                {
                    h.IsHomeless = false;
                    _state.AddLog($"{h.Name} settled into '{bestHouse.ProjectName}' (score {bestScore:F2}).");
                }
            }
        }
    }

    /// <summary>
    /// Computes a [0, 1] affinity score for how well <paramref name="citizen"/> fits
    /// <paramref name="house"/> using two weighted signals.
    /// </summary>
    private float ScoreHouseForCitizen(
        Citizen citizen,
        ProjectHouse house,
        Dictionary<(int, int), float> similarityMatrix)
    {
        // ── Signal 1: Namespace string similarity (weight 0.5) ────────────
        float nsScore = ComputeLevenshteinSimilarity(
            citizen.NamespaceFamily ?? string.Empty,
            house.RootNamespace     ?? string.Empty);

        // ── Signal 2: File-dependency proximity (weight 0.5) ──────────────
        // For each file the citizen owns, check how similar it is to the files
        // already tracked in the house. We use the pre-built similarity matrix
        // when the pair of citizen IDs appears; otherwise fall back to the raw
        // Levenshtein similarity on the file paths themselves.
        float depScore = 0f;
        int   depPairs = 0;

        var houseCitizens = _state.Citizens
            .Where(c => c.IsActive && !c.IsHomeless &&
                        c.NamespaceFamily == house.RootNamespace)
            .ToList();

        foreach (var ownedFile in citizen.OwnedFiles)
        {
            foreach (var resident in houseCitizens)
            {
                // Try the pre-built matrix first (keyed by citizen-id pair).
                if (similarityMatrix.TryGetValue((citizen.Id, resident.Id), out float matrixScore) ||
                    similarityMatrix.TryGetValue((resident.Id, citizen.Id), out matrixScore))
                {
                    depScore += matrixScore;
                }
                else
                {
                    // Fall back to direct path similarity for newly created citizens.
                    foreach (var residentFile in resident.OwnedFiles)
                        depScore += ComputeLevenshteinSimilarity(ownedFile, residentFile);
                }
                depPairs++;
            }

            // Also score against the house's tracked FileNodeAssets directly.
            foreach (var asset in house.TrackedFiles)
            {
                depScore += ComputeLevenshteinSimilarity(ownedFile, asset.FilePath);
                depPairs++;
            }
        }

        float normDep = depPairs > 0 ? depScore / depPairs : 0f;

        return 0.5f * nsScore + 0.5f * normDep;
    }

    public void GiftHomelessToCitizen(Citizen homeless, Citizen target)
    {
        foreach (var file in homeless.OwnedFiles)
        {
            if (!target.OwnedFiles.Contains(file))
                target.OwnedFiles.Add(file);
        }
        target.CompliantLinesContributed += homeless.CompliantLinesContributed;
        _state.AddLog($"{homeless.Name} gifted their files to {target.Name} and disappears.");
        homeless.IsActive = false;
        _state.RemoveCitizen(homeless);
    }
}
