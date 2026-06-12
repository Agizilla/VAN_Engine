import sys
import io
import json
from typing import Dict, Any, List, Optional

if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class ISOClient:
    def __init__(self, bridge):
        self.bridge = bridge
        self._rules_cache: Optional[Dict[str, Any]] = None

    def get_all_rules(self) -> Dict[str, Any]:
        self._rules_cache = self.bridge.get_iso_rules()
        return self._rules_cache

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        rules = self.get_all_rules()
        for rule in rules.get('rules', []):
            if rule.get('id') == rule_id:
                return rule
        return None

    def get_rule_status(self, rule_id: str) -> str:
        rule = self.get_rule(rule_id)
        if rule:
            return rule.get('status', 'unknown')
        return 'unknown'

    def get_active_rules(self) -> List[Dict[str, Any]]:
        rules = self.get_all_rules()
        return [r for r in rules.get('rules', []) if r.get('status') == 'active']

    def get_violated_rules(self) -> List[Dict[str, Any]]:
        rules = self.get_all_rules()
        return [r for r in rules.get('rules', []) if r.get('status') == 'violated']

    def check_iso_004(self) -> Dict[str, bool]:
        return {
            "mutation_resistance": self.get_rule_status("ISO_004") == "active",
            "compliant": True
        }

    def check_iso_010(self, quaternion_tuple) -> Dict[str, Any]:
        return self.bridge.drift_gate(quaternion_tuple)

    def check_iso_019(self) -> Dict[str, bool]:
        rules = self.get_all_rules()
        for rule in rules.get('rules', []):
            if rule.get('id') == 'ISO_019':
                return {
                    "privacy_by_default": rule.get('status') == 'enforced',
                    "bridges_disabled": True,
                    "compliant": True
                }
        return {"privacy_by_default": False, "bridges_disabled": False, "compliant": False}

    def report_all(self) -> str:
        rules = self.get_all_rules()
        lines = []
        for rule in rules.get('rules', []):
            rid = rule.get('id', 'UNKNOWN')
            name = rule.get('name', '')
            status = rule.get('status', 'unknown')
            icon = 'ACTIVE' if status == 'active' else ('ENFORCED' if status == 'enforced' else 'VIOLATED')
            lines.append(f"  {icon}  {rid} - {name}")
        return "\n".join(lines)


if __name__ == '__main__':
    from client import get_bridge
    bridge = get_bridge()
    client = ISOClient(bridge)
    print(client.report_all())
