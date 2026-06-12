# Sprint 3 — Analytical IK Framework & Skeleton Solvers

## Objective
Replace keyframe interpolation with full analytical inverse kinematics. Build a CCD/FABRIK quaternion chain solver and GPU-driven surface raycaster.

## Deliverables
- `quaternion_ik.js` — CCD/FABRIK skeletal chain solver (pure quaternion math, no iteration objects)
- `surface_raycaster.js` — GPU bounding-box raycaster (limb → surface trace)
- `joint_clamping.js` — Per-axis rotational angle limits preventing hyper-extension

## Integration
IK solver reads/writes quaternion history from Sprint 1's buffer partition. Raycaster feeds surface contact points back into IK targets.
