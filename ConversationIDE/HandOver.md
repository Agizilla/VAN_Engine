# ConversationIDE / VAN_Engine Handover

## Decision

The Python server is the single source of truth for the active brain.

ConversationIDE stays standalone and separate from the `VAN_Engine` C# runtime.

The C# engine is preserved as a later port target. For now, the Python brain owns:
- chat response generation
- memory capture
- audit/session export
- ISO rule evaluation
- state persistence

The next implementation pass should mirror the engine-facing surface of `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src` into Python where needed, but should not attempt a blind file-for-file copy of every C# file.

## Goals

1. Make the Python brain authoritative.
2. Keep ConversationIDE thin.
3. Export session context into markdown memory events for later C# import.
4. Mirror the engine-facing runtime components from C# to Python in a controlled way.
5. Keep the runtime contract explicit and local-only.

## Non-Goals

1. Do not wire ConversationIDE directly to `VAN_Engine.LLMGateway`.
2. Do not make ConversationIDE depend on the C# runtime at runtime.
3. Do not duplicate UI code from ConversationIDE into Python.
4. Do not port every C# file under `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src` unless it is needed by the active brain.

## Recommended Runtime Topology

### Active runtime

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\api\server.py`
  - local HTTP brain server
  - owns the active session
  - owns chat orchestration
  - imports the Python brain package under `ConversationIDE\src\VanEngine.Core\VAN`

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\VanEngine.Core\VAN\`
  - Python implementation of the active brain runtime
  - source of truth for brain logic during this phase

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\renderer\`
  - UI only
  - must remain a thin client

### Preserved reference runtime

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\`
  - C# reference implementation
  - do not modify unless explicitly asked
  - use as the semantic source for the Python mirror

## What the Python server must own

The Python server must be the only process that ConversationIDE calls for chat.

It must:
- accept chat messages over HTTP
- produce OpenAI-compatible `v1/chat/completions` responses
- keep brain state in memory for the active session
- persist session exports
- write audit entries
- expose health and status endpoints
- optionally call the local LLM gateway later, but only through the Python server contract

## Files already created in this phase

These files currently exist in the ConversationIDE tree and are the base of the Python brain:

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\VanEngine.Core\VAN\__init__.py`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\VanEngine.Core\VAN\enums.py`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\VanEngine.Core\VAN\envelope.py`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\VanEngine.Core\VAN\results.py`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\VanEngine.Core\VAN\memory.py`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\VanEngine.Core\VAN\state.py`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\VanEngine.Core\VAN\brain.py`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\VanEngine.Core\VAN\engine.py`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\api\server.py`

The next LLM should inspect these files before adding more code so it can extend the current implementation instead of rewriting it.

## C# Source Files To Mirror First

Mirror these C# files first because they define the active brain semantics:

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\VANEngineBrain.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\VanEngine.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\VanEnvelope.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\DomainResults.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\VanBlockType.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\ProcessingMode.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\State\VanStateEngine.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\State\MemoryStore.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Compiler\Lexer\Token.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Compiler\Lexer\VanLexer.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Compiler\Parser\VanParser.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Compiler\Runtime\VanContext.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Compiler\Runtime\CortexRuntime.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Security\RighteousnessFilter.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Audit\AuditLog.cs`

## Porting Strategy

Do not copy the full `src` tree blindly.

Instead:
1. Identify the C# files required for active brain operation.
2. Create Python equivalents under `ConversationIDE\src\VanEngine.Core\VAN\`.
3. Keep names and responsibilities close to the C# originals where practical.
4. Preserve stable file boundaries for the parts that ConversationIDE will depend on.
5. Defer non-brain files until the active runtime proves stable.

## Target Python File Layout

Create or extend the following Python files in:

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\VanEngine.Core\VAN\`

Recommended modules:

- `brain.py`
  - `VANEngineBrain`
  - `QueryResult`
  - `SelfTestResult`
  - `BrainStats`
  - `BrainAuditEvent`

- `engine.py`
  - `VanEngine`
  - runtime processing methods
  - compliance / governance hooks
  - parser entry points
  - format conversion helpers

- `envelope.py`
  - `VanEnvelope`

- `enums.py`
  - `VanBlockType`
  - `ProcessingMode`

- `results.py`
  - `GCodePoint`
  - `LlmAttentionResult`
  - `GCodeResult`
  - `PixelPhaseResult`
  - `SteelResonanceResult`
  - `VoiceSynthesisResult`
  - `PersonaResult`
  - `VanSpectrogram`

- `memory.py`
  - `MemoryStore`
  - `MemoryEntry`

- `state.py`
  - `VanStateEngine`

- `lexer.py`
  - Python port of `Token`, `TokenType`, and lexer behavior from `Compiler\Lexer\Token.cs` and `Compiler\Lexer\VanLexer.cs`

- `parser.py`
  - Python port of `VanParser` from `Compiler\Parser\VanParser.cs`

- `runtime.py`
  - Python port of `VanContext` and `CortexRuntime`

- `audit.py`
  - Python port of `AuditLog`

- `security.py`
  - Python port of `RighteousnessFilter`

If the implementation needs additional helper modules, add them only if they are strictly required for parity with the C# behavior.

## Export Format Requirement

The Python brain must export session context in markdown form so the C# runtime can import it later.

Create a deterministic export file in a dedicated folder such as:

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\memoryEvents\`

Recommended export filename pattern:

- `session_YYYYMMDD_HHMMSS.md`

Each export should include:
- timestamp
- session id
- user prompt
- assistant response
- active ISO rules
- memory references
- audit summary
- optional parser/runtime diagnostics

Do not store export data only in ephemeral memory.

## Suggested Markdown Export Schema

Each memory event file should include these sections in order:

1. `# Session Memory Event`
2. `## Metadata`
3. `## User Prompt`
4. `## Brain Response`
5. `## ISO State`
6. `## Memory Hits`
7. `## Audit Trail`
8. `## Diagnostics`
9. `## Next Actions`

Keep the format stable so the future C# importer can parse it without ambiguity.

## Python Server Contract

The Python server at:

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\api\server.py`

must expose at minimum:

- `GET /health`
- `GET /status`
- `POST /v1/chat/completions`
- `POST /v1/session/export`
- `POST /v1/memory/index`
- `POST /v1/memory/search`
- `POST /v1/audit`

### `/v1/chat/completions`

Must accept OpenAI-style payloads:

- `model`
- `messages`
- `stream`

Must return:
- `id`
- `object`
- `created`
- `model`
- `choices[0].message.role`
- `choices[0].message.content`
- `choices[0].finish_reason`
- `usage`
- `metadata`

### Response behavior

The chat handler should:
1. read the latest user message
2. create or update the active brain session
3. route the message through `VANEngineBrain`
4. optionally query the local LLM gateway only if the brain decides it is necessary
5. persist the session event
6. return the assistant response to ConversationIDE

## ConversationIDE Integration Rules

ConversationIDE should only call the Python server.

The IDE must not:
- call the LLM gateway directly
- call C# brain code directly
- own memory logic
- own audit logic

ConversationIDE should only:
- start the Python server if needed
- send chat requests
- render returned state
- show health/status indicators

Relevant ConversationIDE files:

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\main\index.ts`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\main\ipc\chat.ts`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\renderer\store\chatStore.ts`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\renderer\components\Chat\ChatPanel.tsx`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ConversationIDE\src\renderer\components\Status\StatusBar.tsx`

## Startup Order

Implement startup in this order:

1. ConversationIDE launches.
2. ConversationIDE starts the Python server if it is not already running.
3. Python server loads the Python brain package.
4. Python brain loads any local state and ISO rule data.
5. Python server answers `/health` and `/status`.
6. ConversationIDE enables chat input.
7. First chat message is routed through the Python server.
8. Python server writes a memory event markdown file.
9. Python server returns the assistant response.

## Porting Priority

If the next LLM is porting more files from C# to Python, use this order:

### Phase 1: Brain identity and session state

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\VANEngineBrain.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\VanEngine.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\VanEnvelope.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\State\VanStateEngine.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\State\MemoryStore.cs`

### Phase 2: Parsing and runtime

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Compiler\Lexer\Token.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Compiler\Lexer\VanLexer.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Compiler\Parser\VanParser.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Compiler\Runtime\VanContext.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Compiler\Runtime\CortexRuntime.cs`

### Phase 3: Governance and audit

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Security\RighteousnessFilter.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Audit\AuditLog.cs`

### Phase 4: Remaining supportive types

- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\DomainResults.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\FryasAlphabet.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\FryasComplianceEngine.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\FryasDirective.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\GardenConfig.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\JuulLexer.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\JuulMask.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\Metrics.cs`
- `C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\src\VanEngine.Core\VAN\TelemetryGuard.cs`

## Required Implementation Behaviors

### Brain identity

- `VANEngineBrain` should be a singleton.
- It should own token storage, audit events, and uptime tracking.
- It should expose methods similar to the C# version:
  - `ExecuteQueryAsync`
  - `SelfTest`
  - `GetStats`
  - `StoreToken`
  - `LookupToken`
  - `GetAuditTrail`

### Session export

- Every response should optionally produce a markdown event file.
- A session export must be deterministic and human-readable.
- Later C# code should be able to import the markdown without needing the IDE.

### Status reporting

- `/status` should report:
  - brain ready state
  - ISO availability
  - memory count
  - audit count
  - uptime
  - current model or gateway state if applicable

### Error handling

- If the gateway is unavailable, the Python server should still respond with a clear degraded-mode result.
- Do not crash the brain for non-fatal gateway errors.
- Return structured diagnostics in the response payload.

## Code Style Notes

- Keep the Python code modular.
- Prefer explicit dataclasses for return values.
- Keep file names stable and predictable.
- Use ASCII unless there is a compelling reason otherwise.
- Avoid collapsing unrelated concerns into one giant file.

## Verification Checklist

Before considering the pass complete, verify:

1. `ConversationIDE` starts the Python server automatically.
2. `GET /health` returns OK.
3. `GET /status` returns a useful brain summary.
4. `POST /v1/chat/completions` works with a minimal `messages` array.
5. A chat response produces a `memoryEvent.md` export.
6. The status bar shows brain state clearly.
7. The Python brain package imports cleanly.
8. ConversationIDE still stays separate from `VAN_Engine` runtime code.

## Suggested Next Implementation Steps

1. Expand `api/server.py` to expose the full brain contract.
2. Port the remaining required C# runtime files into `ConversationIDE\src\VanEngine.Core\VAN\`.
3. Add markdown session export helpers.
4. Add status and memory endpoints.
5. Update ConversationIDE UI to render the richer brain state.
6. Keep the C# engine untouched until the Python runtime is stable.

## Final Note

The objective of this phase is not to recreate the entire C# ecosystem immediately.

The objective is to make the Python brain authoritative, stable, and explicit, with a clean export path for later backporting into C#.
