# Sprint 2 — Direct-Memory Signal Generation

## Objective
Establish raw WebGL interleaved vertex arrays and a dedicated AudioWorklet audio thread. Implement zero-allocation signal pipelines that operate directly on the 4MB buffer.

## Deliverables
- `vbo_interleave.js` — WebGL VBO packing (pos/normal/uv in single typed array stream)
- `audioworklet_processor.js` — Base64-encoded AudioWorkletProcessor string (loads on separate core)
- `zero_alloc_loops.js` — O(1) GC-proof pipelines for coordinate math and audio stream computation

## Key Constraint
No object instantiation during frame execution. All loops operate on pre-allocated typed arrays.
