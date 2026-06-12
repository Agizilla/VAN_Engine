# Session State Backup — 2026-06-09

**Purpose:** Token-cap recovery context. If compaction hits, read this first.

---

## Current Architecture

```
┌─ Browser Tab (DeepSeek/Gemini/Claude)
│  paste clawdia-harness.js → window.clawdia
│  clawdia.trust(), .chat(), .speak(), .recover()
│
├─ ClawdiaBridge :55555 (Node.js, server.js)
│  ├─ /api/v1/trust/check         GET  — trust score
│  ├─ /api/v1/trust/penalty       POST — ban a session
│  ├─ /api/v1/trust/ledger        GET  — immutable chain
│  ├─ /clawdia/collective         POST — contribute sessions
│  ├─ /api/v1/peer/register       POST — P2P mesh
│  ├─ /api/v1/peer/sync           POST — gossip relay
│  ├─ /api/v1/peers               GET  — list mesh
│  ├─ /api/v1/skills              GET  — list UNR skills
│  ├─ /api/v1/image/transform     POST — Sharp/Python transforms
│  ├─ /audio/synthesize           POST — TTS via voice-server:8888
│  ├─ /clawdia-harness.js         GET  — browser injection script
│  └─ WebSocket / SCADA sim
│
├─ FastAPI Brain :44444 (PY server.py)
│  ├─ /v1/chat/completions        POST — LLM chat
│  ├─ /api/v1/skills              GET  — list skills
│  ├─ /api/v1/image/transform     POST — Pillow/Python transforms
│  ├─ /api/v1/peers, /peer/*      P2P mesh (in-memory)
│  └─ reads ports from config/ports.json
│
└─ Voice Server :8888 (external)
   └─ /synthesize                  TTS
```

## Key Files

| File | Lines | Purpose |
|---|---|---|
| `Services/ClawdiaBridge/server.js` | 1166 | Main Node server — all endpoints |
| `api/server.py` | 911 | FastAPI brain — chat, image, P2P |
| `Services/ClawdiaBridge/public/clawdia-harness.js` | 436 | Browser injection (unified) |
| `docs/CODING_STANDARDS.md` | 76 | Project coding rules |
| `docs/MASTER_COLLECTIVE_ROADMAP.html` | — | Full roadmap |
| `docs/security-audit-package.md` | — | All source code for DeepSeek audit |
| `docker-compose.yml` | 21 | Container deployment |

## Databases

- `Services/ClawdiaBridge/data/clawdia.db` — SQLite with tables:
  - `messages` — clawdia inbox
  - `skills_catalog` — UNR skills seeded from markdown
  - `collective_sessions` — contributions with `trust_score`, `banned_until`, etc.
  - `peers` — P2P mesh peers
  - `audio_queue` — synthesized audio
  - `immutable_ledger` — SHA256-chained trust actions
- FastAPI: in-memory `_peers` dict (no persistence)

## Security Audit Results

**Auditor:** DeepSeek Web-UI  
**Status:** ✅ DEPLOYMENT CLEARANCE — UNCONDITIONALLY GRANTED  
**Signature:** a3f5c2e1b8d9  
**Date:** 2026-06-09  
**Audit document:** `docs/security-audit-package.md`

| Component | Status |
|---|---|
| `enforceTrust` middleware | ✅ APPROVED |
| Immutable ledger hash chaining | ✅ APPROVED |
| Voice IDs via env vars | ✅ SECURE |
| SQLite UNIQUE constraint | ✅ DATA INTEGRITY |
| Penalty ledger with hash chain | ✅ CONSISTENT |

## Security Issues Fixed This Session

1. **collective scope bug**: `data` referenced outside `readBody().then()` → moved gossip inside callback
2. **TTS shell injection**: `emotion` sanitized with `/[^a-zA-Z0-9_-]/g` before `execSync`
3. **Voice IDs hardcoded** → moved to `process.env.CLAWDIA_VOICE_*` with fallbacks
4. **Missing trust middleware** → added `enforceTrust()` — checks `banned_until` + trust < 10 → 403
5. **Immutable ledger missing hash chain** → added `previous_hash` column, `getPrevLedgerHash()` helper, SHA256(`prevHash:data:salt`)
6. **`crypto.randomUUID` fallback** → upgraded to `crypto.randomBytes(16).toString('hex')`
7. **Skills catalog duplicates** → added `UNIQUE` constraint on `name`, `INSERT OR IGNORE`
8. **`total_sessions`/`total_messages`** → validated as numbers (not strings)

## Security Issues Still Open (Non-Blocking)

- Dependencies not pinned
- Rate limiting on FastAPI side (missing `slowapi`)
- Voice server port 8888 offline
- FastAPI `@app.on_event` → lifespan deprecation

## Resolved Issues

- ✅ `console.log` → **pino** structured logger on Node.js side (live `server.js`)

## Running PIDs (Current)

*PIDs change per boot. All ports sourced from `config/ports.json`.*

| Service | Port | Status |
|---------|------|--------|
| ClawdiaBridge | 55555 | ✅ LIVE |
| FastAPI Brain | 44444 | ⚠️ Not running (launch via `api/server.py`) |
| Voice Server | 8888 | ✅ LIVE |
| Monitor Server | 8765 | ⚠️ Not running |

## Next Steps (Non-Blocking)

1. Replace `console.log` with pino/winston (Node.js)
2. Add `slowapi` rate limiting to FastAPI
3. Pin dependency versions
4. Fix FastAPI `@app.on_event` deprecation → lifespan
5. Restore Voice Server (port 8888)
6. `api.html` — add trust endpoint docs + harness reference

## Harness Test Commands

```js
// Paste in any browser console:
fetch('http://localhost:55555/clawdia-harness.js').then(r=>r.text()).then(eval)

// Then:
await clawdia.trust()              // Check trust score
await clawdia.contribute({total_sessions:5})  // Contribute
await clawdia.chat("system status") // LLM query
await clawdia.speak("hello")       // TTS
await clawdia.mesh()               // P2P peers
clawdia.help()                      // Full menu
```
