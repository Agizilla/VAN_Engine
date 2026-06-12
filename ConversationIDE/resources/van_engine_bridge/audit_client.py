import sys
import io
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class AuditClient:
    def __init__(self, bridge):
        self.bridge = bridge

    def log_event(self, component: str, action: str,
                  before: Optional[Tuple[float, float, float, float]] = None,
                  after: Optional[Tuple[float, float, float, float]] = None):
        self.bridge.log_audit(component, action, before, after)

    def read_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        audit_path = self.bridge.audit_path
        if not audit_path.exists():
            return []

        events = []
        with open(audit_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return events[-limit:]

    def get_events_by_component(self, component: str, limit: int = 50) -> List[Dict[str, Any]]:
        events = self.read_events(limit * 10)
        return [e for e in events if e.get('component') == component][-limit:]

    def get_events_by_action(self, action: str, limit: int = 50) -> List[Dict[str, Any]]:
        events = self.read_events(limit * 10)
        return [e for e in events if e.get('action') == action][-limit:]

    def get_drift_events(self, min_drift: float = 0.0, limit: int = 50) -> List[Dict[str, Any]]:
        events = self.read_events(limit * 10)
        return [
            e for e in events
            if e.get('magnitude_drift') is not None and e['magnitude_drift'] >= min_drift
        ][-limit:]

    def get_recent_audit_summary(self, minutes: int = 60) -> Dict[str, Any]:
        cutoff = time.time() - (minutes * 60)
        events = self.read_events(1000)
        recent = [e for e in events if e.get('timestamp', 0) >= cutoff]

        components = {}
        actions = {}
        for event in recent:
            comp = event.get('component', 'unknown')
            act = event.get('action', 'unknown')
            components[comp] = components.get(comp, 0) + 1
            actions[act] = actions.get(act, 0) + 1

        return {
            "total_recent": len(recent),
            "time_window_minutes": minutes,
            "components": components,
            "actions": actions,
            "drift_events": len([e for e in recent if e.get('magnitude_drift') is not None])
        }


if __name__ == '__main__':
    from client import get_bridge
    bridge = get_bridge()
    client = AuditClient(bridge)
    client.log_event("test", "system_check")
    print(json.dumps(client.get_recent_audit_summary(), indent=2))
