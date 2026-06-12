"""
LARA — Connectome Engine
Version: 0.1.1 | Build: 002 | Date: 2026-02-23

Inspired by Sebastian Seung's "Connectome: How the Brain's Wiring Makes Us Who We Are".
Models a persona's voice, emotion, rhythm, and speech traits as a weighted neural graph.

Architecture:
  - Nodes     → individual mobjects (modular objects): voice params, emotion, rhythm, pitch...
  - Edges     → directional influence between nodes (synaptic connections)
  - Weights   → scalar influence strengths [0.0 – 1.0]
  - Plasticity→ rules that update weights automatically based on trigger events
  - Synthesis → graph traversal + weighted aggregation produces final TTS/voice parameters

Key design choices:
  - Sigmoid activation: prevents runaway weight amplification
  - Topological sort: processes nodes in dependency order, respecting feedback loops
  - Immutable history: every weight change logged to masterlog.txt via logger
  - Serialised as JSON: the connectome IS the persona's brain — save/load from disk
  - Config-toggled: connectome.enabled in config.yaml

Plasticity triggers (extensible):
  - audio_training   → new voice model registered
  - user_rating      → user thumbs up/down a synthesis output
  - new_lyrics       → fresh lyric content generated
  - chat_interaction → general conversation turn
  - media_ingestion  → image/video processed
"""

import json
import math
import copy
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lara_core.constants import (
    APP_VERSION, BUILD_NUMBER,
    error as fmt_error
)

# ── Constants ────────────────────────────────────────────────

DIR_CONNECTOMES = "connectomes"         # ~/lara_data/connectomes/
FILE_CONNECTOME_SUFFIX = "_connectome.json"

# Recognised mobject node types
NODE_TYPES = {
    "voice_pitch",        # Fundamental frequency shaping
    "voice_tempo",        # Speech rate (syllables per second)
    "voice_timbre",       # Spectral colour / resonance character
    "voice_energy",       # Loudness / amplitude envelope
    "emotion_valence",    # Positive ↔ Negative emotional tone
    "emotion_arousal",    # Calm ↔ Excited activation level
    "emotion_dominance",  # Submissive ↔ Dominant social stance
    "rhythm_stress",      # Lexical stress patterns
    "rhythm_pause",       # Inter-phrase pause duration
    "rhythm_cadence",     # Sentence-ending intonation shape
    "speech_register",    # Formal ↔ Casual language register
    "speech_vocabulary",  # Vocabulary breadth / complexity
    "speech_syntax",      # Syntactic complexity preference
    "prosody_emphasis",   # Which syllables receive stress boosts
    "prosody_melody",     # Overall pitch melody contour
}

# Default parameter ranges per node type
NODE_PARAM_RANGES: Dict[str, Dict[str, Tuple[float, float]]] = {
    "voice_pitch":       {"base_hz": (80.0, 300.0), "variance": (0.0, 1.0)},
    "voice_tempo":       {"syllables_per_sec": (2.0, 8.0), "variance": (0.0, 0.5)},
    "voice_timbre":      {"brightness": (0.0, 1.0), "warmth": (0.0, 1.0)},
    "voice_energy":      {"amplitude": (0.3, 1.0), "attack_ms": (10.0, 200.0)},
    "emotion_valence":   {"value": (-1.0, 1.0)},
    "emotion_arousal":   {"value": (0.0, 1.0)},
    "emotion_dominance": {"value": (0.0, 1.0)},
    "rhythm_stress":     {"strength": (0.0, 1.0), "regularity": (0.0, 1.0)},
    "rhythm_pause":      {"mean_ms": (50.0, 800.0), "variance_ms": (0.0, 300.0)},
    "rhythm_cadence":    {"fall_hz": (0.0, 50.0), "rise_hz": (0.0, 50.0)},
    "speech_register":   {"formality": (0.0, 1.0)},
    "speech_vocabulary": {"richness": (0.0, 1.0)},
    "speech_syntax":     {"complexity": (0.0, 1.0)},
    "prosody_emphasis":  {"strength": (0.0, 1.0)},
    "prosody_melody":    {"range_semitones": (0.0, 24.0)},
}

# Global weight families (analogous to neuromodulators)
GLOBAL_WEIGHT_KEYS = [
    "voice_family",      # Scales all voice_* nodes
    "emotion_family",    # Scales all emotion_* nodes
    "rhythm_family",     # Scales all rhythm_* nodes
    "speech_family",     # Scales all speech_* nodes
    "prosody_family",    # Scales all prosody_* nodes
]

# ── Activation functions ─────────────────────────────────────

def sigmoid(x: float) -> float:
    """Maps any real number to (0, 1). Prevents runaway amplification."""
    return 1.0 / (1.0 + math.exp(-x))

def linear_clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))

def apply_activation(raw: float, mode: str = "sigmoid") -> float:
    if mode == "sigmoid":
        return sigmoid(raw)
    elif mode == "linear":
        return linear_clamp(raw)
    elif mode == "relu":
        return max(0.0, raw)
    return sigmoid(raw)


# ════════════════════════════════════════════════════════════
# Core data classes (plain dicts in JSON, classes in memory)
# ════════════════════════════════════════════════════════════

class MobjectNode:
    """A single modular object — one trait or capability of the persona."""

    def __init__(self, mobject_id: str, node_type: str, params: Dict[str, Any],
                 weight: float = 1.0, activation: str = "sigmoid",
                 description: str = ""):
        self.mobject_id = mobject_id
        self.node_type = node_type
        self.params = dict(params)
        self.weight = linear_clamp(weight)
        self.activation = activation
        self.description = description
        # Runtime: effective output after graph traversal (not persisted)
        self._effective_output: Optional[Dict[str, float]] = None

    def compute_output(self, incoming_influence: float = 0.0) -> Dict[str, float]:
        """
        Compute effective parameter values after applying weight and
        incoming influence from connected nodes.
        Returns dict of param_name → effective_value.
        """
        effective = {}
        total_scale = apply_activation(self.weight + incoming_influence, self.activation)
        for param, value in self.params.items():
            if isinstance(value, (int, float)):
                effective[param] = value * total_scale
            else:
                effective[param] = value  # Non-numeric params pass through
        self._effective_output = effective
        return effective

    def to_dict(self) -> dict:
        return {
            "mobject_id": self.mobject_id,
            "node_type": self.node_type,
            "params": self.params,
            "weight": self.weight,
            "activation": self.activation,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MobjectNode":
        return cls(
            mobject_id=d["mobject_id"],
            node_type=d["node_type"],
            params=d.get("params", {}),
            weight=d.get("weight", 1.0),
            activation=d.get("activation", "sigmoid"),
            description=d.get("description", ""),
        )


class ConnectomeEdge:
    """A directional synaptic-like connection between two mobject nodes."""

    DIRECTIONS = {"forward", "feedback", "bidirectional"}

    def __init__(self, source_id: str, target_id: str,
                 influence: float = 0.5,
                 direction: str = "forward",
                 label: str = ""):
        self.source_id = source_id
        self.target_id = target_id
        self.influence = linear_clamp(influence)
        self.direction = direction if direction in self.DIRECTIONS else "forward"
        self.label = label

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "influence": self.influence,
            "direction": self.direction,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ConnectomeEdge":
        return cls(
            source_id=d["source_id"],
            target_id=d["target_id"],
            influence=d.get("influence", 0.5),
            direction=d.get("direction", "forward"),
            label=d.get("label", ""),
        )


class PlasticityRule:
    """
    Defines how a node's weight changes when a trigger event fires.

    trigger:    event name (audio_training, user_rating, new_lyrics, ...)
    target_id:  mobject_id to modify (or "*" for all nodes)
    condition:  comparison string, e.g. "weight < 0.8" or "always"
    delta:      amount to add/subtract from weight (can be negative)
    decay:      optional per-step decay applied to weight (0 = no decay)
    max_weight: upper bound after adaptation
    min_weight: lower bound after adaptation
    """

    def __init__(self, rule_id: str, trigger: str, target_id: str,
                 condition: str = "always", delta: float = 0.05,
                 decay: float = 0.0, max_weight: float = 1.0,
                 min_weight: float = 0.0, description: str = ""):
        self.rule_id = rule_id
        self.trigger = trigger
        self.target_id = target_id
        self.condition = condition
        self.delta = delta
        self.decay = decay
        self.max_weight = max_weight
        self.min_weight = min_weight
        self.description = description

    def evaluate_condition(self, current_weight: float, context: Dict[str, Any] = None) -> bool:
        """Evaluate whether the plasticity condition is satisfied."""
        ctx = context or {}
        if self.condition == "always":
            return True
        try:
            # Safe eval of simple comparison expressions
            allowed_names = {"weight": current_weight, **ctx}
            # Only allow simple comparisons — no function calls
            safe_expr = self.condition.replace("and", " and ").replace("or", " or ")
            # Validate it's just comparisons
            import ast
            tree = ast.parse(safe_expr, mode="eval")
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    return False  # No function calls allowed
            return bool(eval(safe_expr, {"__builtins__": {}}, allowed_names))
        except Exception:
            return False

    def apply(self, current_weight: float, context: Dict[str, Any] = None) -> Tuple[float, bool]:
        """
        Apply rule to current_weight. Returns (new_weight, was_applied).
        """
        if not self.evaluate_condition(current_weight, context):
            return current_weight, False

        new_w = current_weight + self.delta
        # Apply decay toward 0.5 (neutral) if configured
        if self.decay > 0:
            new_w = new_w - self.decay * (new_w - 0.5)
        new_w = linear_clamp(new_w, self.min_weight, self.max_weight)
        return new_w, True

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "trigger": self.trigger,
            "target_id": self.target_id,
            "condition": self.condition,
            "delta": self.delta,
            "decay": self.decay,
            "max_weight": self.max_weight,
            "min_weight": self.min_weight,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PlasticityRule":
        return cls(
            rule_id=d["rule_id"],
            trigger=d["trigger"],
            target_id=d["target_id"],
            condition=d.get("condition", "always"),
            delta=d.get("delta", 0.05),
            decay=d.get("decay", 0.0),
            max_weight=d.get("max_weight", 1.0),
            min_weight=d.get("min_weight", 0.0),
            description=d.get("description", ""),
        )


# ════════════════════════════════════════════════════════════
# The Connectome — full persona neural graph
# ════════════════════════════════════════════════════════════

class Connectome:
    """
    The complete neural-wiring model of a persona.

    Analogous to a biological connectome: all nodes (neurons) + all
    edges (synapses) + plasticity rules (learning) + global modulators.
    """

    def __init__(self, persona_id: str, persona_name: str):
        self.persona_id = persona_id
        self.persona_name = persona_name
        self.nodes: Dict[str, MobjectNode] = {}
        self.edges: List[ConnectomeEdge] = []
        self.global_weights: Dict[str, float] = {k: 1.0 for k in GLOBAL_WEIGHT_KEYS}
        self.plasticity_rules: List[PlasticityRule] = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "lara_version": APP_VERSION,
            "build": BUILD_NUMBER,
            "schema": "connectome_v1",
            "plasticity_trigger_count": 0,
            "total_adaptations": 0,
        }
        # Runtime: adjacency list for graph traversal
        self._adj: Dict[str, List[ConnectomeEdge]] = defaultdict(list)
        self._radj: Dict[str, List[ConnectomeEdge]] = defaultdict(list)  # reverse edges
        self._dirty = False

    # ── Node management ──────────────────────────────────────

    def add_node(self, node: MobjectNode) -> "Connectome":
        self.nodes[node.mobject_id] = node
        self._dirty = True
        return self

    def remove_node(self, mobject_id: str) -> "Connectome":
        self.nodes.pop(mobject_id, None)
        self.edges = [e for e in self.edges
                      if e.source_id != mobject_id and e.target_id != mobject_id]
        self._dirty = True
        return self

    def set_node_weight(self, mobject_id: str, weight: float):
        if mobject_id in self.nodes:
            self.nodes[mobject_id].weight = linear_clamp(weight)
            self._dirty = True

    # ── Edge management ──────────────────────────────────────

    def add_edge(self, edge: ConnectomeEdge) -> "Connectome":
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError(
                f"Both nodes must exist before adding edge: "
                f"{edge.source_id} → {edge.target_id}"
            )
        self.edges.append(edge)
        self._build_adj()
        return self

    def get_edges_from(self, mobject_id: str) -> List[ConnectomeEdge]:
        return self._adj.get(mobject_id, [])

    def get_edges_to(self, mobject_id: str) -> List[ConnectomeEdge]:
        return self._radj.get(mobject_id, [])

    # ── Global weights (neuromodulators) ────────────────────

    def set_global_weight(self, family: str, value: float):
        if family in self.global_weights:
            self.global_weights[family] = linear_clamp(value)
            self._dirty = True

    def _get_family_for_node(self, node: MobjectNode) -> Optional[str]:
        """Map a node type to its global weight family key."""
        prefix = node.node_type.split("_")[0]
        key = f"{prefix}_family"
        return key if key in self.global_weights else None

    # ── Graph traversal & synthesis ─────────────────────────

    def _build_adj(self):
        self._adj = defaultdict(list)
        self._radj = defaultdict(list)
        for edge in self.edges:
            self._adj[edge.source_id].append(edge)
            self._radj[edge.target_id].append(edge)
            if edge.direction == "bidirectional":
                self._adj[edge.target_id].append(
                    ConnectomeEdge(edge.target_id, edge.source_id,
                                   edge.influence, "forward", f"{edge.label}_rev")
                )
                self._radj[edge.source_id].append(edge)

    def _topological_sort(self) -> List[str]:
        """
        Kahn's algorithm topological sort.
        Falls back to all-nodes list if graph has cycles (feedback loops).
        """
        in_degree = {nid: 0 for nid in self.nodes}
        for edge in self.edges:
            if edge.direction != "feedback":  # Skip feedback for topo sort
                in_degree[edge.target_id] = in_degree.get(edge.target_id, 0) + 1

        queue = deque([n for n, d in in_degree.items() if d == 0])
        order = []
        while queue:
            nid = queue.popleft()
            order.append(nid)
            for edge in self._adj.get(nid, []):
                if edge.direction != "feedback":
                    in_degree[edge.target_id] -= 1
                    if in_degree[edge.target_id] == 0:
                        queue.append(edge.target_id)

        # If cycle detected, append remaining nodes in arbitrary order
        remaining = set(self.nodes.keys()) - set(order)
        order.extend(list(remaining))
        return order

    def synthesise(self) -> Dict[str, Any]:
        """
        Full graph traversal → compute effective parameters for all nodes.

        Returns a flat dict of:
          {
            "voice_pitch": {"base_hz": 165.3, "variance": 0.42},
            "emotion_valence": {"value": 0.65},
            ...
            "_meta": {synthesis timestamp, total influence, etc.}
          }
        """
        if self._dirty:
            self._build_adj()
            self._dirty = False

        order = self._topological_sort()

        # Accumulate incoming influence per node
        incoming: Dict[str, float] = defaultdict(float)

        result: Dict[str, Any] = {}

        for nid in order:
            node = self.nodes.get(nid)
            if not node:
                continue

            # Global family modulation
            family_key = self._get_family_for_node(node)
            family_scale = self.global_weights.get(family_key, 1.0) if family_key else 1.0

            # Effective output: node computes its params given incoming signal
            raw_influence = incoming[nid] * family_scale
            effective = node.compute_output(raw_influence)

            # Apply family scale to all numeric params
            for k, v in effective.items():
                if isinstance(v, float):
                    effective[k] = v * family_scale

            result[node.node_type] = effective

            # Propagate this node's influence forward
            for edge in self._adj.get(nid, []):
                if edge.direction in ("forward", "bidirectional"):
                    # Signal = node_weight × edge_influence (multiplicative)
                    signal = node.weight * edge.influence * family_scale
                    incoming[edge.target_id] += signal

        result["_meta"] = {
            "synthesised_at": datetime.now().isoformat(),
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "global_weights": dict(self.global_weights),
            "traversal_order": order,
        }
        return result

    def get_voice_params(self) -> Dict[str, Any]:
        """
        Convenience: return only voice-relevant synthesised parameters,
        formatted for passing to VoiceManager.speak().
        """
        full = self.synthesise()
        voice_keys = {k: v for k, v in full.items()
                      if k.startswith("voice_") or k.startswith("prosody_")}
        # Extract scalar values suitable for TTS
        flat = {}
        for node_type, params in voice_keys.items():
            for param, value in params.items():
                flat[f"{node_type}.{param}"] = value
        return flat

    def get_emotion_state(self) -> Dict[str, float]:
        """Return VAD (valence-arousal-dominance) emotional state."""
        full = self.synthesise()
        return {
            "valence":   full.get("emotion_valence", {}).get("value", 0.0),
            "arousal":   full.get("emotion_arousal", {}).get("value", 0.5),
            "dominance": full.get("emotion_dominance", {}).get("value", 0.5),
        }

    # ── Plasticity ───────────────────────────────────────────

    def add_plasticity_rule(self, rule: PlasticityRule) -> "Connectome":
        self.plasticity_rules.append(rule)
        return self

    def fire_trigger(self, trigger: str, context: Dict[str, Any] = None,
                     logger=None) -> List[Dict[str, Any]]:
        """
        Fire a plasticity trigger. Applies all matching rules.
        Returns list of adaptation records (for audit logging).
        """
        context = context or {}
        adaptations = []

        for rule in self.plasticity_rules:
            if rule.trigger != trigger:
                continue

            target_ids = (
                list(self.nodes.keys()) if rule.target_id == "*"
                else [rule.target_id]
            )

            for tid in target_ids:
                if tid not in self.nodes:
                    continue
                node = self.nodes[tid]
                old_w = node.weight
                new_w, applied = rule.apply(old_w, context)
                if applied:
                    node.weight = new_w
                    adaptation = {
                        "rule_id": rule.rule_id,
                        "trigger": trigger,
                        "mobject_id": tid,
                        "old_weight": round(old_w, 6),
                        "new_weight": round(new_w, 6),
                        "delta": round(new_w - old_w, 6),
                        "fired_at": datetime.now().isoformat(),
                        "context_keys": list(context.keys()),
                    }
                    adaptations.append(adaptation)

                    if logger:
                        logger.info(
                            f"Connectome plasticity | persona={self.persona_id} | "
                            f"trigger={trigger} | mobject={tid} | "
                            f"weight {old_w:.4f}→{new_w:.4f} | rule={rule.rule_id}"
                        )

        if adaptations:
            self.metadata["total_adaptations"] += len(adaptations)
            self.metadata["plasticity_trigger_count"] += 1
            self.metadata["updated_at"] = datetime.now().isoformat()
            self._dirty = True

        return adaptations

    # ── Serialisation ────────────────────────────────────────

    def to_dict(self) -> dict:
        """Full JSON-serialisable representation."""
        return {
            "persona_id": self.persona_id,
            "persona_name": self.persona_name,
            "connectome": {
                "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
                "connections": [e.to_dict() for e in self.edges],
                "global_weights": dict(self.global_weights),
                "plasticity_rules": [r.to_dict() for r in self.plasticity_rules],
            },
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Connectome":
        c = cls(d["persona_id"], d.get("persona_name", d["persona_id"]))
        ct = d.get("connectome", {})
        for nid, nd in ct.get("nodes", {}).items():
            c.nodes[nid] = MobjectNode.from_dict(nd)
        c.edges = [ConnectomeEdge.from_dict(e) for e in ct.get("connections", [])]
        c.global_weights = ct.get("global_weights", {k: 1.0 for k in GLOBAL_WEIGHT_KEYS})
        c.plasticity_rules = [PlasticityRule.from_dict(r)
                               for r in ct.get("plasticity_rules", [])]
        c.metadata = d.get("metadata", c.metadata)
        c._build_adj()
        return c

    def diff(self, other: "Connectome") -> Dict[str, Any]:
        """
        Compare two connectomes (e.g., before/after plasticity).
        Returns a summary of changed node weights and new/removed nodes.
        """
        changes = {"weight_changes": {}, "added_nodes": [], "removed_nodes": []}
        for nid, node in self.nodes.items():
            if nid in other.nodes:
                old_w = other.nodes[nid].weight
                new_w = node.weight
                if abs(new_w - old_w) > 1e-6:
                    changes["weight_changes"][nid] = {
                        "old": round(old_w, 6),
                        "new": round(new_w, 6),
                        "delta": round(new_w - old_w, 6),
                    }
            else:
                changes["added_nodes"].append(nid)
        for nid in other.nodes:
            if nid not in self.nodes:
                changes["removed_nodes"].append(nid)
        return changes


# ════════════════════════════════════════════════════════════
# Connectome Manager — file I/O, lifecycle, integration layer
# ════════════════════════════════════════════════════════════

class ConnectomeManager:
    """
    Manages connectome files on disk, integrates with PersonaManager
    and VoiceManager, and provides the public API used by CommandRouter.
    """

    def __init__(self, data_dir: Path, config: dict, logger=None):
        self.data_dir = data_dir
        self.conn_dir = data_dir / DIR_CONNECTOMES
        self.conn_dir.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.logger = logger
        self.enabled = config.get("connectome", {}).get("enabled", True)
        self.activation_mode = config.get("connectome", {}).get("activation", "sigmoid")
        self._cache: Dict[str, Connectome] = {}   # In-memory loaded connectomes

    # ── File I/O ─────────────────────────────────────────────

    def _path(self, persona_id: str) -> Path:
        return self.conn_dir / f"{persona_id}{FILE_CONNECTOME_SUFFIX}"

    def save(self, connectome: Connectome):
        """Persist connectome to disk as JSON."""
        connectome.metadata["updated_at"] = datetime.now().isoformat()
        connectome.metadata["version"] = connectome.metadata.get("version", 1) + 1
        path = self._path(connectome.persona_id)
        path.write_text(json.dumps(connectome.to_dict(), indent=2, default=str))
        self._cache[connectome.persona_id] = connectome
        if self.logger:
            self.logger.info(
                f"Connectome saved | persona={connectome.persona_id} | "
                f"nodes={len(connectome.nodes)} | edges={len(connectome.edges)} | "
                f"v={connectome.metadata['version']}"
            )

    def load(self, persona_id: str) -> Optional[Connectome]:
        """Load connectome from disk (or return cached version)."""
        if persona_id in self._cache:
            return self._cache[persona_id]
        path = self._path(persona_id)
        if not path.exists():
            if self.logger:
                self.logger.warning(
                    fmt_error("E011", f"No connectome for persona '{persona_id}'")
                )
            return None
        try:
            data = json.loads(path.read_text())
            c = Connectome.from_dict(data)
            self._cache[persona_id] = c
            if self.logger:
                self.logger.info(
                    f"Connectome loaded | persona={persona_id} | "
                    f"nodes={len(c.nodes)} | edges={len(c.edges)}"
                )
            return c
        except Exception as e:
            if self.logger:
                self.logger.error(fmt_error("E015", f"Connectome load failed: {e}"))
            return None

    def exists(self, persona_id: str) -> bool:
        return self._path(persona_id).exists()

    def list_personas(self) -> List[str]:
        return [p.stem.replace("_connectome", "")
                for p in self.conn_dir.glob(f"*{FILE_CONNECTOME_SUFFIX}")]

    # ── Factory: build default connectome for a new persona ──

    def create_default(self, persona_id: str, persona_name: str,
                       base_params: Dict[str, Any] = None) -> Connectome:
        """
        Build a well-connected default connectome for a new persona.
        base_params can override default node parameters.
        """
        bp = base_params or {}
        c = Connectome(persona_id, persona_name)

        # ── Define all nodes ─────────────────────────────────
        nodes_def = [
            # Voice family
            ("vp", "voice_pitch",    {"base_hz": bp.get("pitch_hz", 180.0), "variance": 0.3},      0.8),
            ("vt", "voice_tempo",    {"syllables_per_sec": bp.get("tempo", 4.5), "variance": 0.2},  0.7),
            ("vi", "voice_timbre",   {"brightness": bp.get("brightness", 0.6), "warmth": 0.5},      0.75),
            ("ve", "voice_energy",   {"amplitude": bp.get("amplitude", 0.7), "attack_ms": 30.0},    0.8),
            # Emotion family
            ("ev", "emotion_valence",   {"value": bp.get("valence", 0.4)},    0.6),
            ("ea", "emotion_arousal",   {"value": bp.get("arousal", 0.5)},    0.55),
            ("ed", "emotion_dominance", {"value": bp.get("dominance", 0.5)},  0.5),
            # Rhythm family
            ("rs", "rhythm_stress",  {"strength": 0.6, "regularity": 0.7},   0.65),
            ("rp", "rhythm_pause",   {"mean_ms": 200.0, "variance_ms": 80.0}, 0.6),
            ("rc", "rhythm_cadence", {"fall_hz": 15.0, "rise_hz": 5.0},       0.6),
            # Speech family
            ("sg", "speech_register",   {"formality": bp.get("formality", 0.5)}, 0.7),
            ("sv", "speech_vocabulary", {"richness": bp.get("vocab_richness", 0.6)}, 0.65),
            ("sx", "speech_syntax",     {"complexity": bp.get("syntax_complexity", 0.5)}, 0.6),
            # Prosody family
            ("pe", "prosody_emphasis", {"strength": 0.55},             0.6),
            ("pm", "prosody_melody",   {"range_semitones": 8.0},        0.65),
        ]
        for nid, ntype, params, weight in nodes_def:
            full_id = f"{persona_id}_{nid}"
            c.add_node(MobjectNode(full_id, ntype, params, weight,
                                   activation=self.activation_mode))

        def nid(suffix): return f"{persona_id}_{suffix}"

        # ── Define synaptic connections ──────────────────────
        # Biological analogy: pitch influences melody, emotion colours tempo, etc.
        edges_def = [
            # Voice internal wiring
            (nid("vp"), nid("pm"), 0.6, "forward",       "pitch→melody"),
            (nid("vt"), nid("rs"), 0.5, "forward",       "tempo→stress"),
            (nid("vi"), nid("pe"), 0.4, "forward",       "timbre→emphasis"),
            (nid("ve"), nid("vp"), 0.3, "feedback",      "energy↩pitch"),
            # Emotion → Voice modulation
            (nid("ev"), nid("vp"), 0.55, "forward",      "valence→pitch"),
            (nid("ev"), nid("vt"), 0.4,  "forward",      "valence→tempo"),
            (nid("ea"), nid("ve"), 0.6,  "forward",      "arousal→energy"),
            (nid("ea"), nid("vt"), 0.5,  "forward",      "arousal→tempo"),
            (nid("ed"), nid("vi"), 0.35, "forward",      "dominance→timbre"),
            (nid("ed"), nid("sg"), 0.5,  "forward",      "dominance→register"),
            # Emotion ↔ Emotion lateral inhibition
            (nid("ev"), nid("ea"), 0.3,  "bidirectional","valence↔arousal"),
            # Rhythm ↔ Speech coupling
            (nid("rs"), nid("pe"), 0.55, "forward",      "stress→emphasis"),
            (nid("rp"), nid("rc"), 0.4,  "forward",      "pause→cadence"),
            (nid("rc"), nid("pm"), 0.5,  "forward",      "cadence→melody"),
            (nid("sg"), nid("sv"), 0.45, "forward",      "register→vocab"),
            (nid("sv"), nid("sx"), 0.4,  "forward",      "vocab→syntax"),
            # Cross-family: speech complexity feeds back to rhythm
            (nid("sx"), nid("rp"), 0.3,  "feedback",     "syntax↩pause"),
        ]
        for src, tgt, inf, direction, label in edges_def:
            try:
                c.add_edge(ConnectomeEdge(src, tgt, inf, direction, label))
            except ValueError:
                pass  # Skip if nodes don't exist

        # ── Global weights ───────────────────────────────────
        c.global_weights = {
            "voice_family":   1.0,
            "emotion_family": 0.85,
            "rhythm_family":  0.8,
            "speech_family":  0.9,
            "prosody_family": 0.75,
        }

        # ── Default plasticity rules ─────────────────────────
        rules = [
            # Audio training: strengthen voice nodes
            PlasticityRule("pr_audio_pitch",  "audio_training", nid("vp"),
                           "weight < 0.95", delta=+0.04, decay=0.002,
                           max_weight=0.95, description="Pitch adapts with new voice training"),
            PlasticityRule("pr_audio_timbre", "audio_training", nid("vi"),
                           "weight < 0.90", delta=+0.03, decay=0.001,
                           max_weight=0.90, description="Timbre adapts with voice training"),
            PlasticityRule("pr_audio_tempo",  "audio_training", nid("vt"),
                           "always", delta=+0.02, decay=0.001,
                           max_weight=0.85, description="Tempo fine-tunes with training data"),

            # User positive rating: reinforce current voice settings
            PlasticityRule("pr_rating_pos_energy", "user_rating_positive", nid("ve"),
                           "always", delta=+0.05, max_weight=0.95,
                           description="Positive rating reinforces energy level"),
            PlasticityRule("pr_rating_pos_valence", "user_rating_positive", nid("ev"),
                           "weight < 0.8", delta=+0.04, max_weight=0.85,
                           description="Positive feedback lifts emotional valence"),
            PlasticityRule("pr_rating_neg_energy", "user_rating_negative", nid("ve"),
                           "always", delta=-0.04, min_weight=0.3,
                           description="Negative rating reduces voice energy"),
            PlasticityRule("pr_rating_neg_arousal", "user_rating_negative", nid("ea"),
                           "always", delta=-0.03, min_weight=0.2,
                           description="Negative feedback calms arousal level"),

            # Lyric generation: loosen rhythm/prosody
            PlasticityRule("pr_lyrics_rhythm", "new_lyrics", nid("rs"),
                           "always", delta=+0.03, decay=0.005, max_weight=0.9,
                           description="Lyric writing engages stress patterns"),
            PlasticityRule("pr_lyrics_melody", "new_lyrics", nid("pm"),
                           "always", delta=+0.04, max_weight=0.9,
                           description="Lyric writing broadens melodic range"),

            # Chat interaction: nudge register toward current conversation style
            PlasticityRule("pr_chat_register", "chat_interaction", nid("sg"),
                           "always", delta=+0.01, decay=0.003, max_weight=0.85,
                           description="Conversational register adapts with use"),
            PlasticityRule("pr_chat_vocab",    "chat_interaction", nid("sv"),
                           "always", delta=+0.01, decay=0.002, max_weight=0.9,
                           description="Vocabulary richness grows with conversation"),

            # Media ingestion: arousal spike
            PlasticityRule("pr_media_arousal", "media_ingestion", nid("ea"),
                           "weight < 0.7", delta=+0.05, decay=0.01, max_weight=0.8,
                           description="Processing new media briefly raises arousal"),

            # Global decay rule: prevent any node drifting above 0.98
            PlasticityRule("pr_global_decay",  "daily_decay", "*",
                           "weight > 0.98", delta=-0.01, max_weight=0.98,
                           description="Daily soft-cap prevents weight saturation"),
        ]
        for rule in rules:
            c.add_plasticity_rule(rule)

        self.save(c)
        if self.logger:
            self.logger.info(
                f"Default connectome created | persona={persona_id} | "
                f"nodes={len(c.nodes)} | edges={len(c.edges)} | "
                f"plasticity_rules={len(c.plasticity_rules)}"
            )
        return c

    # ── Trigger API ──────────────────────────────────────────

    def trigger(self, persona_id: str, event: str,
                context: Dict[str, Any] = None, auto_save: bool = True) -> List[Dict[str, Any]]:
        """
        Fire a plasticity trigger for a persona's connectome.
        Saves updated weights to disk and logs all adaptations.
        """
        if not self.enabled:
            return []
        c = self.load(persona_id)
        if c is None:
            return []

        snapshot_before = copy.deepcopy(c)
        adaptations = c.fire_trigger(event, context, self.logger)

        if adaptations and auto_save:
            self.save(c)
            # Log diff to masterlog via logger
            diff = c.diff(snapshot_before)
            if self.logger and diff["weight_changes"]:
                self.logger.info(
                    f"Connectome diff after trigger={event} | "
                    f"persona={persona_id} | "
                    f"changed_nodes={list(diff['weight_changes'].keys())}"
                )
        return adaptations

    def synthesise(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Run graph synthesis for a persona. Returns full parameter dict."""
        c = self.load(persona_id)
        if c is None:
            return None
        return c.synthesise()

    def get_voice_params(self, persona_id: str) -> Dict[str, Any]:
        """Return synthesised voice parameters for TTS modulation."""
        c = self.load(persona_id)
        if c is None:
            return {}
        return c.get_voice_params()

    def get_emotion_state(self, persona_id: str) -> Dict[str, float]:
        """Return current VAD emotional state for a persona."""
        c = self.load(persona_id)
        if c is None:
            return {"valence": 0.0, "arousal": 0.5, "dominance": 0.5}
        return c.get_emotion_state()

    def describe(self, persona_id: str) -> str:
        """Return a human-readable summary of the connectome state."""
        c = self.load(persona_id)
        if c is None:
            return f"No connectome found for persona '{persona_id}'"

        emotion = c.get_emotion_state()
        voice_p = c.get_voice_params()

        node_summary = sorted(
            [(nid, f"{node.node_type:<20} weight={node.weight:.3f}")
             for nid, node in c.nodes.items()],
            key=lambda x: x[1]
        )

        lines = [
            f"Connectome — {c.persona_name} ({persona_id})",
            f"  Schema v{c.metadata.get('version',1)} | "
            f"nodes={len(c.nodes)} | edges={len(c.edges)} | "
            f"plasticity_rules={len(c.plasticity_rules)}",
            f"  Total adaptations: {c.metadata.get('total_adaptations', 0)}",
            f"  Updated: {c.metadata.get('updated_at','?')}",
            "",
            "  Emotional State (VAD):",
            f"    Valence={emotion['valence']:.3f}  "
            f"Arousal={emotion['arousal']:.3f}  "
            f"Dominance={emotion['dominance']:.3f}",
            "",
            "  Global Modulators:",
        ]
        for k, v in c.global_weights.items():
            lines.append(f"    {k:<20} {v:.3f}")

        lines += ["", "  Node Weights:"]
        for _, desc in node_summary:
            lines.append(f"    {desc}")

        return "\n".join(lines)

    def set_global_weight(self, persona_id: str, family: str, value: float) -> bool:
        c = self.load(persona_id)
        if c is None:
            return False
        c.set_global_weight(family, value)
        self.save(c)
        return True

    def set_node_weight(self, persona_id: str, mobject_id: str, weight: float) -> bool:
        c = self.load(persona_id)
        if c is None:
            return False
        c.set_node_weight(mobject_id, weight)
        self.save(c)
        return True

    def add_node(self, persona_id: str, node: MobjectNode) -> bool:
        """Add a new mobject node to an existing connectome."""
        c = self.load(persona_id)
        if c is None:
            return False
        c.add_node(node)
        self.save(c)
        return True

    def add_edge(self, persona_id: str, edge: ConnectomeEdge) -> bool:
        """Add a new synaptic connection to an existing connectome."""
        c = self.load(persona_id)
        if c is None:
            return False
        try:
            c.add_edge(edge)
            self.save(c)
            return True
        except ValueError as e:
            if self.logger:
                self.logger.error(fmt_error("E015", str(e)))
            return False
