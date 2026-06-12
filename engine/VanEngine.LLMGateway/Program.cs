using VanEngine.LLMGateway;
using VanEngine.Core.VAN;
using VanEngine.Core.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
        policy.AllowAnyHeader()
              .AllowAnyMethod()
              .AllowAnyOrigin());
});

// Register VAN_Engine services
builder.Services.AddSingleton(_ => VANEngineBrain.Instance);
builder.Services.AddSingleton(svc => svc.GetRequiredService<VANEngineBrain>().InferenceService);
builder.Services.AddSingleton<TranscriptParser>(_ => new TranscriptParser(""));
builder.Services.AddSingleton<SkillLoader>(_ => new SkillLoader(Environment.CurrentDirectory));
builder.Services.AddSingleton<WisdomDomainClassifier>(_ => new WisdomDomainClassifier(Environment.CurrentDirectory));
builder.Services.AddSingleton<ActivityParser>(_ => new ActivityParser(Environment.CurrentDirectory));

var app = builder.Build();
app.UseCors();

var gatewayOptions = new LLMGatewayOptions
{
    Port = 11434
};


var portSetting = builder.Configuration["LLMGateway:Port"];
if (int.TryParse(portSetting, out var configuredPort))
{
    gatewayOptions.Port = configuredPort;
}

var configuredModels = builder.Configuration.GetSection("LLMGateway:Models").Get<string[]>();
if (configuredModels is { Length: > 0 })
{
    gatewayOptions.ModelIds = configuredModels.Where(model => !string.IsNullOrWhiteSpace(model)).ToList();
}

var maxContextLengthSetting = builder.Configuration["LLMGateway:MaxContextLength"];
if (int.TryParse(maxContextLengthSetting, out var configuredMaxContext))
{
    gatewayOptions.MaxContextLength = configuredMaxContext;
}

var temperatureSetting = builder.Configuration["LLMGateway:DefaultTemperature"];
if (double.TryParse(temperatureSetting, out var configuredTemperature))
{
    gatewayOptions.DefaultTemperature = configuredTemperature;
}

var streamingSetting = builder.Configuration["LLMGateway:EnableStreaming"];
if (bool.TryParse(streamingSetting, out var configuredStreaming))
{
    gatewayOptions.EnableStreaming = configuredStreaming;
}

var systemPrompt = builder.Configuration["LLMGateway:SystemPrompt"];
if (!string.IsNullOrWhiteSpace(systemPrompt))
{
    gatewayOptions.SystemPrompt = systemPrompt;
}

ApplyEnvironmentOverrides(gatewayOptions);

var port = gatewayOptions.Port;
if (args.Length > 0)
{
    for (int i = 0; i < args.Length; i++)
    {
        if (args[i] == "--port" && i + 1 < args.Length && int.TryParse(args[i + 1], out var parsedPort))
        {
            port = parsedPort;
        }
    }
}

gatewayOptions.Port = port;

var gateway = new LLMGateway(BrainClientFactory.CreateDefault(), gatewayOptions);
gateway.MapEndpoints(app);
gateway.StartBanner();

await app.RunAsync($"http://0.0.0.0:{port}");

static void ApplyEnvironmentOverrides(LLMGatewayOptions gatewayOptions)
{
    var portSetting = Environment.GetEnvironmentVariable("VAN_LLMGATEWAY_PORT");
    if (int.TryParse(portSetting, out var configuredPort))
    {
        gatewayOptions.Port = configuredPort;
    }

    var modelListSetting = Environment.GetEnvironmentVariable("VAN_LLMGATEWAY_MODELS");
    if (!string.IsNullOrWhiteSpace(modelListSetting))
    {
        var models = modelListSetting
            .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Where(model => !string.IsNullOrWhiteSpace(model))
            .ToList();

        if (models.Count > 0)
        {
            gatewayOptions.ModelIds = models;
        }
    }

    var maxContextLengthSetting = Environment.GetEnvironmentVariable("VAN_LLMGATEWAY_MAX_CONTEXT_LENGTH");
    if (int.TryParse(maxContextLengthSetting, out var configuredMaxContext))
    {
        gatewayOptions.MaxContextLength = configuredMaxContext;
    }

    var temperatureSetting = Environment.GetEnvironmentVariable("VAN_LLMGATEWAY_DEFAULT_TEMPERATURE");
    if (double.TryParse(temperatureSetting, out var configuredTemperature))
    {
        gatewayOptions.DefaultTemperature = configuredTemperature;
    }

    var streamingSetting = Environment.GetEnvironmentVariable("VAN_LLMGATEWAY_ENABLE_STREAMING");
    if (bool.TryParse(streamingSetting, out var configuredStreaming))
    {
        gatewayOptions.EnableStreaming = configuredStreaming;
    }

    var systemPrompt = Environment.GetEnvironmentVariable("VAN_LLMGATEWAY_SYSTEM_PROMPT");
    if (!string.IsNullOrWhiteSpace(systemPrompt))
    {
        gatewayOptions.SystemPrompt = systemPrompt;
    }
}
