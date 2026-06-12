"""MIDI routes: composer UI and render endpoint."""
import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from skills_manager import discover_skills, validate_params, format_result
from routes.ui_assets import UI_STYLES, MIDI_UI_STYLES, MIDI_SCRIPT, MIDI_UI_HTML

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/hooks/ui/midi")
async def ui_midi_composer(request: Request):
    html = MIDI_UI_HTML.replace("{UI_STYLES}", UI_STYLES).replace("{MIDI_UI_STYLES}", MIDI_UI_STYLES).replace("{MIDI_SCRIPT}", MIDI_SCRIPT)
    return HTMLResponse(html)


@router.post("/hooks/midi/render")
async def midi_render_nested(request: Request):
    skills = discover_skills()
    skill = skills.get("midi_render")
    if not skill:
        raise HTTPException(404, "midi_render skill not found")
    try:
        raw = await request.body()
        params = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        params = {}
    errors = validate_params(params, skill)
    if errors:
        raise HTTPException(422, {"errors": errors})
    try:
        result = skill.execute(**params) if hasattr(skill, "execute") else skill.run(payload=params)
        return format_result(result)
    except Exception as e:
        raise HTTPException(500, {"error": str(e)})
