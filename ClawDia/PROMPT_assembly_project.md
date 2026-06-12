# NOFAIP Assembly Project — 4 Draft Specification

## Session Handoff Document
*Load this file at the start of a fresh session to continue.*

---

### Project Vision
Build a local, deterministic, offline-first Assembly project that generates infinite explorable worlds using pure math — no neural networks, no training data, no cloud. The project evolves across 4 drafts, each adding a layer of interactivity.

### Core Principles
- **NOFAIP**: Non-greedy, Offline-first, Alternative Intelligence Paradigm
- **Deterministic**: Same input always produces same output — no hidden randomness
- **Self-contained**: 64KB-128K max, single executable, zero dependencies
- **Math over models**: Sacred geometry, fractals, waveguide physics, constraint solving

---

## Draft 1 — Infinite Explorable Sacred Geometry World
**Goal**: A 64KB demo of an infinite 3D world generated from pure mathematical formulas.

### Components
1. **Software rasterizer** — 320x200 or 640x480, VGA or framebuffer
2. **Geometry engine** — Mandelbrot/Julia set exploration, golden ratio spiral, Platonic solid generators
3. **Camera movement** — WASD + mouse look, zoom in/out
4. **Infinite detail** — As camera zooms in, new geometry emerges from deeper recursion levels
5. **Color palette** — Derived from position in the geometric field, not pre-baked

### Key Techniques
- Fixed-point math (no FPU required)
- Mode 13h (320x200 256-color) or linear framebuffer
- Real-mode x86 assembly (NASM)
- Recursive L-system or iterated function system for infinite detail
- Keyboard interrupt handling for movement

### Deliverable
`nofaip_d1.com` or `nofaip_d1.exe` — single file, under 64KB, opens to an explorable fractal universe.

---

## Draft 2 — Adding Text Tokens & Emoticons
**Goal**: Layer a semantic dimension on top of the geometry — text tokens and emoticons float in 3D space as collectible objects.

### Components
1. **Text rasterizer** — Minimal bitmap font renderer for 3D-projected text strings
2. **Token system** — Words from a lexicon array placed at spatial coordinates (derived from hash of word)
3. **Collection mechanic** — Player moves near a token, key to "grab" it
4. **Emoticon sprites** — Simple pixel art faces rendered as billboard sprites
5. **Inventory/HUD** — Collected tokens displayed on screen border
6. **Markov-chain expansion** — Moving closer to a word reveals connected words (2nd-order Markov from a seed narrative)

### Design
- Tokens arranged in a 3D lattice following Yule Wheel geometry (6 radial axes)
- High-value tokens (thematically dense) are deeper in the structure, requiring more exploration
- Distance-to-token affects font size and opacity (proximity-based reveal)
- Collected tokens form a "poem" or "narrative fragment" displayed at session end

### Deliverable
`nofaip_d2.com` — 64KB-96KB, adds text rendering + token collection to Draft 1.

---

## Draft 3 — 2D Game Variations (3 Versions)
**Goal**: Step back to 2D and explore different game mechanics. Three versions with different movement, objectives, and audio-visual feedback.

### Version A — "The Lexicon Descent"
- **Genre**: Vertical scroller / falling
- **Movement**: Left/right only, auto-scrolls downward
- **Objective**: Navigate through falling word fragments, collect ones that complete the target sentence
- **Audio**: Pitch increases as you approach high-value tokens
- **Fail state**: Miss too many target words → level resets
- **Visual**: Words fade in from top, grow larger as they approach

### Version B — "Signal Chase"
- **Genre**: Side-scroller / runner
- **Movement**: Jump (space), duck (down), left/right precision
- **Objective**: Follow the "cleanest signal" — visual and audio cues guide toward areas of low entropy / high coherence
- **Audio**: Stereo pan indicates direction to target; volume indicates proximity
- **Mechanic**: Moving in the right direction clarifies the waveform display at screen bottom
- **Visual**: Sine waves as platforms, noise as obstacles

### Version C — "Token Arena"
- **Genre**: Top-down arena
- **Movement**: 8-directional, dash
- **Objective**: Grab glowing tokens before AI-controlled "echo" characters reach them
- **Echo AI**: Simple chase behavior based on proximity to nearest token
- **Scoring**: Chain multiplier for consecutive grabs
- **Visual**: 2D top-down, tokens pulse with entropy-based color (red = high entropy, blue = low)

### Deliverable
`nofaip_d3a.com`, `nofaip_d3b.com`, `nofaip_d3c.com` — each 48-64KB.

---

## Draft 4 — Unified 2D/3D Hybrid Engine
**Goal**: Combine the best mechanics from Drafts 1-3 into a single unified experience that generates infinite locally-curated entertainment artifacts.

### Core Game Loop
1. Player exists in a 3D world of geometric structures (Draft 1)
2. Text tokens float within the geometry, arranged by semantic proximity (Draft 2)
3. Player navigates toward "interesting" regions guided by audio cues — cleaner signal = closer to meaning (Draft 3B)
4. Other entities (echoes of previous players or AI-driven characters) compete for high-value tokens (Draft 3C)
5. Collected tokens assemble into a session artifact — a poem, a voice param preset, a JSON telemetry log, or a new world seed

### Convergence Points
- **Audio**: All sounds generated via waveguide synthesis (Kelly-Lochbaum filters), no sample files
- **Visual**: Unified rendering pipeline — 3D geometry + billboard text + 2D HUD
- **Input**: Keyboard + mouse, with optional drag-and-drop file injection
- **Output**: Session exports as JSON telemetry (player trajectory, collected tokens, decisions)

### Drag-and-Drop File Injection
- Dropping a .txt file onto the window seeds the Markov chain with new vocabulary
- Dropping a .wav file extracts formant parameters and generates a "voice" for entities
- Dropping a .json file loads a previous session's telemetry for replay or remix
- Dropping an image file creates a new geometry field from its pixel hash

### Artifact Generation Pipeline
```
Play Session → Telemetry JSON → Local LLM / Engine → New Artifact
                                                      ├── Poem / Narrative
                                                      ├── Voice Preset (F0, formants)
                                                      ├── World Seed (geometry params)
                                                      ├── Comic Panel (stick figure keyframe)
                                                      └── Music (waveguide instrument patch)
```

### Deliverable
`nofaip_d4.com` or `nofaip_d4.exe` — target 128KB, full hybrid engine.

---

## Technical Requirements (All Drafts)
- **Assembler**: NASM (Netwide Assembler), Intel syntax
- **Target**: x86 real mode (DOS/FreeDOS) or protected mode (32-bit flat binary)
- **Build**: Single `nasm -f bin` command, output .com or flat binary
- **Testing**: DOSBox or QEMU for real-mode; Wine or native for protected mode
- **Max Size**: Draft 1-3: 64KB each. Draft 4: 128KB.
- **Audio**: PC speaker (real-mode) or waveform buffer (protected mode + SDL)
- **Input**: Keyboard BIOS interrupts (real-mode) or event loop (protected mode)

## Architecture Reference (From Gemini Conversation)
Three key assembly modules from the conversation:

1. **3D Software Rasterizer** — Projects text/geometry from 3D to 2D screen buffer, scales by inverse Z
2. **Yule Wheel Mapper** — 6-axis navigation matrix, keyboard shifts camera along primary axes
3. **Procedural Markov Decompressor** — Dense vocabulary table, spatial coordinates as PRNG seeds

See: `tools/animation/conversation_viewer.html` for the full Gemini conversation context.
