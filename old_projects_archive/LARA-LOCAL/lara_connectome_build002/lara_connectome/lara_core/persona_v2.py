"""
LARA — Persona Manager v2 (Connectome-integrated)
Version: 0.1.1 | Build: 002 | Date: 2026-02-23

DROP-IN REPLACEMENT for persona.py.
All original CRUD + inheritance is preserved.
New: connectome_mgr integration — every persona creation/update
     also creates/updates its connectome and fires plasticity triggers.

Changes from v1:
  - __init__ accepts optional connectome_mgr
  - create() auto-generates a default connectome for new personas
  - update() fires "chat_interaction" plasticity trigger
  - get_connectome_summary() — human-readable neural state
  - set_emotion() — directly shift emotion node weights
  - apply_rating() — fire user_rating plasticity trigger
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from lara_core.constants import (
    APP_VERSION, BUILD_NUMBER,
    DIR_PERSONAS, error as fmt_error
)


class PersonaManager:

    def __init__(self, data_dir: Path, config: dict,
                 connectome_mgr=None, logger=None):
        self.personas_dir = data_dir / DIR_PERSONAS
        self.personas_dir.mkdir(parents=True, exist_ok=True)
        self.inheritance_enabled = config.get("persona", {}).get("inheritance_enabled", True)
        self.connectome_mgr = connectome_mgr   # May be None if connectome disabled
        self.logger = logger

    # ── CRUD ────────────────────────────────────────────────

    def create(self, persona_id: str, name: str, voice_model: str = None,
               face_model: str = None, inherits: str = None,
               traits: dict = None, description: str = "",
               base_connectome_params: Dict[str, Any] = None) -> dict:
        """
        Create a new persona. Auto-generates a connectome if connectome_mgr is set.
        base_connectome_params: optional overrides for default node params, e.g.
          {"pitch_hz": 200, "valence": 0.7, "formality": 0.8}
        """
        if self.exists(persona_id):
            if self.logger:
                self.logger.warning(f"Persona '{persona_id}' already exists — updating instead")
            return self.update(persona_id, name=name, voice_model=voice_model,
                               face_model=face_model, traits=traits)

        if inherits and self.inheritance_enabled:
            if not self.exists(inherits):
                msg = fmt_error("E011", f"Parent persona '{inherits}' not found")
                if self.logger:
                    self.logger.error(msg)
                raise ValueError(msg)
            self._check_loop(persona_id, inherits)

        persona = {
            "id": persona_id,
            "name": name,
            "inherits": inherits if self.inheritance_enabled else None,
            "voice_model": voice_model,
            "face_model": face_model,
            "description": description,
            "traits": traits or {},
            "connectome_enabled": self.connectome_mgr is not None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "lara_version": APP_VERSION,
            "build": BUILD_NUMBER,
        }
        self._save(persona_id, persona)

        # ── Auto-create connectome ───────────────────────────
        if self.connectome_mgr and not self.connectome_mgr.exists(persona_id):
            self.connectome_mgr.create_default(
                persona_id, name,
                base_params=base_connectome_params or {}
            )

        if self.logger:
            self.logger.info(
                f"Persona created | id={persona_id} | name={name} | "
                f"inherits={inherits} | connectome={'yes' if self.connectome_mgr else 'no'}"
            )
        return persona

    def get(self, persona_id: str, resolve_inheritance: bool = True) -> Optional[dict]:
        path = self._path(persona_id)
        if not path.exists():
            if self.logger:
                self.logger.error(fmt_error("E011", f"Persona '{persona_id}' not found"))
            return None
        persona = json.loads(path.read_text())
        if resolve_inheritance and persona.get("inherits") and self.inheritance_enabled:
            persona = self._resolve_inheritance(persona)
        # Attach live connectome summary if available
        if self.connectome_mgr and self.connectome_mgr.exists(persona_id):
            try:
                persona["_emotion_state"] = self.connectome_mgr.get_emotion_state(persona_id)
                persona["_voice_params_available"] = True
            except Exception:
                pass
        return persona

    def update(self, persona_id: str, **kwargs) -> Optional[dict]:
        persona = self.get(persona_id, resolve_inheritance=False)
        if not persona:
            return None
        for k, v in kwargs.items():
            if v is not None and k in persona:
                persona[k] = v
        persona["updated_at"] = datetime.now().isoformat()
        persona["version"] = persona.get("version", 1) + 1
        self._save(persona_id, persona)

        # Persona update → fire chat_interaction plasticity
        if self.connectome_mgr and self.connectome_mgr.exists(persona_id):
            self.connectome_mgr.trigger(persona_id, "chat_interaction",
                                        {"update_fields": list(kwargs.keys())})

        if self.logger:
            self.logger.info(f"Persona updated | id={persona_id} | v={persona['version']}")
        return persona

    def delete(self, persona_id: str) -> bool:
        path = self._path(persona_id)
        if path.exists():
            path.unlink()
            if self.logger:
                self.logger.info(f"Persona deleted | id={persona_id}")
            return True
        return False

    def list_all(self) -> List[str]:
        return [p.stem for p in self.personas_dir.glob("*.json")]

    def exists(self, persona_id: str) -> bool:
        return self._path(persona_id).exists()

    # ── Connectome integration API ───────────────────────────

    def get_connectome_summary(self, persona_id: str) -> str:
        """Return human-readable connectome state for a persona."""
        if not self.connectome_mgr:
            return "Connectome not enabled in config."
        return self.connectome_mgr.describe(persona_id)

    def apply_rating(self, persona_id: str, positive: bool,
                     context: Dict[str, Any] = None):
        """Fire user_rating plasticity trigger. Call after TTS output review."""
        if not self.connectome_mgr:
            return
        trigger = "user_rating_positive" if positive else "user_rating_negative"
        adaptations = self.connectome_mgr.trigger(persona_id, trigger, context)
        if self.logger:
            self.logger.info(
                f"Rating applied | persona={persona_id} | "
                f"positive={positive} | adaptations={len(adaptations)}"
            )
        return adaptations

    def notify_audio_training(self, persona_id: str, model_id: str):
        """Call when a new voice model is registered for this persona."""
        if not self.connectome_mgr:
            return
        return self.connectome_mgr.trigger(
            persona_id, "audio_training",
            {"model_id": model_id, "timestamp": datetime.now().isoformat()}
        )

    def notify_lyrics(self, persona_id: str, topic: str = ""):
        """Call when lyrics are generated for this persona."""
        if not self.connectome_mgr:
            return
        return self.connectome_mgr.trigger(
            persona_id, "new_lyrics", {"topic": topic}
        )

    def notify_media(self, persona_id: str, media_type: str = ""):
        """Call when media is ingested (OCR, face extract, etc.)."""
        if not self.connectome_mgr:
            return
        return self.connectome_mgr.trigger(
            persona_id, "media_ingestion", {"media_type": media_type}
        )

    def set_global_modulator(self, persona_id: str,
                             family: str, value: float) -> bool:
        """Directly set a global weight (neuromodulator) for a persona."""
        if not self.connectome_mgr:
            return False
        ok = self.connectome_mgr.set_global_weight(persona_id, family, value)
        if ok and self.logger:
            self.logger.info(
                f"Global modulator set | persona={persona_id} | "
                f"family={family} | value={value:.3f}"
            )
        return ok

    def get_voice_params(self, persona_id: str) -> Dict[str, Any]:
        """
        Return synthesised voice parameters from the connectome.
        Returns {} if connectome not available.
        """
        if not self.connectome_mgr:
            return {}
        return self.connectome_mgr.get_voice_params(persona_id)

    # ── Inheritance (unchanged from v1) ─────────────────────

    def _resolve_inheritance(self, persona: dict, chain: List[str] = None) -> dict:
        chain = chain or [persona["id"]]
        parent_id = persona.get("inherits")
        if not parent_id:
            return persona
        parent_path = self._path(parent_id)
        if not parent_path.exists():
            if self.logger:
                self.logger.warning(
                    fmt_error("E011", f"Parent '{parent_id}' missing in chain {chain}")
                )
            return persona
        parent = json.loads(parent_path.read_text())
        if parent.get("inherits"):
            parent = self._resolve_inheritance(parent, chain + [parent_id])
        merged = {**parent, **{k: v for k, v in persona.items() if v is not None}}
        merged["_inheritance_chain"] = chain + [parent_id]
        return merged

    def _check_loop(self, new_id: str, parent_id: str, visited: set = None):
        visited = visited or {new_id}
        if parent_id in visited:
            raise ValueError(
                fmt_error("E014", f"Circular inheritance: {visited} -> {parent_id}")
            )
        visited.add(parent_id)
        parent = self.get(parent_id, resolve_inheritance=False)
        if parent and parent.get("inherits"):
            self._check_loop(new_id, parent["inherits"], visited)

    # ── Helpers ──────────────────────────────────────────────

    def _path(self, persona_id: str) -> Path:
        return self.personas_dir / f"{persona_id}.json"

    def _save(self, persona_id: str, data: dict):
        self._path(persona_id).write_text(json.dumps(data, indent=2, default=str))
