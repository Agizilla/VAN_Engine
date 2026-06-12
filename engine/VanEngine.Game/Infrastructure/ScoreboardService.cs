using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using VanEngine.Game.Core;

namespace VanEngine.Game.Infrastructure;

public sealed class ScoreToken
{
    public string PlayerName { get; set; } = "Anonymous";
    public int Year { get; set; }
    public double Sovereignty { get; set; }
    public double LanguagePurity { get; set; }
    public int TotalCompliantLines { get; set; }
    public int CitizenCount { get; set; }
    public int HouseCount { get; set; }
    public int TotalWealth { get; set; }
    public int TotalFood { get; set; }
    public string Signature { get; set; } = string.Empty;
    public string Timestamp { get; set; } = string.Empty;
}

public sealed class ScoreboardService
{
    private const string SigningKey = "OeraLindaSimScore_v1_secret";
    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        WriteIndented = true,
        IncludeFields = true,
    };

    public static ScoreToken GenerateToken(SovereignState state, string playerName = "Anonymous")
    {
        var res = state.Resources;
        var token = new ScoreToken
        {
            PlayerName = playerName,
            Year = state.Year,
            Sovereignty = state.Sovereignty,
            LanguagePurity = state.LanguagePurity,
            TotalCompliantLines = state.TotalCompliantLines,
            CitizenCount = state.Citizens.Count,
            HouseCount = state.Houses.Count,
            TotalWealth = res.Wealth + res.Gold,
            TotalFood = res.Food,
            Timestamp = DateTime.Now.ToString("O"),
        };
        token.Signature = ComputeSignature(token);
        return token;
    }

    public static string ExportTokenJson(SovereignState state, string playerName = "Anonymous")
    {
        var token = GenerateToken(state, playerName);
        return JsonSerializer.Serialize(token, JsonOpts);
    }

    public static void SaveToken(SovereignState state, string? filePath = null, string playerName = "Anonymous")
    {
        filePath ??= Path.Combine(
            Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "scoreboard"),
            $"score_{DateTime.Now:yyyyMMdd_HHmmss}.json");
        Directory.CreateDirectory(Path.GetDirectoryName(filePath)!);
        File.WriteAllText(filePath, ExportTokenJson(state, playerName));
    }

    public static bool VerifyToken(string json)
    {
        try
        {
            var token = JsonSerializer.Deserialize<ScoreToken>(json, JsonOpts);
            if (token == null) return false;

            string expectedSig = ComputeSignature(token);
            return token.Signature == expectedSig;
        }
        catch
        {
            return false;
        }
    }

    public static async Task<bool> SubmitToLeaderboard(string json, string leaderboardUrl = "https://example.com/api/score")
    {
        try
        {
            using var client = new HttpClient();
            client.Timeout = TimeSpan.FromSeconds(10);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var response = await client.PostAsync(leaderboardUrl, content);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private static string ComputeSignature(ScoreToken token)
    {
        string payload = $"{token.PlayerName}|{token.Year}|{token.Sovereignty:F2}|{token.LanguagePurity:F2}|{token.TotalCompliantLines}|{token.Timestamp}|{SigningKey}";
        byte[] hash = SHA256.HashData(Encoding.UTF8.GetBytes(payload));
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    public static string GetDefaultScoreDir()
    {
        var dir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "scoreboard");
        Directory.CreateDirectory(dir);
        return dir;
    }
}
