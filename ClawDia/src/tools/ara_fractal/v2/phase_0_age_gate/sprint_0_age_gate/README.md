# Sprint 0 — Age Gate & Consent Verification

## Objective
Implement a mandatory age verification gate that blocks all engine content until the user affirms they are of legal age and consents to viewing adult-oriented erotic material.

## Deliverables
- `age_gate.js` — Session-based gate logic (DOB validation, terms check, sessionStorage token)
- `age_gate.css` — Full-viewport overlay styling (dark theme, centered card, dropdown selects)
- Integrated into all 3 UI entry points (index.html, marketplace.html, wordmesh.html)

## Architecture
- **Storage**: `sessionStorage` (clears on tab close — no persistent age records)
- **Token key**: `ara_age_verified`
- **Gate position**: First child of `<body>`, z-index 9999, visible by default
- **Inline script**: Synchronous non-module `<script>` before all other scripts
- **Double-check**: Module scripts verify gate before initializing engine (throws if missing)

## Validation Rules
1. All 3 DOB fields required (month/day/year)
2. Age must be 18+ (compared to `new Date(now.getFullYear() - 18, ...)`)
3. Terms checkbox must be checked
4. Invalid/missing fields disable the ENTER button
5. Underage displays rejection message and blocks all access

## Entry Point
Loaded as inline `<script>` before any module imports. Runs synchronously on DOM parse. No engine code executes until gate passes.

## Files
- `v2/phase_0_age_gate/sprint_0_age_gate/README.md` — This document
- `v2/phase_5_system_integration/ui/index.html` — Fractal viewer with age gate
- `v2/phase_5_system_integration/ui/marketplace.html` — Marketplace with age gate
- `v2/phase_5_system_integration/ui/wordmesh.html` — Word graph with age gate
