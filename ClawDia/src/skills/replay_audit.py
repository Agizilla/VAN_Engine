import base64
import hashlib
import hmac
import json
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from .base import BaseSkill, register_skill, SkillContext

DB_PATH = Path(__file__).resolve().parents[2] / "replay_audit.db"
CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
SETTINGS_PATH = CONFIG_DIR / "Settings.json"
ARCHIVE_PATH = Path(__file__).resolve().parents[2] / "replay_audit_archive.jsonl"
EXPIRY_DAYS = 30


def _load_settings() -> dict:
    if SETTINGS_PATH.exists():
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    return {}


def _save_settings(s: dict):
    SETTINGS_PATH.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


def _get_audit_key() -> bytes:
    settings = _load_settings()
    key_b64 = settings.get("audit_hmac_key")
    if key_b64:
        return base64.b64decode(key_b64)
    new_key = secrets.token_bytes(32)
    settings["audit_hmac_key"] = base64.b64encode(new_key).decode()
    _save_settings(settings)
    return new_key


_AUDIT_KEY = _get_audit_key()


def _compute_signature(timestamp: str, action: str, skill_id: str, intent_hash: str, preview: str) -> str:
    def pack(s: str) -> bytes:
        b = s.encode("utf-8")
        return len(b).to_bytes(4, "big") + b
    msg = pack(timestamp) + pack(action) + pack(skill_id) + pack(intent_hash) + pack(preview)
    return hmac.new(_AUDIT_KEY, msg, hashlib.sha256).hexdigest()


def _init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS replay_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            skill_id TEXT NOT NULL,
            intent_hash TEXT NOT NULL,
            preview TEXT,
            signature TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON replay_events(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_action ON replay_events(action)")
    conn.commit()
    conn.close()


_init_db()


@register_skill("replay_audit", "system")
class ReplayAuditSkill(BaseSkill):
    name = "replay_audit"
    description = "SQLite audit store with HMAC row-level signatures, expiry, and JSON migration"
    author = "DeepSeek / ARC / ClawDia"
    version = "1.0.0"
    category = "system"
    tags = ["audit", "sqlite", "hmac", "expiry", "migration"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["log", "list", "verify", "expire", "migrate", "stats"],
                "default": "list",
            },
            "timestamp": {"type": "string", "default": ""},
            "action_type": {"type": "string", "default": ""},
            "skill_id": {"type": "string", "default": ""},
            "intent_hash": {"type": "string", "default": ""},
            "preview": {"type": "string", "default": ""},
            "limit": {"type": "integer", "default": 10},
            "verify_flag": {"type": "boolean", "default": False},
            "json_path": {"type": "string", "default": ""},
        },
    }

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "list")

        if action == "log":
            return self._log(kwargs)
        elif action == "list":
            return self._list(kwargs)
        elif action == "verify":
            return self._verify_all()
        elif action == "expire":
            return self._expire()
        elif action == "migrate":
            return self._migrate(kwargs)
        elif action == "stats":
            return self._stats()
        return {"error": f"Unknown action: {action}", "result": None}

    def _log(self, kwargs: dict) -> dict:
        conn = sqlite3.connect(str(DB_PATH))
        try:
            timestamp = kwargs.get("timestamp") or datetime.now().isoformat()
            action_type = kwargs.get("action_type", "UNKNOWN")
            skill_id = kwargs.get("skill_id", "unknown")
            intent_hash = kwargs.get("intent_hash", "")
            preview = (kwargs.get("preview") or "")[:500]
            signature = _compute_signature(timestamp, action_type, skill_id, intent_hash, preview)

            conn.execute(
                "INSERT INTO replay_events (timestamp, action, skill_id, intent_hash, preview, signature) VALUES (?, ?, ?, ?, ?, ?)",
                (timestamp, action_type, skill_id, intent_hash, preview, signature),
            )
            conn.commit()
            self.publish("replay_audit:logged", {"timestamp": timestamp, "action": action_type, "skill_id": skill_id})
            return {"error": None, "result": {"logged": True, "signature": signature[:12] + "..."}}
        finally:
            conn.close()

    def _list(self, kwargs: dict) -> dict:
        limit = min(kwargs.get("limit", 10), 100)
        verify_flag = kwargs.get("verify_flag", False)
        conn = sqlite3.connect(str(DB_PATH))
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM replay_events ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            results = []
            for row in rows:
                entry = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "action": row["action"],
                    "skill_id": row["skill_id"],
                    "preview": (row["preview"] or "")[:100],
                }
                if verify_flag:
                    expected = _compute_signature(
                        row["timestamp"], row["action"], row["skill_id"], row["intent_hash"], row["preview"] or ""
                    )
                    entry["signature_valid"] = hmac.compare_digest(row["signature"], expected)
                results.append(entry)
            return {"error": None, "result": {"events": results, "total": len(results)}}
        finally:
            conn.close()

    def _verify_all(self) -> dict:
        conn = sqlite3.connect(str(DB_PATH))
        try:
            rows = conn.execute("SELECT * FROM replay_events").fetchall()
            invalid = []
            for row in rows:
                expected = _compute_signature(
                    row[1], row[2], row[3], row[4], row[5] or ""
                )
                if not hmac.compare_digest(row[6], expected):
                    invalid.append(row[0])
            return {"error": None, "result": {"total": len(rows), "invalid_ids": invalid, "all_valid": len(invalid) == 0}}
        finally:
            conn.close()

    def _expire(self) -> dict:
        cutoff = (datetime.now() - timedelta(days=EXPIRY_DAYS)).isoformat()
        conn = sqlite3.connect(str(DB_PATH))
        try:
            old_rows = conn.execute(
                "SELECT * FROM replay_events WHERE timestamp < ?", (cutoff,)
            ).fetchall()
            self._archive_events(old_rows)
            c = conn.execute("DELETE FROM replay_events WHERE timestamp < ?", (cutoff,))
            deleted = c.rowcount
            conn.commit()
            self.publish("replay_audit:expired", {"deleted": deleted, "cutoff": cutoff})
            return {"error": None, "result": {"deleted": deleted, "cutoff": cutoff, "expiry_days": EXPIRY_DAYS}}
        finally:
            conn.close()

    def _archive_events(self, rows: list[sqlite3.Row]):
        if not rows:
            return
        with open(str(ARCHIVE_PATH), "a", encoding="utf-8") as f:
            for row in rows:
                entry = {
                    "id": row[0],
                    "timestamp": row[1],
                    "action": row[2],
                    "skill_id": row[3],
                    "intent_hash": row[4],
                    "preview": row[5],
                    "signature": row[6],
                    "archived_at": datetime.now().isoformat(),
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _migrate(self, kwargs: dict) -> dict:
        json_path = Path(kwargs.get("json_path", "replay_event_log.json"))
        if not json_path.exists():
            return {"error": f"JSON file not found: {json_path}", "result": None}
        data = json.loads(json_path.read_text(encoding="utf-8"))
        events = data.get("events", [])
        if not events:
            return {"error": None, "result": {"migrated": 0, "source": str(json_path)}}

        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("BEGIN TRANSACTION")
        count = 0
        rows_to_insert = []
        try:
            for ev in events:
                timestamp = ev.get("timestamp", datetime.now().isoformat())
                action_type = ev.get("action", "UNKNOWN")
                skill_id = ev.get("skill_id", "unknown")
                intent_hash = ev.get("intent_hash", "")
                preview = (ev.get("preview") or "")[:500]
                signature = _compute_signature(timestamp, action_type, skill_id, intent_hash, preview)
                rows_to_insert.append((timestamp, action_type, skill_id, intent_hash, preview, signature))
                count += 1
            c.executemany(
                "INSERT INTO replay_events (timestamp, action, skill_id, intent_hash, preview, signature) VALUES (?, ?, ?, ?, ?, ?)",
                rows_to_insert,
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"error": f"Migration failed: {e}", "result": None}
        conn.close()
        return {"error": None, "result": {"migrated": count, "source": str(json_path)}}

    def _stats(self) -> dict:
        conn = sqlite3.connect(str(DB_PATH))
        try:
            total = conn.execute("SELECT COUNT(*) FROM replay_events").fetchone()[0]
            by_action = dict(conn.execute("SELECT action, COUNT(*) FROM replay_events GROUP BY action").fetchall())
            oldest = conn.execute("SELECT MIN(timestamp) FROM replay_events").fetchone()[0] or ""
            return {"error": None, "result": {
                "total_events": total,
                "by_action": by_action,
                "oldest_event": oldest,
                "db_path": str(DB_PATH),
                "expiry_days": EXPIRY_DAYS,
            }}
        finally:
            conn.close()

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, dict):
            result = self.execute(**payload)
        else:
            result = self.execute(action="list")
        if result.get("error"):
            return False, result["error"]
        return True, result["result"]
