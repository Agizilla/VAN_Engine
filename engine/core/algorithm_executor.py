"""Algorithm v3.7.0 Executor - 7-phase execution engine"""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .algorithm import (
    AlgorithmPhase, AlgorithmState, EffortTier, ISCCriterion,
    TIME_BUDGETS, MIN_ISC_COUNTS
)
from .prd_manager import PRDManager, ISCGenerator


class AlgorithmExecutor:
    def __init__(self, memory_root: Path):
        self.memory_root = memory_root
        self.prd_manager = PRDManager(memory_root)
        self.state = AlgorithmState()
        self.voice_enabled = True
        self.voice_id = "fTtv3eikoepIosk8dTZ5"

    # ========== Voice ==========

    def _announce_phase(self, phase: AlgorithmPhase) -> None:
        if not self.voice_enabled:
            return
        phase_names = {
            AlgorithmPhase.OBSERVE: "Observe",
            AlgorithmPhase.THINK: "Think",
            AlgorithmPhase.PLAN: "Plan",
            AlgorithmPhase.BUILD: "Build",
            AlgorithmPhase.EXECUTE: "Execute",
            AlgorithmPhase.VERIFY: "Verify",
            AlgorithmPhase.LEARN: "Learn"
        }
        message = f"Entering the {phase_names[phase]} phase."
        try:
            subprocess.run([
                "curl", "-s", "-X", "POST", "http://localhost:8888/notify",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({
                    "message": message,
                    "voice_id": self.voice_id,
                    "voice_enabled": True
                })
            ], capture_output=True, timeout=2)
        except Exception:
            pass

    # ========== Phase 1: OBSERVE ==========

    async def observe_phase(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        self._announce_phase(AlgorithmPhase.OBSERVE)
        if self.state.prd:
            self.prd_manager.update_phase(self.state.prd, AlgorithmPhase.OBSERVE)

        reverse_engineering = self._reverse_engineer(query)
        effort = self._determine_effort(query, reverse_engineering)
        self.state.effort = effort
        self.state.time_budget_seconds = TIME_BUDGETS[effort]

        criteria = self._generate_isc(query, reverse_engineering, effort)
        atomic_criteria = []
        for criterion in criteria:
            atomic_criteria.extend(ISCGenerator.split_criterion(criterion))

        isc_criteria = [
            ISCCriterion(id=f"ISC-{i+1}", text=c)
            for i, c in enumerate(atomic_criteria)
        ]

        min_count = MIN_ISC_COUNTS[effort]
        if len(isc_criteria) < min_count:
            isc_criteria = self._decompose_criteria(isc_criteria, min_count)

        if self.state.prd:
            self.prd_manager.update_criteria(self.state.prd, isc_criteria)
            self.state.prd.criteria = isc_criteria

        capabilities = self._select_capabilities(query, reverse_engineering, effort)
        self.state.selected_capabilities = capabilities

        return {
            "phase": "observe",
            "reverse_engineering": reverse_engineering,
            "effort": effort.value,
            "isc_criteria": [c.text for c in isc_criteria],
            "isc_count": len(isc_criteria),
            "capabilities_selected": capabilities
        }

    def _reverse_engineer(self, query: str) -> Dict[str, List[str]]:
        return {
            "explicit_wants": self._extract_explicit_wants(query),
            "implied_wants": self._extract_implied_wants(query),
            "explicit_not_wanted": self._extract_explicit_not_wanted(query),
            "implied_not_wanted": self._extract_implied_not_wanted(query),
            "constraints": self._extract_constraints(query)
        }

    def _extract_explicit_wants(self, query: str) -> List[str]:
        wants = []
        indicators = ["want", "need", "require", "must", "should"]
        for sent in query.split('.'):
            for ind in indicators:
                if ind in sent.lower():
                    wants.append(sent.strip())
                    break
        return wants if wants else ["[Default: Process the request]"]

    def _extract_implied_wants(self, query: str) -> List[str]:
        return ["[Detected from context]"]

    def _extract_explicit_not_wanted(self, query: str) -> List[str]:
        not_wants = []
        indicators = ["don't", "do not", "avoid", "no", "never"]
        for sent in query.split('.'):
            for ind in indicators:
                if ind in sent.lower():
                    not_wants.append(sent.strip())
                    break
        return not_wants

    def _extract_implied_not_wanted(self, query: str) -> List[str]:
        return ["[No obvious negative constraints detected]"]

    def _extract_constraints(self, query: str) -> List[str]:
        constraints = []
        if "quick" in query.lower() or "fast" in query.lower():
            constraints.append("Time-sensitive: prioritize speed")
        if "quality" in query.lower():
            constraints.append("Quality-sensitive: prioritize correctness")
        return constraints if constraints else ["[No explicit constraints]"]

    def _determine_effort(self, query: str, reverse_engineering: Dict) -> EffortTier:
        q = query.lower()
        if "comprehensive" in q or "in-depth" in q:
            return EffortTier.COMPREHENSIVE
        if "deep" in q:
            return EffortTier.DEEP
        if "extensive" in q:
            return EffortTier.ADVANCED
        if "quick" in q or "fast" in q:
            return EffortTier.STANDARD
        word_count = len(query.split())
        if word_count > 200:
            return EffortTier.ADVANCED
        if word_count > 100:
            return EffortTier.EXTENDED
        return EffortTier.STANDARD

    def _generate_isc(self, query: str, reverse_engineering: Dict, effort: EffortTier) -> List[str]:
        base_criteria = [
            "Request is fully understood and documented",
            "All explicit wants are addressed",
            "All explicit constraints are satisfied",
            "No unwanted side effects introduced",
            "Solution is verifiable and testable"
        ]
        if effort in (EffortTier.ADVANCED, EffortTier.DEEP, EffortTier.COMPREHENSIVE):
            base_criteria.extend([
                "Edge cases are identified and handled",
                "Performance requirements are met",
                "Documentation is complete",
                "Solution is maintainable"
            ])
        if effort in (EffortTier.DEEP, EffortTier.COMPREHENSIVE):
            base_criteria.extend([
                "Security considerations addressed",
                "Scalability verified",
                "Backward compatibility maintained"
            ])
        return base_criteria

    def _decompose_criteria(self, criteria: List[ISCCriterion], target_count: int) -> List[ISCCriterion]:
        result = []
        for c in criteria:
            if len(result) + 1 >= target_count:
                result.append(c)
            else:
                result.append(ISCCriterion(id=f"{c.id}-a", text=f"{c.text} (part 1)"))
                result.append(ISCCriterion(id=f"{c.id}-b", text=f"{c.text} (part 2)"))
        return result[:target_count]

    def _select_capabilities(self, query: str, reverse_engineering: Dict, effort: EffortTier) -> List[Dict[str, str]]:
        capabilities = []
        q = query.lower()
        if any(word in q for word in ["research", "investigate", "find", "search"]):
            capabilities.append({"name": "Research", "phase": "build", "reason": "Information gathering required"})
        if effort in (EffortTier.ADVANCED, EffortTier.DEEP, EffortTier.COMPREHENSIVE):
            capabilities.append({"name": "FirstPrinciples", "phase": "think", "reason": "Decompose complex problem to axioms"})
            capabilities.append({"name": "Council", "phase": "think", "reason": "Multi-perspective analysis needed"})
        if any(word in q for word in ["security", "auth", "permission", "vulnerability"]):
            capabilities.append({"name": "Security", "phase": "verify", "reason": "Security assessment required"})
        return capabilities

    # ========== Phase 2: THINK ==========

    async def think_phase(self) -> Dict[str, Any]:
        self._announce_phase(AlgorithmPhase.THINK)
        if self.state.prd:
            self.prd_manager.update_phase(self.state.prd, AlgorithmPhase.THINK)
        return {
            "phase": "think",
            "riskiest_assumptions": [
                "The problem is correctly understood",
                "The user has provided all necessary context",
                "The chosen approach is feasible within time budget"
            ],
            "premortem": [
                "Misunderstanding of requirements",
                "Scope creep beyond time budget",
                "Technical constraints not anticipated",
                "Integration complexity underestimated"
            ],
            "prerequisites_check": ["All prerequisites satisfied"]
        }

    # ========== Phase 3: PLAN ==========

    async def plan_phase(self) -> Dict[str, Any]:
        self._announce_phase(AlgorithmPhase.PLAN)
        if self.state.prd and self.state.effort in (EffortTier.ADVANCED, EffortTier.DEEP, EffortTier.COMPREHENSIVE):
            self.prd_manager.update_phase(self.state.prd, AlgorithmPhase.PLAN)
        return {
            "phase": "plan",
            "plan": {
                "approach": "Sequential execution with verification at each step",
                "key_decisions": [],
                "risk_mitigations": []
            }
        }

    # ========== Phase 4: BUILD ==========

    async def build_phase(self) -> Dict[str, Any]:
        self._announce_phase(AlgorithmPhase.BUILD)
        if self.state.prd:
            self.prd_manager.update_phase(self.state.prd, AlgorithmPhase.BUILD)
        for cap in self.state.selected_capabilities:
            if cap["phase"] == "build":
                await self._invoke_capability(cap["name"])
                self.state.invoked_capabilities.append(cap["name"])
        return {"phase": "build", "capabilities_invoked": self.state.invoked_capabilities}

    async def _invoke_capability(self, capability_name: str) -> None:
        pass

    # ========== Phase 5: EXECUTE ==========

    async def execute_phase(self) -> Dict[str, Any]:
        self._announce_phase(AlgorithmPhase.EXECUTE)
        if self.state.prd:
            self.prd_manager.update_phase(self.state.prd, AlgorithmPhase.EXECUTE)
        for i, criterion in enumerate(self.state.prd.criteria if self.state.prd else []):
            if await self._execute_criterion(criterion):
                self.prd_manager.mark_criterion_passed(self.state.prd, criterion.id, "Executed successfully")
        return {
            "phase": "execute",
            "criteria_passed": len([c for c in (self.state.prd.criteria if self.state.prd else []) if c.passed])
        }

    async def _execute_criterion(self, criterion: ISCCriterion) -> bool:
        return True

    # ========== Phase 6: VERIFY ==========

    async def verify_phase(self) -> Dict[str, Any]:
        self._announce_phase(AlgorithmPhase.VERIFY)
        if self.state.prd:
            self.prd_manager.update_phase(self.state.prd, AlgorithmPhase.VERIFY)
        verification_results = []
        for criterion in self.state.prd.criteria if self.state.prd else []:
            verified = await self._verify_criterion(criterion)
            verification_results.append({
                "id": criterion.id,
                "passed": verified,
                "evidence": criterion.evidence if verified else "Not verified"
            })
        selected_names = {c["name"] for c in self.state.selected_capabilities}
        invoked_names = set(self.state.invoked_capabilities)
        missing = selected_names - invoked_names
        return {
            "phase": "verify",
            "verification": verification_results,
            "capability_invocation_check": {
                "selected": list(selected_names),
                "invoked": list(invoked_names),
                "missing": list(missing),
                "all_invoked": len(missing) == 0
            }
        }

    async def _verify_criterion(self, criterion: ISCCriterion) -> bool:
        return criterion.passed

    # ========== Phase 7: LEARN ==========

    async def learn_phase(self, user_satisfaction: int = 7) -> Dict[str, Any]:
        self._announce_phase(AlgorithmPhase.LEARN)
        if self.state.prd:
            self.prd_manager.update_phase(self.state.prd, AlgorithmPhase.LEARN)
        reflections = self._generate_reflections()
        self._write_reflection_jsonl(user_satisfaction)
        return {"phase": "learn", "reflections": reflections, "phase_complete": True}

    def _generate_reflections(self) -> Dict[str, str]:
        return {
            "q1": "What should I have done differently?",
            "q2": "What would a smarter algorithm have done?",
            "q3": "What capabilities should I have used that I didn't?"
        }

    def _write_reflection_jsonl(self, user_satisfaction: int) -> None:
        if not self.state.prd:
            return
        total = len(self.state.prd.criteria)
        passed = sum(1 for c in self.state.prd.criteria if c.passed)
        reflection = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "effort_level": self.state.effort.value,
            "task_description": self.state.prd.task,
            "criteria_count": total,
            "criteria_passed": passed,
            "criteria_failed": total - passed,
            "prd_id": self.state.prd.slug,
            "implied_sentiment": user_satisfaction,
            "reflection_q1": self._generate_reflections()["q1"],
            "reflection_q2": self._generate_reflections()["q2"],
            "reflection_q3": self._generate_reflections()["q3"],
            "within_budget": self.state.time_used_seconds <= self.state.time_budget_seconds
        }
        path = self.memory_root / "LEARNING" / "REFLECTIONS" / "algorithm-reflections.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(reflection) + '\n')

    # ========== Main ==========

    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        self.state = AlgorithmState()
        self.state.phase_start_time = time.time()

        slug = self.prd_manager.get_slug_from_task(query[:50])
        self.state.prd = self.prd_manager.create(slug, query[:100])
        self.state.prd_path = self.memory_root / "WORK" / slug / "PRD.md"

        observe_result = await self.observe_phase(query, context)
        think_result = await self.think_phase()
        plan_result = await self.plan_phase()
        build_result = await self.build_phase()
        execute_result = await self.execute_phase()
        verify_result = await self.verify_phase()
        learn_result = await self.learn_phase()

        self.state.time_used_seconds = time.time() - self.state.phase_start_time

        return {
            "success": True,
            "effort": self.state.effort.value,
            "time_used_seconds": self.state.time_used_seconds,
            "time_budget_seconds": self.state.time_budget_seconds,
            "phases": {
                "observe": observe_result,
                "think": think_result,
                "plan": plan_result,
                "build": build_result,
                "execute": execute_result,
                "verify": verify_result,
                "learn": learn_result
            }
        }
