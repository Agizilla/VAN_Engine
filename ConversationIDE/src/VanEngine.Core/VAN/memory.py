from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
from math import log10
from pathlib import Path
from typing import List, Optional


@dataclass
class MemoryEntry:
    Hash: str = ""
    Summary: str = ""
    Tags: list[str] = field(default_factory=list)
    LastAccessed: str = ""
    AccessCount: int = 0


class MemoryStore:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._entries: List[MemoryEntry] = []

    @property
    def Count(self) -> int:
        return len(self._entries)

    def Index(self, hash: str, summary: str, tags: list[str]) -> None:
        entry = MemoryEntry(hash, summary, list(tags), datetime.now(timezone.utc).isoformat(), 0)
        for i, existing in enumerate(self._entries):
            if existing.Hash == hash:
                entry.AccessCount = existing.AccessCount
                self._entries[i] = entry
                return
        self._entries.append(entry)

    def Search(self, query: str, max_results: int = 5) -> List[MemoryEntry]:
        q = query.lower()
        query_tags = [t for t in q.split() if t]

        def score(entry: MemoryEntry) -> float:
            s = 0.0
            if q in entry.Summary.lower():
                s += 5
            for tag in entry.Tags:
                if tag.lower() in q:
                    s += 3
            for qt in query_tags:
                if any(tag.lower() == qt for tag in entry.Tags):
                    s += 10
            s += log10(entry.AccessCount + 1) * 0.5
            return s

        scored = sorted(((score(e), e) for e in self._entries), key=lambda x: x[0], reverse=True)
        out = []
        for _, entry in scored[:max_results]:
            entry.AccessCount += 1
            entry.LastAccessed = datetime.now(timezone.utc).isoformat()
            out.append(entry)
        return out

    def GetByTag(self, tag: str, max_results: int = 10) -> List[MemoryEntry]:
        return [e for e in sorted(self._entries, key=lambda e: e.LastAccessed, reverse=True) if tag.lower() in [t.lower() for t in e.Tags]][:max_results]

    def GetAll(self) -> List[MemoryEntry]:
        return list(self._entries)

    def Evict(self, hash: str) -> None:
        self._entries = [e for e in self._entries if e.Hash != hash]

    async def SaveAsync(self, path: str, ct=None) -> None:
        Path(path).write_text(json.dumps([asdict(e) for e in self._entries], indent=2), encoding="utf-8")

    async def LoadAsync(self, path: str, ct=None) -> None:
        p = Path(path)
        if not p.exists():
            return
        loaded = json.loads(p.read_text(encoding="utf-8"))
        self._entries = [MemoryEntry(**item) for item in loaded]

    async def ExportEventsToYaml(self, events_dir: str, session_id: str = "unknown") -> int:
        events_path = Path(events_dir)
        events_path.mkdir(parents=True, exist_ok=True)
        count = 0
        for entry in self._entries:
            ts = entry.LastAccessed or datetime.now(timezone.utc).isoformat()
            slug = ts.replace(":", "-").replace(".", "_")[:30]
            filename = f"memory_{slug}_{entry.Hash[:8]}.md"
            filepath = events_path / filename
            if filepath.exists():
                continue
            tags_yaml = "\n".join(f"  - {tag}" for tag in entry.Tags)
            content = f"""---
hash: {entry.Hash}
session: {session_id}
timestamp: {ts}
access_count: {entry.AccessCount}
tags:
{tags_yaml}
---

# Memory Event

**Hash:** `{entry.Hash}`
**Summary:** {entry.Summary}
**Tags:** {', '.join(entry.Tags) if entry.Tags else 'none'}
**Accessed:** {ts}
"""
            filepath.write_text(content.strip(), encoding="utf-8")
            count += 1
        return count

    def Dispose(self) -> None:
        self._entries.clear()
