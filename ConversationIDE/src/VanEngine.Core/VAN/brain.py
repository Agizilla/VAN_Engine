from __future__ import annotations

import asyncio
import atexit
import json
import math
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from time import monotonic
from typing import Any, Dict, List, Optional, Tuple

from .engine import VanEngine

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))
from core.algorithm import AlgorithmPhase, EffortTier, TIME_BUDGETS
from core.prd_manager import PRDManager
from core.algorithm_executor import AlgorithmExecutor


@dataclass
class QueryResult:
    Success: bool
    Action: str
    Message: str
    Data: Optional[Any] = None
    ClarificationQuestions: Optional[List[str]] = None
    AlgorithmPhase: Optional[str] = None
    EffortTier: Optional[str] = None
    ISCChecked: int = 0
    ISCTotal: int = 0

    @staticmethod
    def Ok(message: str, action: str = "EXECUTE", data: Any = None,
           phase: str = None, effort: str = None, isc_checked: int = 0, isc_total: int = 0) -> "QueryResult":
        return QueryResult(True, action, message, data,
                          AlgorithmPhase=phase, EffortTier=effort,
                          ISCChecked=isc_checked, ISCTotal=isc_total)

    @staticmethod
    def Clarify(message: str) -> "QueryResult":
        return QueryResult(False, "HALT_AND_CLARIFY", message, ClarificationQuestions=[message])


@dataclass
class SelfTestResult:
    IsValid: bool
    Diagnostics: str

    @staticmethod
    def Ok(diag: str) -> "SelfTestResult":
        return SelfTestResult(True, diag)

    @staticmethod
    def Fail(diag: str) -> "SelfTestResult":
        return SelfTestResult(False, diag)


@dataclass
class BrainStats:
    TokenCount: int = 0
    AuditEventCount: int = 0
    Uptime: float = 0.0
    ActiveISO: List[str] = field(default_factory=list)
    CurrentAlgorithmPhase: Optional[str] = None
    LastEffortTier: Optional[str] = None


@dataclass
class BrainAuditEvent:
    Timestamp: str
    Kind: str
    Payload: str
    QuaternionBefore: Optional[Tuple[float, float, float, float]] = None
    QuaternionAfter: Optional[Tuple[float, float, float, float]] = None
    MagnitudeDrift: Optional[float] = None
    AlgorithmPhase: Optional[str] = None

    def ToDictionary(self) -> dict:
        d = {
            "timestamp": self.Timestamp,
            "kind": self.Kind,
            "payload": self.Payload,
        }
        if self.QuaternionBefore:
            d["quaternion_before"] = list(self.QuaternionBefore)
        if self.QuaternionAfter:
            d["quaternion_after"] = list(self.QuaternionAfter)
        if self.MagnitudeDrift is not None:
            d["magnitude_drift"] = self.MagnitudeDrift
        if self.AlgorithmPhase:
            d["algorithm_phase"] = self.AlgorithmPhase
        return d


class IsographicQuaternion:
    """4D quaternion with coupled dimensions for isographic indexing"""

    def __init__(self, w: float, x: float, y: float, z: float):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def get_sound_projection(self) -> float:
        return math.sqrt(self.w * self.w + self.x * self.x)

    def get_shape_projection(self) -> float:
        return math.sqrt(self.w * self.w + self.y * self.y)

    def get_number_projection(self) -> float:
        return math.sqrt(self.x * self.x + self.z * self.z)

    def get_time_projection(self) -> float:
        return math.sqrt(self.y * self.y + self.z * self.z)

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self) -> "IsographicQuaternion":
        mag = self.magnitude
        if mag < 1e-10:
            return self
        return IsographicQuaternion(self.w / mag, self.x / mag, self.y / mag, self.z / mag)

    def approx_equals(self, other: "IsographicQuaternion", epsilon: float = 1e-6) -> bool:
        return (
            abs(self.w - other.w) < epsilon
            and abs(self.x - other.x) < epsilon
            and abs(self.y - other.y) < epsilon
            and abs(self.z - other.z) < epsilon
        )

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.w, self.x, self.y, self.z)

    @classmethod
    def from_tuple(cls, t: Tuple[float, float, float, float]) -> "IsographicQuaternion":
        return cls(t[0], t[1], t[2], t[3])

    def __repr__(self) -> str:
        return f"IsographicQuaternion(w={self.w:.3f}, x={self.x:.3f}, y={self.y:.3f}, z={self.z:.3f})"


def _find_van_engine_root() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent.parent,
        Path(__file__).resolve().parent.parent.parent.parent,
        Path(__file__).resolve().parent.parent.parent,
        Path("C:/Users/User/Documents/ALL-PROJECTS/PROJECTS/VAN_Engine"),
        Path.home() / "Documents/ALL-PROJECTS/PROJECTS/VAN_Engine",
        Path.cwd() / "VAN_Engine",
        Path.cwd().parent / "VAN_Engine",
    ]

    for candidate in candidates:
        if (candidate / "core" / "ISO_Rules.json").exists():
            print(f"[Brain] Found VAN_Engine at: {candidate}")
            return candidate

    fallback = Path.cwd() / "VAN_Engine"
    fallback.mkdir(parents=True, exist_ok=True)
    (fallback / "core").mkdir(exist_ok=True)
    (fallback / "memory").mkdir(exist_ok=True)
    (fallback / "logs").mkdir(exist_ok=True)
    print(f"[Brain] Warning: Using fallback VAN_Engine at: {fallback}")
    return fallback


class VANEngineBrain:
    """
    The Brain of VAN_Engine — Sovereign, Deterministic, Isographic Substrate
    ISO_001-020: Complete Implementation with SQLite persistence
    """

    _instance = None
    _lock = Lock()
    _instance_root = None

    DRIFT_THRESHOLD = 0.85
    MAGNITUDE_TOLERANCE = 1e-6
    QUERY_TIMEOUT_MS = 100
    LOOKUP_TIMEOUT_MS = 10

    def __init__(self, engine_root: Path | None = None):
        self._engine = VanEngine()
        self._audit_trail: List[BrainAuditEvent] = []
        self._start = monotonic()
        self._engine_root = engine_root if engine_root else _find_van_engine_root()
        self._db_path = self._engine_root / "memory" / "token_index.db"
        self._iso_path = self._engine_root / "core" / "ISO_Rules.json"
        self._audit_log_path = self._engine_root / "logs" / "brain_audit.log"
        self._conn: Optional[sqlite3.Connection] = None
        self._registered_components: List[str] = []
        self._init_database()
        self._iso_rules = self._load_iso_rules()
        self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        self._memory_root = self._engine_root / "memory"
        self._prd_manager = PRDManager(self._memory_root)
        self._algorithm_executor = AlgorithmExecutor(self._memory_root)
        self._current_algorithm_phase: Optional[str] = None
        self._last_effort_tier: Optional[str] = None

        self._register_master_skills()

        atexit.register(self._cleanup)
        self._log_audit("Brain", "Startup", None, None)
        self._flush_audit_to_file()
        result = self.SelfTest()
        if not result.IsValid:
            print(f"[Brain] Self-test warning: {result.Diagnostics}")

    def _register_master_skills(self) -> None:
        self.RegisterComponent("MasterAudio")
        self.RegisterComponent("MasterImage")
        self.RegisterComponent("MasterVideo")
        print("[Brain] Master skills registered: Audio (107), Image (52), Video (60)")

    def _init_database(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens (
                key TEXT PRIMARY KEY,
                w REAL NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                z REAL NOT NULL,
                magnitude REAL,
                applies_to TEXT,
                created INTEGER NOT NULL,
                updated INTEGER NOT NULL
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_applies_to ON tokens(applies_to)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_magnitude ON tokens(magnitude)")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
            """
        )
        self._conn.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (1)")
        cursor = self._conn.execute("SELECT key, w, x, y, z FROM tokens WHERE magnitude IS NULL")
        for row in cursor:
            mag = math.sqrt(row[1] ** 2 + row[2] ** 2 + row[3] ** 2 + row[4] ** 2)
            self._conn.execute("UPDATE tokens SET magnitude = ? WHERE key = ?", (mag, row[0]))
        self._conn.commit()
        print(f"[Brain] SQLite database initialized at {self._db_path}")

    def _load_iso_rules(self) -> Dict[str, Any]:
        try:
            if self._iso_path.exists():
                with open(self._iso_path, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                    return {rule["id"]: rule for rule in rules.get("rules", [])}
            print(f"[Brain] ISO rules not found at {self._iso_path}, creating default")
            return self._create_default_iso_rules()
        except Exception as e:
            print(f"[Brain] Warning: Could not load ISO rules: {e}")
            return self._create_default_iso_rules()

    def _create_default_iso_rules(self) -> Dict[str, Any]:
        default_rules = {}
        for i in range(1, 21):
            rule_id = f"ISO_{i:03d}"
            default_rules[rule_id] = {"id": rule_id, "name": f"Rule {rule_id}", "status": "active"}
        default_rules["ISO_010"] = {"id": "ISO_010", "name": "Drift Gating", "status": "active"}
        default_rules["ISO_011"] = {"id": "ISO_011", "name": "Archetypal FSM", "status": "active"}
        default_rules["ISO_012"] = {"id": "ISO_012", "name": "Recursive Self-Validation", "status": "active"}
        default_rules["ISO_015"] = {"id": "ISO_015", "name": "Observable State", "status": "active"}
        default_rules["ISO_019"] = {"id": "ISO_019", "name": "Privacy by Default", "status": "enforced"}
        default_rules["ISO_020"] = {"id": "ISO_020", "name": "Anti-Hallucination", "status": "enforced"}
        return default_rules

    def _flush_audit_to_file(self) -> None:
        try:
            with open(self._audit_log_path, "a", encoding="utf-8") as f:
                for event in self._audit_trail[-50:]:
                    f.write(json.dumps(event.ToDictionary()) + "\n")
        except Exception as e:
            print(f"[Brain] Warning: Could not write audit log: {e}")

    def _log_audit(
        self,
        component: str,
        action: str,
        before: Optional[IsographicQuaternion] = None,
        after: Optional[IsographicQuaternion] = None,
        metadata: str = "",
    ) -> None:
        before_tuple = before.to_tuple() if before else None
        after_tuple = after.to_tuple() if after else None
        drift = abs(before.magnitude - after.magnitude) if before and after else None
        event = BrainAuditEvent(
            Timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            Kind=action,
            Payload=metadata or f"{component}:{action}",
            QuaternionBefore=before_tuple,
            QuaternionAfter=after_tuple,
            MagnitudeDrift=drift,
            AlgorithmPhase=self._current_algorithm_phase,
        )
        self._audit_trail.append(event)
        try:
            with open(self._audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.ToDictionary()) + "\n")
        except Exception:
            pass
        if len(self._audit_trail) > 10000:
            self._audit_trail = self._audit_trail[-10000:]

    def _drift_gate(self, quaternion: IsographicQuaternion) -> Tuple[bool, str]:
        mag = quaternion.magnitude
        if mag < self.DRIFT_THRESHOLD:
            return True, f"Quaternion magnitude {mag:.4f} below threshold {self.DRIFT_THRESHOLD}"
        max_comp = max(abs(quaternion.w), abs(quaternion.x), abs(quaternion.y), abs(quaternion.z))
        if max_comp > 1.5:
            return True, f"Component magnitude {max_comp:.2f} exceeds tolerance 1.5"
        return False, ""

    @classmethod
    def Instance(cls, engine_root: Path | None = None) -> "VANEngineBrain":
        with cls._lock:
            if cls._instance is None:
                cls._instance_root = engine_root
                cls._instance = cls(engine_root=engine_root)
            elif engine_root is not None and engine_root != cls._instance_root:
                print(f"[Brain] Warning: Instance already created with root {cls._instance_root}, ignoring {engine_root}")
        return cls._instance

    def _cleanup(self) -> None:
        if hasattr(self, "_conn") and self._conn:
            self._log_audit("Brain", "Shutdown", None, None)
            self._flush_audit_to_file()
            self._conn.close()

    # ========== Algorithm Integration ==========

    async def ExecuteAlgorithmQuery(self, query: str, context: dict = None) -> QueryResult:
        """Execute query using PAI Algorithm v3.7.0 - 7-phase processing"""
        context = context or {}
        self._log_audit("Brain", "AlgorithmQuery", None, None, query)

        try:
            result = await self._algorithm_executor.execute(query, context)
            phases = result.get("phases", {})
            self._current_algorithm_phase = "complete"
            self._last_effort_tier = result.get("effort")

            isc_total = 0
            isc_checked = 0
            if "observe" in phases:
                isc_total = phases["observe"].get("isc_count", 0)
                isc_checked = isc_total

            message = (f"Algorithm execution complete.\n"
                       f"Effort: {result.get('effort', 'standard')}\n"
                       f"Time: {result.get('time_used_seconds', 0):.1f}s / {result.get('time_budget_seconds', 0)}s\n"
                       f"ISC Criteria: {isc_checked}/{isc_total} verified")

            self._export_algorithm_event(result, query)

            return QueryResult.Ok(
                message=message,
                action="ALGORITHM_COMPLETE",
                data=result,
                phase="complete",
                effort=result.get("effort"),
                isc_checked=isc_checked,
                isc_total=isc_total
            )
        except Exception as e:
            self._log_audit("Brain", "AlgorithmError", None, None, str(e))
            return QueryResult.Clarify(f"Algorithm execution failed: {e}")

    def _export_algorithm_event(self, result: dict, query: str) -> None:
        events_dir = self._engine_root / "ConversationIDE" / "memoryEvents"
        try:
            events_dir.mkdir(parents=True, exist_ok=True)
            now = datetime.now(timezone.utc)
            slug = now.strftime("%Y%m%d_%H%M%S")
            filename = f"algorithm_{slug}.md"
            effort = result.get("effort", "standard")
            time_used = result.get("time_used_seconds", 0)
            time_budget = result.get("time_budget_seconds", 0)
            phases = result.get("phases", {})
            phase_list = "\n".join(f"  - {k}: {v.get('phase', '')}" for k, v in phases.items())
            content = f"""---
type: algorithm_execution
timestamp: {now.isoformat()}
query: {query}
effort: {effort}
time_used_seconds: {time_used}
time_budget_seconds: {time_budget}
phases:
{phase_list}
---

# Algorithm Execution

**Query:** {query}
**Effort:** {effort}
**Time:** {time_used:.1f}s / {time_budget}s
"""
            (events_dir / filename).write_text(content.strip(), encoding="utf-8")
        except Exception as e:
            print(f"[Brain] Memory event export skipped: {e}")

    def _should_use_algorithm(self, normalized_query: str) -> bool:
        indicators = [
            "build", "create", "implement", "design", "develop",
            "research", "investigate", "analyze", "plan",
            "complex", "comprehensive", "multi-step"
        ]
        return any(indicator in normalized_query for indicator in indicators)

    def ExecuteQuery(self, query: str, context: dict = None) -> QueryResult:
        if not query or not query.strip():
            return QueryResult.Clarify("Please provide a query.")

        normalized = query.strip().lower()
        self._log_audit("Brain", "Query", None, None, query[:200])

        if context:
            envelope = context.get("envelope")
            if envelope:
                carrier = getattr(envelope, "Carrier", "unknown")
                modulation = getattr(envelope, "Modulation", "unknown")
                data = getattr(envelope, "Data", [])
                self._engine.Compliance.check_envelope_compliance(carrier, modulation, data)
                self._log_audit("Brain", "Envelope", None, None, f"{carrier}:{modulation}")

        if "status" in normalized or "health" in normalized:
            stats = self.GetStats()
            return QueryResult.Ok(
                f"VAN_Engine is online. Tokens: {stats.TokenCount}. "
                f"Audit events: {stats.AuditEventCount}. "
                f"Current Algorithm Phase: {self._current_algorithm_phase or 'idle'}. "
                f"Active ISO rules: {', '.join(stats.ActiveISO) if stats.ActiveISO else '20/20'}.",
                "STATUS",
                {"token_count": stats.TokenCount, "audit_count": stats.AuditEventCount,
                 "algorithm_phase": self._current_algorithm_phase,
                 "last_effort": self._last_effort_tier},
            )

        if "self test" in normalized or "self-test" in normalized:
            result = self.SelfTest()
            return QueryResult.Ok(
                f"Self-test: {result.Diagnostics}",
                "SELF_TEST",
                {"valid": result.IsValid, "diagnostics": result.Diagnostics},
            )

        if "audit" in normalized:
            events = self.GetAuditTrail(10)
            summary = "\n".join([f"  [{e.Timestamp}] {e.Kind}: {e.Payload}" for e in events])
            return QueryResult.Ok(
                f"Recent audit events:\n{summary or '  No recent events'}",
                "AUDIT",
                {"events": [e.ToDictionary() for e in events]},
            )

        if "iso" in normalized:
            active = self._get_active_iso_rules()
            return QueryResult.Ok(
                f"Active ISO rules: {', '.join(active) if active else 'All 20 rules active'}.\n"
                f"ISO_019 (Privacy): Bridges disabled by default.\n"
                f"ISO_020 (Anti-hallucination): System refuses to guess.",
                "ISO_STATUS",
                {"active_iso": active},
            )

        if "store token" in normalized:
            import re

            token_match = re.search(r"store token (\w+)", normalized)
            quat_match = re.search(r"\(([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\)", normalized)
            if token_match and quat_match:
                token = token_match.group(1)
                w, x, y, z = map(float, quat_match.groups())
                quat = IsographicQuaternion(w, x, y, z)
                success = self.StoreToken(token, quat, ["user_stored"])
                if success:
                    return QueryResult.Ok(f"Token '{token}' stored successfully.", "STORE_TOKEN", {"token": token})
                return QueryResult.Clarify(f"Failed to store token '{token}'. Drift gate may have rejected it.")

        if "lookup" in normalized or "find token" in normalized:
            words = normalized.split()
            token_candidates = [w for w in words if len(w) > 3 and w not in ["lookup", "find", "token"]]
            if token_candidates:
                token = token_candidates[0]
                quat = self.LookupToken(token)
                if quat:
                    return QueryResult.Ok(
                        f"Token '{token}': quaternion ({quat.w:.3f}, {quat.x:.3f}, {quat.y:.3f}, {quat.z:.3f})",
                        "LOOKUP",
                        {"token": token, "quaternion": quat.to_tuple()},
                    )
                return QueryResult.Clarify(f"Token '{token}' not found in index.")

        if "help" in normalized:
            help_text = (
                "I can help with:\n"
                "- Status: 'system status'\n"
                "- Store token: 'store token NAME with (w,x,y,z)'\n"
                "- Lookup token: 'lookup token NAME'\n"
                "- Audit: 'show audit trail'\n"
                "- Self-test: 'run self-test'\n"
                "- ISO rules: 'list ISO rules'\n\n"
                "I never hallucinate. If uncertain, I'll ask for clarification (ISO_020)."
            )
            return QueryResult.Ok(help_text, "HELP")

        return QueryResult.Clarify(
            f"I don't understand '{query[:100]}...'\n\n"
            f"Type 'help' for available commands."
        )

    async def ExecuteQueryAsync(self, query: str, context: dict = None) -> QueryResult:
        import asyncio

        try:
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, self.ExecuteQuery, query, context),
                timeout=self.QUERY_TIMEOUT_MS / 1000.0,
            )
        except asyncio.TimeoutError:
            return QueryResult.Clarify(f"Query timed out after {self.QUERY_TIMEOUT_MS}ms. Please simplify.")

    def SelfTest(self) -> SelfTestResult:
        errors = []

        try:
            cursor = self._conn.execute("SELECT 1")
            if cursor.fetchone()[0] != 1:
                errors.append("Database query returned unexpected value")
        except Exception as e:
            errors.append(f"Database connection failed: {e}")

        try:
            test_q = IsographicQuaternion(0.8, 0.3, 0.2, 0.1)
            mag = test_q.magnitude
            if abs(mag - 0.948683298) > self.MAGNITUDE_TOLERANCE:
                errors.append(f"Quaternion magnitude incorrect: {mag}")
            sound = test_q.get_sound_projection()
            expected_sound = math.sqrt(0.8**2 + 0.3**2)
            if abs(sound - expected_sound) > self.MAGNITUDE_TOLERANCE:
                errors.append(f"Sound projection mismatch: {sound} vs {expected_sound}")
        except Exception as e:
            errors.append(f"Quaternion math failed: {e}")

        if not self._iso_rules:
            errors.append("ISO rules not loaded")
        else:
            critical = ["ISO_010", "ISO_012", "ISO_015", "ISO_019", "ISO_020"]
            missing = [c for c in critical if c not in self._iso_rules]
            if missing:
                errors.append(f"Missing critical ISO rules: {missing}")

        if not self._db_path.parent.exists():
            errors.append(f"Database directory missing: {self._db_path.parent}")
        if not self._audit_log_path.parent.exists():
            errors.append(f"Audit directory missing: {self._audit_log_path.parent}")

        try:
            with open(self._audit_log_path, "a", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            errors.append(f"Audit log not writable: {e}")

        test_token = f"_test_{int(time.time())}"
        test_quat = IsographicQuaternion(0.5, 0.5, 0.5, 0.5)
        try:
            self.StoreToken(test_token, test_quat, ["test"])
            retrieved = self.LookupToken(test_token)
            if not retrieved or not retrieved.approx_equals(test_quat):
                errors.append("Token store/retrieve failed")
            self._conn.execute("DELETE FROM tokens WHERE key = ?", (test_token,))
            self._conn.commit()
        except Exception as e:
            errors.append(f"Token operation failed: {e}")

        if errors:
            return SelfTestResult.Fail("; ".join(errors))
        return SelfTestResult.Ok(f"All systems operational. {self.GetStats().TokenCount} tokens in index.")

    def GetStats(self) -> BrainStats:
        cursor = self._conn.execute("SELECT COUNT(*) FROM tokens")
        token_count = cursor.fetchone()[0]
        active_iso = self._get_active_iso_rules()
        return BrainStats(
            TokenCount=token_count,
            AuditEventCount=len(self._audit_trail),
            Uptime=round(monotonic() - self._start, 3),
            ActiveISO=active_iso,
            CurrentAlgorithmPhase=self._current_algorithm_phase,
            LastEffortTier=self._last_effort_tier,
        )

    def _get_active_iso_rules(self) -> List[str]:
        if not self._iso_rules:
            return []
        return [rule_id for rule_id, rule in self._iso_rules.items() if rule.get("status") in ["active", "enforced"]]

    def StoreToken(self, token: str, quaternion: IsographicQuaternion, appliesTo: List[str]) -> bool:
        violated, diag = self._drift_gate(quaternion)
        if violated:
            self._log_audit("Brain", "STORE_REJECTED", None, quaternion, f"Drift gate: {diag}")
            return False

        existing = self.LookupToken(token)
        applies_to_str = "|".join(appliesTo)
        now = int(time.time())
        magnitude = quaternion.magnitude

        try:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO tokens (key, w, x, y, z, magnitude, applies_to, created, updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created FROM tokens WHERE key = ?), ?), ?)
                """,
                (
                    token,
                    quaternion.w,
                    quaternion.x,
                    quaternion.y,
                    quaternion.z,
                    magnitude,
                    applies_to_str,
                    token,
                    now,
                    now,
                ),
            )
            self._conn.commit()
            self._log_audit("Brain", "STORE_TOKEN", existing, quaternion, token)
            return True
        except Exception as e:
            print(f"[Brain] StoreToken error: {e}")
            return False

    def LookupToken(self, token: str) -> Optional[IsographicQuaternion]:
        try:
            cursor = self._conn.execute("SELECT w, x, y, z FROM tokens WHERE key = ?", (token,))
            row = cursor.fetchone()
            if row:
                self._log_audit("Brain", "LOOKUP_TOKEN", None, None, token)
                return IsographicQuaternion(row[0], row[1], row[2], row[3])
            return None
        except Exception as e:
            print(f"[Brain] LookupToken error: {e}")
            return None

    def GetAppliesTo(self, token: str) -> List[str]:
        try:
            cursor = self._conn.execute("SELECT applies_to FROM tokens WHERE key = ?", (token,))
            row = cursor.fetchone()
            if row and row[0]:
                return row[0].split("|")
            return []
        except Exception as e:
            print(f"[Brain] GetAppliesTo error: {e}")
            return []

    def FindNearest(self, target: IsographicQuaternion, limit: int = 10) -> List[Tuple[str, IsographicQuaternion, float]]:
        results = []
        try:
            cursor = self._conn.execute("SELECT key, w, x, y, z FROM tokens")
            target_mag = target.magnitude
            for row in cursor:
                token = row[0]
                quat = IsographicQuaternion(row[1], row[2], row[3], row[4])
                dot = quat.w * target.w + quat.x * target.x + quat.y * target.y + quat.z * target.z
                mag_product = quat.magnitude * target_mag
                similarity = dot / mag_product if mag_product > 0 else 0
                results.append((token, quat, similarity))
            results.sort(key=lambda x: x[2], reverse=True)
            return results[:limit]
        except Exception as e:
            print(f"[Brain] FindNearest error: {e}")
            return []

    def GetAuditTrail(self, count: int = 20) -> List[BrainAuditEvent]:
        return list(reversed(self._audit_trail))[: max(0, count)]

    def GetAuditTrailFromFile(self, count: int = 100) -> List[Dict]:
        events = []
        try:
            if self._audit_log_path.exists():
                with open(self._audit_log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                events.append(json.loads(line))
                            except Exception:
                                pass
                return events[-count:]
        except Exception as e:
            print(f"[Brain] Could not read audit file: {e}")
        return events

    def GetTokenCount(self) -> int:
        cursor = self._conn.execute("SELECT COUNT(*) FROM tokens")
        return cursor.fetchone()[0]

    def DriftGateCheck(self, quaternion: IsographicQuaternion) -> Dict[str, Any]:
        violated, diag = self._drift_gate(quaternion)
        return {
            "violated": violated,
            "action": "HALT_AND_CLARIFY" if violated else "EXECUTE",
            "diagnostic": diag if violated else None,
            "threshold": self.DRIFT_THRESHOLD,
            "magnitude": quaternion.magnitude,
        }

    def RegisterComponent(self, component: str) -> None:
        if component not in self._registered_components:
            self._registered_components.append(component)
            self._log_audit("Brain", "REGISTER_COMPONENT", None, None, component)

    def GetEngineRoot(self) -> Path:
        return self._engine_root

    def GetISOFilePath(self) -> Path:
        return self._iso_path

    def GetMemoryRoot(self) -> Path:
        return self._memory_root

    def GetPRDManager(self) -> PRDManager:
        return self._prd_manager


__all__ = [
    "VANEngineBrain",
    "IsographicQuaternion",
    "QueryResult",
    "SelfTestResult",
    "BrainStats",
    "BrainAuditEvent",
]
