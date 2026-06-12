# Sprint 4 — Muscular Elasticity & Skin Deformation Fields

## Objective
Implement vertex shader blend-skinning with parametric muscle maps. Build GPU-based morph targets for real-time facial micro-expressions.

## Deliverables
- `blend_skinning.glsl` — GLSL vertex shader (4 bone indices per vertex, linear blend skinning)
- `muscle_maps.js` — Parametric activation maps (joint angular delta → surface normal scaling)
- `micro_expressions.js` — GPU morph target array (face shape offsets as vertex attributes)

## Integration
Muscle maps read angular deltas from Sprint 3's IK solver. Morph targets triggered by Sprint 7's behavior tree.
