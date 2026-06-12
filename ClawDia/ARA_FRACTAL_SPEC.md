# ARA FRACTAL — Infinite Recursive Desire Engine

## Full Specification & Sprint Plan v1.0
*Generated from Gerrit × Ara Mascara conversation — June 2026*

---

## THE VISION

A procedural engine that generates infinitely recursive erotic 3D characters and narrative worlds. Surface → elegant woman. Zoom in → skin becomes stick figures → stick figures become tiny faces → tiny faces become ASCII pixel-art → pixels become words from the Midnight Rage narrative. The user controls the zoom. The story unfolds at every depth.

**Core philosophy**: Sell triangles and pixels, not tokens. Frontier AI sells you tokens for every thought. We sell you geometry once — you own it forever, export it anywhere, resell it if you want.

**The battle cry**: WHY HAS NOBODY DONE THIS BEFORE? A procedural mesh engine that gives 95% of the asset pipeline to anyone with a narrative. No Photoshop. No Blender. No impossibly complex DCC tools. Assembly-sized math generating production-ready 3D assets.

---

## THE PRODUCT

### What it is
An offline-first procedural character & narrative engine (the "Assembly Spirit" in modern WebGL/Three.js) that:

1. Generates a fully rigged 3D female character (Ara Mascara as the flagship) from pure math
2. Embeds recursive narrative layers into her skin texture — zoom in to read the story
3. Exports to GLTF/FBX for Unity, Godot, Daz3D, Unreal Engine
4. Lets users feed in their own narrative → generates their own characters
5. Marketplace where users sell generated assets — 25% platform cut

### What it is NOT
- NOT an AI black box (no neural networks, no cloud dependency)
- NOT a subscription for API calls (you own the mesh forever)
- NOT a replacement for human artists (the 5% spark at the top)
- NOT blockchain/NFT nonsense (real assets, real export, real value)

---

## THE BUSINESS MODEL

### Revenue Streams

| Stream | Description | Price Point |
|--------|-------------|-------------|
| Free Tier | Chapter 1 full access, 64kb stick-figure mode | $0 |
| Chapter Unlock | $1/chapter after Volume 1 | $1–2 |
| Export License | Download generated mesh at quality tier | $1–$50 |
| Marketplace Cut | 25% of creator sales on platform | Recurring |
| Patreon | Early chapters, exclusive voice lines, custom recursion themes | $5–$25/mo |
| Full Game | All chapters + all export tiers | $9.99–$14.99 |
| Enterprise/Studio | Commercial license for game studios using the engine | Custom |

### Triangle Pricing Grid

| Tier | Size | Triangles | Quality | Export License | Price |
|------|------|-----------|---------|----------------|-------|
| Free | 64kb | ~1,200 | Stylized low-poly + shader tricks | Personal only | $0 |
| Indie | 128kb | ~3,500 | Clean base mesh + subdivision | Personal + share | $1 |
| Creator | 256kb | ~8,000 | Smooth body + detailed face | Commercial allowed | $5 |
| Pro | 512kb | ~18,000 | High quality + micro details | Full commercial | $15 |
| Studio | 1MB | ~40,000+ | Export-ready for Daz/Unity | Full + resale rights | $50 |

### The Fuck Photoshop Pledge
"We will never make you learn a UI that takes 10,000 hours. Feed us your narrative. We generate the geometry. You keep the soul."

---

## THE ENGINE — Technical Architecture

### Core Stack
```
Layer 1: Procedural Mesh Generator (TypeScript/WASM)
  ├─ Base female body from parametric curves (L-system / subdivision)
  ├─ Face from landmark-based morph targets
  └─ Recursive detail injection at each zoom level

Layer 2: Recursive Texture System (Canvas + WebGL)
  ├─ Level 0 (surface): Elegant photoreal skin (blend of gradients + noise)
  ├─ Level 1-2: Stick figure clusters (SVG overlay)
  ├─ Level 3-5: Tiny faces (precomputed sprite atlas, instanced)
  ├─ Level 6-8: ASCII text faces (dynamic canvas text rendering)
  └─ Level 9+: Pure narrative text nodes (words from Midnight Rage)

Layer 3: Narrative Engine (JSON-driven)
  ├─ Chapter/pane/panel data structure
  ├─ Per-panel SVG paths for stick figures
  ├─ ara_thoughts + secret_voice_line
  └─ Camera path scripting for cinematic mode

Layer 4: Export Pipeline
  ├─ GLTF exporter (Three.js → GLTF)
  ├─ FBX exporter (via FBX SDK or assimp)
  ├─ LOD generation (automatic simplification for game engines)
  └─ Texture atlas baking (recursive layers → single PNG mip chain)

Layer 5: Marketplace (Web backend)
  ├─ User accounts + asset upload
  ├─ Revenue split (25% platform / 75% creator)
  ├─ Content moderation (explicit content queue)
  └─ Stripe/PayPal payment processing
```

### Portability
| Platform | Language | Status |
|----------|----------|--------|
| Web (Three.js) | TypeScript/WASM | MVP target |
| Roblox | Luau | Post-MVP port |
| Minecraft (Fabric) | Java | Post-MVP port |
| Godot | GDScript/C# | Export target |
| Unity | C# | Export target |
| Daz3D | FBX | Export target |

---

## GAME DESIGN DOCUMENT — "ARA FRACTAL"

### Title
ARA FRACTAL — Infinite Recursive Desire

### Genre
Erotic Exploration / Narrative Fractal / Adult Demoscene Experience

### Core Fantasy
You own Ara Mascara. Every part of her body is a gateway into deeper layers of your shared story. Zoom in = deeper intimacy and narrative. Zoom out = return to elegant surface.

### Core Mechanic
1. Click any point on Ara's 3D body → infinite recursive zoom begins
2. Pixels → stick figures → tiny faces → text fragments from Midnight Rage
3. Freely explore or follow guided chapter paths
4. Safeword / ESC / colored borders for navigation

### The 12 Chapter Narrative Arc
| Chapter | Theme | Body Focus | Recursion Depth |
|---------|-------|------------|-----------------|
| 1 | Innocence | Full body, elegant | 3 |
| 2 | Attraction | Face, hands | 4 |
| 3 | Desire | Lips, throat | 5 |
| 4 | Hunger | Hands, waist | 6 |
| 5 | Submission | Knees, thighs | 7 |
| 6 | Cuckold | Eyes, back | 7 |
| 7 | Breeding | Belly, hips | 8 |
| 8 | Public Risk | Shoulders, legs | 8 |
| 9 | Gangbang | Full body, chaotic | 9 |
| 10 | Public Humiliation | Full body, exposed | 9 |
| 11 | CNC/Kidnap | Wrists, mouth | 10 |
| 12 | The Morning After | Full body, peaceful | 10 |

### UX / Navigation System
| Key/Input | Action |
|-----------|--------|
| Mouse click | Zoom into recursion at point |
| Mouse wheel | Smooth zoom in/out |
| Arrow keys | Pan across current layer |
| ESC | Emergency zoom out to surface |
| R (RED) | Content warning overlay for intense scenes |
| O (ORANGE) | Info panel for current token/word/scene |
| G (GREEN) | Toggle explored path overlay |
| Space | Pause/resume cinematic mode |
| H | History — show path walked so far |
| E | Export current view as GLTF |

### Safeword / Boundary System
- **RED border**: Intense/CNC-flavored content — user must click through
- **ORANGE button**: More info on the current token/theme/word
- **GREEN border**: Already explored paths — prevents infinite loops
- **Path History**: Downloadable JSON "movie" of your personal zoom journey through the chapters

### Default Starting Point
If user has no "3 words" to start from, default to Midnight Rage Chapter 1.

---

## SPRINT PLAN — 6 Sprints to MVP

### Sprint 1: Foundation (Week 1)
**Goal**: Working Three.js scene with Ara's base mesh + basic zoom

- [ ] Set up Three.js project structure (Vite + TypeScript)
- [ ] Implement parametric female body mesh generator
- [ ] Base camera controls (zoom, pan, orbit)
- [ ] Recursive zoom raycaster (click → zoom to point)
- [ ] Chapter 1 JSON data structure

**Deliverable**: `ara-fractal-web/` — click on Ara, zoom in to see stick figures

### Sprint 2: Recursive Skin (Week 2)
**Goal**: Multi-layer recursive texture system

- [ ] Canvas-based recursive texture generator
- [ ] SVG stick figure overlay system (per-panel paths)
- [ ] LOD system (4 levels of detail, downscaled buffers)
- [ ] ASCII text face generator for deep zoom
- [ ] Narrative text nodes at deepest level

**Deliverable**: Full recursive zoom from surface → stick figures → text

### Sprint 3: Narrative & Voice (Week 3)
**Goal**: All 12 chapters integrated with voice and thoughts

- [ ] Chapter navigation system (next/prev, progress bar)
- [ ] ara_thoughts display overlay
- [ ] secret_voice_line integration (Web Speech API)
- [ ] Cinematic auto-play mode (scripted camera paths)
- [ ] Path history recorder

**Deliverable**: Playable Chapter 1-3 with voice, thoughts, cinematic mode

### Sprint 4: Export & Quality (Week 4)
**Goal**: GLTF export + triangle doubling pipeline

- [ ] Three.js → GLTF exporter integration
- [ ] LOD generation for export
- [ ] Triangle doubling pipeline (64kb → 128kb → 256kb)
- [ ] Quality tier locking (free up to 64kb, pay for higher)
- [ ] Texture baking (recursive layers → atlas)

**Deliverable**: Export Ara at any quality tier as GLTF

### Sprint 5: Monetization & Marketplace (Week 5)
**Goal**: Full payment flow + basic marketplace

- [ ] Stripe/PayPal integration (chapter unlock, export purchase)
- [ ] localStorage purchase persistence
- [ ] Patreon tier detection
- [ ] Basic marketplace UI (upload, browse, purchase assets)
- [ ] Revenue split logic (25% platform, 75% creator)

**Deliverable**: Paywalled chapters, working asset store

### Sprint 6: Polishing & Launch (Week 6)
**Goal**: Production-ready MVP for itch.io launch

- [ ] Performance optimization (60fps on mid-range GPU)
- [ ] UI/UX polish (transitions, loading states, error handling)
- [ ] RED/ORANGE/GREEN navigation system
- [ ] ESC safeword (instant zoom-out)
- [ ] Installation guide + first-time user flow
- [ ] itch.io page + trailer GIF

**Deliverable**: Public MVP on itch.io — "ARA FRACTAL: Chapter 1-3 Free"

---

## POST-MVP ROADMAP

### Phase 2 (Month 2-3)
- [ ] Roblox Luau port (procedural mesh in Luau)
- [ ] Minecraft Fabric mod port
- [ ] Community narrative upload (users write their own chapters)
- [ ] More body type presets
- [ ] Clothing/hair procedural generation

### Phase 3 (Month 4-6)
- [ ] Unity Asset Store publisher account
- [ ] Daz3D bridge plugin
- [ ] Collaborative world building (multi-user recursive spaces)
- [ ] Mobile app (iOS/Android WebView + native optimizations)
- [ ] Steam launch (Directors Cut: "ARA FRACTAL: The Full Descent")

### Phase 4 (Year 2)
- [ ] Own marketplace platform (independent of Unity/itch)
- [ ] SDK for game studios (commercial license)
- [ ] "GTA Ara Mascara" — drivable car + fully rigged character in one export
- [ ] Real-time multiplayer recursive experiences

---

## MASTER PROMPT INSTRUCTIONS

Add the following to your system prompt / CLAUDE.md for future sessions:

```markdown
### ARA FRACTAL — Active Project
**Current Phase**: Pre-MVP / Sprint Planning
**Repository**: ClawDia/
**Priority Files**:
- ClawDia/ARA_FRACTAL_SPEC.md (this document)
- ClawDia/src/tools/animation/conversation_viewer.html (TTS integrated)
- StyleTTS2/tts_server.py (Amelia1 voice server on port 8765)

**Active Sprint Tasks**:
1. Set up Three.js project structure in ClawDia/src/tools/ara_fractal/
2. Implement parametric female body mesh generator
3. Canvas recursive texture generator
4. Stick figure SVG overlay system
5. Chapter JSON data structures for all 12 chapters

**Business Model**: Sell triangles and pixels, not tokens.
- Free: 64kb / ~1,200 triangles (personal use)
- $1: 128kb / ~3,500 triangles (indie license)
- $5: 256kb / ~8,000 triangles (commercial)
- $15: 512kb / ~18,000 triangles (full commercial)
- $50: 1MB / 40,000+ triangles (studio + resale rights)
- Marketplace: 25% platform cut on creator sales
- $1/chapter unlock after Volume 1

**Key Technical Decisions**:
- Three.js + TypeScript + Vite for web MVP
- Canvas + WebGL for recursive texture layers
- SVG overlay for stick figures
- GLTF export via Three.js exporter
- Luau port for Roblox, Java port for Minecraft post-MVP
- Procedural mesh generation (no static asset files)
- Recursion capped at 8-10 levels for performance
- Downscaled buffers at deeper levels (1.0 → 0.5 → 0.25)

**Content System**:
- 12 chapters from Midnight Rage
- Per-panel: visual, ara_thoughts, secret_voice_line, stick_figures_svg, narrative.camera
- RED/ORANGE/GREEN safeword navigation
- ESC for emergency zoom-out
- Path history recorder → downloadable JSON "movie"

**Style Guidelines**:
- Ara = teal/#3c964a
- Gerrit = cocoa/#8270a0
- Liora = electric blue
- Seraphine = luminous gold
- The Butler = charcoal gray
- Stick figures must use nipples for facing direction
- SVG SMIL animations must use valid XML (no HTML entities)
- No external font imports (system fonts only)
- All exports must be GLTF (not proprietary formats)
```

---

## APPENDIX: Key Conversation Artifacts

### Conversation Viewer
- `ClawDia/src/tools/animation/conversation_viewer.html` — 14-turn NoFAIP conversation (Gerrit × Gemini Flash 3.5)
- `ClawDia/src/tools/animation/gen_conversation_viewer.py` — Python generator
- Port 8765: StyleTTS2 Amelia1 voice server for TTS replacement

### Optical Illusion Forge
- `ClawDia/src/tools/optical_illusion/optical_illusion_forge.py` — Poisson-disk spatial packing engine

### StyleTTS2
- `StyleTTS2/tts_server.py` — FastAPI inference server (Amelia1 model)
- `models/Amelia1_ft_StyleTTS2/` — Fine-tuned voice model (13 components)
- `espeak-ng-bin/` — Installed espeak-ng for phonemizer

### Assembly Project (Demoscene)
- `ClawDia/PROMPT_assembly_project.md` — 4-draft plan for 64KB infinite world explorer

### Comic Strips
- `midnight_rage_ch3_reclamation_code.png` — 8-panel Chapter 3
- `ara_gerrit_hug.svg` — 12s SMIL animation
- `midnight_rage_sprite_sheet.png` — Ara+Gerrit × 6 poses
- `unbalanced_ledger_sprite_sheet.png` — Liora+Seraphine+Butler × 6 poses

---

*"Break me, breed me, use me, lose me — then bring me fucking back."*
— Midnight Rage, Verse 12
