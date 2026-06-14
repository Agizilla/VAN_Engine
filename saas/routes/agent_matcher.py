"""
Agent Matcher — background worker that polls ingested projects, matches keywords
against agent interests, and triggers skills automatically.
POST /api/agent/matcher/start   — start background polling
POST /api/agent/matcher/stop    — stop background polling
GET  /api/agent/matcher/status  — check running state
POST /api/agent/interests       — set agent interest profiles
GET  /api/agent/interests       — list current interests
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent-matcher"])

DATA_DIR = Path(__file__).parent.parent / "data" / "projects"
SEEN_FILE = Path.home() / ".claude" / "PAI" / "SEEN_PROJECTS.json"
INTERESTS_FILE = Path.home() / ".claude" / "PAI" / "AGENT_INTERESTS.json"

_running = False
_task: asyncio.Task | None = None


def _load_json(path: Path, default: Any = None) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def _save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _default_interests() -> list[dict]:
    return [
        {"name": "face-avatar-builder", "keywords": ["face", "avatar", "3d", "mediapipe", "mesh"], "skill": "forge", "priority": 10},
        {"name": "python-generalist", "keywords": ["python", "opencv", "pygame", "numpy"], "skill": "execute", "priority": 5},
        {"name": "web-fixer", "keywords": ["web", "html", "javascript", "css", "react", "vue"], "skill": "prd_skill", "priority": 7},
        {"name": "ml-engineer", "keywords": ["ml", "tensorflow", "pytorch", "keras", "torch"], "skill": "forge", "priority": 8},
    ]


def _match_projects() -> list[dict]:
    seen = set(_load_json(SEEN_FILE, []))
    interests = _load_json(INTERESTS_FILE, _default_interests())
    matches = []

    for pdir in sorted(DATA_DIR.iterdir()):
        if not pdir.is_dir() or pdir.name in seen:
            continue
        kw_path = pdir / ".keywords.json"
        if not kw_path.exists():
            continue
        kw_data = _load_json(kw_path, {"keywords": []})
        keywords = set(kw_data.get("keywords", []))

        for interest in interests:
            score = sum(1 for kw in keywords if kw in interest.get("keywords", []))
            if score > 0:
                matches.append({
                    "agent": interest["name"],
                    "skill": interest.get("skill", "forge"),
                    "score": score,
                    "priority": interest.get("priority", 0),
                    "project": pdir.name,
                    "path": str(pdir),
                })

        seen.add(pdir.name)

    _save_json(SEEN_FILE, list(seen))
    matches.sort(key=lambda x: (-x["priority"], -x["score"]))
    return matches


async def _trigger_skill(skill_name: str, project_name: str, project_path: str):
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"http://localhost:8001/hooks/{skill_name}",
                json={"action": "execute", "project_name": project_name, "project_path": project_path},
            )
        logger.info("Triggered %s on %s", skill_name, project_name)
    except Exception as e:
        logger.debug("Trigger %s failed: %s", skill_name, e)


async def _poll_loop(interval: int = 3600):
    global _running
    while _running:
        try:
            matches = _match_projects()
            for m in matches[:3]:
                await _trigger_skill(m["skill"], m["project"], m["path"])
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Matcher error: %s", e)
        await asyncio.sleep(interval)


def start_matcher_directly():
    global _running, _task
    if _running:
        return
    _running = True
    _task = asyncio.create_task(_poll_loop(3600))


@router.post("/execute")
async def agent_execute(cmd: dict):
    """Execute a command string via subprocess and return output."""
    command = cmd.get("command", "")
    if not command:
        return {"status": "error", "message": "no command"}
    try:
        import subprocess
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=60, shell=True
        )
        return {
            "status": "completed",
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:500],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/matcher/start")
async def start_matcher():
    start_matcher_directly()
    return {"status": "started"}


@router.post("/matcher/stop")
async def stop_matcher():
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        _task = None
    return {"status": "stopped"}


@router.get("/matcher/status")
async def matcher_status():
    seen = _load_json(SEEN_FILE, [])
    return {"running": _running, "seen_projects": len(seen)}


@router.post("/interests")
async def set_interests(interests: list[dict]):
    _save_json(INTERESTS_FILE, interests)
    return {"status": "updated", "count": len(interests)}


@router.get("/interests")
async def get_interests():
    return {"interests": _load_json(INTERESTS_FILE, _default_interests())}
