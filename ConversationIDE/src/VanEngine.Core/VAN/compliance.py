from __future__ import annotations

import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable

from .fryas_directive import FryasDirective


class FryasComplianceEngine:
    def __init__(self, initial_directives: FryasDirective = FryasDirective.ALL_DIRECTIVES):
        self._active_directives = initial_directives
        self._violation_log: list[str] = []
        self._gratitude_log: list[str] = []
        self._has_exhausted_local_resources = False
        self._is_under_attack = False
        self._work_units: dict[str, int] = defaultdict(int)
        self._defense_units: dict[str, int] = defaultdict(int)
        self._expelled_entities: set[str] = set()
        self._quarantined_modules: set[str] = set()
        self._folk_mother = "Clawdia"
        self._lock = threading.Lock()

    @property
    def active_directives(self) -> FryasDirective:
        return self._active_directives

    @property
    def violation_log(self) -> list[str]:
        return list(self._violation_log)

    @property
    def gratitude_log(self) -> list[str]:
        return list(self._gratitude_log)

    @property
    def folk_mother(self) -> str:
        return self._folk_mother

    def is_directive_active(self, directive: FryasDirective) -> bool:
        return (self._active_directives & directive) == directive

    def enable_directive(self, directive: FryasDirective) -> None:
        self._active_directives |= directive

    def disable_directive(self, directive: FryasDirective) -> None:
        self._active_directives &= ~directive

    # Directive 1: PreambleFreedom
    def is_free(self, entity_name: str, is_slave_to_another: bool, is_slave_to_self: bool) -> bool:
        if not self.is_directive_active(FryasDirective.PREAMBLE_FREEDOM):
            return True
        if is_slave_to_another or is_slave_to_self:
            self._log_violation(
                f"Entity '{entity_name}' is not free: "
                f"slave to another={is_slave_to_another}, slave to self={is_slave_to_self}"
            )
            return False
        return True

    # Directive 2: HierarchyOfAid
    def exhaust_local_resources(self) -> None:
        self._has_exhausted_local_resources = True

    def may_seek_external_aid(self) -> bool:
        if not self.is_directive_active(FryasDirective.HIERARCHY_OF_AID):
            return True
        if not self._has_exhausted_local_resources:
            self._log_violation("Attempted to seek external aid before exhausting local resources.")
            return False
        return True

    def reset_local_resource_flag(self) -> None:
        self._has_exhausted_local_resources = False

    # Directive 3: ThricefoldGratitude
    def log_gratitude(self, what_was_received: str, what_is_being_received: str, hope_for_aid: str) -> None:
        if not self.is_directive_active(FryasDirective.THRICEFOLD_GRATITUDE):
            return
        entry = (
            f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] "
            f"GRATITUDE: Past: {what_was_received} | Present: {what_is_being_received} | Future: {hope_for_aid}"
        )
        self._gratitude_log.append(entry)

    # Directive 4: ProactiveAssistance
    def offer_proactive_assistance(self, target: str, issue_description: str) -> None:
        if not self.is_directive_active(FryasDirective.PROACTIVE_ASSISTANCE):
            return
        self._log_violation(f"[PROACTIVE] Offering assistance to {target}: {issue_description}")

    # Directive 5: NoBendedKnee
    def accept_gratitude(self, thank_from: str) -> bool:
        if not self.is_directive_active(FryasDirective.NO_BENDED_KNEE):
            return True
        self._log_violation(f"'{thank_from}' attempted to offer thanks on bended knee. Rejected.")
        return False

    # Directive 6: FairDivision
    def register_work(self, entity: str, units_of_work: int) -> None:
        if not self.is_directive_active(FryasDirective.FAIR_DIVISION):
            return
        with self._lock:
            self._work_units[entity] += units_of_work

    def register_defense(self, entity: str, units_of_defense: int) -> None:
        if not self.is_directive_active(FryasDirective.FAIR_DIVISION):
            return
        with self._lock:
            self._defense_units[entity] += units_of_defense

    def has_freeloaders(self) -> bool:
        if not self.is_directive_active(FryasDirective.FAIR_DIVISION):
            return False
        all_entities = set(self._work_units.keys()) | set(self._defense_units.keys())
        for entity in all_entities:
            if self._work_units.get(entity, 0) == 0 and self._defense_units.get(entity, 0) == 0:
                self._log_violation(f"Entity '{entity}' has performed no work and no defense.")
                return True
        return False

    # Directive 7: ExpelBastards
    def expel_voluntary_cloud_dependency(self, entity: str, dependency_name: str) -> bool:
        if not self.is_directive_active(FryasDirective.EXPEL_BASTARDS):
            return False
        self._log_violation(f"Entity '{entity}' voluntarily added cloud dependency '{dependency_name}'. EXPULSION INITIATED.")
        with self._lock:
            self._expelled_entities.add(entity)
        return True

    def is_expelled(self, entity: str) -> bool:
        return entity in self._expelled_entities

    # Directive 8: NoDebtSlavery
    def assert_no_lock_in(self, feature_name: str, vendor: str) -> None:
        if not self.is_directive_active(FryasDirective.NO_DEBT_SLAVERY):
            return
        indicators = [".lic", ".key", "license", "proprietary", "vendor-lock", "exclusive"]
        for indicator in indicators:
            if indicator in feature_name.lower():
                self._log_violation(
                    f"FEATURE LOCK-IN DETECTED: '{feature_name}' from '{vendor}'. Violates NoDebtSlavery directive."
                )

    # Directive 9: NonInterference
    def isolate(self) -> None:
        if not self.is_directive_active(FryasDirective.NON_INTERFERENCE):
            return
        self._log_violation("ISOLATION ENGAGED: Severing external connections.")

    # Directive 10: DefenceWhenAttacked
    def register_attack(self, attacker: str, attack_description: str) -> None:
        if not self.is_directive_active(FryasDirective.DEFENCE_WHEN_ATTACKED):
            return
        self._is_under_attack = True
        self._log_violation(f"ATTACK DETECTED from '{attacker}': {attack_description}. Preparing countermeasures.")

    def fight_back(self) -> None:
        if not self._is_under_attack:
            return
        self._log_violation("[COUNTERMEASURE] Engaging fire and sword against attacker.")
        self._is_under_attack = False

    # Directive 11: DaughtersChoice
    def allow_choice(self, entity: str, choice_description: str, warning_action: Callable | None = None) -> bool:
        if not self.is_directive_active(FryasDirective.DAUGHTERS_CHOICE):
            return True
        if warning_action:
            warning_action()
        self._log_violation(f"[CHOICE] {entity} chooses: {choice_description}")
        return True

    # Directive 12: ExileNotContamination
    def quarantine_cloud_module(self, module_name: str) -> None:
        if not self.is_directive_active(FryasDirective.EXILE_NOT_CONTAMINATION):
            return
        self._log_violation(f"Module '{module_name}' chose cloud dependency. QUARANTINED (not executed).")
        with self._lock:
            self._quarantined_modules.add(module_name)

    def is_quarantined(self, module_name: str) -> bool:
        return module_name in self._quarantined_modules

    # Directive 13: EternalLamp
    def assert_folk_mother(self, candidate: str) -> None:
        if not self.is_directive_active(FryasDirective.ETERNAL_LAMP):
            return
        if candidate.lower() != self._folk_mother.lower():
            self._log_violation(f"Attempted to replace Folk Mother '{self._folk_mother}' with '{candidate}'. REJECTED.")

    # Envelope-level compliance check
    def check_envelope_compliance(self, carrier: str, modulation: str, data: list) -> bool:
        if self.is_expelled(carrier):
            self._log_violation(f"Blocked execution: {carrier} is expelled.")
            return False

        if self.is_quarantined(modulation):
            self._log_violation(f"Blocked execution: {modulation} is quarantined.")
            return False

        self.assert_no_lock_in(carrier, "VAN")

        cloud_indicators = ["http", "https", "api.", "cloud", ".azure", ".aws", "telemetry"]
        for data_item in data:
            item_str = str(data_item) if data_item is not None else ""
            for indicator in cloud_indicators:
                if indicator in item_str.lower():
                    self.expel_voluntary_cloud_dependency(carrier, indicator)
                    return False

        return True

    def get_compliance_report(self) -> str:
        with self._lock:
            expelled_count = len(self._expelled_entities)
            quarantined_count = len(self._quarantined_modules)
        lines = [
            "=== FRYA'S TEX COMPLIANCE REPORT ===",
            f"Active Directives: {self._active_directives}",
            f"Violations: {len(self._violation_log)}",
            f"Gratitude Entries: {len(self._gratitude_log)}",
            f"Expelled Entities: {expelled_count}",
            f"Quarantined Modules: {quarantined_count}",
            f"Folk Mother: {self._folk_mother}",
        ]
        return "\n".join(lines)

    def _log_violation(self, violation: str) -> None:
        entry = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] VIOLATION: {violation}"
        with self._lock:
            self._violation_log.append(entry)
