# -*- coding: utf-8 -*-
"""
ISO Registry — Single Source of Truth for ISO Rules
ISO_020: Never report unverified status. Query or clarify.
ISO_015: Every query leaves an immutable audit trail.
Windows UTF-8 safe
"""

import sys
import io
import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer and not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


@dataclass(frozen=True)
class AuditEntry:
    """ISO_015: Immutable audit event for every registry query"""
    timestamp: str
    query_type: str
    query_arg: str
    result: str


class ISORegistry:
    """Single source of truth for ISO rule status.

    ISO_020: All status reports must trace to ISO_Rules.json.
    No module may hardcode or assume a rule's status.
    """

    _rules: Dict[str, dict] = {}
    _loaded: bool = False
    _audit_log: List[AuditEntry] = []

    @classmethod
    def load(cls, path: Optional[Path] = None) -> int:
        """Load rules from ISO_Rules.json. Returns rule count."""
        if path is None:
            path = Path(__file__).parent / "ISO_Rules.json"

        if not path.exists():
            raise FileNotFoundError(f"ISO_Rules.json not found at {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cls._rules = {}
        for rule in data.get("rules", []):
            cls._rules[rule["id"]] = rule

        cls._loaded = True
        return len(cls._rules)

    @classmethod
    def _audit(cls, qtype: str, qarg: str, result: str):
        """ISO_015: Record every query as an immutable audit entry."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            query_type=qtype,
            query_arg=qarg,
            result=result
        )
        cls._audit_log.append(entry)

    @classmethod
    def get_status(cls, iso_id: str) -> dict:
        """Query a single rule's status. Never assumes.

        ISO_020: Returns {"status": "unknown"} if not found —
        never fabricates a result.
        """
        if not cls._loaded:
            cls.load()

        result = cls._rules.get(iso_id, {"status": "unknown"})
        cls._audit("get_status", iso_id, result.get("status", "unknown"))
        return result

    @classmethod
    def report_all(cls) -> str:
        """Generate status report from actual data, not memory.

        Returns a deterministic string suitable for context windows.
        """
        if not cls._loaded:
            cls.load()

        lines = []
        for iso_id in sorted(cls._rules.keys()):
            rule = cls._rules[iso_id]
            status = rule["status"]
            name = rule.get("name", "")
            lines.append(f"{iso_id} ({name}): {status}")

        report = "\n".join(lines)
        cls._audit("report_all", "", f"{len(cls._rules)} rules reported")
        return report

    @classmethod
    def get_audit_log(cls) -> List[AuditEntry]:
        """ISO_015: Return immutable audit trail."""
        return list(cls._audit_log)

    @classmethod
    def rule_count(cls) -> int:
        """Number of loaded rules."""
        if not cls._loaded:
            cls.load()
        return len(cls._rules)

    @classmethod
    def validate_all(cls) -> List[str]:
        """Validate that all rules have required fields.

        ISO_012: Self-validation — each rule checks its own integrity.
        Returns list of validation errors (empty = all valid).
        """
        if not cls._loaded:
            cls.load()

        errors = []
        for iso_id, rule in cls._rules.items():
            if "status" not in rule:
                errors.append(f"{iso_id}: missing status")
            elif rule["status"] not in ("active", "enforced"):
                errors.append(f"{iso_id}: invalid status '{rule['status']}'")
            if "name" not in rule:
                errors.append(f"{iso_id}: missing name")

        cls._audit("validate_all", "", f"{len(errors)} errors")
        return errors


def demo():
    """Demonstration of ISORegistry usage."""
    ISORegistry.load()

    print("=== ISO Registry Demo ===")
    print()

    # Query a single rule
    iso_020 = ISORegistry.get_status("ISO_020")
    print(f"ISO_020 status: {iso_020['status']}")
    print(f"ISO_020 rule: {iso_020.get('rule', 'N/A')}")
    print()

    # Generate full report
    print("=== Full Status Report ===")
    print(ISORegistry.report_all())
    print()

    # Self-validate
    errors = ISORegistry.validate_all()
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("All rules validated successfully")
    print()

    # Show audit trail
    print("=== Audit Trail ===")
    for entry in ISORegistry.get_audit_log():
        print(f"  [{entry.timestamp}] {entry.query_type}({entry.query_arg}) -> {entry.result}")


if __name__ == "__main__":
    demo()
