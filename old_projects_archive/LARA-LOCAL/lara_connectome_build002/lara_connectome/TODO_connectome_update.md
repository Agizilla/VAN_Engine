# LARA TODO — Connectome Update
**Version:** 0.1.1 | **Build:** 002 | **Date:** 2026-02-23

## ✅ DONE (Build 002 additions)

| # | Task | Notes |
|---|------|-------|
| D03 | lara_core/connectome.py — Full neural graph engine (961 lines) | MobjectNode, ConnectomeEdge, PlasticityRule, Connectome, ConnectomeManager |
| D04 | lara_core/persona_v2.py — Connectome-integrated PersonaManager | Drop-in replacement, auto-creates connectome on persona creation |
| D05 | lara_core/voice_v2.py — Connectome-integrated VoiceManager | Reads synthesised params, applies to Coqui/pyttsx3/stub |
| D06 | lara_core/command_router_v2_patch.py — New connectome commands | connectome describe/synthesise/trigger/set-weight/set-modulator, rate, set emotion |
| D07 | lara_core/lara_v2_boot_patch.py — Boot wiring documentation | Step-by-step patch guide |
| D08 | config_defaults/config_connectome_additions.yaml | All connectome config toggles |
| D09 | config_defaults/personas_example/vivian_connectome_example.json | Full 15-node example with real weights |
| D10 | docs/CONNECTOME_GUIDE.md — Developer guide (362 lines) | Schema ref, design rationale, upgrade checklist, example session |

## 📋 PENDING (Build 002 — remaining integration work)

| Priority | # | Task | Notes |
|----------|---|------|-------|
| P1 | C01 | Apply boot patch to lara.py | Wire ConnectomeManager into boot() |
| P1 | C02 | Apply mixin to command_router.py | Add ConnectomeCommandMixin inheritance |
| P1 | C03 | Add DIR_CONNECTOMES to constants.py | One-line addition |
| P1 | C04 | Update housekeeping.py for daily_decay trigger | Auto-fire on schedule |
| P2 | C05 | skills_builtin/connectome_visualise_skill.py | ASCII/Mermaid graph renderer |
| P2 | C06 | skills_builtin/connectome_export_skill.py | Export graph as CSV edges or Gephi format |
| P3 | C07 | TUI panel: live connectome weight bars | Textual panel showing real-time node weights |
| P3 | C08 | Add connectome.diff() to self-test output | Show before/after weight changes in self-test report |
| P3 | C09 | Connectome inheritance | Child persona inherits parent connectome structure, overrides selected nodes |
| P3 | C10 | Multi-persona influence | Persona A's emotion state can modulate Persona B's global weights |

## 📋 PENDING — Phase 3 (Build 003, unchanged from Build 001)

| # | Task |
|---|------|
| P26 | TUI dashboard (Textual) |
| P27 | Real GPG verification |
| P28 | cgroup/Job Object resource limits |
| P29 | Pre-built wheelhouse |
