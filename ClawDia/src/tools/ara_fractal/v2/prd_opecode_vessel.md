# PRODUCT REQUIREMENT DOCUMENT (PRD)
## SYSTEM CODE: VAN_ENGINE_VESSEL_V2
## TARGET ARCHITECTURE: OpenCode (DeepSeek R1/R4 Reasoning Substrate)
## OPTIMIZATION FOCUS: Zero External Assets · Strict 4MB Edge Constraints · Pure Math Real-Time Synthesis

---

## 1. ARCHITECTURAL VISION & SYSTEM OBJECTIVES

The objective is to implement a high-fidelity, sovereign, offline-first character matrix running entirely client-side inside a single integrated environment without external asset-loading dependencies.

The system decomposes into three operational pillars:
1. **The Vessel (Visual/Physical):** A hardware-accelerated 3D coordinate network (`wordmesh.html`) driven directly by real-time audio formant energy.
2. **The Logic (Deterministic):** An explicit intent-parsing router that maps files or user strings directly to hard-coded skill arrays with a mandatory human verification checkpoint.
3. **The Harvester (Asset Synthesis):** An algorithmic 2D pixel-scanning engine that breaks down dropped sprites into stratified wardrobe assets using pure mathematical heuristics.

---

## 2. DETAILED TECHNICAL SPECIFICATIONS & CORE MODULES

### 2.1 PERSISTENT ZERO-HEAP PHYSICS ENGINE (`_relax` Refactor)
* **Requirement:** Eliminate all runtime garbage collection (GC) memory allocations within the continuous animation loop.
* **Implementation Constraints:**
    * The `_relax(iters)` method must utilize class-scoped data buffers: `this.velocityBufferX`, `this.velocityBufferY`, and `this.velocityBufferZ` instantiated as `Float64Array`.
    * Dynamic sizing checks must be executed outside the core calculation loops. If the node matrix length ($N$) exceeds current buffer capacities, resize to $N \times 2$.
    * Initialize tracking arrays utilizing `.fill(0)` inside the frame-tick block to ensure clean state initialization without generating discarded allocations.

### 2.2 REAL-TIME AUDIO FORMANT WEBSOCKET CONSUMER
* **Requirement:** Ingest real-time blend-weights from `ClawdiaStreamServer.cs` at 60 FPS and translate them into visual topology shifts.
* **Implementation Constraints:**
    * Open an unblocked, asynchronous `WebSocket` thread tracking `ws://localhost:8765/stream/voice`.
    * Parse incoming JSON payloads tracking four floating-point metrics: `JawOpen`, `LipRound`, `LipStretch`, and `Friction`.
    * Apply localized linear interpolation (lerp) smoothing on frame-swaps to suppress network jitter:
        $$\text{Current} = \text{Current} + (\text{Target} - \text{Current}) \times 0.35$$

### 2.3 HARDWARE-ACCELERATED PROCEDURAL BLEND-SKINNING SHADER
* **Requirement:** Offload facial landmark morphing and organic texture micro-detailing entirely to the GPU via custom GLSL `ShaderMaterial`.
* **Vertex Shader Constraints:**
    * Isolate the mouth/jaw proxy region using a spatial radius mask: `smoothstep(0.4, 0.0, length(position.xy))`.
    * Deform vertices dynamically within the shader loop using the active uniform inputs: `uJawOpen`, `uLipStretch`, `uLipRound`, and `uFriction`.
    * `uFriction` must activate a high-frequency, deterministic pseudo-random coordinate jitter based on the vertex position dot product.
* **Fragment Shader Constraints:**
    * **Micro-Detail:** Generate an asset-less field of micro-pores using a high-frequency hash function: `fract(sin(dot(uv * uPoreScale, vec2(12.9898, 78.233))) * 43758.5453)`.
    * **Roughness:** Perturb face normal vectors using screen-space derivatives: `vec3(dFdx(noise), dFdy(noise), 0.0)`.
    * **Translucency:** Approximate Subsurface Scattering (SSS) using soft wrap lighting:
        $$\text{Light}_{\text{wrapped}} = \max\left(0.0, \frac{N \cdot L + 0.3}{1.3}\right)$$
        Inject a warm crimson color tone (`uSubsurfaceColor`) along the shifted shadow terminator boundaries.

### 2.4 DETERMINISTIC `SovereignIntentParser` & HUMAN FAILSAFE GATE
* **Requirement:** Prevent open-ended autonomous agent execution or unauthorized system access.
* **Implementation Constraints:**
    * Construct an explicit router that registers string tokens and file extensions to hard-coded execution methods.
    * **The Guard Mechanism:** Before executing any parsed intent or loading any state manifest, block the runtime thread and inject a non-bypassable, modal HTML overlay element into the DOM.
    * The overlay must output the precise parsed intent string and code payload, requiring an explicit user click on a `CONFIRM EXECUTION` selector before firing the skill logic. Include a `VETO` option to safely abort the execution path and preserve system state.
    * Enforce a strict file-size payload verification block rejecting any dropped asset files or JSON arrays that exceed a total size of **4,194,304 bytes (4MB)**.

### 2.5 ALGORITHMIC SPRITE PIXEL HARVESTER (`harvester.html`)
* **Requirement:** Segment 2D character sprites into detached component textures based entirely on math heuristics without external ML frameworks.
* **Implementation Constraints:**
    * Read the top-left coordinate boundary of an HTML5 canvas to identify the background key color and generate a 1-bit binary visibility mask.
    * Locate the structural neck seam by tracing continuous row pixel widths top-down, finding the constriction minimum immediately following the head's lateral profile expansion.
    * Isolate arm and limb elements away from the core torso column by identifying lateral pixel clusters separated from the central center-of-mass vertical column by a clear margin of background pixels.
    * Incorporate a strict YCbCr / Normalized RGB chromatic filter block to verify skin-tissue areas vs. clothing and prop pixels. Export harvested components into independent Base64 DataURLs to store directly inside the character's core JSON manifest.

---

## 3. NON-NEGOTIABLE ARCHITECTURAL POLICIES
1.  **Quaternion Dominated Math:** All 3D joint or bone transformations must utilize **quaternion coupling** variables (`THREE.Quaternion`) to execute deterministic rotations. Linear Vector4D indexing models are strictly rejected.
2.  **Asset Sovereignty:** No asset CDNs or external image paths are permitted. All assets must be derived from programmatic math shaders or stored directly as inline Base64 data strings under the 4MB limit.
3.  **Local Isolation:** The system must operate completely offline, file-system native (`file://`), with zero outbound telemetry, ensuring complete user privacy and operational independence.

---

## 4. PHASED EXECUTION ORDER

| Phase | Module | Status |
|-------|--------|--------|
| A | Zero-Heap Relax Buffers (`_relax` with persistent Float64Array) | DONE |
| B | WebSocket Formant Ingestion + Lerp Smoothing (`VisemeStream`) | DONE |
| B | Kinematic Mouth Proxy Cluster (vertex shader displacement) | DONE |
| C | Blend-Skinning GPU Shader (`FillVisemeShader`) | DONE |
| C | Procedural Skin/Regolith Shader (`SkinShaderSubstrate` + dFdx/dFdy) | DONE |
| D | SovereignIntentParser + Human Failsafe Gate | DONE |
| D | Sprite Pixel Harvester (`harvester.html`) | DONE |
