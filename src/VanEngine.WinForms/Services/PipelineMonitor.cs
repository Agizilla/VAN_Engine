using System.Net.Http;
using System.Text;
using System.Text.Json;
using VanEngine.WinForms.Models;

namespace VanEngine.WinForms.Services;

public class PipelineMonitor
{
    private readonly HttpClient _httpClient;
    private const string BaseUrl = "http://localhost:8765";

    public PipelineMonitor()
    {
        _httpClient = new HttpClient();
        _httpClient.Timeout = TimeSpan.FromSeconds(10);
    }

    public async Task<List<PipelineExecution>> GetExecutionsAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{BaseUrl}/api/executions");
            if (response.IsSuccessStatusCode)
            {
                var json = await response.Content.ReadAsStringAsync();
                var data = JsonSerializer.Deserialize<ExecutionsResponse>(json);
                return data?.Executions ?? new List<PipelineExecution>();
            }
        }
        catch { }
        return new List<PipelineExecution>();
    }

    public async Task<string?> StartPipelineAsync(string pipeline, string agent, List<StepExecution> steps)
    {
        try
        {
            var request = new { pipeline, agent, steps = steps.Select(s => new { s.Id, s.Action }) };
            var content = new StringContent(JsonSerializer.Serialize(request), Encoding.UTF8, "application/json");
            var response = await _httpClient.PostAsync($"{BaseUrl}/api/start", content);
            if (response.IsSuccessStatusCode)
            {
                var json = await response.Content.ReadAsStringAsync();
                var data = JsonSerializer.Deserialize<StartResponse>(json);
                return data?.Id;
            }
        }
        catch { }
        return null;
    }

    public async Task UpdatePipelineAsync(string id, string status, string? result = null, string? error = null)
    {
        try
        {
            var request = new { id, status, result, error };
            var content = new StringContent(JsonSerializer.Serialize(request), Encoding.UTF8, "application/json");
            await _httpClient.PostAsync($"{BaseUrl}/api/update", content);
        }
        catch { }
    }

    public async Task<bool> CheckHealthAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{BaseUrl}/health");
            return response.IsSuccessStatusCode;
        }
        catch { return false; }
    }
}

public class ExecutionsResponse
{
    public List<PipelineExecution> Executions { get; set; } = new();
}

public class StartResponse
{
    public string? Id { get; set; }
}
