"""Shared skill discovery, validation, and formatting utilities."""
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BASE = Path(__file__).resolve().parent
_SRC = _BASE / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_LEGACY_SRC = _BASE.parent / "ClawDia" / "src"
if str(_LEGACY_SRC) not in sys.path:
    sys.path.insert(0, str(_LEGACY_SRC))

from skills.base import get_registered_skills, BaseSkill
from skills.loader import SkillLoader

_loader = SkillLoader(skills_dir=str(_SRC / "skills"))

_SKILL_CACHE: dict[str, BaseSkill] = {}


def discover_skills() -> dict[str, BaseSkill]:
    if _SKILL_CACHE:
        return _SKILL_CACHE
    cache: dict[str, BaseSkill] = {}
    for s in _loader.discover_skills():
        if s.name:
            cache[s.name] = s
    for name, info in get_registered_skills().items():
        if name not in cache:
            try:
                inst = info["cls"]()
                if inst is not None:
                    cache[name] = inst
            except Exception:
                pass
    _SKILL_CACHE.update(cache)
    return _SKILL_CACHE


def get_manifest(skill: BaseSkill) -> dict:
    return {
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "version": skill.version,
        "author": skill.author,
        "tags": list(skill.tags) if hasattr(skill, "tags") else [],
        "required_libs": list(skill.required_libs) if hasattr(skill, "required_libs") else [],
        "input_schema": skill.input_schema if hasattr(skill, "input_schema") else {},
        "output_schema": skill.output_schema if hasattr(skill, "output_schema") else {},
        "instructions": (skill.instructions or "")[:500] if hasattr(skill, "instructions") else "",
    }


def validate_params(params: dict, skill: BaseSkill) -> list[str]:
    errors = []
    schema = getattr(skill, "input_schema", {}) or {}
    props = schema.get("properties", {})
    required = schema.get("required", [])
    for key in required:
        if key not in params:
            errors.append(f"Missing required field: '{key}'")
    for key, val in params.items():
        if key in props:
            expected = props[key].get("type", "string")
            enum_vals = props[key].get("enum")
            if enum_vals and val not in enum_vals:
                errors.append(f"'{key}' must be one of {enum_vals}, got '{val}'")
            elif expected == "string" and not isinstance(val, str):
                errors.append(f"'{key}' expected string, got {type(val).__name__}")
            elif expected == "integer" and not isinstance(val, int):
                errors.append(f"'{key}' expected integer, got {type(val).__name__}")
            elif expected == "array" and not isinstance(val, (list, tuple)):
                errors.append(f"'{key}' expected array, got {type(val).__name__}")
    return errors


def format_result(result: Any) -> dict:
    if isinstance(result, dict):
        return result
    if isinstance(result, (list, tuple)):
        return {"data": list(result)}
    if isinstance(result, (bool, int, float)):
        return {"data": result}
    s = str(result)
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}
    except (json.JSONDecodeError, TypeError):
        return {"data": s}
