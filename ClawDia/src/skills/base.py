import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

SKILL_REGISTRY: dict[str, dict] = {}
_SKILL_MANIFEST_DIRS: list[str] = []
_registry_lock = threading.RLock()


def register_skill(name: str, category: str = "general"):
    def decorator(cls):
        with _registry_lock:
            SKILL_REGISTRY[name] = {"cls": cls, "name": name, "category": category}
        return cls
    return decorator


def get_registered_skills() -> dict:
    with _registry_lock:
        return dict(SKILL_REGISTRY)


# ── Bus / Context ──────────────────────────────────────────────────

@dataclass
class SkillContext:
    """Unified context object — replaces ARC LADE's 'bus' + carries state."""
    skill_id: str = ""
    conversation_id: str = ""
    memory: Optional[Any] = None
    rag: Optional[Any] = None
    _listeners: dict[str, list[Callable]] = field(default_factory=dict)
    _event_log: list[dict] = field(default_factory=list)
    _store: dict[str, Any] = field(default_factory=dict)

    def publish(self, event: str, data: dict):
        """ARC LADE bus-compatible: emit event to listeners."""
        entry = {"event": event, "data": data, "timestamp": datetime.now().isoformat()}
        self._event_log.append(entry)
        for listener in self._listeners.get(event, []):
            listener(entry)

    def on(self, event: str, callback: Callable):
        """Register listener for an event."""
        self._listeners.setdefault(event, []).append(callback)

    def fetch(self, key: str, default: Any = None) -> Any:
        """ARC LADE bus-compatible: read shared state."""
        return self._store.get(key, default)

    def store(self, key: str, value: Any):
        """ARC LADE bus-compatible: write shared state."""
        self._store[key] = value

    def event_log(self, since: Optional[str] = None) -> list[dict]:
        if since:
            return [e for e in self._event_log if e["timestamp"] >= since]
        return list(self._event_log)


# ── Manifest (Skills.md support) ───────────────────────────────────

@dataclass
class SkillManifest:
    name: str = ""
    description: str = ""
    author: str = "ClawDia"
    version: str = "1.0.0"
    category: str = "general"
    required_libs: list[str] = field(default_factory=list)
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)
    instructions: str = ""
    tags: list[str] = field(default_factory=list)
    grid_coords: Optional[dict] = None

    def __eq__(self, other):
        if not isinstance(other, SkillManifest):
            return NotImplemented
        return self.name == other.name and self.version == other.version

    def __hash__(self):
        return hash((self.name, self.version))

    def validate_dependencies(self) -> list[str]:
        missing = []
        for lib in self.required_libs:
            try:
                __import__(lib)
            except ImportError:
                missing.append(lib)
        return missing

    @classmethod
    def from_markdown(cls, text: str) -> "SkillManifest":
        import re
        m = cls()
        m.name = _extract_md_field(text, r"#+\s*Skill\s*:\s*(.+)")
        m.description = _extract_md_field(text, r"\*\*Description\*\*:\s*(.+)")
        m.author = _extract_md_field(text, r"\*\*Author\*\*:\s*(.+)") or "ClawDia"
        m.version = _extract_md_field(text, r"\*\*Version\*\*:\s*(.+)") or "1.0.0"
        m.category = _extract_md_field(text, r"\*\*Category\*\*:\s*(.+)") or "general"
        m.instructions = _extract_md_block(text, r"##\s*Instructions?\s*\n(.*?)(?=\n##|\Z)", re.DOTALL)
        libs_str = _extract_md_field(text, r"\*\*Required Libs?\*\*:\s*(.+)")
        if libs_str:
            m.required_libs = [x.strip() for x in libs_str.replace("[", "").replace("]", "").split(",") if x.strip()]
        m.tags = [x.strip() for x in _extract_md_field(text, r"\*\*Tags?\*\*:\s*(.+)", "").replace("[", "").replace("]", "").split(",") if x.strip()]
        return m

    @classmethod
    def from_yaml(cls, text: str) -> "SkillManifest":
        import yaml
        data = yaml.safe_load(text)
        m = cls()
        m.name = data.get("name", "")
        m.description = data.get("description", "")
        m.author = data.get("author", "ClawDia")
        m.version = str(data.get("version", "1.0.0"))
        m.category = data.get("category", "general")
        m.instructions = data.get("instructions", "")
        m.required_libs = data.get("required_libs", [])
        m.tags = data.get("tags", [])
        m.input_schema = data.get("input_schema", {})
        m.output_schema = data.get("output_schema", {})
        m.grid_coords = data.get("grid_coords")
        return m

    def to_markdown(self) -> str:
        lines = [
            f"# Skill: {self.name}",
            "",
            f"**Description**: {self.description}",
            f"**Author**: {self.author}",
            f"**Version**: {self.version}",
            f"**Category**: {self.category}",
            f"**Required Libs**: {self.required_libs}",
            f"**Tags**: {self.tags}",
            "",
        ]
        if self.input_schema:
            lines.append("## Input Schema")
            lines.append("```json")
            import json
            lines.append(json.dumps(self.input_schema, indent=2))
            lines.append("```")
            lines.append("")
        if self.output_schema:
            lines.append("## Output Schema")
            lines.append("```json")
            import json
            lines.append(json.dumps(self.output_schema, indent=2))
            lines.append("```")
            lines.append("")
        if self.grid_coords:
            lines.append("## Isographic Grid")
            lines.append(f"- Action: {self.grid_coords.get('x', '?')}")
            lines.append(f"- Domain: {self.grid_coords.get('y', '?')}")
            lines.append(f"- Constraint: {self.grid_coords.get('z', '?')}")
            lines.append("")
        if self.instructions:
            lines.append("## Instructions")
            lines.append(self.instructions)
            lines.append("")
        return "\n".join(lines)


def _extract_md_field(text: str, pattern: str, default: str = "") -> str:
    import re
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else default


def _extract_md_block(text: str, pattern: str, flags: int = 0) -> str:
    import re
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else ""


# ── Unified Base Skill ─────────────────────────────────────────────

class BaseSkill(ABC):
    """Unified skill base — merges ClawDia + ARC LADE + frontier manifest conventions."""

    # ClawDia fields
    name: str = ""
    description: str = ""
    category: str = "general"
    required_libs: list[str] = []

    # LadaSkill fields (ARC LADE compatibility)
    author: str = "ClawDia"
    version: str = "1.0.0"

    # Frontier manifest fields
    input_schema: dict = {}
    output_schema: dict = {}
    instructions: str = ""
    tags: list[str] = []

    # Isographic Grid (set by intent enricher)
    grid_coords: Optional[dict] = None

    def __init__(self):
        self._manifest: Optional[SkillManifest] = None
        self._context: Optional[SkillContext] = None

    # ── Primary interface (ClawDia compatible) ──────────────────

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """Main entry. Returns {"error": ..., "result": ...}."""
        ...

    # ── Secondary interface (ARC LADE compatible) ───────────────

    def run(self, context: Optional[SkillContext] = None, payload: Any = None) -> tuple:
        """ARC LADE LadaSkill.run(bus, payload) compatible.
        Default impl delegates to execute(). Skills override for bus access.
        Returns (bool, message_or_data).
        """
        self._context = context or SkillContext()
        kwargs = payload if isinstance(payload, dict) else {"payload": payload}
        result = self.execute(**kwargs)
        ok = result.get("error") is None
        return (ok, result.get("result", result) if ok else result["error"])

    # ── Context ─────────────────────────────────────────────────

    @property
    def context(self) -> SkillContext:
        if self._context is None:
            self._context = SkillContext()
        return self._context

    def publish(self, event: str, data: dict):
        self.context.publish(event, data)

    # ── Manifest ────────────────────────────────────────────────

    @property
    def manifest(self) -> SkillManifest:
        if self._manifest is None:
            self._manifest = self._build_manifest()
        return self._manifest

    def _build_manifest(self) -> SkillManifest:
        return SkillManifest(
            name=self.name,
            description=self.description,
            author=self.author,
            version=self.version,
            category=self.category,
            required_libs=list(self.required_libs),
            input_schema=dict(self.input_schema),
            output_schema=dict(self.output_schema),
            instructions=self.instructions or self.description,
            tags=list(self.tags),
            grid_coords=self.grid_coords,
        )

    def to_markdown(self) -> str:
        return self.manifest.to_markdown()

    @classmethod
    def from_markdown(cls, text: str) -> "BaseSkill":
        manifest = SkillManifest.from_markdown(text)
        skill = _GenericManifestSkill()
        skill.name = manifest.name
        skill.description = manifest.description
        skill.author = manifest.author
        skill.version = manifest.version
        skill.category = manifest.category
        skill.required_libs = manifest.required_libs
        skill.input_schema = manifest.input_schema
        skill.output_schema = manifest.output_schema
        skill.instructions = manifest.instructions
        skill.tags = manifest.tags
        skill._manifest = manifest
        return skill

    @classmethod
    def from_yaml(cls, text: str) -> "BaseSkill":
        manifest = SkillManifest.from_yaml(text)
        skill = _GenericManifestSkill()
        skill.name = manifest.name
        skill.description = manifest.description
        skill.author = manifest.author
        skill.version = manifest.version
        skill.category = manifest.category
        skill.required_libs = manifest.required_libs
        skill.input_schema = manifest.input_schema
        skill.output_schema = manifest.output_schema
        skill.instructions = manifest.instructions
        skill.tags = manifest.tags
        skill._manifest = manifest
        return skill

    # ── Validation ──────────────────────────────────────────────

    def validate_inputs(self, **kwargs) -> list[str]:
        errors = []
        for key, schema_type in self.input_schema.get("properties", {}).items():
            if key not in kwargs and schema_type.get("required"):
                errors.append(f"Missing required input: {key}")
        return errors

    def get_metadata(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "author": self.author,
            "version": self.version,
            "required_libs": self.required_libs,
            "tags": self.tags,
            "grid_coords": self.grid_coords,
        }


# ── Generic Skill from manifest (for frontier model Skills.md) ────

class _GenericManifestSkill(BaseSkill):
    """Stand-in skill created from a Skills.md manifest. No execute logic."""
    name = "from_manifest"
    description = "Loaded from Skills.md manifest"

    def execute(self, **kwargs) -> dict:
        return {"error": f"Skill '{self.name}' loaded from manifest — no implementation yet", "result": None}


# ── Skill discovery from Skills.md / .yml / .yaml files ──────────

def discover_manifest_skills(manifest_dirs: Optional[list[str]] = None) -> list[BaseSkill]:
    """Scan directories for Skills.md, skills.yml, skills.yaml files and load as manifest skills."""
    skills: list[BaseSkill] = []
    dirs = manifest_dirs or _SKILL_MANIFEST_DIRS
    for d in dirs:
        for pattern in ("Skills.md", "skills.yml", "skills.yaml"):
            for f in Path(d).rglob(pattern):
                try:
                    text = f.read_text(encoding="utf-8")
                    if f.suffix in (".yml", ".yaml"):
                        skill = BaseSkill.from_yaml(text)
                    else:
                        skill = BaseSkill.from_markdown(text)
                    skills.append(skill)
                except Exception:
                    continue
    return skills


def register_manifest_dir(path: str):
    with _registry_lock:
        if path not in _SKILL_MANIFEST_DIRS:
            _SKILL_MANIFEST_DIRS.append(path)
