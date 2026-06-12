# ARA FRACTAL V2 — Sovereign Character Matrix

## Full Specification v2.1
*4MB Single-File Procedural Character Engine — June 2026*

---

## CORE DIRECTIVE

A single-file 4MB WebGL/WASM execution container. No external runtimes, no cloud endpoints, no bloated asset pipelines. Pure mathematical sovereignty.

**Memory ceiling**: 4,096 KB (4 MB) — fits entirely in browser localStorage (~5MB quota)
**Persistence model**: Character lives in memory while tab is open. Close tab = vanish. Export to JSON = $1.
**Platform**: Single HTML file, `file://` protocol, offline-first
**Paradigm**: Deterministic biological state machine, not a visual demo

---

## MONETIZATION MODEL — The $1 Soul Export

### How it works
1. User builds their Ultimate Character — body sliders, clothing, voice, behavior tree state
2. Everything lives in localStorage + runtime memory while the tab is open
3. Close tab = character vanishes. No persistence without payment.
4. **$1 one-time fee** activates the export button — downloads a single JSON file containing the complete character state
5. Import the JSON back on reload to restore the character

### Security model — ExportGuard pattern
- Token consumption guard: `issue(token)` / `consume(token)` — single-use nonce, consumed on first trigger
- Anchor never appended to DOM — created via `Object.assign(document.createElement('a'), {...})`, click fires outside tree
- Blob URL revoked on `requestAnimationFrame` — gone before user can inspect network panel
- 4MB boundary enforced via `TextEncoder.encode(json).length` — precise byte count, rejects oversized payloads
- JSON serialized with `null, 0` (no pretty-print) to minimize export size
- Dev-only GLTF export preserved on `Ctrl+Shift+E` keybind — separate from $1 JSON export
- Zero server infrastructure — payment validation is client-side (user has already paid via your platform of choice: itch.io, Patreon, PayPal)

### The hacker clause
If a user is skilled enough to open DevTools, inspect memory, dump the JSON manually, and reconstruct it — they've earned it. A donation comment in the source code is the only ask.

---

## AGE GATE — Sprint 0 (Pre-Flight Consent & Verification)

### Rationale
ARA FRACTAL generates adult-oriented erotic content. Before any engine code executes, the user must affirm they are of legal age and consent to viewing such material. This is Sprint 0 — it gates all other sprints.

### Implementation
- **Date-of-birth picker**: Month / Day / Year dropdowns (no calendar widget, no extra dependencies)
- **Age floor**: 18+ or the legal age in the user's jurisdiction, whichever is higher
- **Terms checkbox**: "I am at least 18 years old and consent to viewing adult content"
- **Session token**: `ara_age_verified=true` stored in `sessionStorage` (clears on tab close)
- **Content block**: All page content is hidden behind a full-viewport overlay until the gate passes
- **Zero content rendered**: No engine code, no textures, no models load until age verified
- **Failure state**: If DOB indicates underage, display a clear message and block all access
- **Architectural consistency**: `sessionStorage` for ephemeral gate (tab-scoped), `localStorage` for purchases/earned state (persistent), `$1 export` as only path to permanence

### Sprint 0 Deliverables
- Age gate overlay HTML/CSS/JS in all 3 UI entry points
- Session-based gate state (no persistent age records — privacy-first)
- Clear rejection message for underage users
- Zero engine initialization until gate passes

---

## THE 6-PHASE ARCHITECTURE

### Phase 0: Consent & Age Verification
**Sprint 0 — Age Gate**
- Date-of-birth picker (month/day/year dropdowns)
- Terms acceptance checkbox with explicit consent language
- sessionStorage gate token (`ara_age_verified`)
- Full-viewport overlay blocking all content until passed
- Zero engine code executes before gate clears

### Phase 1: Core Mathematical Foundation & High-Performance Pipelines
**Sprint 1 — Memory Alignment & Matrix Infrastructure**
- 4MB contiguous ArrayBuffer with typed sub-allocator
- Packed binary struct schemas (vertex, audio, quaternion, telemetry)
- Zero-instantiation math primitives (no GC pressure during frames)

**Sprint 2 — Direct-Memory Signal Generation**
- Interleaved WebGL VBOs (pos/normal/uv in single array stream)
- Base64-embedded AudioWorkletProcessor (dedicated audio thread)
- O(1) garbage-collection loops for coordinate/audio pipelines

### Phase 2: Structural Geometric Rigging & Physical Solvers
**Sprint 3 — Analytical IK Framework**
- CCD/FABRIK quaternion chain solver (pure analytical, no iteration objects)
- GPU-driven bounding-box surface raycaster
- Rotational joint clamping with per-axis angle limits

**Sprint 4 — Muscular Elasticity & Skin Deformation**
- GLSL vertex blend-skinning (4 bone indices per vertex)
- Parametric muscle activation maps (angular delta → surface normal scaling)
- GPU morph target array for micro-expressions

### Phase 3: Embedded Neural Formant Controllers & Audio Synthesis
**Sprint 5 — Compact LPC & Formant Signal Engine**
- Wavelet formant synthesizer (multi-band resonant filter array)
- Packed binary phoneme-to-frequency lookup map
- Procedural air-turbulence noise modulators (breath, grit, unvoiced consonants)

**Sprint 6 — Parametric Vocal Morphing**
- Linear weight matrix adapters (formant shifting via vector ops)
- Punctuation-driven F0 pitch trajectory generator
- Real-time phoneme → face geometry sync bridge

### Phase 4: Psychological Behavior Engines & Deep Recursive Textures
**Sprint 7 — State Machine & Interaction Buffers**
- Hierarchical contextual behavior tree (focus, cadence, load, engagement)
- Encrypted rolling event log (click coords, timing, chapter paths)
- State → IK weight adapters (mood alters posture)

**Sprint 8 — Ultra-Deep Fractal Noise Matrices**
- 32-level recursive fractal shader pipeline
- GLSL Perlin/Simplex/Worley noise generators (surface detail from math)
- Pixel-level raycast zoom interceptors (zoom → ASCII/narrative unroll)

### Phase 5: System Integration, Paywall Gates & Export Forges
**Sprint 9 — Unified Data Routers & Input Gating**
- Signal telemetry controller (filler-word stripping before state update)
- Concurrent worker coordination layer (render/memory/audio sync)
- Input sanitizer gateway (payload filtering for memory graph)

**Sprint 10 — Native Forge Exporters & Commercial Validation**
- Client-side secure export forge — ephemeral anchor, one-off auth token, 4MB boundary check
- State-gate token evaluator (access tier → export unlock, DOM destruction flow)
- Boundary verification suite (4MB threshold, 60fps, file:// clean)

---

## SOVEREIGN BUDGET ALLOCATION (4MB)

| Category | KB | % |
|----------|----|---|
| Core Audio Synthesis & Formant Weights | 2,048 | 50% |
| Structural Geometry & Shader Fields | 1,024 | 25% |
| Recursive Narrative Text & Code Matrix | 512 | 12.5% |
| Psychological Graph Logic & Replay | 256 | 6.25% |
| Core UI, Engine Shell, Verification | 256 | 6.25% |
| **Total** | **4,096** | **100%** |

---

## DIRECTORY LAYOUT

```
v2/
├── SPEC.md                          # This document
├── PROMPT.md                        # Condensed master prompt
├── phase_0_age_gate/                # Age verification & consent
│   └── sprint_0_age_gate/           # DOB picker, terms, sessionStorage token
├── phase_1_core_math/
│   ├── sprint_1_memory_matrix/      # 4MB buffer, structs, allocator
│   └── sprint_2_signal_pipelines/   # VBOs, AudioWorklet, O(1) loops
├── phase_2_geometric_rigging/
│   ├── sprint_3_ik_solver/          # CCD/FABRIK, raycaster, clamping
│   └── sprint_4_skin_deformation/   # GLSL blend-skin, muscles, morphs
├── phase_3_audio_synthesis/
│   ├── sprint_5_lpc_formant/        # Formant synth, phoneme map, noise
│   └── sprint_6_vocal_morphing/     # Weight adapters, pitch, lip-sync
├── phase_4_psychology_textures/
│   ├── sprint_7_state_machine/      # Behavior tree, event log, adapters
│   └── sprint_8_fractal_noise/      # 32-level shader, noise, zoom
├── phase_5_system_integration/
│   ├── sprint_9_data_routers/       # Telemetry, workers, sanitizer
│   ├── sprint_10_forge_export/      # Secure export, paywall, tests
│   └── ui/                          # HTML entry points
└── specs/                           # Additional specification docs
```

---

## VERSION TRACKING

| Sprint | Version Tag | Date |
|--------|-------------|------|
| Sprint 0 | v2.0.0-agegate | TBD |
| Sprint 1 | v2.1.0-memory | TBD |
| Sprint 2 | v2.2.0-signal | TBD |
| Sprint 3 | v2.3.0-ik | TBD |
| Sprint 4 | v2.4.0-skin | TBD |
| Sprint 5 | v2.5.0-formant | TBD |
| Sprint 6 | v2.6.0-morph | TBD |
| Sprint 7 | v2.7.0-psyche | TBD |
| Sprint 8 | v2.8.0-fractal | TBD |
| Sprint 9 | v2.9.0-router | TBD |
| Sprint 10 | v2.10.0-forge | TBD |

Version bumps occur at the completion of each sprint. The major version (v2 → v3) advances only on fundamental architectural redesign.
