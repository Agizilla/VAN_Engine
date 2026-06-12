# Oera Linda Simulator — Implementation vs. Specification Gap Analysis

## Executive Summary

The current implementation (**4-tier feature board sprint**) addresses a subset of the Master_Prompt requirements but diverges significantly in scope and philosophy.

**Current**: Game-like CI/CD tracker with workspace management, threats, tech tree, citizen skills, trade routes, scripting, git integration.

**Specification**: Full community governance simulation with 27 laws, 22 person types, Juul Wheel economy, generational mechanics, crime/justice tribunal, and sovereignty/language purity dual meters based on the Oera Linda Tex.

**Gap**: ~60-70% missing core systems. Major omissions include law engine, person AI, economy formulas, most person types, crime escalation, faction diplomacy, and generational mechanics.

---

## 1. Architecture Comparison

### Current Implementation
```
├── Tier 1: Foundation
│   ├── MultiWorkspaceManager ✓
│   ├── SaveLoad (JSON only) ✓
│   ├── FileSystemWatcher ✓
│   ├── Camera/Zoom/Minimap ✓
│   └── SettingsManager ✓
├── Tier 2: Core Gameplay
│   ├── DependencyGraphAnalyzer ✓
│   ├── OverlapDetector ✓
│   ├── SharedLibraryZone ✓
│   ├── HistoryTimeline ✓
│   ├── InspectorPanel ✓
│   ├── RefactoringActions ✓
│   ├── DirectiveConfig ✓
│   └── PhaseTransition ✓
├── Tier 3: Advanced
│   ├── ThreatSystem ✓
│   ├── HouseUpgradeSystem (Hamlet→Citadel) ✓
│   ├── GeckoShift (partial) ✓
│   ├── CitizenSkillSystem ✓
│   ├── TradeRouteSystem ✓
│   ├── EventSocketServer ✓
├── Tier 4: Endgame
│   ├── GitIntegration ✓
│   ├── ReportGenerator ✓
│   ├── ScriptingEngine (Lua) ✓
│   └── CommunityScoreboard ✓
└── File Analysis
    ├── TexStaticAnalyzer ✓
    ├── LanguageAnalyzerFactory ✓
    └── Multi-language support (.cs, .py, .ts, .rs, .go) ✓
```

### Master_Prompt Specification
```
├── Core Game Systems
│   ├── GameState (42 fields) ✗ Only partial
│   ├── Resources (7 types) ✗ Not implemented
│   ├── Game Loop (29-step sequence) ✗ Missing
│   └── Constants (42 values) ✗ Only SCREEN/MAP basics
├── Person System
│   ├── PersonType enum (22 types) ✗
│   ├── Person dataclass (21 fields) ✗
│   ├── PersonAI (22 behavior trees) ✗
│   ├── LegacySystem (aging, reproduction, inheritance) ✗
│   └── Colors & symbols (22 mappings) ✗
├── Law System
│   ├── Law enum (12 citadel laws) ✗
│   ├── FryasDirective (5 bitflags) ✗
│   ├── LawEngine (7 methods) ✗
│   ├── Minno's justice laws (15 penalties) ✗
│   └── BuildState enum ✗
├── Economy System
│   ├── Resources (7 types) ✗
│   ├── Production formulas (6 types) ✗
│   ├── Juul Wheel (6 spokes × 5 effects) ✗
│   ├── TradeSystem ✗
│   └── Military School ✗
├── Combat System
│   ├── CVE threat model (5 layers) ✗ (Simplified to 1)
│   ├── Invasion physics (radar approach) ✗
│   └── Combat resolution ✗
├── Crime & Justice
│   ├── CrimeRecord dataclass ✗
│   ├── CRIME_PENALTIES (6 crimes × escalation) ✗
│   ├── TribunalSystem ✗
│   └── Crime escalation (3-strike theft, 2-strike backbiting) ✗
├── Diplomacy
│   ├── FactionReputation (7 factions) ✗
│   ├── Trade routes (0-5) ✗ (Implemented but different context)
│   └── Foreign population effects ✗
├── Sovereignty & Language Purity
│   ├── Sovereignty meter (5 tiers) ✗
│   ├── 40+ modifiers ✗
│   ├── Language purity meter (4 tiers) ✗
│   └── Victory/Loss conditions ✗
├── Lamp of Texland
│   ├── Lamp mechanics ✗
│   ├── Folk Mother system ✗
│   ├── Maiden system ✗
│   ├── Adelbond rule ✗
│   └── Apprentice mechanics ✗
└── UI & Rendering
    ├── Renderer (19 draw methods) ✗
    ├── 15 UI panels ✗
    ├── 7 buildings ✗
    └── Particle system ✗
```

---

## 2. Detailed Gap Analysis by System

### A. Core Game State

| Field | Spec | Current | Status |
|-------|------|---------|--------|
| year | int | int (in TimeController) | ⚠️ Different location |
| sovereignty | float 0-100 | Not tracked | ❌ Missing |
| language_purity | float 0-100 | Not tracked | ❌ Missing |
| lamp_burning | bool | Not tracked | ❌ Missing |
| resources (7 types) | ResourcePack | None | ❌ Missing |
| people[] | list[Person] | None | ❌ Missing |
| selected_person | Person\|None | None | ❌ Missing |
| message_log | deque[str] | message_log exists | ⚠️ Different impl |
| crime_log | deque[str] | None | ❌ Missing |
| war_active | bool | Not tracked | ❌ Missing |
| emergency_active | bool | Not tracked | ❌ Missing |
| juul_spoke/progress | int | Not implemented | ❌ Missing |
| faction_reputation | dict | None | ❌ Missing |
| plague_risk_factor | float | None | ❌ Missing |
| tribunal_active | bool | None | ❌ Missing |
| **Coverage** | **42 fields** | **~5 fields** | **~12%** |

### B. Person System

| Component | Spec | Current | Status |
|-----------|------|---------|--------|
| PersonType enum (22 types) | Required | None | ❌ Missing |
| Person dataclass (21 fields) | Required | ProjectHouse exists | ❌ Wrong model |
| PersonAI (22 behavior trees) | Required | None | ❌ Missing |
| LegacySystem (aging/death/inheritance) | Required | None | ❌ Missing |
| Colors & symbols | 22 mappings | None | ❌ Missing |
| **Coverage** | **22 types** | **0 types** | **0%** |

### C. Law System

| Component | Spec | Current | Status |
|-----------|------|---------|--------|
| Law enum (12 laws) | Required | None | ❌ Missing |
| FryasDirective (5 bitflags) | Required | Partial in TexStaticAnalyzer | ⚠️ Incomplete |
| LawEngine (7 methods) | Required | None | ❌ Missing |
| Minno's laws (15 penalties) | Required | None | ❌ Missing |
| BuildState enum | Required | BuildState exists | ✓ Partial match |
| **Coverage** | **27 laws total** | **1 enum** | **~5%** |

### D. Economy System

| Component | Spec | Current | Status |
|-----------|------|---------|--------|
| Resources (7 types) | food, wood, stone, metal, wealth, gold, slaves | None | ❌ Missing |
| Production formulas (6 types) | farming, wood, stone, metal, wealth, gold | None | ❌ Missing |
| Juul Wheel (6 spokes) | 333-year cycle with 6 spokes | Not implemented | ❌ Missing |
| JuulWheel effects (6×5) | 6 spokes × 5 effect types | None | ❌ Missing |
| TradeSystem | Navigator, trade items, contamination | TradeRouteSystem exists | ⚠️ Different scope |
| Military School | Build cost, training effects | None | ❌ Missing |
| **Coverage** | **Full economy loop** | **Partial trade routes** | **~10%** |

### E. Combat System

| Component | Spec | Current | Status |
|-----------|------|---------|--------|
| CVE (5 layers) | Code contamination, supply chain, invasion, plague, priest | ThreatSystem (simplified) | ⚠️ ~30% coverage |
| Invasion physics | Radar approach, speed, arrival | ThreatSystem exists | ⚠️ Simplified |
| Combat resolution | Damage, death, wounding, widow spawn | None | ❌ Missing |
| Militia defense | Reduce plunder, patrol | None | ❌ Missing |
| **Coverage** | **Full CVE + combat** | **Simplified threats** | **~20%** |

### F. Crime & Justice System

| Component | Spec | Current | Status |
|-----------|------|---------|--------|
| CrimeRecord dataclass | Required | None | ❌ Missing |
| CRIME_PENALTIES (6 crimes) | theft, violence, arson, backbiting, treason | None | ❌ Missing |
| Crime escalation (3-strike) | Theft: restore, mines, no protection | None | ❌ Missing |
| TribunalSystem | Case generation, judgment | None | ❌ Missing |
| Crime log panel | deque[str] | None | ❌ Missing |
| **Coverage** | **Complete justice system** | **None** | **0%** |

### G. Diplomacy System

| Component | Spec | Current | Status |
|-----------|------|---------|--------|
| FactionReputation (7 factions) | Magy, Finn, Gaul, Jutlander, Dane, Twisklander, Geertman | None | ❌ Missing |
| Reputation range (-100 to 100) | Required | None | ❌ Missing |
| Trade routes (0-5) | Navigator auto-trade, decay | TradeRouteSystem exists | ⚠️ Different model |
| Foreign population effects | Plague risk, language decay | None | ❌ Missing |
| **Coverage** | **7 factions + trade** | **Abstract trade routes** | **~15%** |

### H. Sovereignty & Language Purity

| Component | Spec | Current | Status |
|-----------|------|---------|--------|
| Sovereignty meter (0-100%) | 5 tiers: Gold/Green/Yellow/Orange/Red | Not implemented | ❌ Missing |
| Sovereignty modifiers (40+) | Victory bonus, starvation penalty, etc. | None | ❌ Missing |
| Language purity meter (0-100%) | 4 tiers: Pure/Corrupted/Decaying/Lost | Not implemented | ❌ Missing |
| Language modifiers (20+) | Foreign type penalties, etc. | None | ❌ Missing |
| Victory condition | year >= 100 AND sovereignty >= 70 | None | ❌ Missing |
| Loss condition | sovereignty <= 0 | None | ❌ Missing |
| **Coverage** | **Dual meters + 60+ modifiers** | **None** | **0%** |

### I. Lamp of Texland

| Component | Spec | Current | Status |
|-----------|------|---------|--------|
| Lamp mechanics | Burn status, extinguish on FM death | None | ❌ Missing |
| Folk Mother system | Immortal leader, +1 sov AI | None | ❌ Missing |
| Maiden system | Lamp keepers, messengers | None | ❌ Missing |
| Adelbond rule | Noble council rule if FM dies | None | ❌ Missing |
| Apprentice system | Inherits skills from mentor | None | ❌ Missing |
| **Coverage** | **Complete spiritual system** | **None** | **0%** |

### J. UI & Rendering

| Component | Spec | Current | Status |
|-----------|------|---------|--------|
| Renderer (19 draw methods) | Main drawing system | DashboardView exists | ⚠️ Different impl |
| Top bar UI (13 elements) | Sovereignty, language, year, resources, lamp | Partial | ⚠️ ~30% coverage |
| Message log panel | deque display | Exists | ✓ Implemented |
| Person panel | Selected person info | InspectorPanel | ✓ Similar |
| Faction panel | Faction reputation display | None | ❌ Missing |
| Juul Wheel render | 6-spoke visualization | None | ❌ Missing |
| Radar | Invasion approach display | None | ❌ Missing |
| Action menu | Work/Train/Trade/Pray/Patrol | None | ❌ Missing |
| **Coverage** | **Complete 15+ panels** | **Partial 3-4 panels** | **~20%** |

---

## 3. Scope Divergence

### Current Implementation: Code Management Simulator
- **Focus**: Multi-project CI/CD tracking with gamification
- **Metaphor**: Code files → Citizens; Compliance → Sovereignty; Directives → Laws
- **Mechanics**: Workspace switching, file analysis, threats, tech tree, trade routes, skill progression
- **Vision**: "Manage overlapping projects, detect duplication, track code health"

### Master_Prompt Specification: Historical Governance Simulation
- **Focus**: Community governance based on Oera Linda Tex (14th-century Dutch chronicle)
- **Metaphor**: Actual civilization with people, laws, economy, justice, spirituality
- **Mechanics**: 27 laws, 22 person types, Juul Wheel economy, generational lineage, tribunal justice, sovereignty/language meters
- **Vision**: "Simulate the rise and fall of Frya's folk under immutable law"

### Key Philosophical Differences

| Aspect | Current | Specification |
|--------|---------|---------------|
| Primary Entity | File/Project | Person/Citizen |
| Economy | Implied (trade routes) | Explicit (7 resources, formulas) |
| Justice | Modal cases (Tribunal) | Deep system (crime escalation, penalties, legacy) |
| Generations | Skill inheritance | Full lineage, ultimogeniture, name-on-shield |
| Victory | Implied | year >= 100 AND sov >= 70 |
| Time Scale | Per-workspace | Per-year ticks, 2000-year meta-cycle |
| World | Abstract grid | 20×15 tile map with 22 person types |

---

## 4. Critical Missing Systems (By Priority)

### Tier 0 (Blocking)
1. **GameState** — 42-field core state class (only 5 exist)
2. **PersonType enum & Person class** — 22 types, 21 fields each (0 exist)
3. **Resources struct** — 7 resource types (0 exist)
4. **Game Loop** — 29-step year tick (not implemented)
5. **Law enum** — 12 citadel laws + Minno's justice (not implemented)

### Tier 1 (Foundation Gap)
6. **PersonAI** — 22 behavior trees (not implemented)
7. **LawEngine** — Law enforcement & compliance (not implemented)
8. **LegacySystem** — Aging, death, reproduction, inheritance (not implemented)
9. **EconomySystem** — Resource production & consumption formulas (not implemented)
10. **Sovereignty/Language Purity meters** — Dual meters with 60+ modifiers (not implemented)

### Tier 2 (Feature Gap)
11. **Crime/Justice System** — Crime escalation, tribunal, penalties (not implemented)
12. **JusticeSystem** — Minno's laws, crime records (not implemented)
13. **DiplomacySystem** — 7 factions, reputation tracking (not implemented)
14. **Lamp of Texland** — Folk Mother, Maiden, Apprentice, Adelbond (not implemented)
15. **ParticleSystem** — Emission per build_state (not implemented)

### Tier 3 (UI Gap)
16. **Full Renderer** — 19 draw methods, 15 panels (partial ~20%)
17. **Juul Wheel visualization** — 6-spoke chart (not implemented)
18. **Radar rendering** — Invasion approach display (not implemented)
19. **Faction panel** — Reputation display (not implemented)
20. **Action menu** — Work/Train/Trade/Pray/Patrol (not implemented)

---

## 5. Remediation Plan

### Phase 0: Architectural Decision (Required)
**Question**: Should the implementation pivot to full Master_Prompt compliance, or continue as a CI/CD tracker with light thematic wrapping?

**Option A: Full Pivot** (Recommended for Oera Linda authenticity)
- Abandon "files as citizens" metaphor
- Implement all 22 person types with real AI
- Build full law engine, economy, justice system
- Estimate: 8–12 weeks for one engineer
- Benefit: Complete game; publishable
- Risk: Significant refactor of existing code

**Option B: Hybrid** (Pragmatic)
- Keep current workspace/file system
- Layer in Oera Linda theming without changing core mechanics
- Map: File compliance → Sovereignty; Projects → Factions; Directives → Laws (cosmetic)
- Estimate: 2–3 weeks
- Benefit: Faster delivery; keeps existing work
- Risk: Shallow implementation; doesn't fully capture Master_Prompt vision

**Option C: Continue As-Is** (Status Quo)
- Finish Tier 1-4 CI/CD features as planned
- Mark Oera Linda spec as "reference" but separate from this product
- Estimate: 4–6 weeks to complete Tier 4
- Benefit: Clear scope; on-budget
- Risk: Diverges from Master_Prompt; may feel incomplete

### Phase 1A (Full Pivot): Core State & Person System
```
Week 1-2:
  ├── GameState class (42 fields, serialization)
  ├── Person class (21 fields, all 22 types)
  ├── Resources struct (7 types)
  ├── All enums (Law, PersonType, BuildState, FryasDirective)
  └── Unit tests for all above

Week 3-4:
  ├── Game Loop (29-step year tick)
  ├── LegacySystem (aging, death, reproduction, inheritance)
  ├── PersonAI dispatch system
  └── Initial AI behavior implementations (5 per week, 22 total)
```

### Phase 1B (Full Pivot): Law & Economy
```
Week 5-6:
  ├── LawEngine (all 12 citadel laws + Minno's 15 laws)
  ├── FryasDirective code analysis (5 flags)
  └── Test coverage for law compliance

Week 7-8:
  ├── EconomySystem (all 6 production formulas)
  ├── JuulWheel (6 spokes, 333-year cycle, effects table)
  ├── TradeSystem (Navigator, trade items, contamination)
  └── Military School mechanics
```

### Phase 1C (Full Pivot): Justice & Diplomacy
```
Week 9-10:
  ├── CrimeRecord & CRIME_PENALTIES
  ├── TribunalSystem (case generation, judgment)
  ├── Crime escalation (3-strike, 2-strike, cascades)
  └── Crime log panel

Week 11-12:
  ├── DiplomacySystem (7 factions, reputation -100 to 100)
  ├── Trade route system (0-5, decay, profit sharing)
  ├── Foreign population effects (plague, language)
  └── Faction rep panel
```

### Phase 2: UI & Polish
```
Week 13-14:
  ├── Full Renderer refactor (19 draw methods)
  ├── All 15 UI panels
  ├── Juul Wheel visualization
  ├── Radar display
  └── Action menu
```

---

## 6. Recommendation

**If the goal is "Oera Linda Simulator faithful to Master_Prompt":**
→ **Option A (Full Pivot)** is required. The current implementation, while well-engineered, is in the wrong problem domain. A pragmatic hybrid risks delivering 40% of a game and 60% of a CI tracker — neither compelling.

**If the goal is "Gamified multi-project CI/CD tracker":**
→ **Option C (Continue As-Is)** makes sense. The 4-tier sprint is a solid feature board. Accept that it's inspired by Oera Linda theming but not a faithful simulation.

**If the goal is "Ship something by deadline":**
→ **Option B (Hybrid)** is a middle path. Map file compliance to a "Sovereignty" score, projects to "Factions," and call it "Oera Linda: Code Edition." Fast, thematic, but less authentic.

---

## 7. File-by-File Mapping

### What Maps to Spec

| Current | Spec | Notes |
|---------|------|-------|
| `DashboardView.cs` | Renderer | Only ~20% overlap; needs major refactor |
| `TimePhaseController.cs` | Game Loop | Only time tracking; missing 28/29 steps |
| `ProjectHouse.cs` | (No direct map) | File-based model; incompatible with Person |
| `SovereignState.cs` | GameState | Name collision but different purpose |
| `TexStaticAnalyzer.cs` | FryasDirective analysis | Partial; 3/5 directives implemented |
| `ThreatSystem.cs` | CVE threat model | Simplified; ~30% of spec |
| `HouseUpgradeSystem.cs` | (No direct map) | File building progression |
| `TradeRouteSystem.cs` | Trade system | Different scope; partial |

### What Doesn't Exist

- PersonType.cs, Person.cs (22 types)
- PersonAI.cs (22 behavior trees)
- LawEngine.cs (27 laws)
- EconomySystem.cs (production formulas)
- JusticeSystem.cs (crime escalation)
- DiplomacySystem.cs (7 factions)
- LegacySystem.cs (aging/death/inheritance)
- JuulWheel.cs (333-year economy cycle)
- LampOfTexland.cs (Folk Mother, Maiden, Apprentice)
- 12+ UI panels (faction, radar, action menu, etc.)

---

## 8. Conclusion

The current 4-tier sprint implements a **gamified multi-project manager with Oera Linda theming**, while the Master_Prompt specifies a **faithful simulation of a historical community under immutable law**.

**Alignment**: ~15-20% across all systems
**Coverage by system**:
- Core state: 12%
- Person system: 0%
- Law system: 5%
- Economy: 10%
- Combat: 20%
- Crime/Justice: 0%
- Diplomacy: 15%
- Sovereignty: 0%
- UI: 20%

**Recommendation**: 
1. Clarify product intent (tracker vs. simulator)
2. If simulator: commit to Option A (full pivot, 12-week refactor)
3. If tracker: accept current direction and retrospectively align with Oera Linda cosmetics

**Critical path for faithful spec**: Implement Tier 0 systems (GameState, Person, PersonAI, Laws, Economy, Game Loop) — these block all downstream features.

