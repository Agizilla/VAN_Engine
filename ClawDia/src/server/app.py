import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from ..core.config import load_config, resolve_path
from ..core.memory.episodic import EpisodicMemory
from ..core.memory.semantic import SemanticMemory
from ..skills.loader import SkillLoader

from .routes.memory import router as memory_router
from .routes.skills import router as skills_router
from .routes.voice import router as voice_router
from .routes.rag import router as rag_router
from .routes.database import router as db_router
from .routes.hooks import router as hooks_router


def create_app():
    cfg = load_config()
    cfg = resolve_path(cfg)
    episodic = EpisodicMemory(
        db_path=cfg.memory.episodic.database_path,
        faiss_path=cfg.memory.episodic.faiss_index_path,
    )
    semantic = SemanticMemory(
        graph_path=cfg.memory.semantic.graph_path,
        schema_path=cfg.memory.semantic.schema_path,
    )
    skill_loader = SkillLoader()

    app = FastAPI(title="ClawDia Dashboard", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    app.state.episodic = episodic
    app.state.semantic = semantic
    app.state.skill_loader = skill_loader

    app.include_router(memory_router)
    app.include_router(skills_router)
    app.include_router(voice_router)
    app.include_router(rag_router)
    app.include_router(db_router)
    app.include_router(hooks_router)

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                msg_type = msg.get("type", "")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "get_skills":
                    skills = skill_loader.discover_skills()
                    await websocket.send_json({
                        "type": "skills",
                        "skills": [{"name": s.name, "description": s.description, "category": s.category} for s in skills],
                    })
                elif msg_type == "execute_skill":
                    skill_name = msg.get("name", "")
                    for s in skill_loader.discover_skills():
                        if s.name == skill_name:
                            result = s.execute(**msg.get("params", {}))
                            await websocket.send_json({"type": "skill_result", "name": skill_name, "result": result})
                            break
                elif msg_type == "get_conversations":
                    from datetime import datetime
                    rows = episodic.query_by_date_range(datetime(2000, 1, 1), datetime.utcnow(), msg.get("user_id", "default"))
                    rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
                    await websocket.send_json({
                        "type": "conversations",
                        "conversations": [{"id": r["id"], "role": r.get("metadata", {}).get("role", "user"), "content": r["text"], "timestamp": r.get("created_at", "")} for r in rows[:50]],
                    })
        except WebSocketDisconnect:
            pass

    _paths_file = Path(__file__).resolve().parent.parent.parent.parent.parent / ".clawdia_paths"
    _paths = {}
    if _paths_file.exists():
        for _line in _paths_file.read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _paths[_k.strip()] = _v.strip()

    static_dir = Path(_paths.get("CLAWDIA_STATIC", str(Path(__file__).parent / "static")))
    static_dir = static_dir.resolve()
    static_dir.mkdir(parents=True, exist_ok=True)

    @app.get("/")
    async def root():
        return RedirectResponse(url="/dashboard.html")

    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()
