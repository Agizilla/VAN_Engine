# OpenCode Integration Instructions

## Project Root
`C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\`

## Current Status
All 20 ISO rules (001-020) are implemented. Substrate is complete.

## Files to Materialize

### Core C# Files (VAN_Engine/core/)
| File | Content | Source |
|------|---------|--------|
| IsographicQuaternion.cs | Quaternion with coupled dimensions | Earlier code dump |
| ISO_Rules.json | All 20 ISO rules | Earlier code dump |
| ArchetypalFSM.cs | ISO_011 Tarot state machine | Gemini final deliverable |
| ISelfValidating.cs | ISO_012 validation interface | Gemini ISO_012/015 deliverable |
| AuditEvent.cs | ISO_015 immutable snapshot | Gemini ISO_012/015 deliverable |
| SubstrateSupervisor.cs | ISO_012+015 coordinator | Gemini ISO_012/015 deliverable |
| IBoundedExecutor.cs | ISO_014+017 interface | Gemini ISO_013-018 deliverable |
| DeterministicExecutor.cs | ISO_014 timeout enforcement | Gemini ISO_013-018 deliverable |
| IdempotentIndexManager.cs | ISO_016+018 caching | Gemini ISO_013-018 deliverable |
| DegradationRouter.cs | ISO_013 fallback handler | Gemini ISO_013-018 deliverable |

### Python Files (VAN_Engine/)
| File | Path | Source |
|------|------|--------|
| IsographicQuaternion.py | core/ | Earlier code dump |
| drift_gating.py | modules/ | Earlier code dump |
| tarot_fsm.py | modules/ | Earlier code dump |
| test_invariance.py | tests/ | Earlier code dump |
| test_drift_gating.py | tests/ | Earlier code dump |
| gemini_bridge.py | bridges/ | Earlier code dump |
| mm458_debug.py | projects/MM458/ | Earlier code dump |
| bootstrap.py | root/ | Latest DeepSeek deliverable |

### Configuration Files
| File | Path | Content |
|------|------|---------|
| bootstrap.yaml | config/ | Bootstrap settings |
| OpenCodeInstructions.md | root/ | This file |

### Documentation Files
| File | Path |
|------|------|
| SPECIFICATION.html | root/ |
| INVESTMENT_BRIEFING.html | root/ |

## Directory Structure to Create
/VAN_Engine/
├── bootstrap.py
├── SPECIFICATION.html
├── INVESTMENT_BRIEFING.html
├── OpenCodeInstructions.md
├── config/
│ └── bootstrap.yaml
├── core/
│ ├── IsographicQuaternion.cs
│ ├── IsographicQuaternion.py
│ ├── ISO_Rules.json
│ ├── ArchetypalFSM.cs
│ ├── ISelfValidating.cs
│ ├── AuditEvent.cs
│ ├── SubstrateSupervisor.cs
│ ├── IBoundedExecutor.cs
│ ├── DeterministicExecutor.cs
│ ├── IdempotentIndexManager.cs
│ └── DegradationRouter.cs
├── modules/
│ ├── drift_gating.py
│ └── tarot_fsm.py
├── tests/
│ ├── test_invariance.py
│ └── test_drift_gating.py
├── bridges/
│ └── gemini_bridge.py
├── logs/ (created by bootstrap)
├── memory/ (created by bootstrap)
└── projects/
└── MM458/
└── mm458_debug.py

## Execution Instructions

### After materializing all files:
```bash
cd C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine
python bootstrap.py --verbose
```

Expected output:
```
======================================================================
VAN_ENGINE BOOTSTRAP COMPLETE
======================================================================
✓ Environment: Windows | Python 3.10.x
✓ Root: C:\...\VAN_Engine
✓ Index: Created (empty)
✓ ISO Rules: Validated (20 rules)
✓ Services: Running
✓ Bridges: None (ISO_019)
----------------------------------------------------------------------
Stage Results:
  ✅ Environment: Environment validation passed (Xms)
  ✅ Index: Index created (empty) (Xms)
  ✅ ISO_Rules: ISO rules validation passed (Xms)
  ✅ Services: Services initialized (Xms)
  ✅ Bridges: No external bridges active (ISO_019 compliant) (Xms)
----------------------------------------------------------------------
Total bootstrap time: Xms

🟢 SYSTEM READY
   Listening for commands...
   ISO_019: No external bridges active
   ISO_020: Anti-hallucination enforced
======================================================================
```

## Rules for OpenCode
- Never merge across project roots — Each project stays in its own folder
- Windows encoding — All Python files include UTF-8 wrapper at top
- Bridges disabled by default — ISO_019 enforcement
- Ask before overwriting existing files
- After materialization, run bootstrap.py to verify
