from __future__ import annotations

import sys
from typing import ClassVar


class OfflineOnlyAttribute:
    def __init__(self, reason: str):
        self.reason = reason


class TelemetryGuard:
    _blocked_types: ClassVar[frozenset[str]] = frozenset({
        "http.client",
        "urllib.request",
        "urllib.request.urlopen",
        "socket.create_connection",
        "socket.socket.connect",
        "ssl.wrap_socket",
    })

    _warnings: ClassVar[list[str]] = []
    _initialized: ClassVar[bool] = False

    @classmethod
    def warnings(cls) -> list[str]:
        return list(cls._warnings)

    @classmethod
    def has_violations(cls) -> bool:
        return len(cls._warnings) > 0

    @classmethod
    def scan_module(cls, module_name: str) -> None:
        if cls._initialized:
            return
        cls._initialized = True
        if module_name in sys.modules:
            mod = sys.modules[module_name]
            name = getattr(mod, "__name__", module_name)
            for blocked in cls._blocked_types:
                if blocked in name:
                    cls._warnings.append(f"Offline violation: {blocked} referenced by {name}")

    @classmethod
    def scan_all_loaded(cls) -> None:
        for mod_name in list(sys.modules.keys()):
            cls.scan_module(mod_name)

    @classmethod
    def assert_offline(cls) -> None:
        if cls.has_violations():
            msg = f"Offline telemetry violations detected:\n" + "\n".join(cls.warnings())
            raise RuntimeError(msg)
