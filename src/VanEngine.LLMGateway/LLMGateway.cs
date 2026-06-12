using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;

namespace VanEngine.LLMGateway;

public sealed class LLMGateway : IDisposable
{
    private readonly IBrainClient _brain;
    private readonly int _port;
    private readonly LLMGatewayOptions _options;
    private bool _isRunning;

    public LLMGateway(IBrainClient brain, LLMGatewayOptions options)
    {
        _brain = brain;
        _options = options;
        _port = options.Port;
    }

    public void MapEndpoints(WebApplication app)
    {
        app.MapPost("/v1/chat/completions", HandleChatCompletions);
        app.MapPost("/v1/completions", HandleCompletions);
        app.MapGet("/v1/models", HandleModels);
        app.MapGet("/health", HandleHealth);
    }

    public void StartBanner()
    {
        if (_isRunning)
        {
            return;
        }

        _isRunning = true;
        Console.WriteLine($"[LLMGateway] VAN_Engine Brain available at http://localhost:{_port}");
        Console.WriteLine("[LLMGateway] OpenAI-compatible endpoints:");
        Console.WriteLine("  POST /v1/chat/completions");
        Console.WriteLine("  POST /v1/completions");
        Console.WriteLine("  GET  /v1/models");
        Console.WriteLine($"\nConfigure OpenCode to use: http://localhost:{_port}");
    }

    // ============================================================================
    // Validation Helpers
    // ============================================================================

    private static async Task<(bool isValid, string? query, ChatCompletionRequest? request)> ValidateChatRequest(HttpContext context)
    {
        // Read raw request body for debugging
        string rawBody;
        using (var reader = new StreamReader(context.Request.Body))
        {
            rawBody = await reader.ReadToEndAsync();
        }
        Console.WriteLine($"[LLMGateway] Raw request body: {rawBody}");

        ChatCompletionRequest? request;
        try
        {
            request = JsonSerializer.Deserialize<ChatCompletionRequest>(rawBody);
        }
        catch (JsonException ex)
        {
            Console.WriteLine($"[LLMGateway] JSON parse error: {ex.Message}");
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsJsonAsync(new { error = $"Invalid JSON: {ex.Message}" });
            return (false, null, null);
        }

        if (request == null)
        {
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsJsonAsync(new { error = "Invalid request body" });
            return (false, null, null);
        }

        if (string.IsNullOrEmpty(request.Model))
        {
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsJsonAsync(new { error = "model is required" });
            return (false, null, null);
        }

        if (request.Messages == null || request.Messages.Count == 0)
        {
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsJsonAsync(new { error = "messages array is required" });
            return (false, null, null);
        }

        var lastMessage = request.Messages.LastOrDefault(m => m?.Role == "user");
        var query = lastMessage?.Content ?? request.Prompt ?? string.Empty;

        if (string.IsNullOrWhiteSpace(query))
        {
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsJsonAsync(new { error = "No user message found" });
            return (false, null, null);
        }

        return (true, query, request);
    }

    private static async Task<(bool isValid, string? query, CompletionRequest? request)> ValidateCompletionRequest(HttpContext context)
    {
        // Read raw request body for debugging
        string rawBody;
        using (var reader = new StreamReader(context.Request.Body))
        {
            rawBody = await reader.ReadToEndAsync();
        }
        Console.WriteLine($"[LLMGateway] Raw request body: {rawBody}");

        CompletionRequest? request;
        try
        {
            request = JsonSerializer.Deserialize<CompletionRequest>(rawBody);
        }
        catch (JsonException ex)
        {
            Console.WriteLine($"[LLMGateway] JSON parse error: {ex.Message}");
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsJsonAsync(new { error = $"Invalid JSON: {ex.Message}" });
            return (false, null, null);
        }

        if (request == null)
        {
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsJsonAsync(new { error = "Invalid request body" });
            return (false, null, null);
        }

        if (string.IsNullOrEmpty(request.Model))
        {
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsJsonAsync(new { error = "model is required" });
            return (false, null, null);
        }

        var query = request.Prompt ?? string.Empty;

        if (string.IsNullOrWhiteSpace(query))
        {
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsJsonAsync(new { error = "prompt is required" });
            return (false, null, null);
        }

        return (true, query, request);
    }

    // ============================================================================
    // Endpoint Handlers
    // ============================================================================

    private async Task HandleChatCompletions(HttpContext context)
    {
        Console.WriteLine("[LLMGateway] Received POST /v1/chat/completions");

        if (!context.Request.HasJsonContentType())
        {
            Console.WriteLine("[LLMGateway] Error: No JSON content type");
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsync("Expected JSON body");
            return;
        }

        var (isValid, query, request) = await ValidateChatRequest(context);
        if (!isValid)
        {
            return;
        }

        var result = await _brain.ExecuteQueryAsync(query!, new Dictionary<string, object>
        {
            ["temperature"] = request!.Temperature ?? _options.DefaultTemperature,
            ["max_tokens"] = request.MaxTokens ?? _options.MaxContextLength,
            ["stream"] = request.Stream
        });

        var content = FormatResponse(result, query!);
        var response = new ChatCompletionResponse
        {
            Id = $"chatcmpl-{Guid.NewGuid():N}",
            Object = "chat.completion",
            Created = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
            Model = ResolveModelId(request.Model),
            Choices =
            [
                new Choice
                {
                    Index = 0,
                    Message = new ResponseMessage
                    {
                        Role = "assistant",
                        Content = content
                    },
                    FinishReason = result.Success ? "stop" : "content_filter"
                }
            ],
            Usage = new Usage
            {
                PromptTokens = EstimateTokens(query!),
                CompletionTokens = EstimateTokens(content),
                TotalTokens = EstimateTokens(query!) + EstimateTokens(content)
            }
        };

        if (request.Stream && _options.EnableStreaming)
        {
            await HandleStreamingResponse(context, response);
            return;
        }

        context.Response.ContentType = "application/json";
        await JsonSerializer.SerializeAsync(context.Response.Body, response);
    }

    private async Task HandleStreamingResponse(HttpContext context, ChatCompletionResponse response)
    {
        context.Response.ContentType = "text/event-stream";
        context.Response.Headers["Cache-Control"] = "no-cache";
        context.Response.Headers["Connection"] = "keep-alive";

        var words = response.Choices![0].Message!.Content!.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        foreach (var word in words)
        {
            var chunk = new ChatCompletionChunk
            {
                Id = response.Id,
                Object = "chat.completion.chunk",
                Created = response.Created,
                Model = response.Model,
                Choices =
                [
                    new ChunkChoice
                    {
                        Index = 0,
                        Delta = new DeltaMessage { Content = word + " " },
                        FinishReason = null
                    }
                ]
            };

            var json = JsonSerializer.Serialize(chunk);
            await context.Response.WriteAsync($"data: {json}\n\n");
            await context.Response.Body.FlushAsync();
            await Task.Delay(20);
        }

        var finalChunk = new ChatCompletionChunk
        {
            Id = response.Id,
            Object = "chat.completion.chunk",
            Created = response.Created,
            Model = response.Model,
            Choices =
            [
                new ChunkChoice
                {
                    Index = 0,
                    Delta = new DeltaMessage(),
                    FinishReason = "stop"
                }
            ]
        };

        await context.Response.WriteAsync($"data: {JsonSerializer.Serialize(finalChunk)}\n\n");
        await context.Response.WriteAsync("data: [DONE]\n\n");
    }

    private async Task HandleCompletions(HttpContext context)
    {
        Console.WriteLine("[LLMGateway] Received POST /v1/completions");

        if (!context.Request.HasJsonContentType())
        {
            Console.WriteLine("[LLMGateway] Error: No JSON content type");
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsync("Expected JSON body");
            return;
        }

        var (isValid, query, request) = await ValidateCompletionRequest(context);
        if (!isValid)
        {
            return;
        }

        var result = await _brain.ExecuteQueryAsync(query!);
        var content = FormatResponse(result, query!);

        var response = new CompletionResponse
        {
            Id = $"cmpl-{Guid.NewGuid():N}",
            Object = "text_completion",
            Created = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
            Model = ResolveModelId(request!.Model),
            Choices =
            [
                new CompletionChoice
                {
                    Text = content,
                    Index = 0,
                    FinishReason = result.Success ? "stop" : "content_filter"
                }
            ],
            Usage = new Usage
            {
                PromptTokens = EstimateTokens(query!),
                CompletionTokens = EstimateTokens(content),
                TotalTokens = EstimateTokens(query!) + EstimateTokens(content)
            }
        };

        context.Response.ContentType = "application/json";
        await JsonSerializer.SerializeAsync(context.Response.Body, response);
    }

    private Task HandleModels(HttpContext context)
    {
        var modelIds = _options.ModelIds.Count > 0
            ? _options.ModelIds
            : ["van_engine-brain"];

        var models = new ModelsResponse
        {
            Object = "list",
            Data = modelIds
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .Select(modelId => new ModelInfo
                {
                    Id = modelId,
                    Object = "model",
                    Created = 1_700_000_000,
                    OwnedBy = "VAN_Engine"
                })
                .ToArray()
        };

        context.Response.ContentType = "application/json";
        return JsonSerializer.SerializeAsync(context.Response.Body, models);
    }

    private async Task HandleHealth(HttpContext context)
    {
        try
        {
            var selfTest = _brain.SelfTest();
            context.Response.StatusCode = selfTest.IsValid ? StatusCodes.Status200OK : StatusCodes.Status500InternalServerError;
            await context.Response.WriteAsync(selfTest.IsValid ? "OK" : "Degraded");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[LLMGateway] Health check error: {ex.Message}");
            context.Response.StatusCode = StatusCodes.Status500InternalServerError;
            await context.Response.WriteAsync($"Error: {ex.Message}");
        }
    }

    // ============================================================================
    // Helper Methods
    // ============================================================================

    private string FormatResponse(BrainQueryResult result, string originalQuery)
    {
        if (!result.Success && result.Action == "HALT_AND_CLARIFY")
        {
            var clarification = result.ClarificationQuestions?.FirstOrDefault()
                ?? "I cannot answer with confidence. Please provide more context or rephrase your question.";

            return $"[ISO_010: Drift Gate Triggered]\n{clarification}\n\nConfidence too low to proceed.";
        }

        if (result.Success)
        {
            return result.Message ?? "Query processed successfully.";
        }

        return $"Unable to process: {result.Message ?? "Unknown error"}";
    }

    private static int EstimateTokens(string text)
    {
        if (string.IsNullOrEmpty(text))
        {
            return 0;
        }

        return (int)Math.Ceiling(text.Length / 4.0);
    }

    private string ResolveModelId(string? requestedModel)
    {
        if (!string.IsNullOrWhiteSpace(requestedModel))
        {
            return requestedModel;
        }

        return _options.ModelIds.FirstOrDefault() ?? "van_engine-brain";
    }

    public void Dispose()
    {
        _isRunning = false;
    }
}