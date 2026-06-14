"""SAAS Hooks API Server — slim entry point importing route modules."""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from skills_manager import discover_skills, logger
from routes.api import router as api_router
from routes.ui_routes import router as ui_router
from routes.forge import router as forge_router
from routes.midi import router as midi_router
from routes.github_watch import router as github_watch_router
from routes.optimiser import router as optimiser_router
from routes.learning_gossip import router as gossip_router
from routes.project_ingest import router as project_router
from routes.agent_matcher import router as agent_router
from routes.cognition import router as cognition_router
from routes.simulations import router as simulations_router
from routes.dirty_talker import router as dirty_talker_router
from routes.tts import router as tts_router
from routes.memory import router as memory_router


_gossip_shutdown = asyncio.Event()
_gossip_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _gossip_task
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    skills = discover_skills()
    logger.info("SAAS Hooks API ready \u2014 %d skills loaded", len(skills))
    for name in sorted(skills):
        logger.info("  POST /hooks/%-26s  %s", name, getattr(skills[name], "description", "")[:60])
    github_repo = os.environ.get("GITHUB_REPO", "")
    if "/" in github_repo:
        owner = github_repo.split("/")[0]
        from routes.github_watch import start_watchdog
        start_watchdog(owner, interval=60)
        logger.info("Auto-started watchdog for %s (from GITHUB_REPO)", owner)
    from routes.gossip_worker import background_gossip_worker
    _gossip_task = asyncio.create_task(background_gossip_worker(3600, _gossip_shutdown))
    logger.info("Gossip worker started (hourly)")
    from routes.agent_matcher import start_matcher_directly
    start_matcher_directly()
    logger.info("Agent matcher started")
    yield
    _gossip_shutdown.set()
    if _gossip_task:
        _gossip_task.cancel()
        try:
            await _gossip_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan, title="SAAS Hooks API", version="1.0.0", description="256-skill auto-generated hooks server. POST /hooks/:skill_name to execute.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Specific routes MUST be included before the api catch-all (/hooks/{skill_name})
app.include_router(midi_router)          # GET /hooks/ui/midi, POST /hooks/midi/render
app.include_router(forge_router)         # POST /hooks/forge
app.include_router(github_watch_router)  # GET/POST /hooks/github_watch/{username}
app.include_router(optimiser_router)     # POST /api/optimise
app.include_router(project_router)       # POST /api/project/ingest, GET /api/projects
app.include_router(agent_router)         # POST /api/agent/matcher/*, POST/GET /api/agent/interests
app.include_router(cognition_router)     # POST /api/cognition/event, GET /api/cognition/stream, /hooks/ui/cognition
app.include_router(simulations_router)   # GET /hooks/ui/simulations/* (before ui_router's {skill_name} catch-all)
app.include_router(dirty_talker_router)  # GET /hooks/ui/dirty-talker, POST /api/dirty-talker/*
app.include_router(tts_router)           # POST /api/tts/speak, GET /api/tts/last
app.include_router(memory_router)        # POST/GET /api/memory/archive, GET /api/memory/boot-context
app.include_router(ui_router)            # GET /hooks/ui/* (menu, clawdia, forge-entanglement, etc.)
app.include_router(gossip_router)        # gossip protocol endpoints
app.include_router(api_router)           # POST /hooks/{skill_name} catch-all


@app.get("/")
async def root():
    return {"service": "SAAS Hooks API", "version": "1.0.0", "skills": len(discover_skills()), "gossip": "enabled"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
