# Sprint 6 — Parametric Vocal Morphing Weight Filters

## Objective
Build linear transformation filters for dynamic formant shifting. Implement punctuation-driven pitch curves and real-time lip-sync.

## Deliverables
- `linear_adapters.js` — Weight matrix filters (formant characteristics → vector operations)
- `pitch_trajectory.js` — F0 curve generator (punctuation/text-length → smooth pitch contour)
- `lipsync_bridge.js` — Audio amplitude + phoneme status → face geometry morph targets

## Integration
Morphing adapters read from Sprint 7's psychological state. Lip-sync bridge writes to Sprint 4's morph target array.
