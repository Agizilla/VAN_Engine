// VAN_Engine.WinForms/Services/BrainBridge.cs
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace VanEngine.WinForms.Services;

public class BrainBridge
{
    private readonly HttpClient _httpClient;
    private const string BaseUrl = "http://localhost:11434";

    public BrainBridge()
    {
        _httpClient = new HttpClient();
        _httpClient.Timeout = TimeSpan.FromSeconds(60);
    }

    public async Task<BrainStatus> GetStatusAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{BaseUrl}/health");
            if (response.IsSuccessStatusCode)
            {
                return new BrainStatus { Available = true, TokenCount = 0 };
            }
        }
        catch { }
        return new BrainStatus { Available = false };
    }

    public async Task<QueryResponse> QueryAsync(string query)
    {
        var request = new
        {
            model = "van_engine-brain",
            messages = new[] { new { role = "user", content = query } },
            stream = false
        };

        var content = new StringContent(
            JsonSerializer.Serialize(request),
            Encoding.UTF8,
            "application/json"
        );

        try
        {
            var response = await _httpClient.PostAsync($"{BaseUrl}/v1/chat/completions", content);
            var responseText = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                var data = JsonSerializer.Deserialize<ChatResponse>(responseText);
                return new QueryResponse
                {
                    Success = true,
                    Message = data?.Choices?.FirstOrDefault()?.Message?.Content ?? "No response",
                    Action = "EXECUTE",
                    Confidence = 0.95
                };
            }

            return new QueryResponse
            {
                Success = false,
                Message = $"API Error: {response.StatusCode}",
                Action = "ERROR",
                Confidence = 0
            };
        }
        catch (HttpRequestException)
        {
            return new QueryResponse
            {
                Success = false,
                Message = "⚠️ VAN_Engine API not reachable at http://localhost:11434\n\nStart the brain with: dotnet run --project ../VAN_Engine",
                Action = "ERROR",
                Confidence = 0
            };
        }
    }
}

public class BrainStatus
{
    public bool Available { get; set; }
    public int TokenCount { get; set; }
}

public class QueryResponse
{
    public bool Success { get; set; }
    public string Message { get; set; } = "";
    public string Action { get; set; } = "";
    public double Confidence { get; set; }
}

public class ChatResponse
{
    public Choice[]? Choices { get; set; }
}

public class Choice
{
    public Message? Message { get; set; }
}

public class Message
{
    public string? Content { get; set; }
}