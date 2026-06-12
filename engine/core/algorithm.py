"""PAI Algorithm v3.7.0 - Core execution engine"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path


class AlgorithmPhase(Enum):
    OBSERVE = "observe"
    THINK = "think"
    PLAN = "plan"
    BUILD = "build"
    EXECUTE = "execute"
    VERIFY = "verify"
    LEARN = "learn"


class EffortTier(Enum):
    STANDARD = "standard"
    EXTENDED = "extended"
    ADVANCED = "advanced"
    DEEP = "deep"
    COMPREHENSIVE = "comprehensive"


@dataclass
class ISCCriterion:
    id: str
    text: str
    passed: bool = False
    evidence: Optional[str] = None

    def to_markdown(self) -> str:
        status = "[x]" if self.passed else "[ ]"
        return f"- {status} {self.id}: {self.text}"


@dataclass
class PRD:
    slug: str
    task: str
    effort: EffortTier = EffortTier.STANDARD
    phase: AlgorithmPhase = AlgorithmPhase.OBSERVE
    progress: str = "0/0"
    mode: str = "interactive"
    started: Optional[datetime] = None
    updated: Optional[datetime] = None
    iteration: Optional[int] = None
    context: str = ""
    criteria: List[ISCCriterion] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    verification: Dict[str, str] = field(default_factory=dict)

    def to_yaml_frontmatter(self) -> str:
        return f"""---
task: {self.task}
slug: {self.slug}
effort: {self.effort.value}
phase: {self.phase.value}
progress: {self.progress}
mode: {self.mode}
started: {self.started.isoformat() if self.started else ''}
updated: {self.updated.isoformat() if self.updated else ''}
{'iteration: ' + str(self.iteration) if self.iteration else ''}
---
"""

    def to_markdown(self) -> str:
        frontmatter = self.to_yaml_frontmatter()
        criteria_section = "\n".join([c.to_markdown() for c in self.criteria])
        decisions_section = "\n".join([f"- {d}" for d in self.decisions])
        verification_section = "\n".join([f"- {k}: {v}" for k, v in self.verification.items()])

        return f"""{frontmatter}
## Context

{self.context}

## Criteria

{criteria_section}

## Decisions

{decisions_section}

## Verification

{verification_section}
"""


@dataclass
class AlgorithmState:
    phase: AlgorithmPhase = AlgorithmPhase.OBSERVE
    effort: EffortTier = EffortTier.STANDARD
    time_budget_seconds: int = 120
    time_used_seconds: float = 0.0
    phase_start_time: Optional[float] = None
    prd: Optional[PRD] = None
    prd_path: Optional[Path] = None
    selected_capabilities: List[Dict[str, str]] = field(default_factory=list)
    invoked_capabilities: List[str] = field(default_factory=list)
    key_results: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)


TIME_BUDGETS = {
    EffortTier.STANDARD: 120,
    EffortTier.EXTENDED: 480,
    EffortTier.ADVANCED: 960,
    EffortTier.DEEP: 1920,
    EffortTier.COMPREHENSIVE: 7200
}

MIN_ISC_COUNTS = {
    EffortTier.STANDARD: 8,
    EffortTier.EXTENDED: 16,
    EffortTier.ADVANCED: 24,
    EffortTier.DEEP: 40,
    EffortTier.COMPREHENSIVE: 64
}
