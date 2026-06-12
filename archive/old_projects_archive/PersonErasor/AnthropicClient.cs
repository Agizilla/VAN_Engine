using System.Net.Http.Json;
using System.Runtime.Serialization;
using System.Text.Json;
using System.Text.Json.Serialization;
using SovereignIDE.Core.Exceptions;

namespace SovereignIDE.Core.AI;

#region Models

public record Message(
    [property: JsonPropertyName("role")] string Role,
    [property: JsonPropertyName("content")] string Content
);

public record ContentBlock(
    [property: JsonPropertyName("type")] string Type,
    [property: JsonPropertyName("text")] string? Text
);

public record Usage(
    [property: JsonPropertyName("input_tokens")] int InputTokens,
    [property: JsonPropertyName("output_tokens")] int OutputTokens
);

public record MessageResponse(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("type")] string Type,
    [property: JsonPropertyName("role")] string Role,
    [property: JsonPropertyName("content")] List<ContentBlock> Content,
    [property: JsonPropertyName("model")] string Model,
    [property: JsonPropertyName("stop_reason")] string? StopReason,
    [property: JsonPropertyName("usage")] Usage Usage
);

public record StreamEvent(
    [property: JsonPropertyName("type")] string Type,
    [property: JsonPropertyName("delta")] JsonElement? Delta = null,
    [property: JsonPropertyName("message")] MessageResponse? Message = null
);

#endregion

/// <summary>
/// Anthropic API client with retry logic and streaming support.
/// Matches Python SDK functionality, fully implemented in C#.
/// </summary>
public class AnthropicClient : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly string _apiKey;
    private readonly int _maxRetries;
    private readonly TimeSpan _timeout;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) }
    };

    /// <summary>
    /// Creates Anthropic API client.
    /// </summary>
    /// <param name="apiKey">Anthropic API key (sk-ant-...)</param>
    /// <param name="baseUrl">API base URL</param>
    /// <param name="timeout">Request timeout</param>
    /// <param name="maxRetries">Max retry attempts on failure</param>
    public AnthropicClient(
        string apiKey,
        string baseUrl = "https://api.anthropic.com",
        TimeSpan? timeout = null,
        int maxRetries = 2)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(apiKey, nameof(apiKey));

        _apiKey = apiKey;
        _maxRetries = maxRetries;
        _timeout = timeout ?? TimeSpan.FromSeconds(600);

        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(baseUrl),
            Timeout = _timeout
        };

        _httpClient.DefaultRequestHeaders.Add("x-api-key", _apiKey);
        _httpClient.DefaultRequestHeaders.Add("anthropic-version", "2023-06-01");
    }

    /// <summary>
    /// Create a message with automatic retry logic.
    /// 
    /// Contract:
    /// - model MUST be valid Anthropic model string
    /// - messages MUST be non-empty list
    /// - maxTokens MUST be positive
    /// - temperature MUST be 0.0-1.0
    /// </summary>
    /// <exception cref="ArgumentException">Invalid parameters</exception>
    /// <exception cref="SovereignException">API or network error</exception>
    public async Task<MessageResponse> CreateMessageAsync(
        string model,
        List<Message> messages,
        int maxTokens = 1024,
        double temperature = 1.0,
        string? system = null,
        List<string>? stopSequences = null,
        CancellationToken cancellationToken = default)
    {
        // Contract validation
        ArgumentException.ThrowIfNullOrWhiteSpace(model, nameof(model));
        ArgumentNullException.ThrowIfNull(messages, nameof(messages));

        if (messages.Count == 0)
            throw new ArgumentException("Messages cannot be empty", nameof(messages));

        if (maxTokens <= 0)
            throw new ArgumentException("MaxTokens must be positive", nameof(maxTokens));

        if (temperature < 0.0 || temperature > 1.0)
            throw new ArgumentException("Temperature must be between 0.0 and 1.0", nameof(temperature));

        var payload = new Dictionary<string, object>
        {
            ["model"] = model,
            ["messages"] = messages,
            ["max_tokens"] = maxTokens,
            ["temperature"] = temperature
        };

        if (!string.IsNullOrWhiteSpace(system))
            payload["system"] = system;

        if (stopSequences?.Count > 0)
            payload["stop_sequences"] = stopSequences;

        // Retry logic with exponential backoff
        for (int attempt = 0; attempt <= _maxRetries; attempt++)
        {
            try
            {
                var response = await _httpClient.PostAsJsonAsync(
                    "/v1/messages",
                    payload,
                    JsonOptions,
                    cancellationToken
                );

                // Handle rate limiting
                if (response.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
                {
                    if (attempt == _maxRetries)
                    {
                        var error = await response.Content.ReadAsStringAsync(cancellationToken);
                        throw new ExecutionException(
                            $"Rate limit exceeded: {error}",
                            "Anthropic API rate limit",
                            "api-call"
                        );
                    }

                    // Exponential backoff
                    var waitTime = TimeSpan.FromSeconds(Math.Pow(2, attempt));
                    await Task.Delay(waitTime, cancellationToken);
                    continue;
                }

                // Handle other errors
                if (!response.IsSuccessStatusCode)
                {
                    var error = await response.Content.ReadAsStringAsync(cancellationToken);
                    throw new ExecutionException(
                        $"API error ({response.StatusCode}): {error}",
                        "Anthropic API request failed",
                        "api-call"
                    );
                }

                var result = await response.Content.ReadFromJsonAsync<MessageResponse>(
                    JsonOptions,
                    cancellationToken
                );

                return result ?? throw new ExecutionException(
                    "Empty response from API",
                    "Anthropic API returned null",
                    "api-call"
                );
            }
            catch (HttpRequestException ex) when (attempt < _maxRetries)
            {
                // Network error - retry after 1 second
                await Task.Delay(TimeSpan.FromSeconds(1), cancellationToken);
            }
            catch (TaskCanceledException) when (!cancellationToken.IsCancellationRequested)
            {
                // Timeout
                throw new ProcessTimeoutException(
                    "Request timed out",
                    (int)_timeout.TotalSeconds,
                    "Anthropic API request"
                );
            }
        }

        throw new ExecutionException(
            "Max retries exceeded",
            $"Failed after {_maxRetries + 1} attempts",
            "api-call"
        );
    }

    /// <summary>
    /// Stream message responses using Server-Sent Events.
    /// </summary>
    public async IAsyncEnumerable<StreamEvent> CreateMessageStreamAsync(
        string model,
        List<Message> messages,
        int maxTokens = 1024,
        double temperature = 1.0,
        string? system = null,
        List<string>? stopSequences = null,
        CancellationToken cancellationToken = default)
    {
        // Contract validation (same as CreateMessageAsync)
        ArgumentException.ThrowIfNullOrWhiteSpace(model, nameof(model));
        ArgumentNullException.ThrowIfNull(messages, nameof(messages));

        if (messages.Count == 0)
            throw new ArgumentException("Messages cannot be empty", nameof(messages));

        var payload = new Dictionary<string, object>
        {
            ["model"] = model,
            ["messages"] = messages,
            ["max_tokens"] = maxTokens,
            ["temperature"] = temperature,
            ["stream"] = true
        };

        if (!string.IsNullOrWhiteSpace(system))
            payload["system"] = system;

        if (stopSequences?.Count > 0)
            payload["stop_sequences"] = stopSequences;

        var request = new HttpRequestMessage(HttpMethod.Post, "/v1/messages")
        {
            Content = JsonContent.Create(payload, options: JsonOptions)
        };

        var response = await _httpClient.SendAsync(
            request,
            HttpCompletionOption.ResponseHeadersRead,
            cancellationToken
        );

        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync(cancellationToken);
            throw new ExecutionException(
                $"API error ({response.StatusCode}): {error}",
                "Anthropic streaming request failed",
                "api-stream"
            );
        }

        using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        using var reader = new StreamReader(stream);

        while (!reader.EndOfStream)
        {
            var line = await reader.ReadLineAsync(cancellationToken);

            if (string.IsNullOrWhiteSpace(line))
                continue;

            if (line.StartsWith("data: "))
            {
                var dataStr = line.Substring(6); // Remove "data: " prefix

                if (dataStr == "[DONE]")
                    break;

                StreamEvent? streamEvent;
                try
                {
                    streamEvent = JsonSerializer.Deserialize<StreamEvent>(dataStr, JsonOptions);
                }
                catch (JsonException)
                {
                    // Malformed JSON - skip
                    continue;
                }

                if (streamEvent != null)
                    yield return streamEvent;
            }
        }
    }

    public void Dispose()
    {
        _httpClient?.Dispose();
    }
}
