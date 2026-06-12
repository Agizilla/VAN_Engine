namespace VanEngine.Game.Forensics;

public struct Overlap
{
    public Guid Workspace1 { get; set; }
    public Guid Workspace2 { get; set; }
    public string File1 { get; set; }
    public string File2 { get; set; }
    public float Similarity { get; set; }
}

public static class OverlapDetector
{
    public static List<Overlap> FindDuplications(Dictionary<Guid, List<string>> workspaceFiles)
    {
        var overlaps = new List<Overlap>();
        var allFiles = new List<(Guid wsId, string file)>();

        foreach (var (wsId, files) in workspaceFiles)
            foreach (var f in files)
                allFiles.Add((wsId, f));

        for (int i = 0; i < allFiles.Count; i++)
        {
            for (int j = i + 1; j < allFiles.Count; j++)
            {
                if (allFiles[i].wsId == allFiles[j].wsId) continue;

                float sim = ComputeLevenshteinSimilarity(allFiles[i].file, allFiles[j].file);
                if (sim > 0.8f)
                {
                    overlaps.Add(new Overlap
                    {
                        Workspace1 = allFiles[i].wsId,
                        Workspace2 = allFiles[j].wsId,
                        File1 = allFiles[i].file,
                        File2 = allFiles[j].file,
                        Similarity = sim
                    });
                }
            }
        }
        return overlaps;
    }

    public static float ComputeLevenshteinSimilarity(string a, string b)
    {
        if (string.IsNullOrEmpty(a) || string.IsNullOrEmpty(b)) return 0;
        int dist = LevenshteinDistance(a, b);
        return 1.0f - (float)dist / Math.Max(a.Length, b.Length);
    }

    public static int LevenshteinDistance(string s, string t)
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
}
