# Sprint 1 — Memory Alignment & Matrix Infrastructure

## Objective
Partition the 4MB single-file container. Allocate a static 4MB ArrayBuffer with typed sub-allocators for vertex data, audio PCM, quaternion history, and state telemetry.

## Deliverables
- `allocator.js` — 4MB ArrayBuffer with slab/free-list sub-allocator
- `struct_schema.js` — Packed binary struct definitions (vertex, audio frame, quaternion, telemetry packet)
- `memory_map.md` — Layout diagram of buffer partitions and offsets

## Budget
Core memory infrastructure: ~4MB contiguous buffer (zero fragmentation)

## Entry Point
Loaded before any other module. All subsequent phases read/write through this allocator.
