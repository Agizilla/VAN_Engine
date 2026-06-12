# DeepSeek Handover: VanEngine LLM Gateway

## Purpose
This document hands off the `VanEngine.LLMGateway` work so DeepSeek can finish the remaining improvements without re-discovering the current architecture.

The gateway already works as a local OpenAI-compatible HTTP server for VanEngine, with:
- `GET /health`
- `GET /v1/models`
- `POST /v1/completions`
- `POST /v1/chat/completions`

It currently runs with:
- `appsettings.json` defaults
- environment-variable overrides
- a Windows batch launcher at `run-llm-gateway.cmd`
- a runtime brain adapter that prefers the local `VanEngine.Core.dll` when available and falls back to a mock brain when not

## Current File Map
- `src/VanEngine.LLMGateway/Program.cs`
- `src/VanEngine.LLMGateway/LLMGateway.cs`
- `src/VanEngine.LLMGateway/BrainClient.cs`
- `src/VanEngine.LLMGateway/OpenAiModels.cs`
- `src/VanEngine.LLMGateway/appsettings.json`
- `src/VanEngine.LLMGateway/README.md`
- `run-llm-gateway.cmd`

## Important Behavior
- `Program.cs` builds the web app, reads `LLMGateway:*` config, then applies `VAN_LLMGATEWAY_*` environment overrides.
- `BrainClientFactory` first tries `VAN_ENGINE_CORE_DLL`, then a local fallback path, then a mock brain.
- `LLMGateway` exposes the OpenAI-compatible routes and maps the brain result into OpenAI-style responses.
- `/v1/models` is driven by configured model IDs rather than hardcoded values.
- Streaming is implemented as simple SSE chunking over word boundaries.

## Verified State
- The gateway starts successfully on a free port like `11500`.
- Port `11434` may already be in use on the machine, so the launcher should be treated as a convenience wrapper rather than a port guarantee.
- The gateway no longer needs a compile-time project reference to `VanEngine.Core`.

## What DeepSeek Should Implement Next

### 1. Auto-pick a free port
Make the launcher and/or `Program.cs` choose an available port automatically when `11434` is occupied.

Recommended behavior:
- try `11434` first
- if occupied, scan a small range such as `11435-11550`
- print the chosen port clearly at startup
- keep `VAN_LLMGATEWAY_PORT` and `--port` as explicit overrides

Why this matters:
- removes the most common first-run failure
- avoids manual port hunting
- makes `run-llm-gateway.cmd` safer for casual use

### 2. Improve error handling in the reflection adapter
Harden `BrainClient.cs` so adapter failures are easier to diagnose.

Recommended behavior:
- log whether `VAN_ENGINE_CORE_DLL` was used
- log when fallback to mock brain happens
- surface a clear startup warning if the real brain could not be loaded
- include the exact assembly path that was tried

Why this matters:
- today the fallback is functional, but not transparent enough
- it is easy to misread a mock-backed session as a real VanEngine session

### 3. Add a real health distinction
Make `/health` distinguish between:
- `real brain loaded`
- `mock brain fallback`
- `brain unavailable`

Recommended behavior:
- `200` for real brain
- `206` or `200` with a warning payload for mock mode if you want the server to remain usable
- `503` if the server cannot serve requests at all

Why this matters:
- helps OpenCode or external tooling know whether this is a true VanEngine session
- makes local debugging much easier

### 4. Add response metadata
Enrich the OpenAI-compatible responses with a small amount of gateway metadata.

Recommended behavior:
- include `model` exactly as requested or resolved
- include `usage` consistently on every response
- add a `system_fingerprint` or internal gateway marker if useful
- keep payloads minimal and OpenAI-compatible

Why this matters:
- helps client integrations and debugging
- keeps the gateway predictable when OpenCode inspects responses

### 5. Tighten streaming behavior
The current SSE implementation is acceptable for MVP use, but it is not token-accurate.

Recommended behavior:
- stream more like OpenAI chunk payloads
- preserve whitespace more carefully
- allow disabling streaming entirely through config
- keep a non-stream path identical in meaning to the stream path

Why this matters:
- current word-by-word chunking is fine for demos, but not ideal for tool compatibility
- better chunk shaping reduces client-side edge cases

### 6. Add a proper README quickstart
Expand the gateway README into a real operator guide.

Recommended sections:
- prerequisites
- launch options
- environment variables
- port selection
- real-brain vs mock-brain behavior
- how to point OpenCode at the gateway

Why this matters:
- the handoff is easier for future contributors
- reduces guesswork when someone launches the gateway for the first time

### 7. Decide whether to keep reflection loading
The current approach is intentionally pragmatic, but it is not the cleanest long-term architecture.

You should decide one of two paths:
- keep reflection loading and treat the gateway as a runtime facade
- restore a direct project reference once restore/tooling is stable

Tradeoff:
- reflection loading avoids restore-chain pain today
- direct referencing is cleaner and safer long term

## Known Risks
- `BrainClient.cs` currently falls back to a mock brain if the local assembly cannot be loaded.
- The fallback is useful for developer ergonomics, but it can hide configuration problems if the startup logs are ignored.
- Streaming is simplified and may not match client expectations that assume true token-level chunks.
- The gateway is currently a local development service, not a hardened production daemon.

## Suggested Implementation Order
1. Auto-pick a free port.
2. Improve adapter logging and health status.
3. Tighten streaming shape.
4. Expand the README.
5. Revisit whether reflection loading should remain permanent.

## Acceptance Criteria
DeepSeek can consider the handoff complete when:
- the gateway starts reliably on machines where `11434` is busy
- startup clearly reports whether the real brain or mock fallback is active
- `/health` reflects the actual runtime state
- the README is enough for a new contributor to launch the gateway without asking follow-up questions
- OpenCode can point at the gateway using a stable, documented URL

