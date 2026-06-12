from __future__ import annotations

import threading
import time
from typing import Any


class Metrics:
    def __init__(self):
        self._envelopes_processed = 0
        self._errors_encountered = 0
        self._total_processing_ticks = 0
        self._active_processors = 0
        self._lock = threading.Lock()

    @property
    def envelopes_processed(self) -> int:
        return self._envelopes_processed

    @property
    def errors_encountered(self) -> int:
        return self._errors_encountered

    @property
    def total_processing_ticks(self) -> int:
        return self._total_processing_ticks

    @property
    def active_processors(self) -> int:
        return self._active_processors

    @property
    def average_processing_ms(self) -> float:
        count = self.envelopes_processed
        return (self.total_processing_ticks / count / 10_000) if count > 0 else 0.0

    def begin_processing(self) -> _MetricsScope:
        with self._lock:
            self._active_processors += 1
        return _MetricsScope(self)

    def record_envelope(self) -> None:
        with self._lock:
            self._envelopes_processed += 1

    def record_error(self) -> None:
        with self._lock:
            self._errors_encountered += 1

    def record_ticks(self, ticks: int) -> None:
        with self._lock:
            self._total_processing_ticks += ticks

    def snapshot(self) -> dict[str, Any]:
        return {
            "envelopes_processed": self.envelopes_processed,
            "errors_encountered": self.errors_encountered,
            "average_processing_ms": self.average_processing_ms,
            "active_processors": self.active_processors,
            "total_processing_ticks": self.total_processing_ticks,
        }

    def reset(self) -> None:
        with self._lock:
            self._envelopes_processed = 0
            self._errors_encountered = 0
            self._total_processing_ticks = 0
            self._active_processors = 0


class _MetricsScope:
    def __init__(self, metrics: Metrics):
        self._metrics = metrics
        self._start = time.perf_counter_ns()

    def __enter__(self) -> _MetricsScope:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        elapsed_ns = time.perf_counter_ns() - self._start
        elapsed_ticks = elapsed_ns  # 1 tick = 100ns in .NET; use ns directly
        self._metrics.record_ticks(elapsed_ticks)
        with self._metrics._lock:
            self._metrics._active_processors -= 1
