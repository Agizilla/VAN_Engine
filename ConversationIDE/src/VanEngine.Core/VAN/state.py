from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .enums import VanBlockType


class VanStateEngine:
    def __init__(self, persist_path: str):
        self._persist_path = persist_path
        self._state: dict[str, object] = {}
        self._dirty = False

    @property
    def Count(self) -> int:
        return len(self._state)

    @property
    def Keys(self):
        return list(self._state.keys())

    def Get(self, key: str, default=None):
        return self._state.get(key, default)

    def Set(self, key: str, value) -> None:
        self._state[key] = value
        self._dirty = True

    def Remove(self, key: str) -> bool:
        return self._state.pop(key, None) is not None

    def ApplyEnvelope(self, envelope) -> None:
        if envelope.BlockType != VanBlockType.State or len(envelope.Data) < 2:
            return
        key = str(envelope.Data[0] or "")
        value = str(envelope.Data[1] or "")
        for cast in (float, lambda v: {"true": True, "false": False}[v.lower()], int):
            try:
                self.Set(key, cast(value))
                return
            except Exception:
                pass
        self.Set(key, value)

    def Merge(self, external: dict[str, object]) -> None:
        self._state.update(external)
        self._dirty = True

    def Snapshot(self) -> dict[str, object]:
        return dict(self._state)

    async def SaveAsync(self, ct=None) -> None:
        if not self._dirty:
            return
        p = Path(self._persist_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
        self._dirty = False

    async def LoadAsync(self, ct=None) -> None:
        p = Path(self._persist_path)
        if not p.exists():
            return
        self._state = json.loads(p.read_text(encoding="utf-8"))
        self._dirty = False

    def Save(self) -> None:
        p = Path(self._persist_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
        self._dirty = False

    def Load(self) -> None:
        p = Path(self._persist_path)
        if not p.exists():
            return
        self._state = json.loads(p.read_text(encoding="utf-8"))
        self._dirty = False

    def Dispose(self) -> None:
        if self._dirty:
            self.Save()
        self._state.clear()
