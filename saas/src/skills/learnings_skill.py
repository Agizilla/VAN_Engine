"""Learnings Skill — shared knowledge registry for agents.
Reads/writes ~/.claude/PAI/LEARNINGS/algorithm_learnings.jsonl

Usage:
  GET  /hooks/learnings              → list last 10 learnings
  POST /hooks/learnings {"action":"list","limit":5}
  POST /hooks/learnings {"action":"add","task":"...","effort":"standard","learnings":["..."],"adjusted_behaviour":"..."}
  POST /hooks/learnings {"action":"fix"}  → repair malformed lines
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from .base import BaseSkill, register_skill
except ImportError:
    from skills.base import BaseSkill, register_skill

_LEARNINGS_PATH = Path.home() / ".claude" / "PAI" / "LEARNINGS" / "algorithm_learnings.jsonl"


def _read_raw() -> list[str]:
    if not _LEARNINGS_PATH.exists():
        return []
    return _LEARNINGS_PATH.read_text(encoding="utf-8").splitlines()


def _parse_entries(lines: list[str]) -> list[dict]:
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            if isinstance(entry, dict):
                entries.append(entry)
        except json.JSONDecodeError:
            pass
    return entries


def _append_entry(entry: dict):
    _LEARNINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(str(_LEARNINGS_PATH), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _fix_file() -> dict:
    """Repair malformed JSONL: keep only valid lines."""
    raw = _read_raw()
    valid = []
    fixed_count = 0
    for line in raw:
        line = line.strip()
        if not line:
            continue
        try:
            json.loads(line)
            valid.append(line)
        except json.JSONDecodeError:
            fixed_count += 1
    _LEARNINGS_PATH.write_text("\n".join(valid) + "\n", encoding="utf-8")
    return {"fixed": fixed_count, "remaining": len(valid)}


@register_skill("learnings", "system")
class LearningsSkill(BaseSkill):
    name = "learnings"
    description = "Shared knowledge registry — agents read before acting, write after learning"
    category = "system"
    version = "1.0.0"
    author = "ClawDia / OpenCode / Captain"
    tags = ["learnings", "registry", "memory", "agents", "self-improvement"]
    required_libs = []
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "add", "fix", "list_peers", "add_peer", "broadcast"],
                "description": "list=query, add=new entry, fix=repair, list_peers/show peers, add_peer=register peer, broadcast=gossip to all peers",
                "default": "list",
            },
            "url": {
                "type": "string",
                "description": "Peer URL (add_peer action)",
                "default": "",
            },
            "limit": {
                "type": "integer",
                "description": "Max entries to return (list only)",
                "default": 10,
                "minimum": 1,
                "maximum": 100,
            },
            "task": {
                "type": "string",
                "description": "Filter by task substring (list only)",
                "default": "",
            },
            "effort": {
                "type": "string",
                "enum": ["", "quick", "standard", "extended", "deep"],
                "description": "Filter by effort level (list only)",
                "default": "",
            },
            "since": {
                "type": "string",
                "description": "ISO timestamp — only entries after this date (list only)",
                "default": "",
            },
            "learnings": {
                "type": "array",
                "description": "Array of learning strings or objects with id/learning/source (add only)",
                "items": {},
                "default": [],
            },
            "adjusted_behaviour": {
                "type": "string",
                "description": "Behaviour override for future sessions (add only)",
                "default": "",
            },
            "author": {
                "type": "object",
                "description": "Attribution info: {name, role, model, session_id} (add only)",
                "default": None,
            },
            "tags": {
                "type": "array",
                "description": "Tags for filtering (add only)",
                "items": {"type": "string"},
                "default": [],
            },
            "context": {
                "type": "object",
                "description": "Contextual metadata: {repo, branch, session, trigger} (add only)",
                "default": None,
            },
            "references": {
                "type": "array",
                "description": "Reference list: skill names, files, or URLs (add only)",
                "items": {"type": "string"},
                "default": [],
            },
        },
        "required": ["action"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "entries": {"type": "array"},
            "count": {"type": "integer"},
            "total": {"type": "integer"},
        },
    }

    def execute(self, **kwargs):
        action = kwargs.get("action", "list")

        if action == "fix":
            result = _fix_file()
            return {"result": {"action": "fix", "fixed": result["fixed"], "remaining": result["remaining"]}}

        if action in ("list_peers", "add_peer", "broadcast"):
            import requests
            base = "http://localhost:8001/hooks/learnings/gossip"
            try:
                if action == "list_peers":
                    resp = requests.get(f"{base}/peers", timeout=10)
                    return {"result": {"action": "list_peers", **resp.json()}}
                elif action == "add_peer":
                    url = kwargs.get("url", "").strip()
                    if not url:
                        return {"result": {"action": "add_peer", "status": "error", "message": "url required"}}
                    resp = requests.post(f"{base}/peers", json={"url": url}, timeout=10)
                    return {"result": {"action": "add_peer", **resp.json()}}
                else:
                    resp = requests.post(f"{base}/broadcast", timeout=30)
                    return {"result": {"action": "broadcast", **resp.json()}}
            except Exception as e:
                return {"result": {"action": action, "status": "error", "message": str(e)}}

        raw = _read_raw()
        all_entries = _parse_entries(raw)

        if action == "add":
            task = kwargs.get("task", "").strip()
            if not task:
                return {"error": "task is required for add action"}
            learnings = kwargs.get("learnings", [])
            if not isinstance(learnings, list):
                learnings = [str(learnings)]
            if not learnings:
                return {"error": "learnings array is required for add action"}

            entry = {
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "effort": kwargs.get("effort", "standard"),
                "task": task,
                "learnings": learnings,
            }

            for field in ["adjusted_behaviour", "author", "tags", "context", "references"]:
                val = kwargs.get(field)
                if val is not None and val != "" and val != []:
                    entry[field] = val

            _append_entry(entry)
            all_entries.append(entry)
            return {"result": {"action": "add", "entry": entry, "total": len(all_entries)}}

        # list action
        limit = kwargs.get("limit", 10)
        task_filter = kwargs.get("task", "").strip().lower()
        effort_filter = kwargs.get("effort", "").strip().lower()
        since_filter = kwargs.get("since", "").strip()

        filtered = list(all_entries)
        if task_filter:
            filtered = [e for e in filtered if task_filter in e.get("task", "").lower()]
        if effort_filter:
            filtered = [e for e in filtered if e.get("effort", "").lower() == effort_filter]
        if since_filter:
            filtered = [e for e in filtered if e.get("timestamp", "") >= since_filter]

        filtered.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        page = filtered[:limit]

        return {
            "result": {
                "action": "list",
                "entries": page,
                "count": len(page),
                "total": len(all_entries),
                "filtered_total": len(filtered),
            }
        }
