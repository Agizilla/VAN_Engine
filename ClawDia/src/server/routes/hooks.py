"""SAAS Hooks API — auto-generated POST /hooks/:skill_name from SkillRegistry.

Each discovered skill becomes a hook endpoint. Input validated against
skill.input_schema. Output follows consistent JSON envelope.
"""

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import JSONResponse

from ...skills.base import BaseSkill, get_registered_skills
from ...skills.loader import SkillLoader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hooks", tags=["hooks"])


def _get_loader(request: Request) -> SkillLoader:
    return request.app.state.skill_loader


def _build_skill_index(request: Request) -> dict[str, BaseSkill]:
    loader = _get_loader(request)
    skills = loader.discover_skills()
    index: dict[str, BaseSkill] = {}
    for s in skills:
        if s.name:
            index[s.name] = s
    for name, info in get_registered_skills().items():
        if name not in index:
            try:
                instance = info["cls"]()
                index[name] = instance
            except Exception as e:
                logger.warning("Failed to instantiate registered skill '%s': %s", name, e)
    return index


def _validate_against_schema(params: dict, schema: dict) -> list[str]:
    errors = []
    props = schema.get("properties", {})
    required = schema.get("required", [])
    for key in required:
        if key not in params:
            errors.append(f"Missing required field: '{key}'")
    for key, val in params.items():
        if key in props:
            expected_type = props[key].get("type", "string")
            enum_vals = props[key].get("enum")
            if enum_vals and val not in enum_vals:
                errors.append(f"'{key}' must be one of {enum_vals}, got '{val}'")
            elif expected_type == "string" and not isinstance(val, str):
                errors.append(f"'{key}' expected string, got {type(val).__name__}")
            elif expected_type == "integer" and not isinstance(val, int):
                errors.append(f"'{key}' expected integer, got {type(val).__name__}")
            elif expected_type == "number" and not isinstance(val, (int, float)):
                errors.append(f"'{key}' expected number, got {type(val).__name__}")
            elif expected_type == "boolean" and not isinstance(val, bool):
                errors.append(f"'{key}' expected boolean, got {type(val).__name__}")
            elif expected_type == "array" and not isinstance(val, (list, tuple)):
                errors.append(f"'{key}' expected array, got {type(val).__name__}")
    return errors


def _format_result(result: Any) -> dict:
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


def _skill_to_manifest(skill: BaseSkill) -> dict:
    return {
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "version": skill.version,
        "author": skill.author,
        "tags": skill.tags,
        "required_libs": skill.required_libs,
        "input_schema": skill.input_schema,
        "output_schema": skill.output_schema,
        "instructions": skill.instructions[:500] if skill.instructions else "",
    }


# ── Endpoints ────────────────────────────────────────────────────────


@router.get("/")
def list_hooks(request: Request):
    """List all available hooks with their manifests."""
    index = _build_skill_index(request)
    result = []
    for name, skill in sorted(index.items()):
        result.append({
            "hook": name,
            "endpoint": f"POST /hooks/{name}",
            "manifest": _skill_to_manifest(skill),
        })
    return {"hooks": result, "total": len(result)}


@router.get("/{skill_name}")
def get_hook_info(skill_name: str, request: Request):
    """Get manifest for a specific hook."""
    index = _build_skill_index(request)
    skill = index.get(skill_name)
    if not skill:
        raise HTTPException(404, f"Hook '{skill_name}' not found")
    return {
        "hook": skill_name,
        "endpoint": f"POST /hooks/{skill_name}",
        "manifest": _skill_to_manifest(skill),
    }


@router.post("/{skill_name}")
async def execute_hook(skill_name: str, request: Request):
    """Execute a hook by name. Body is the skill's input parameters."""
    index = _build_skill_index(request)
    skill = index.get(skill_name)
    if not skill:
        raise HTTPException(404, f"Hook '{skill_name}' not found")

    try:
        raw = await request.body()
        params = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        params = {}

    schema = skill.input_schema or {}
    errors = _validate_against_schema(params, schema)
    if errors:
        raise HTTPException(422, {"errors": errors, "hook": skill_name})

    try:
        result = skill.execute(**params)
        return _format_result(result)
    except Exception as e:
        logger.exception("Hook '%s' execution failed", skill_name)
        raise HTTPException(500, {"error": str(e), "hook": skill_name})


@router.post("/batch")
async def execute_batch(request: Request):
    """Execute multiple hooks in sequence.

    Body: {"calls": [{"hook": str, "params": dict}, ...]}
    """
    try:
        raw = await request.body()
        data = json.loads(raw) if raw else {"calls": []}
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(422, "Invalid JSON body")

    calls = data.get("calls", []) if isinstance(data, dict) else []
    if not isinstance(calls, list):
        raise HTTPException(422, "'calls' must be an array")

    index = _build_skill_index(request)
    results = []
    for i, call in enumerate(calls):
        hook_name = call.get("hook", "") if isinstance(call, dict) else ""
        params = call.get("params", {}) if isinstance(call, dict) else {}
        skill = index.get(hook_name)
        if not skill:
            results.append({"index": i, "hook": hook_name, "status": "error", "error": "Hook not found"})
            continue
        schema_errors = _validate_against_schema(params, skill.input_schema or {})
        if schema_errors:
            results.append({"index": i, "hook": hook_name, "status": "validation_error", "errors": schema_errors})
            continue
        try:
            result = skill.execute(**params)
            results.append({"index": i, "hook": hook_name, "status": "ok", "result": _format_result(result)})
        except Exception as e:
            logger.exception("Batch hook '%s' failed", hook_name)
            results.append({"index": i, "hook": hook_name, "status": "error", "error": str(e)})

    return {"results": results, "total": len(calls), "succeeded": sum(1 for r in results if r["status"] == "ok")}
