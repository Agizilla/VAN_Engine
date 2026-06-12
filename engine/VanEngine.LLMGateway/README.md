# VanEngine.LLMGateway

OpenAI-compatible HTTP gateway for `VanEngine.Core.VAN.VANEngineBrain`.

## What it exposes
- `GET /health`
- `GET /v1/models`
- `POST /v1/completions`
- `POST /v1/chat/completions`

## Notes
- The project uses only the .NET 8 web SDK and the existing `VanEngine.Core` project reference.
- There are no extra gateway-specific NuGet packages.
- The default port is `11434` to match common OpenAI-compatible local tooling.
- Runtime defaults live in `appsettings.json` under the `LLMGateway` section.
- Environment overrides:
  - `VAN_LLMGATEWAY_PORT`
  - `VAN_LLMGATEWAY_MODELS` as a comma-separated list
  - `VAN_LLMGATEWAY_MAX_CONTEXT_LENGTH`
  - `VAN_LLMGATEWAY_DEFAULT_TEMPERATURE`
  - `VAN_LLMGATEWAY_ENABLE_STREAMING`
  - `VAN_LLMGATEWAY_SYSTEM_PROMPT`

## Run
```powershell
dotnet run --project src/VanEngine.LLMGateway/VanEngine.LLMGateway.csproj -- --port 11434
```

## Windows launcher
From the repo root, run:

```powershell
.\run-llm-gateway.cmd
```

You can still pass app arguments through the launcher:

```powershell
.\run-llm-gateway.cmd --port 11500
```
