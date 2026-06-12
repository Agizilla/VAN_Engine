"""PRD Manager - System of record for Algorithm state"""

import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict
import yaml

from .algorithm import PRD, ISCCriterion, AlgorithmPhase, EffortTier, MIN_ISC_COUNTS


class PRDManager:
    def __init__(self, memory_root: Path):
        self.work_dir = memory_root / "WORK"
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def create(self, slug: str, task: str, effort: EffortTier = EffortTier.STANDARD) -> PRD:
        now = datetime.now(timezone.utc)
        prd = PRD(
            slug=slug,
            task=task,
            effort=effort,
            started=now,
            updated=now
        )
        self._write(prd)
        return prd

    def load(self, slug: str) -> Optional[PRD]:
        prd_path = self.work_dir / slug / "PRD.md"
        if not prd_path.exists():
            return None
        content = prd_path.read_text(encoding='utf-8')
        return self._parse(content, prd_path)

    def _parse(self, content: str, prd_path: Path) -> PRD:
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        frontmatter = yaml.safe_load(frontmatter_match.group(1)) if frontmatter_match else {}
        body = content[frontmatter_match.end():] if frontmatter_match else content

        criteria = []
        criteria_pattern = r'- \[(x| )\] (ISC-\d+): (.*?)(?=\n- \[|$|\n##)'
        for match in re.finditer(criteria_pattern, body, re.DOTALL):
            passed = match.group(1) == 'x'
            criteria.append(ISCCriterion(
                id=match.group(2),
                text=match.group(3).strip(),
                passed=passed
            ))

        decisions = []
        decisions_section = re.search(r'## Decisions\n(.*?)(?=\n##|$)', body, re.DOTALL)
        if decisions_section:
            for line in decisions_section.group(1).split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    decisions.append(line[1:].strip())

        verification = {}
        verification_section = re.search(r'## Verification\n(.*?)(?=\n##|$)', body, re.DOTALL)
        if verification_section:
            for line in verification_section.group(1).split('\n'):
                if ': ' in line:
                    k, v = line.split(': ', 1)
                    verification[k.strip()] = v.strip()

        context = ""
        context_section = re.search(r'## Context\n(.*?)(?=\n##|$)', body, re.DOTALL)
        if context_section:
            context = context_section.group(1).strip()

        effort = EffortTier(frontmatter.get('effort', 'standard'))
        phase = AlgorithmPhase(frontmatter.get('phase', 'observe'))

        return PRD(
            slug=frontmatter.get('slug', ''),
            task=frontmatter.get('task', ''),
            effort=effort,
            phase=phase,
            progress=frontmatter.get('progress', '0/0'),
            mode=frontmatter.get('mode', 'interactive'),
            started=datetime.fromisoformat(frontmatter.get('started', '')) if frontmatter.get('started') else None,
            updated=datetime.fromisoformat(frontmatter.get('updated', '')) if frontmatter.get('updated') else None,
            iteration=frontmatter.get('iteration'),
            context=context,
            criteria=criteria,
            decisions=decisions,
            verification=verification
        )

    def _write(self, prd: PRD) -> None:
        prd_path = self.work_dir / prd.slug / "PRD.md"
        prd_path.parent.mkdir(parents=True, exist_ok=True)
        prd_path.write_text(prd.to_markdown(), encoding='utf-8')

    def update_criteria(self, prd: PRD, criteria: List[ISCCriterion]) -> None:
        prd.criteria = criteria
        total = len(criteria)
        passed = sum(1 for c in criteria if c.passed)
        prd.progress = f"{passed}/{total}"
        prd.updated = datetime.now(timezone.utc)
        self._write(prd)

    def mark_criterion_passed(self, prd: PRD, criterion_id: str, evidence: str) -> bool:
        for c in prd.criteria:
            if c.id == criterion_id:
                c.passed = True
                c.evidence = evidence
                prd.verification[criterion_id] = evidence
                break
        else:
            return False
        total = len(prd.criteria)
        passed = sum(1 for c in prd.criteria if c.passed)
        prd.progress = f"{passed}/{total}"
        prd.updated = datetime.now(timezone.utc)
        self._write(prd)
        return True

    def add_decision(self, prd: PRD, decision: str) -> None:
        prd.decisions.append(decision)
        prd.updated = datetime.now(timezone.utc)
        self._write(prd)

    def update_phase(self, prd: PRD, phase: AlgorithmPhase) -> None:
        prd.phase = phase
        prd.updated = datetime.now(timezone.utc)
        self._write(prd)

    def get_slug_from_task(self, task: str) -> str:
        now = datetime.now(timezone.utc)
        slug_base = re.sub(r'[^a-z0-9]+', '-', task.lower().strip())
        slug_base = slug_base.strip('-')[:50]
        return f"{now.strftime('%Y%m%d-%H%M%S')}_{slug_base}"

    def verify_isc_count(self, prd: PRD) -> bool:
        min_count = MIN_ISC_COUNTS[prd.effort]
        actual_count = len(prd.criteria)
        return actual_count >= min_count


DOMAIN_TEMPLATES = {
    "security": [
        "Authentication and authorization are enforced for all endpoints",
        "Input validation prevents injection attacks (SQL, XSS, command)",
        "Sensitive data is encrypted at rest and in transit",
        "Secrets and credentials are never hardcoded or committed",
        "Rate limiting and throttling protect against abuse",
        "Session management follows secure practices (rotation, expiry)",
        "CSRF protection is implemented for state-changing operations",
        "Dependencies are scanned for known vulnerabilities",
    ],
    "performance": [
        "Response times meet the defined SLA under expected load",
        "Database queries are indexed and optimized",
        "Asset bundling and caching minimize load times",
        "Lazy loading defers non-critical resources",
        "Memory usage stays within allocated budget",
        "CPU-intensive operations are offloaded or async",
        "Network requests are batched where possible",
        "Rendering performance meets 60fps target",
    ],
    "accessibility": [
        "All interactive elements are keyboard-navigable",
        "ARIA labels and roles are applied correctly",
        "Color contrast meets WCAG AA minimum ratios",
        "Screen reader announcements cover dynamic content",
        "Focus indicators are visible on all interactive elements",
        "Touch targets meet minimum size requirements",
        "Content is understandable without color alone",
        "Form inputs have associated labels and error announcements",
    ],
    "error_handling": [
        "All error states are handled with user-friendly messages",
        "Network failures trigger automatic retry with backoff",
        "Invalid input produces clear validation feedback",
        "Unhandled exceptions are caught by a global handler",
        "Error boundaries isolate component failures",
        "Graceful degradation works when dependencies are unavailable",
        "Timeout handling prevents hanging operations",
        "Fallback content displays when primary data fails to load",
    ],
    "logging": [
        "Structured logging captures key application events",
        "Log levels (DEBUG, INFO, WARN, ERROR) are used consistently",
        "Sensitive data is never written to logs",
        "Request tracing links logs across service boundaries",
        "Startup and shutdown sequences are logged",
        "Configuration changes are audit-logged",
        "Performance metrics are periodically logged",
        "Error logs include stack traces and contextual data",
    ],
    "testing": [
        "Unit tests cover core business logic",
        "Integration tests validate API contract compliance",
        "Edge cases and boundary conditions have dedicated tests",
        "Error paths are tested for expected failure behavior",
        "State transitions are validated with state-machine tests",
        "Regression tests run in CI for every commit",
        "Load tests verify performance under peak traffic",
        "Security tests cover OWASP Top 10 scenarios",
    ],
    "documentation": [
        "API endpoints are documented with request/response schemas",
        "Setup and installation steps are documented",
        "Configuration options are documented with defaults",
        "Architecture decisions are recorded (ADR format)",
        "Known limitations and caveats are documented",
        "Onboarding guide covers prerequisites and first steps",
        "Environment variables are documented with descriptions",
        "Changelog tracks version changes and migration notes",
    ],
    "cross_platform": [
        "Application renders correctly on all target browsers",
        "Responsive design adapts to mobile, tablet, and desktop",
        "OS-specific file paths use platform separators",
        "Font rendering accounts for system differences",
        "Scroll behavior is consistent across platforms",
        "Date, time, and number formats respect locale",
        "Keyboard shortcuts avoid platform-native conflicts",
        "Touch and mouse input both function correctly",
    ],
    "data_integrity": [
        "Database transactions enforce ACID guarantees",
        "Data migration scripts are reversible",
        "Referential integrity is enforced at the database level",
        "Duplicate records are prevented by unique constraints",
        "Data serialization preserves type fidelity",
        "Concurrent writes are protected by optimistic locking",
        "Schema migrations include rollback procedures",
        "Data validation occurs at both client and server",
    ],
    "state_management": [
        "Global state updates are predictable and traceable",
        "Local component state is cleaned up on unmount",
        "State persistence strategy handles serialization edge cases",
        "Cross-component state synchronization avoids stale data",
        "Undo/redo boundaries are clearly defined",
        "State migration handles version upgrades gracefully",
        "Derived state is computed, not duplicated",
        "Side effects are isolated from pure state updates",
    ],
}

class ISCGenerator:
    @staticmethod
    def split_criterion(criterion_text: str) -> List[str]:
        text = criterion_text.lower()
        if " and " in text or " with " in text:
            return ISCGenerator._split_on_conjunctions(criterion_text)
        scope_words = ["all", "every", "complete", "full"]
        if any(word in text for word in scope_words):
            return ISCGenerator._expand_scope(criterion_text)
        if ISCGenerator._crosses_domain_boundary(criterion_text):
            return ISCGenerator._split_by_domain(criterion_text)
        return [criterion_text]

    @staticmethod
    def _split_on_conjunctions(text: str) -> List[str]:
        import re
        parts = re.split(r'\s+(?:and|with)\s+', text)
        return [p.strip().capitalize() + '.' for p in parts]

    @staticmethod
    def _expand_scope(text: str) -> List[str]:
        return [text.replace("all", "each").replace("every", "each") + " item"]

    @staticmethod
    def _crosses_domain_boundary(text: str) -> bool:
        domains = list(DOMAIN_TEMPLATES.keys()) + ["ui", "api", "data", "logic", "visual", "content"]
        found = sum(1 for domain in domains if domain in text.lower())
        return found > 1

    @staticmethod
    def _split_by_domain(text: str) -> List[str]:
        return [text + " (UI part)", text + " (API part)"]

    @staticmethod
    def expand_criteria(task: str, effort: EffortTier, existing: List[ISCCriterion]) -> List[ISCCriterion]:
        min_count = MIN_ISC_COUNTS[effort]
        combined = list(existing)
        seen = {c.text.lower() for c in combined}

        task_lower = task.lower()
        matched_domains = [d for d in DOMAIN_TEMPLATES if d.replace("_", " ") in task_lower or d in task_lower]

        if effort in (EffortTier.DEEP, EffortTier.COMPREHENSIVE):
            matched_domains = list(DOMAIN_TEMPLATES.keys())
        elif not matched_domains:
            tier_domain_count = {
                EffortTier.STANDARD: 3,
                EffortTier.EXTENDED: 5,
                EffortTier.ADVANCED: 7,
            }
            count = tier_domain_count.get(effort, 3)
            matched_domains = list(DOMAIN_TEMPLATES.keys())[:count]

        for domain in matched_domains:
            if len(combined) >= min_count * 2:
                break
            for template in DOMAIN_TEMPLATES[domain]:
                if len(combined) >= min_count * 2:
                    break
                lower = template.lower()
                if lower not in seen:
                    combined.append(ISCCriterion(
                        id=f"ISC-{len(combined) + 1}",
                        text=template,
                    ))
                    seen.add(lower)

        if len(combined) < min_count and effort == EffortTier.COMPREHENSIVE:
            extra = [
                "System health endpoint reports live status with dependency checks",
                "Backup and recovery procedures are tested and documented",
                "Feature flags control rollout of new capabilities",
                "Migration path from previous version is defined",
                "Observability stack (metrics, traces, logs) is integrated",
                "CI/CD pipeline includes automated quality gates",
                "Canary or blue-green deployment strategy is defined",
                "SLA and SLO targets are documented with measurement approach",
                "Dependency injection enables testable component isolation",
                "Message queue ensures reliable async communication",
            ]
            for text in extra:
                if len(combined) >= min_count:
                    break
                lower = text.lower()
                if lower not in seen:
                    combined.append(ISCCriterion(
                        id=f"ISC-{len(combined) + 1}",
                        text=text,
                    ))
                    seen.add(lower)

        return combined[:min_count * 2]
