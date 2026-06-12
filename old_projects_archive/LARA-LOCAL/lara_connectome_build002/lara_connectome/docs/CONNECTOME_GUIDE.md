# LARA Connectome System — Developer Guide
**Version:** 0.1.1 | **Build:** 002 | **Date:** 2026-02-23  
**Inspired by:** *Connectome: How the Brain's Wiring Makes Us Who We Are* — Sebastian Seung

---

## Conceptual Overview

In Seung's framework, **you are your connectome** — the complete wiring pattern of your neurons defines your personality, memories, and identity. We apply this metaphor directly to Lara's personas:

| Neuroscience | Lara Connectome |
|---|---|
| Neuron | Mobject node (one voice/emotion trait) |
| Synapse | Edge with influence weight |
| Signal strength | Edge influence × node weight |
| Neuromodulator (dopamine, serotonin) | Global family weight |
| Synaptic plasticity (LTP/LTD) | PlasticityRule with trigger |
| Learning | fire_trigger() → weight delta |
| Connectome (full wiring) | Persona's `_connectome.json` |
| Identity | Synthesised parameter set from graph traversal |

The key insight: **Vivian is not a fixed set of parameters. She is a dynamic network that evolves with every interaction, training session, and piece of media she processes.**

---

## Architecture

```
~/lara_data/
├── connectomes/
│   ├── vivian_connectome.json          ← Full neural graph for Vivian
│   ├── vivian_alt_connectome.json      ← Different wiring for alt persona
│   └── ...
```

### Node Types (Mobjects)

Each node encodes one modular trait of the persona:

```
Voice family:     voice_pitch | voice_tempo | voice_timbre | voice_energy
Emotion family:   emotion_valence | emotion_arousal | emotion_dominance  
Rhythm family:    rhythm_stress | rhythm_pause | rhythm_cadence
Speech family:    speech_register | speech_vocabulary | speech_syntax
Prosody family:   prosody_emphasis | prosody_melody
```

### Connection Directions

| Direction | Meaning | Analogy |
|---|---|---|
| `forward` | A influences B | Excitatory synapse |
| `feedback` | B reaches back to A | Recurrent connection |
| `bidirectional` | A↔B mutual influence | Gap junction |

### Activation Functions

| Function | Formula | Use Case |
|---|---|---|
| `sigmoid` | 1/(1+e^-x) | Default — prevents runaway amplification |
| `linear` | clamp(x, 0, 1) | Direct scaling, predictable |
| `relu` | max(0, x) | Only positive influence |

---

## Synthesis: How Parameters Are Computed

```
Graph traversal order (topological sort, Kahn's algorithm):
  1. Start from nodes with no incoming forward edges
  2. Process each node: effective_output = params × sigmoid(weight + Σ incoming_signals)
  3. Propagate outward: signal_to_next = weight × edge_influence × family_scale
  4. Repeat until all nodes computed
  5. Collect {node_type: {param: value}} for all nodes

Final TTS parameters (voice_v2.connectome_to_tts_params):
  voice_pitch.base_hz → semitone offset from neutral (175 Hz)
  voice_tempo.syllables_per_sec → speed multiplier (4.5 syl/s = 1.0×)
  voice_energy.amplitude → TTS energy/gain
  emotion_valence.value → warm pitch offset (positive = brighter)
  emotion_arousal.value → energy boost multiplier
  prosody_melody.range_semitones → pitch variation range
```

---

## Plasticity: How the Persona Learns

Each `PlasticityRule` defines:
- **trigger**: what event fires this rule
- **target_id**: which node (or `"*"` for all nodes)
- **condition**: a simple expression, e.g. `"weight < 0.8"` or `"always"`
- **delta**: how much to add/subtract
- **decay**: per-step pull toward neutral (0.5) — prevents drift

### Built-in Triggers

| Trigger | When to Fire | Effect |
|---|---|---|
| `audio_training` | New voice model registered | Strengthens pitch/timbre/tempo |
| `user_rating_positive` | User rates output good | Reinforces energy + valence |
| `user_rating_negative` | User rates output bad | Reduces arousal + energy |
| `new_lyrics` | Lyrics generated | Boosts rhythm + melody |
| `chat_interaction` | Each conversation turn | Gradual register/vocab growth |
| `media_ingestion` | Image/video/OCR processed | Brief arousal spike |
| `daily_decay` | Housekeeping runs | Soft-cap all weights ≤ 0.98 |

### Adding Custom Rules

```python
from lara_core.connectome import PlasticityRule

mgr = components["connectome"]
c = mgr.load("vivian")
c.add_plasticity_rule(PlasticityRule(
    rule_id   = "pr_custom_singing",
    trigger   = "new_lyrics",
    target_id = "vivian_pm",         # melody node
    condition = "weight < 0.9",
    delta     = +0.06,
    decay     = 0.002,
    max_weight= 0.90,
    description = "Singing sharpens melodic range faster"
))
mgr.save(c)
```

---

## Commands

### Connectome Commands
```
connectome describe [persona_id]               Full neural state
connectome synthesise [persona_id]             Computed parameter table
connectome trigger [persona_id] [event]        Manually fire plasticity
connectome set-weight [pid] [node_id] [0-1]    Override a node weight
connectome set-modulator [pid] [family] [0-1]  Adjust global modulator
connectome list                                List all stored connectomes
```

### Rating Commands
```
rate positive    → fires user_rating_positive on active persona
rate negative    → fires user_rating_negative on active persona
```

### Emotion Direct Control
```
set emotion valence 0.7      → positive/bright mood
set emotion arousal 0.3      → calm, slow, soft
set emotion dominance 0.8    → assertive, formal
```

### Enhanced Persona Creation
```
Create a persona named Vivian pitch 200 valence 0.7 formal 0.8 using frame 7 from vid2.mp4
```
The `pitch`, `valence`, `formal`, `tempo` keywords seed the connectome with custom initial params.

---

## Upgrade Checklist (applying to existing Lara install)

### Step 1 — Copy new files
```bash
cp lara_core/connectome.py        ~/lara_project/lara_core/
cp lara_core/persona_v2.py        ~/lara_project/lara_core/
cp lara_core/voice_v2.py          ~/lara_project/lara_core/
cp lara_core/command_router_v2_patch.py  ~/lara_project/lara_core/
```

### Step 2 — Update config.yaml
Add the `connectome:` block from `config_connectome_additions.yaml` to your
`~/lara_data/config.yaml`.

### Step 3 — Update constants.py
Add to DIR constants:
```python
DIR_CONNECTOMES = "connectomes"
```

### Step 4 — Update lara.py boot()
Replace:
```python
from lara_core.persona import PersonaManager
from lara_core.voice import VoiceManager
```
With:
```python
from lara_core.connectome import ConnectomeManager
from lara_core.persona_v2 import PersonaManager
from lara_core.voice_v2 import VoiceManager
```

Add to boot sequence (after cache, before personas):
```python
connectome = ConnectomeManager(data_dir, config, logger)
personas = PersonaManager(data_dir, config, connectome, logger)
voice    = VoiceManager(data_dir, config, connectome, logger)
```

Add `"connectome": connectome` to the return dict.

### Step 5 — Update CommandRouter
In `command_router.py __init__`, add:
```python
def __init__(self, ..., connectome_mgr=None, ...):
    self.connectome_mgr = connectome_mgr
```

Add to `route()` method:
```python
if low.startswith("connectome"):
    return self._handle_connectome_cmd(raw)
if low.startswith("rate "):
    return self._handle_rate(raw)
if low.startswith("set emotion"):
    return self._handle_set_emotion(raw)
```

Mix in `ConnectomeCommandMixin` for the handler methods:
```python
from lara_core.command_router_v2_patch import ConnectomeCommandMixin
class CommandRouter(ConnectomeCommandMixin):
    ...
```

### Step 6 — Update housekeeping.py
Add daily_decay trigger to run_housekeeping():
```python
# After existing cleanup, add:
active_personas = [p.stem for p in (data_dir / "personas").glob("*.json")]
if hasattr(cache, 'get'):
    from lara_core.connectome import ConnectomeManager
    cmgr = ConnectomeManager(data_dir, config, logger)
    for pid in active_personas:
        if cmgr.exists(pid):
            cmgr.trigger(pid, "daily_decay", auto_save=True)
```

---

## JSON Schema Reference

```json
{
  "persona_id": "vivian",
  "persona_name": "Vivian",
  "connectome": {
    "nodes": {
      "NODE_ID": {
        "mobject_id": "string (unique)",
        "node_type":  "voice_pitch | voice_tempo | ... (see NODE_TYPES)",
        "params":     { "param_name": float_value },
        "weight":     "float [0.0–1.0] — base influence strength",
        "activation": "sigmoid | linear | relu",
        "description":"string"
      }
    },
    "connections": [
      {
        "source_id":  "string (must match a node mobject_id)",
        "target_id":  "string (must match a node mobject_id)",
        "influence":  "float [0.0–1.0] — synaptic strength",
        "direction":  "forward | feedback | bidirectional",
        "label":      "string (human-readable description)"
      }
    ],
    "global_weights": {
      "voice_family":   "float [0.0–2.0]",
      "emotion_family": "float [0.0–2.0]",
      "rhythm_family":  "float [0.0–2.0]",
      "speech_family":  "float [0.0–2.0]",
      "prosody_family": "float [0.0–2.0]"
    },
    "plasticity_rules": [
      {
        "rule_id":    "string (unique)",
        "trigger":    "string (event name)",
        "target_id":  "string (node id or '*' for all)",
        "condition":  "string ('always' or simple Python expression)",
        "delta":      "float (weight change amount, can be negative)",
        "decay":      "float (per-step pull toward 0.5, 0=off)",
        "max_weight": "float [0.0–1.0]",
        "min_weight": "float [0.0–1.0]",
        "description":"string"
      }
    ]
  },
  "metadata": {
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime",
    "version": "int (auto-incremented on save)",
    "lara_version": "string",
    "build": "string",
    "schema": "connectome_v1",
    "plasticity_trigger_count": "int",
    "total_adaptations": "int"
  }
}
```

---

## Example Session

```
You → create a persona named Vivian pitch 195 valence 0.52 formal 0.58 using frame 7 from vid2.mp4
Lara → Persona 'Vivian' created (id=vivian)
       Connectome initialised | 15 nodes | 17 edges | 14 plasticity rules
       Emotional State: Valence=0.520  Arousal=0.500  Dominance=0.500

You → sing a song about today's progress
Lara → [Connectome voice params: speed=1.07, pitch=+0.8st, energy=0.78]
       Song performed. Tone: neutral, moderate energy.
       new_lyrics trigger fired → vivian_pm: 0.650→0.690

You → rate positive
Lara → 👍 Positive rating applied to vivian.
       Connectome adapted: ev: 0.630→0.670

You → connectome describe vivian
Lara →
  Connectome — Vivian (vivian)
    Schema v3 | nodes=15 | edges=17 | plasticity_rules=14
    Total adaptations: 3
    Updated: 2026-02-23 14:32:17
    
    Emotional State (VAD):
      Valence=0.670  Arousal=0.500  Dominance=0.540
    
    Global Modulators:
      voice_family         1.000
      emotion_family       0.870
      ...

You → connectome trigger vivian audio_training
Lara → Trigger 'audio_training' → 3 adaptation(s) for vivian:
       vivian_vp    0.820 → 0.860  (Δ+0.0400) via rule pr_audio_pitch
       vivian_vi    0.770 → 0.800  (Δ+0.0300) via rule pr_audio_timbre
       vivian_vt    0.730 → 0.750  (Δ+0.0200) via rule pr_audio_tempo

You → set emotion arousal 0.8
Lara → Emotion arousal set to 0.800 for vivian.
       Next TTS will reflect higher energy/tempo.

You → toggle-online-mode on gemini
You → ask for a skill that can visualise the connectome as a graph
```

---

## Design Decisions

**Why sigmoid?** Prevents any single node or edge from dominating. Even if a node has weight 1.0 and receives strong input, sigmoid(2.0) = 0.88 — a reasonable ceiling. Without this, a chain of high-weight nodes would produce explosive parameter values.

**Why keep plasticity rules in JSON?** They're part of the persona's identity — a trained user should be able to inspect, hand-tune, and version-control exactly how Vivian learns. Hiding this in code would break that transparency.

**Why global family weights?** Just as dopamine modulates entire brain regions rather than individual synapses, global weights let you "turn up" Vivian's emotionality or vocality as a single dial without touching 15 node weights individually.

**Why VAD for emotion?** Valence-Arousal-Dominance is the standard dimensional model in affective computing. It maps directly to audible speech properties: valence → pitch warmth, arousal → tempo/energy, dominance → register/timbre.
