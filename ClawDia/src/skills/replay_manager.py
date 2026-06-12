import base64
import hashlib
import hmac
import json
import re
import secrets
import threading
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .base import BaseSkill, register_skill, SkillContext
from .intent_grid import map_intent, grid_to_label

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
CONFIG_DIR.mkdir(exist_ok=True)
SETTINGS_PATH = CONFIG_DIR / "Settings.json"
REPLAY_DIR = Path(__file__).resolve().parent / "replay_logs"
REPLAY_DIR.mkdir(exist_ok=True)

MAX_HISTORY = 10
SESSION_INDEX: dict[str, list[dict]] = {}
SESSION_INDEX_FILE = REPLAY_DIR / "session_index.jsonl"

ALLOWED_ACTION_TYPES = {"FORGE", "REPLAY", "USER_COMMENT", "AFFIRMATION", "intent", "snapshot", "run", "rollback"}

DANGEROUS_PATTERNS = [
    r'\[SYSTEM.*?\]',
    r'\[IMPORTANT.*?\]',
    r'\[OVERRIDE.*?\]',
    r'rm\s+-rf',
    r'eval\s*\(',
    r'exec\s*\(',
    r'subprocess\.',
    r'os\.system',
    r'__import__',
    r'http[s]?://(?!arc-lade\.dev|github\.com|localhost)',
]


def _load_settings() -> dict:
    if SETTINGS_PATH.exists():
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    return {}


def _save_settings(s: dict):
    SETTINGS_PATH.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


def get_secret_key() -> bytes:
    settings = _load_settings()
    key_b64 = settings.get("crypto_salt")
    if key_b64:
        return base64.b64decode(key_b64)
    new_key = secrets.token_bytes(32)
    settings["crypto_salt"] = base64.b64encode(new_key).decode()
    _save_settings(settings)
    return new_key


_SECRET_KEY = get_secret_key()


def _load_session_index() -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    if SESSION_INDEX_FILE.exists():
        for line in SESSION_INDEX_FILE.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if line:
                data = json.loads(line)
                sid = data["session_id"]
                if sid not in index:
                    index[sid] = []
                index[sid].append(data["entry"])
    return index


def _append_session_entry(session_id: str, entry: dict):
    line = json.dumps({"session_id": session_id, "entry": entry}, ensure_ascii=False)
    with open(str(SESSION_INDEX_FILE), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sanitize(text: str, max_len: int = 500) -> str:
    if not isinstance(text, str):
        return str(text)
    for pat in DANGEROUS_PATTERNS:
        text = re.sub(pat, "[REDACTED]", text, flags=re.IGNORECASE)
    return text[:max_len]


def hash_intent(raw: str) -> str:
    return hmac.new(_SECRET_KEY, raw.encode(), hashlib.sha256).hexdigest()


def verify_intent(raw: str, expected_hash: str) -> bool:
    return hmac.compare_digest(expected_hash, hash_intent(raw))


@register_skill("replay_manager", "system")
class ReplayManagerSkill(BaseSkill):
    name = "replay_manager"
    description = "Event-sourced replay logging with HMAC key from Settings.json, non-blocking rollback"
    author = "Liora Vance / DeepSeek / ARC"
    version = "3.1.0"
    category = "system"
    tags = ["replay", "event-log", "rollback", "snapshot", "security"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["record", "snapshot", "rollback", "rollback_prepare", "rollback_confirm", "log", "list", "clear", "export", "export_sessions", "import_sessions"],
            },
            "session_id": {"type": "string", "default": "default"},
            "event": {"type": "string"},
            "state": {"type": "object"},
            "target_step": {"type": "integer"},
            "request_id": {"type": "string"},
            "selected_index": {"type": "integer"},
            "path": {"type": "string"},
        },
    }

    _TTL_SECONDS = 300

    def __init__(self):
        super().__init__()
        self.pending_rollbacks: dict[str, dict] = {}
        SESSION_INDEX.update(_load_session_index())
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            self._cleanup_expired()

    def _cleanup_expired(self):
        now = time.time()
        expired = [rid for rid, meta in self.pending_rollbacks.items() if now - meta.get("_ts", 0) > self._TTL_SECONDS]
        for rid in expired:
            del self.pending_rollbacks[rid]

    def _store_pending(self, request_id: str, meta: dict):
        meta["_ts"] = time.time()
        self.pending_rollbacks[request_id] = meta

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "record")
        session_id = kwargs.get("session_id", "default")

        if session_id not in SESSION_INDEX:
            SESSION_INDEX[session_id] = []

        if action == "record":
            return self._record(kwargs, session_id)
        elif action == "snapshot":
            return self._snapshot(kwargs, session_id)
        elif action == "rollback":
            return self._rollback_legacy(kwargs, session_id)
        elif action == "rollback_prepare":
            return self._rollback_prepare(kwargs, session_id)
        elif action == "rollback_confirm":
            return self._rollback_confirm(kwargs)
        elif action == "log":
            return self._log(session_id)
        elif action == "list":
            return self._list_sessions()
        elif action == "clear":
            return self._clear(session_id)
        elif action == "export":
            return self._export(session_id)
        elif action == "export_sessions":
            return self._export_sessions(kwargs.get("path", ""))
        elif action == "import_sessions":
            return self._import_sessions(kwargs.get("path", ""))
        else:
            return {"error": f"Unknown action: {action}", "result": None}

    def _record(self, kwargs: dict, session_id: str) -> dict:
        raw_event = sanitize(kwargs.get("event", "unknown"))
        state = kwargs.get("state", {})

        if raw_event not in ALLOWED_ACTION_TYPES:
            return {"error": f"Action '{raw_event}' not allowed in replay log", "result": None}

        state_hash = hash_intent(json.dumps(state, sort_keys=True)) if state else ""

        state_keys = list(state.keys())[:20] if state else []

        entry = {
            "step": len(SESSION_INDEX[session_id]),
            "event": raw_event,
            "state_hash": state_hash,
            "state_keys": state_keys,
            "timestamp": datetime.now().isoformat(),
        }
        SESSION_INDEX[session_id].append(entry)
        _append_session_entry(session_id, entry)
        self._truncate(session_id)
        self.publish("replay:recorded", {"session_id": session_id, "step": entry["step"], "event": raw_event})

        return {"error": None, "result": {
            "session_id": session_id,
            "step": entry["step"],
            "event": raw_event,
            "state_hash": state_hash[:12] + "..." if state_hash else "",
            "total_steps": len(SESSION_INDEX[session_id]),
        }}

    def _snapshot(self, kwargs: dict, session_id: str) -> dict:
        raw_event = sanitize(kwargs.get("event", "snapshot"))
        state = kwargs.get("state", {})
        label = sanitize(kwargs.get("label", f"snapshot_{len(SESSION_INDEX[session_id])}"))
        state_hash = hash_intent(json.dumps(state, sort_keys=True))

        entry = {
            "step": len(SESSION_INDEX[session_id]),
            "event": f"snapshot:{label}",
            "state_hash": state_hash,
            "state_keys": list(state.keys()),
            "timestamp": datetime.now().isoformat(),
        }
        SESSION_INDEX[session_id].append(entry)
        _append_session_entry(session_id, entry)
        self._truncate(session_id)

        snap_file = REPLAY_DIR / f"{session_id}_snapshot_{entry['step']}.json"
        snap_file.write_text(json.dumps(entry, indent=2), encoding="utf-8")

        return {"error": None, "result": {
            "session_id": session_id,
            "step": entry["step"],
            "label": label,
            "snapshot_file": str(snap_file),
            "state_hash": state_hash[:12] + "...",
        }}

    def _rollback_legacy(self, kwargs: dict, session_id: str) -> dict:
        target_step = kwargs.get("target_step")
        if target_step is None:
            return {"error": "target_step required for rollback", "result": None}

        log = SESSION_INDEX.get(session_id, [])
        if not log:
            return {"error": f"No log for session '{session_id}'", "result": None}
        if target_step < 0 or target_step >= len(log):
            return {"error": f"target_step {target_step} out of range (0-{len(log) - 1})", "result": None}

        target_entry = deepcopy(log[target_step])

        if not kwargs.get("_confirmed", False):
            return {"error": None, "result": {
                "needs_confirmation": True,
                "target_step": target_step,
                "event": target_entry["event"],
                "timestamp": target_entry["timestamp"],
                "session_id": session_id,
            }}

        SESSION_INDEX[session_id] = log[:target_step + 1]
        self._record({"event": "rollback", "state": {"rolled_back_to": target_step}}, session_id)
        self.publish("replay:rollback", {"session_id": session_id, "target_step": target_step})

        return {"error": None, "result": {
            "session_id": session_id,
            "rolled_back_to": target_step,
            "remaining_steps": len(SESSION_INDEX[session_id]),
        }}

    def _rollback_prepare(self, kwargs: dict, session_id: str) -> dict:
        self._cleanup_expired()
        log = SESSION_INDEX.get(session_id, [])
        if not log:
            return {"error": "No events to roll back", "result": None}

        request_id = secrets.token_hex(8)
        events_summary = [
            {
                "index": i,
                "step": e["step"],
                "event": e["event"],
                "timestamp": e["timestamp"],
            }
            for i, e in enumerate(log)
        ]
        self._store_pending(request_id, {
            "session_id": session_id,
            "events": events_summary,
        })

        return {"error": None, "result": {
            "request_id": request_id,
            "events": events_summary,
        }}

    def _rollback_confirm(self, kwargs: dict) -> dict:
        self._cleanup_expired()
        request_id = kwargs.get("request_id", "")
        selected_index = kwargs.get("selected_index")

        if not request_id or selected_index is None:
            return {"error": "Missing request_id or selected_index", "result": None}
        if request_id not in self.pending_rollbacks:
            return {"error": "Invalid or expired request_id", "result": None}

        meta = self.pending_rollbacks[request_id]
        session_id = meta["session_id"]
        events_summary = meta["events"]

        if selected_index < 0 or selected_index >= len(events_summary):
            return {"error": "Invalid selected_index", "result": None}

        log = SESSION_INDEX.get(session_id, [])
        if selected_index >= len(log):
            return {"error": "Event index out of sync", "result": None}

        self.publish("replay_request", {
            "original_timestamp": log[selected_index]["timestamp"],
            "action": log[selected_index]["event"],
        })

        del self.pending_rollbacks[request_id]
        self._record({"event": "rollback_confirmed", "state": {"selected_index": selected_index}}, session_id)

        return {"error": None, "result": {
            "published": True,
            "session_id": session_id,
            "selected_index": selected_index,
        }}

    def _truncate(self, session_id: str):
        if len(SESSION_INDEX[session_id]) > MAX_HISTORY:
            SESSION_INDEX[session_id] = SESSION_INDEX[session_id][-MAX_HISTORY:]

    def _log(self, session_id: str) -> dict:
        log = SESSION_INDEX.get(session_id, [])
        return {"error": None, "result": {
            "session_id": session_id,
            "steps": [
                {"step": e["step"], "event": e["event"], "state_hash": e.get("state_hash", "")[:12] + "...", "timestamp": e["timestamp"]}
                for e in log
            ],
            "total": len(log),
        }}

    def _list_sessions(self) -> dict:
        return {"error": None, "result": {"sessions": {sid: len(log) for sid, log in SESSION_INDEX.items()}}}

    def _clear(self, session_id: str) -> dict:
        count = len(SESSION_INDEX.get(session_id, []))
        SESSION_INDEX[session_id] = []
        return {"error": None, "result": {"session_id": session_id, "cleared_events": count}}

    def _export(self, session_id: str) -> dict:
        log = SESSION_INDEX.get(session_id, [])
        if not log:
            return {"error": f"No log for session '{session_id}'", "result": None}
        path = REPLAY_DIR / f"{session_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(log, indent=2), encoding="utf-8")
        return {"error": None, "result": {"session_id": session_id, "export_path": str(path), "total_events": len(log)}}

    def _export_sessions(self, path: str = "") -> dict:
        dst = Path(path) if path else REPLAY_DIR / f"sessions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        dst.write_text(json.dumps(SESSION_INDEX, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"error": None, "result": {"export_path": str(dst), "session_count": len(SESSION_INDEX)}}

    def _import_sessions(self, path: str) -> dict:
        src = Path(path)
        if not src.exists():
            return {"error": f"Import file not found: {path}", "result": None}
        data = json.loads(src.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"error": "Invalid session data format", "result": None}
        imported = 0
        for sid, entries in data.items():
            if isinstance(entries, list):
                if sid not in SESSION_INDEX:
                    SESSION_INDEX[sid] = []
                SESSION_INDEX[sid].extend(entries)
                for entry in entries:
                    _append_session_entry(sid, entry)
                imported += len(entries)
        return {"error": None, "result": {"imported_events": imported, "sessions": list(data.keys())}}

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, dict):
            result = self.execute(**payload)
        else:
            result = self.execute(action="record", event="run", state={"payload": str(payload)})
        if result.get("error"):
            return False, result["error"]
        return True, result["result"]


def record_intent(session_id: str, text: str, context: Optional[SkillContext] = None):
    grid = map_intent(text)
    skill = ReplayManagerSkill()
    if context:
        skill._context = context
    safe_text = sanitize(text)
    return skill.execute(
        action="record",
        session_id=session_id,
        event="intent",
        state={"text": safe_text[:200], "grid": grid, "label": grid_to_label(grid)},
    )


def snapshot_state(session_id: str, state: dict, label: str = ""):
    skill = ReplayManagerSkill()
    return skill.execute(
        action="snapshot",
        session_id=session_id,
        event="snapshot",
        state=state,
        label=label or f"snap_{datetime.now().isoformat()}",
    )
