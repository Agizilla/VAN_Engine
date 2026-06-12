import sys
import io
import json
import sqlite3
import time
import math
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class VANEngineBridge:
    """Bridge between Conversation-IDE and VAN_Engine substrate"""

    def __init__(self, engine_root: Path):
        self.engine_root = Path(engine_root)
        self.index_path = self.engine_root / "memory" / "token_index.db"
        self.iso_path = self.engine_root / "core" / "ISO_Rules.json"
        self.audit_path = self.engine_root / "logs" / "substrate_audit.log"

        self._validate_engine()

    def _validate_engine(self):
        if not self.engine_root.exists():
            raise FileNotFoundError(f"VAN_Engine not found at {self.engine_root}")
        if not self.index_path.exists():
            self._init_index()
        self._ensure_table()

    def _init_index(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.index_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                key TEXT PRIMARY KEY,
                w REAL, x REAL, y REAL, z REAL,
                applies_to TEXT,
                created INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def _ensure_table(self):
        conn = sqlite3.connect(str(self.index_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tokens'")
        if not cursor.fetchone():
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    key TEXT PRIMARY KEY,
                    w REAL, x REAL, y REAL, z REAL,
                    applies_to TEXT,
                    created INTEGER
                )
            """)
            conn.commit()
        conn.close()

    def quaternion_lookup(self, token: str) -> Optional[Tuple[float, float, float, float]]:
        conn = sqlite3.connect(str(self.index_path))
        cursor = conn.execute("SELECT w, x, y, z FROM tokens WHERE key = ?", (token,))
        row = cursor.fetchone()
        conn.close()
        return row if row else None

    def quaternion_store(self, token: str, w: float, x: float, y: float, z: float, applies_to: str):
        conn = sqlite3.connect(str(self.index_path))
        conn.execute(
            "INSERT OR REPLACE INTO tokens (key, w, x, y, z, applies_to, created) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (token, w, x, y, z, applies_to, int(time.time()))
        )
        conn.commit()
        conn.close()

    def get_iso_rules(self) -> Dict[str, Any]:
        with open(self.iso_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def log_audit(self, component: str, action: str,
                  before: Optional[Tuple[float, float, float, float]] = None,
                  after: Optional[Tuple[float, float, float, float]] = None):
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp": time.time(),
            "component": component,
            "action": action,
            "quaternion_before": before,
            "quaternion_after": after,
            "magnitude_drift": self._compute_drift(before, after) if before and after else None
        }
        with open(self.audit_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event) + '\n')

    def _compute_drift(self, before: Tuple[float, float, float, float],
                       after: Tuple[float, float, float, float]) -> float:
        def mag(q): return math.sqrt(q[0]**2 + q[1]**2 + q[2]**2 + q[3]**2)
        return abs(mag(before) - mag(after))

    def get_token_count(self) -> int:
        conn = sqlite3.connect(str(self.index_path))
        cursor = conn.execute("SELECT COUNT(*) FROM tokens")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def drift_gate(self, quaternion: Tuple[float, float, float, float],
                   threshold: float = 0.85) -> Dict[str, Any]:
        max_comp = max(abs(c) for c in quaternion)
        if max_comp < threshold:
            return {
                "violated": True,
                "action": "HALT_AND_CLARIFY",
                "diagnostic": f"Quaternion magnitude {max_comp} below threshold {threshold}"
            }
        return {"violated": False, "action": "EXECUTE"}


_bridge: Optional[VANEngineBridge] = None


def get_bridge(engine_root: Optional[Path] = None) -> VANEngineBridge:
    global _bridge
    if _bridge is None:
        if engine_root is None:
            engine_root = Path(__file__).resolve().parent.parent.parent.parent
        _bridge = VANEngineBridge(engine_root)
    return _bridge


if __name__ == '__main__':
    bridge = get_bridge()
    print(json.dumps({"status": "connected", "rules": bridge.get_iso_rules()}, indent=2))
