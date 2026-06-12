# ARA FRACTAL V2 — Master Prompt Instructions

**Phase**: Architecture Layout — Sprint 0
**Spec**: `v2/SPEC.md`
**Engine dir**: `ClawDia/src/tools/ara_fractal/v2/`

---

## Core Identity

4MB sovereign character matrix — a single-file offline procedural 3D entity engine. Surface = elegant woman. Zoom = stick figures → faces → ASCII → Midnight Rage text. Every byte is procedural math. No external dependencies, no cloud, no asset pipeline.

**Memory ceiling**: 4MB (4,096 KB) — fits entirely in browser localStorage (~5MB quota)
**Platform**: Single HTML, `file://` protocol
**Persistence**: Character lives in RAM while tab is open. Close = vanish. Export to JSON = $1.
**Ethos**: The intent is the soul, the software is the vessel.

---

## Phase / Sprint Map

| Phase | Sprints | Theme |
|-------|---------|-------|
| 0 — Age Gate | 0 | DOB verification, consent, sessionStorage token |
| 1 — Core Math | 1-2 | Memory matrix, signal pipelines |
| 2 — Geometric Rigging | 3-4 | IK solver, skin deformation |
| 3 — Audio Synthesis | 5-6 | Formant synth, vocal morphing |
| 4 — Psychology | 7-8 | Behavior tree, fractal noise |
| 5 — Integration | 9-10 | Routers, forge export, paywall |

Sprint completion = version bump (v2.0.0, v2.1.0, v2.2.0, ... v2.10.0)

---

## Budget (4MB)

- Audio synthesis & formant weights: 2,048 KB (50%)
- Geometry & shader fields: 1,024 KB (25%)
- Recursive narrative & code matrix: 512 KB (12.5%)
- Psychological graph & replay: 256 KB (6.25%)
- Core UI, shell, verification: 256 KB (6.25%)

---

## Monetization

- **$1 per JSON export** — one-time fee, one-off auth token (`tok_1ff_`)
- Ephemeral anchor download — element created outside DOM, object URL revoked instantly
- 4MB boundary check enforced before serialization
- No persistence without payment — close tab = character vanishes
- **Hacker clause**: If they extract from DevTools memory, they've earned it. Donation comment in source.

---

## Key Technical Directives

1. **Age Gate is Sprint 0** — DOB picker + terms checkbox blocks ALL content until passed. No engine code initializes before gate clears.
2. **sessionStorage for ephemeral state** — age gate token (`ara_age_verified`) stored in sessionStorage, clears on tab close. localStorage reserved for purchases/earned state only.
3. **4MB cap** — all subsystems (audio, geometry, narrative, psychology, UI) fit in localStorage quota
4. **Secure export flow** — ephemeral `<a>`, one-off token, `URL.revokeObjectURL()`, 4MB boundary check
5. **AudioWorklet** replaces StyleTTS2 — formant synthesis from phoneme maps, no external server
6. **8MB** from v1 spec is now **4MB** — tighter packing, same ambition
7. **Donation comment** in every HTML file — PayPal + collaboration email in source
8. Everything else inherits from the v1 technical directives (GLSL blend-skinning, 32-level fractal, behavior tree, etc.)
