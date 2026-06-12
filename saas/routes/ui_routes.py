"""UI route handlers for SAAS Hooks."""
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from skills_manager import discover_skills
from routes.ui_assets import (
    UI_STYLES, FORGE_UI_STYLES, FORGE_SCRIPT,
    render_menu_page, render_form_page,
)

router = APIRouter()


# IMPORTANT: Specific UI paths must be registered before the {skill_name} catch-all


@router.get("/hooks/ui")
def ui_menu(request: Request):
    skills = discover_skills()
    return HTMLResponse(render_menu_page(skills))


@router.get("/hooks/ui/portal")
async def ui_portal(request: Request):
    portal_path = Path(__file__).parent.parent / "static" / "portal.html"
    return HTMLResponse(portal_path.read_text(encoding="utf-8"))


@router.get("/hooks/ui/forge")
async def ui_forge(request: Request):
    skills = discover_skills()
    skill_options = "".join(f'<option value="{n}">{n}</option>' for n in sorted(skills))
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Forge \u2014 Multi-Agent Studio</title>{UI_STYLES}{FORGE_UI_STYLES}{FORGE_SCRIPT}
</head><body>
  <a href="/hooks/ui" class="back">\u2190 Back to menu</a>
  <h1>Forge Studio</h1>
  <p class="subtitle">Spawn agents, give them skills, watch them build together. Every call tests our SAAS.</p>

  <form id="forge-form" onsubmit="event.preventDefault();startForge()">
    <div class="field">
      <label for="seed">Seed / Scenario</label>
      <input type="text" id="seed" class="widget" value="two lovers in a recursive garden" placeholder="Describe the scenario\u2026">
    </div>
    <div class="field">
      <label for="iterations">Iterations (rounds)</label>
      <input type="number" id="iterations" class="widget" value="3" min="1" max="20" style="max-width:100px">
    </div>
    <h2>Agents</h2>
    <div id="agents-container">
      <div class="agent-row">
        <input class="agent-name widget" placeholder="Name" value="Lyricist">
        <input class="agent-role widget" placeholder="Role" value="lyricist">
        <input class="agent-skills widget" placeholder="comic_compiler,vibe_affirmations" value="vibe_affirmations">
        <button type="button" onclick="this.parentElement.remove()" style="background:#da3633;color:#fff;border:none;border-radius:4px;padding:4px 8px;cursor:pointer">\u00d7</button>
      </div>
      <div class="agent-row">
        <input class="agent-name widget" placeholder="Name" value="Composer">
        <input class="agent-role widget" placeholder="Role" value="composer">
        <input class="agent-skills widget" placeholder="audio_analyze,audio_info" value="audio_info">
        <button type="button" onclick="this.parentElement.remove()" style="background:#da3633;color:#fff;border:none;border-radius:4px;padding:4px 8px;cursor:pointer">\u00d7</button>
      </div>
      <div class="agent-row">
        <input class="agent-name widget" placeholder="Name" value="Mike">
        <input class="agent-role widget" placeholder="Role" value="composer">
        <input class="agent-skills widget" placeholder="midi_render" value="midi_render">
        <button type="button" onclick="this.parentElement.remove()" style="background:#da3633;color:#fff;border:none;border-radius:4px;padding:4px 8px;cursor:pointer">\u00d7</button>
      </div>
    </div>
    <button type="button" onclick="addAgent()" style="background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:.4rem 1rem;cursor:pointer;margin-bottom:1rem">+ Add Agent</button>
    <button type="submit" class="submit" id="forge-btn">Forge</button>
  </form>

  <div id="error" class="error" style="display:none"></div>
  <div id="forge-status" style="color:#8b949e;font-size:.85rem;margin-top:.5rem"></div>

  <div class="split-panel">
    <div>
      <h2>Agent Activity</h2>
      <div id="forge-output">Waiting for forge\u2026</div>
    </div>
    <div>
      <h2>Live Preview</h2>
      <div id="live-preview"><p style="color:#8b949e">HTML will appear here as agents collaborate\u2026</p></div>
    </div>
  </div>
</body></html>""")


@router.get("/hooks/ui/forge-entanglement")
async def forge_entanglement_ui():
    fpath = Path(__file__).parent.parent / "static" / "forge.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>forge.html not found</h1>", status_code=404)


@router.get("/hooks/ui/{skill_name}")
async def ui_form(skill_name: str, request: Request):
    skills = discover_skills()
    skill = skills.get(skill_name)
    if not skill:
        raise HTTPException(404, f"Hook '{skill_name}' not found")
    return HTMLResponse(render_form_page(skill_name, skill))
