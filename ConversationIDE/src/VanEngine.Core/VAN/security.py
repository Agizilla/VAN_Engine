from __future__ import annotations

from typing import Optional, Set

from .audit import AuditLog, AuditSeverity


def _contains_forbidden(value: str, forbidden: Set[str]) -> Optional[str]:
    low = value.lower()
    for term in forbidden:
        if term in low:
            return term
    return None


class RighteousnessFilter:
    _DEFAULT_FORBIDDEN = {
        "upload", "phone home", "analytics", "telemetry",
        "exfiltrate", "call home", "beacon", "ping", "track",
        "surveillance", "callback", "cloud", "spy", "snoop",
    }

    def __init__(self, audit: Optional[AuditLog] = None):
        self._audit = audit
        self._forbidden_terms: Set[str] = set(self._DEFAULT_FORBIDDEN)

    def IsRighteous(self, envelope) -> bool:
        for item in envelope.Data:
            s = str(item) if item is not None else ""
            if not s:
                continue
            hit = _contains_forbidden(s, self._forbidden_terms)
            if hit is not None:
                if self._audit is not None:
                    self._audit.Record(
                        "Righteousness",
                        f"Blocked envelope — forbidden term '{hit}' found in DATA "
                        f"(Carrier={envelope.Carrier})",
                        AuditSeverity.Critical,
                    )
                return False

        hit = _contains_forbidden(envelope.Carrier, self._forbidden_terms)
        if hit is not None:
            if self._audit is not None:
                self._audit.Record(
                    "Righteousness",
                    f"Blocked envelope — forbidden CARRIER term '{hit}'",
                    AuditSeverity.Critical,
                )
            return False

        hit = _contains_forbidden(envelope.Modulation, self._forbidden_terms)
        if hit is not None:
            if self._audit is not None:
                self._audit.Record(
                    "Righteousness",
                    f"Blocked envelope — forbidden MODULATION term '{hit}'",
                    AuditSeverity.Critical,
                )
            return False

        return True

    def AddTerm(self, term: str) -> None:
        self._forbidden_terms.add(term)

    def RemoveTerm(self, term: str) -> bool:
        was_present = term in self._forbidden_terms
        self._forbidden_terms.discard(term)
        return was_present

    @property
    def Terms(self) -> Set[str]:
        return set(self._forbidden_terms)
