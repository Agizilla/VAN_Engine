import importlib
import importlib.util
import inspect
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import BaseSkill, register_skill, SKILL_REGISTRY, SkillContext, SkillManifest
from .intent_grid import map_intent, grid_to_label

logger = logging.getLogger(__name__)

GENERATED_DIR = Path(__file__).resolve().parent / "generated"
GENERATED_DIR.mkdir(exist_ok=True)
GENERATED_INIT = GENERATED_DIR / "__init__.py"
if not GENERATED_INIT.exists():
    GENERATED_INIT.write_text("# Auto-generated skills\n")

SKILL_TEMPLATE = '''\"\"\"{module_docstring}\"\"\"
from pathlib import Path
from typing import Any, Optional
# {generated_note}
from ..base import BaseSkill, register_skill


@register_skill("{skill_name}", "{category}")
class {class_name}(BaseSkill):
    name = "{skill_name}"
    description = "{description}"
    category = "{category}"
    author = "{author}"
    version = "{version}"
    tags = {tags}
    grid_coords = {grid_coords}

    def execute(self, **kwargs: Any) -> dict:
        \"\"\"Auto-generated skill for: {intent_summary}\"\"\"
        # TODO: implement {intent_summary} logic
        result = {{
            "intent": "{intent_summary}",
            "params": kwargs,
            "info": "Auto-generated skill stub — implement execute() logic",
        }}
        return {{"error": None, "result": result}}
'''


def _make_class_name(intent_summary: str) -> str:
    words = intent_summary.replace("/", " ").split()
    capitalized = "".join(w.capitalize() for w in words if w)
    import re
    capitalized = re.sub(r"[^a-zA-Z0-9]", "", capitalized)
    return capitalized + "Skill" if not capitalized.endswith("Skill") else capitalized


def _make_skill_name(intent_summary: str) -> str:
    words = intent_summary.replace("/", " ").lower().split()
    import re
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", "_".join(words))
    return cleaned.strip("_")


def _lint_file(file_path: Path):
    try:
        import subprocess
        result = subprocess.run(["black", "--check", str(file_path)], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            logger.warning(f"black lint warnings for {file_path.name}: {result.stdout[:200]}")
    except Exception:
        pass
    try:
        import subprocess
        result = subprocess.run(["isort", "--check", "--diff", str(file_path)], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            logger.warning(f"isort lint warnings for {file_path.name}: {result.stdout[:200]}")
    except Exception:
        pass


@register_skill("intent_forge", "intent")
class IntentForgeSkill(BaseSkill):
    name = "intent_forge"
    description = "Generate a BaseSkill subclass from mapped intent and save to skills/generated/"
    author = "The Forge"
    version = "1.0.0"
    category = "intent"
    tags = ["forge", "generate", "skill", "intent-to-skill", "code-gen"]
    input_schema = {
        "type": "object",
        "properties": {
            "intent_text": {"type": "string", "description": "Raw or cleaned intent text"},
            "grid": {"type": "object", "description": "Pre-mapped grid coords (optional)"},
            "description": {"type": "string", "default": ""},
            "author": {"type": "string", "default": "ClawDia"},
            "version": {"type": "string", "default": "1.0.0"},
            "auto_register": {"type": "boolean", "default": True},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "skill_name": {"type": "string"},
            "file_path": {"type": "string"},
            "class_name": {"type": "string"},
            "intent_summary": {"type": "string"},
            "grid_label": {"type": "string"},
            "registered": {"type": "boolean"},
        },
    }

    def execute(self, **kwargs) -> dict:
        intent_text = kwargs.get("intent_text", "")
        pre_grid = kwargs.get("grid")
        author = kwargs.get("author", "ClawDia")
        version = kwargs.get("version", "1.0.0")
        auto_register = kwargs.get("auto_register", True)

        if not intent_text:
            return {"error": "No intent_text provided", "result": None}

        grid = pre_grid if pre_grid else map_intent(intent_text)
        grid_label = grid_to_label(grid)

        x = grid.get("x", {}).get("category", "misc")
        y = grid.get("y", {}).get("category", "general")
        z = grid.get("z", {}).get("category", "process")

        desc = kwargs.get("description", "") or f"Auto-forged skill for: {intent_text}"
        intent_summary = f"{x}/{y}/{z}"
        class_name = _make_class_name(intent_summary)
        skill_name = _make_skill_name(intent_summary)

        if skill_name in SKILL_REGISTRY:
            return {"error": f"Skill name '{skill_name}' already registered in SKILL_REGISTRY", "result": None}

        generated_note = f"Forged by IntentForge on {datetime.now().isoformat()}"
        tags = [x, y, z, "auto-generated"]

        grid_coords = {"x": x, "y": y, "z": z}
        module_docstring = f"{intent_summary} — Auto-forged skill\n\nGrid coords: {grid_coords}\nIntent source: {intent_text}"

        code = SKILL_TEMPLATE.format(
            module_docstring=module_docstring,
            generated_note=generated_note,
            skill_name=skill_name,
            class_name=class_name,
            description=desc,
            category=y,
            author=author,
            version=version,
            tags=tags,
            grid_coords=grid_coords,
            intent_summary=intent_summary,
        )

        file_path = GENERATED_DIR / f"{skill_name}.py"
        if file_path.exists():
            stem = file_path.stem
            file_path = GENERATED_DIR / f"{stem}_v2.py"
            skill_name = f"{skill_name}_v2"

        file_path.write_text(code, encoding="utf-8")

        _lint_file(file_path)

        init_import = f"from . import {file_path.stem}\n"
        init_content = GENERATED_INIT.read_text(encoding="utf-8")
        if init_import not in init_content:
            GENERATED_INIT.write_text(init_content + init_import, encoding="utf-8")

        registered = skill_name in SKILL_REGISTRY
        if auto_register and not registered:
            try:
                pkg_name = "src.skills.generated"
                for mod_name in list(sys.modules.keys()):
                    if pkg_name in mod_name and mod_name != pkg_name:
                        del sys.modules[mod_name]
                if pkg_name in sys.modules:
                    importlib.reload(sys.modules[pkg_name])
                else:
                    __import__(pkg_name)
                registered = skill_name in SKILL_REGISTRY
            except Exception as e:
                registered = False

        result = {
            "skill_name": skill_name,
            "file_path": str(file_path),
            "class_name": class_name,
            "intent_summary": intent_summary,
            "grid_label": grid_label,
            "registered": registered,
            "code": code,
        }

        self.publish("skill:forged", result)

        return {"error": None, "result": result}

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, str):
            payload = {"intent_text": payload}
        result = self.execute(**payload) if isinstance(payload, dict) else self.execute(intent_text=str(payload))
        if result.get("error"):
            return False, result["error"]
        return True, result["result"]


@register_skill("intent_forge_manifest", "intent")
class IntentForgeManifestSkill(BaseSkill):
    name = "intent_forge_manifest"
    description = "Generate a Skills.md manifest for a forged skill instead of Python code"
    category = "intent"
    tags = ["forge", "manifest", "markdown"]

    def execute(self, **kwargs) -> dict:
        intent_text = kwargs.get("intent_text", "")
        if not intent_text:
            return {"error": "No intent_text provided", "result": None}

        grid = map_intent(intent_text)
        x = grid.get("x", {}).get("category", "misc")
        y = grid.get("y", {}).get("category", "general")
        z = grid.get("z", {}).get("category", "process")

        manifest = SkillManifest(
            name=_make_skill_name(f"{x}_{y}_{z}"),
            description=f"Auto-forged: {intent_text}",
            author="ClawDia",
            version="1.0.0",
            category=y,
            tags=[x, y, z, "auto-generated"],
            grid_coords={"x": x, "y": y, "z": z},
            instructions=f"Implement a skill that handles {x} operations on {y} domain with {z} constraint.\n\nIntent source: {intent_text}",
        )

        md = manifest.to_markdown()
        file_path = GENERATED_DIR / f"{manifest.name}_Skills.md"
        file_path.write_text(md, encoding="utf-8")

        return {"error": None, "result": {
            "name": manifest.name,
            "file_path": str(file_path),
            "markdown": md,
        }}
