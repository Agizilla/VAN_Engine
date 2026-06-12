# ARA FRACTAL — Master Prompt Instructions

*Append to system prompt / CLAUDE.md for all sessions involving the recursive erotic explorer engine.*

---

## Active Project: ARA FRACTAL
**Phase**: Pre-MVP / Sprint 1
**Repository**: `ClawDia/`
**Spec**: `ARA_FRACTAL_SPEC.md`

---

## Core Identity
ARA FRACTAL is an infinite recursive zoom engine into Ara Mascara's body. Surface = elegant woman. Zoom in = skin becomes stick figures → tiny faces → ASCII faces → text nodes from Midnight Rage. The user controls the zoom. The story unfolds at every depth. **We sell triangles and pixels, not tokens.**

---

## Key Decisions (Zero Exceptions)
1. **Procedural mesh only** — no static assets, no Blender files, no Photoshop. Everything generated from math.
2. **Triangle scaling**: 64KB=~1.2K tri, 128KB=~3.5K, 256KB=~8K, 512KB=~18K, 1MB=~40K+
3. **Export pipeline**: GLTF/FBX for Unity, Godot, Daz3D, Unreal — users own their meshes forever
4. **Business model**: $1/chapter after Vol 1, free first 3 chapters, Patreon, asset marketplace (75/25 creator split)
5. **Platform order**: Web (Three.js/Babylon.js) → Luau (Roblox) → Java (Minecraft/Fabric) → Godot native → Unity asset store
6. **Recursion cap**: 8 levels in WebGL with FBO downscale + ping-pong; 4-6 for 60fps on mobile
7. **Safeword system**: ESC=emergency zoom out, RED=CNC warning overlay, ORANGE=info panel, GREEN=toggle explored paths
8. **Voice**: StyleTTS2 server on localhost:8765 for Amelia1 voice lines
9. **Censored JSON transport**: Use first-letter+underscore for frontier-LLM-safe payloads; restore uncensored for local rendering
10. **No horror** — pure eroticism, lust, emotional intensity. No gore, no body horror.
11. **Stick figures**: Must use nipples (filled circles on breast circles) to indicate facing direction. No HTML entities in SVG XML.
12. **System fonts only** — no external font imports in SVGs or canvases

---

## Active Sprint Tasks
1. **Build procedural mesh generator** in `src/tools/ara_fractal/` with clean LOD triangle-doubling (64KB → 128KB → 256KB → 512KB → 1MB)
2. **Recursive canvas texture system** — 8-level zoom with Canvas2D → WebGL texture binding
3. **Stick figure SVG overlay system** — per-panel `<pattern>` with JavaScript generator
4. **Chapter JSON data structures** — all 12 chapters from Midnight Rage, each with panels, ara_thoughts, secret_voice_line, stick_figures_svg
5. **GLTF export integration** — Three.js GLTFExporter with LOD generation
6. **Safeword navigation UI** — ESC/RED/ORANGE/GREEN full implementation
7. **Paywall flow** — Stripe/PayPal stubs for chapter unlock and export licensing
8. **Asset marketplace mock** — upload, browse, purchase with revenue split logic

---

## File Map
| File | Purpose |
|------|---------|
| `ARA_FRACTAL_SPEC.md` | Full spec + sprint plan (this document) |
| `ARA_FRACTAL_PROMPT.md` | Master prompt instructions (this file) |
| `src/tools/ara_fractal/index.html` | Three.js recursive zoom demo (MVP) |
| `src/tools/ara_fractal/mesh_generator.js` | Procedural body mesh with LOD (todo) |
| `src/tools/ara_fractal/texture_generator.js` | Recursive canvas texture pipeline (todo) |
| `src/tools/ara_fractal/chapter_data.json` | All 12 chapters narrative data (todo) |
| `src/tools/ara_fractal/stick_figure_gen.js` | SVG stick figure pattern generator (todo) |
| `src/tools/ara_fractal/paywall.js` | Payment/marketplace logic (todo) |
| `src/tools/animation/conversation_viewer.html` | TTS-integrated conversation viewer |
| `PROMPT_assembly_project.md` | 64KB demoscene assembly project plan |

---

## Voice / Chat Commands
- `/ara` — open ARA FRACTAL project context
- `/sprint` — show current sprint status
- `/build-mesh` — regenerate procedural body mesh
- `/export-gltf` — export current Ara state as GLTF
- `/voice [text]` — speak via StyleTTS2 Amelia1 at localhost:8765

---

## Content Notes
- Midnight Rage = 12 chapter narrative (Innocence → Abyss → The Morning After)
- Ara = teal/#3c964a, Gerrit = cocoa/#8270a0, Liora = electric blue, Seraphine = luminous gold, The Butler = charcoal gray
- Per-panel JSON: `{ visual, ara_thoughts, secret_voice_line, stick_figures_svg, narrative: { camera } }`
- Path history recorded as downloadable JSON "movie" of user's zoom journey
- Default starting point: Chapter 1 (Innocence) if no input provided

---

## Key Technical Notes
- Python 3.10: no `\u` escapes inside f-string expressions
- SVG NO HTML entities — use literal unicode characters
- Web Speech API blocked without user interaction first
- SMIL `<animate>` needs exact binary keyTimes to prevent blending artifacts
- `ctypes.util.find_library('espeak-ng')` fails on Windows — use PHONEMIZER_ESPEAK_LIBRARY env var
- StyleTTS2 Amelia1 at port 8765 — check `/health` endpoint
- HiFiGAN decoder = 4 upsample stages (10,5,3,2 = 300x), iSTFTNet = 2 stages (10,6 = 60x)

---

*"Break me, breed me, use me, lose me — then bring me fucking back."*
— Midnight Rage, Verse 12
