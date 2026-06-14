"""DirtyTalker — SAAS Portal integration. Session auth, chat, voice tags, audio, visual."""
import uuid
import time
import json
import subprocess
import tempfile
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, Response
from pydantic import BaseModel

router = APIRouter()

UI_FILE = Path(__file__).parent.parent / "static" / "dirty-talker-portal.html"
PHOTOS_DIR = Path(__file__).parent.parent / "static" / ".dirty_photos"
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

# ── In-memory session store ──────────────────────────────────────────────
_sessions: dict[str, dict] = {}
_SESSION_TTL = 3600  # 1 hour


def _clean_expired():
    now = time.time()
    expired = [k for k, v in _sessions.items() if now - v["created_at"] > _SESSION_TTL]
    for k in expired:
        del _sessions[k]


def _get_session(token: str) -> dict | None:
    _clean_expired()
    session = _sessions.get(token)
    if session and time.time() - session["created_at"] > _SESSION_TTL:
        del _sessions[token]
        return None
    return session


# ── Lazy loaded skills ───────────────────────────────────────────────────
_dt_skill = None
_audio_skill = None
_vision_skill = None


def _get_dt():
    global _dt_skill
    if _dt_skill is None:
        from skills.dirty_talker_skill import DirtyTalkerSkill
        _dt_skill = DirtyTalkerSkill()
    return _dt_skill


def _get_audio():
    global _audio_skill
    if _audio_skill is None:
        from skills.audio_skills import AudioSynthesizeSkill
        _audio_skill = AudioSynthesizeSkill()
    return _audio_skill


def _get_vision():
    global _vision_skill
    if _vision_skill is None:
        from skills.vision_skills import VisionAnimateSkill
        _vision_skill = VisionAnimateSkill()
    return _vision_skill


# ── Default settings ─────────────────────────────────────────────────────
_DEFAULT_SETTINGS = {
    "stutter_rate": 0.4,
    "template": "",
    "voice": "en_US-amy-medium",
    "sanitize": False,
    "categories": [],
}


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/hooks/ui/dirty-talker")
async def dirty_talker_ui(request: Request):
    if UI_FILE.exists():
        return HTMLResponse(UI_FILE.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>DirtyTalker portal not found</h1>", status_code=404)


class SessionRequest(BaseModel):
    pass


@router.post("/api/dirty-talker/session")
async def create_session(body: SessionRequest):
    _clean_expired()
    token = str(uuid.uuid4())
    _sessions[token] = {
        "created_at": time.time(),
        "settings": dict(_DEFAULT_SETTINGS),
        "photo_path": None,
    }
    return {"session_token": token, "expires_in": _SESSION_TTL, "settings": _DEFAULT_SETTINGS}


class ChatRequest(BaseModel):
    message: str = ""
    session_token: str = ""
    category: str = ""
    voice: str = ""


class SettingsUpdate(BaseModel):
    stutter_rate: float | None = None
    template: str | None = None
    voice: str | None = None
    sanitize: bool | None = None
    categories: list[str] | None = None


def _resolve_session(token: str) -> dict:
    if not token:
        raise HTTPException(401, "Missing session token")
    session = _get_session(token)
    if not session:
        raise HTTPException(401, "Invalid or expired session token")
    return session


def _get_token(request: Request) -> str:
    # Try Authorization header first, then body param, then query param
    auth = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    if auth:
        return auth
    return ""


@router.post("/api/dirty-talker/chat")
async def chat(body: ChatRequest, request: Request):
    token = body.session_token or _get_token(request)
    session = _resolve_session(token)
    settings = session["settings"]
    skill = _get_dt()
    cat = body.category or (settings.get("categories", [None])[0] if settings.get("categories") else "")
    result = skill.execute(
        action="generate",
        template=settings.get("template", ""),
        sanitize=settings.get("sanitize", False),
        category=cat,
    )
    if result.get("error"):
        raise HTTPException(500, result["error"])
    phrase = result["result"]["phrase"]
    voice_name = body.voice or settings.get("voice", "en_US-amy-medium")
    return {
        "phrase": phrase,
        "voice_tag": voice_name,
        "voice_tag_text": f"[voice:{voice_name}]",
        "template": result["result"].get("template", ""),
        "sanitized": result["result"].get("sanitized", False),
        "generated": result["result"].get("generated", ""),
        "response_id": str(uuid.uuid4()),
    }


class SettingsBody(BaseModel):
    session_token: str = ""
    voice: str | None = None
    category: str | None = None
    stutter: float | None = None
    stutter_rate: float | None = None  # legacy
    sanitize: bool | None = None
    categories: list[str] | None = None  # legacy


@router.post("/api/dirty-talker/settings")
async def update_settings(body: SettingsBody, request: Request):
    token = body.session_token or _get_token(request)
    session = _resolve_session(token)
    if body.voice is not None:
        session["settings"]["voice"] = body.voice
    if body.stutter is not None:
        session["settings"]["stutter_rate"] = body.stutter
    if body.stutter_rate is not None:
        session["settings"]["stutter_rate"] = body.stutter_rate
    if body.sanitize is not None:
        session["settings"]["sanitize"] = body.sanitize
    if body.category is not None:
        session["settings"]["categories"] = [body.category]
    if body.categories is not None:
        session["settings"]["categories"] = body.categories
    return {"status": "ok", "settings": session["settings"]}


@router.get("/api/dirty-talker/settings")
async def get_settings(request: Request, session_token: str = ""):
    token = session_token or _get_token(request)
    session = _resolve_session(token)
    return session["settings"]


# ═══════════════════════════════════════════════════════════════════════════
# PHOTO UPLOAD
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/api/dirty-talker/photo")
async def upload_photo(file: UploadFile = File(...), request: Request = None):
    session = _resolve_session(request)
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    photo_path = PHOTOS_DIR / f"{uuid.uuid4()}{ext}"
    content = await file.read()
    photo_path.write_bytes(content)
    session["photo_path"] = str(photo_path)
    return {"status": "ok", "path": str(photo_path)}


@router.get("/api/dirty-talker/photo")
async def get_photo(request: Request):
    session = _resolve_session(request)
    path = session.get("photo_path")
    if not path or not Path(path).exists():
        raise HTTPException(404, "No photo uploaded")
    return FileResponse(path)


# ═══════════════════════════════════════════════════════════════════════════
# SPEAK — TTS for a phrase
# ═══════════════════════════════════════════════════════════════════════════

class SpeakRequest(BaseModel):
    phrase: str = ""
    session_token: str = ""
    response_id: str = ""
    voice: str = ""


@router.post("/api/dirty-talker/speak")
async def speak(body: SpeakRequest, request: Request):
    token = body.session_token or _get_token(request)
    session = _resolve_session(token)
    if not body.phrase.strip():
        raise HTTPException(400, "No phrase provided")

    result = _get_audio().execute(text=body.phrase)
    if result.get("error"):
        raise HTTPException(500, result["error"])

    wav_path = result["result"]["path"]
    return FileResponse(wav_path, media_type="audio/wav", filename="speak.wav")


# ═══════════════════════════════════════════════════════════════════════════
# SPEAK VISUALLY — animate face + TTS audio
# ═══════════════════════════════════════════════════════════════════════════

def _check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


@router.post("/api/dirty-talker/speak-visual")
async def speak_visual(body: SpeakRequest, request: Request):
    token = body.session_token or _get_token(request)
    session = _resolve_session(token)
    if not body.phrase.strip():
        raise HTTPException(400, "No phrase provided")

    photo_path = session.get("photo_path")
    if not photo_path or not Path(photo_path).exists():
        raise HTTPException(400, "No photo uploaded — upload one first via /api/dirty-talker/photo")

    # 1. Generate TTS audio
    audio_result = _get_audio().execute(text=body.phrase)
    if audio_result.get("error"):
        raise HTTPException(500, f"TTS failed: {audio_result['error']}")
    wav_path = Path(audio_result["result"]["path"])

    # 2. Animate face → GIF
    anim_result = _get_vision().execute(
        path=photo_path,
        blink_freq=0.8,
        talk_amp=0.6,
        speed=1.0,
        duration=max(2.0, len(body.phrase) / 8),  # ~8 chars/sec
    )
    if anim_result.get("error"):
        raise HTTPException(500, f"Animation failed: {anim_result['error']}")
    gif_path = Path(anim_result["result"]["gif_path"])

    # 3. Convert GIF → temp MP4
    tmp_dir = Path(tempfile.mkdtemp())
    video_path = tmp_dir / "animated.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(gif_path),
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(video_path),
    ], capture_output=True, timeout=30)

    # 4. Merge audio into video
    output_path = tmp_dir / "speak-visual.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_path), "-i", str(wav_path),
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        str(output_path),
    ], capture_output=True, timeout=30)

    return FileResponse(str(output_path), media_type="video/mp4", filename="speak-visual.mp4")
