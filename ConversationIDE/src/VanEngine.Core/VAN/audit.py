from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import List, Optional


class AuditSeverity(int, Enum):
    Debug = 0
    Info = 1
    Warning = 2
    Error = 3
    Critical = 4


class AuditEntry:
    def __init__(
        self,
        timestamp: datetime | None = None,
        category: str = "",
        message: str = "",
        severity: AuditSeverity = AuditSeverity.Info,
    ):
        self.Timestamp = timestamp or datetime.now(timezone.utc)
        self.Category = category
        self.Message = message
        self.Severity = severity

    def ToString(self) -> str:
        ts = self.Timestamp.isoformat().replace("+00:00", "Z")
        return f"[{ts}] [{self.Severity.name}] [{self.Category}] {self.Message}"

    def ToDictionary(self) -> dict:
        return {
            "timestamp": self.Timestamp.isoformat().replace("+00:00", "Z"),
            "category": self.Category,
            "message": self.Message,
            "severity": self.Severity.name,
        }


class AuditLog:
    def __init__(self, log_path: str, max_entries: int = 10000):
        self._log_path = log_path
        self._max_entries = max_entries
        self._lock = Lock()
        self._entries: List[AuditEntry] = []
        self._writer: Optional[object] = None
        self._ensure_writer()

    @property
    def Count(self) -> int:
        with self._lock:
            return len(self._entries)

    def Record(
        self,
        category: str,
        message: str,
        severity: AuditSeverity = AuditSeverity.Info,
    ) -> None:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            category=category,
            message=message,
            severity=severity,
        )
        with self._lock:
            self._entries.append(entry)
            if self._writer is not None:
                self._writer.write(entry.ToString() + "\n")
                self._writer.flush()
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-(self._max_entries):]

    def RecordEnvelope(self, carrier: str, modulation: str, status: str) -> None:
        self.Record("Envelope", f"Carrier={carrier} Mod={modulation} Status={status}", AuditSeverity.Debug)

    def RecordError(self, context: str, error: str) -> None:
        self.Record("Error", f"[{context}] {error}", AuditSeverity.Error)

    def RecordWarning(self, context: str, warning: str) -> None:
        self.Record("Warning", f"[{context}] {warning}", AuditSeverity.Warning)

    def Query(
        self,
        category: Optional[str] = None,
        min_severity: Optional[AuditSeverity] = None,
        max_results: int = 50,
    ) -> List[AuditEntry]:
        with self._lock:
            result = list(self._entries)
            if category is not None:
                result = [e for e in result if e.Category.lower() == category.lower()]
            if min_severity is not None:
                result = [e for e in result if e.Severity.value >= min_severity.value]
            result.sort(key=lambda e: e.Timestamp, reverse=True)
            return result[:max_results]

    def GetRecent(self, count: int = 20) -> List[AuditEntry]:
        with self._lock:
            sorted_entries = sorted(self._entries, key=lambda e: e.Timestamp, reverse=True)
            return sorted_entries[:count]

    def Clear(self) -> None:
        with self._lock:
            self._entries.clear()

    async def FlushAsync(self) -> None:
        with self._lock:
            if self._writer is not None:
                self._writer.flush()

    def _ensure_writer(self) -> None:
        try:
            dir_path = os.path.dirname(self._log_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            self._writer = open(self._log_path, "a", encoding="utf-8")
        except Exception:
            self._writer = None

    def Dispose(self) -> None:
        with self._lock:
            if self._writer is not None:
                self._writer.close()
                self._writer = None
            self._entries.clear()
