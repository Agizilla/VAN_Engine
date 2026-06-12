"""REST API routes for SAAS Hooks."""
import json
import logging

from fastapi import APIRouter, HTTPException, Request

from skills_manager import discover_skills, get_manifest, validate_params, format_result

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
def root():
    return {
        "service": "SAAS Hooks API",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "This info",
            "GET /hooks": "List all hooks with manifests",
            "GET /hooks/{name}": "Get manifest for a specific hook",
            "POST /hooks/{name}": "Execute a hook (body is skill params JSON)",
            "POST /hooks/batch": "Execute multiple hooks in one request",
            "GET /hooks/ui": "HTML catalog of all hooks",
            "GET /hooks/ui/{name}": "HTML form for a specific hook",
            "GET /hooks/github_watch/{user}": "Watchdog status for GitHub user",
            "POST /hooks/github_watch/{user}/poll": "Trigger watchdog poll",
            "POST /hooks/github_watch/{user}/start": "Start background watchdog polling",
        },
    }


@router.get("/hooks/")
def list_hooks():
    skills = discover_skills()
    result = []
    for name in sorted(skills):
        skill = skills[name]
        result.append({
            "hook": name,
            "endpoint": f"POST /hooks/{name}",
            "manifest": get_manifest(skill),
        })
    return {"hooks": result, "total": len(result)}


@router.get("/hooks/{skill_name}")
def get_hook(skill_name: str):
    skills = discover_skills()
    skill = skills.get(skill_name)
    if not skill:
        raise HTTPException(404, f"Hook '{skill_name}' not found")
    return {
        "hook": skill_name,
        "endpoint": f"POST /hooks/{skill_name}",
        "manifest": get_manifest(skill),
    }


@router.post("/hooks/{skill_name}")
async def execute_hook(skill_name: str, request: Request):
    skills = discover_skills()
    skill = skills.get(skill_name)
    if not skill:
        raise HTTPException(404, f"Hook '{skill_name}' not found")
    try:
        raw = await request.body()
        params = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        params = {}
    errors = validate_params(params, skill)
    if errors:
        raise HTTPException(422, {"errors": errors, "hook": skill_name})
    try:
        if hasattr(skill, "execute"):
            result = skill.execute(**params)
        elif hasattr(skill, "run"):
            result = skill.run(payload=params)
        else:
            raise HTTPException(500, f"Skill '{skill_name}' has no execute or run method")
        return format_result(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Hook '%s' failed", skill_name)
        raise HTTPException(500, {"error": str(e), "hook": skill_name})


@router.post("/hooks/batch")
async def execute_batch(request: Request):
    skills = discover_skills()
    try:
        raw = await request.body()
        data = json.loads(raw) if raw else {"calls": []}
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(422, "Invalid JSON body")
    calls = data.get("calls", []) if isinstance(data, dict) else []
    if not isinstance(calls, list):
        raise HTTPException(422, "'calls' must be an array")
    results = []
    for i, call in enumerate(calls):
        hook_name = call.get("hook", "") if isinstance(call, dict) else ""
        params = call.get("params", {}) if isinstance(call, dict) else {}
        skill = skills.get(hook_name)
        if not skill:
            results.append({"index": i, "hook": hook_name, "status": "error", "error": "Hook not found"})
            continue
        errors = validate_params(params, skill)
        if errors:
            results.append({"index": i, "hook": hook_name, "status": "validation_error", "errors": errors})
            continue
        try:
            if hasattr(skill, "execute"):
                result = skill.execute(**params)
            else:
                result = skill.run(payload=params)
            results.append({"index": i, "hook": hook_name, "status": "ok", "result": format_result(result)})
        except Exception as e:
            results.append({"index": i, "hook": hook_name, "status": "error", "error": str(e)})
    return {
        "results": results,
        "total": len(calls),
        "succeeded": sum(1 for r in results if r["status"] == "ok"),
    }
