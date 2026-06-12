"""SAAS Hooks API Server — slim entry point importing route modules."""
import asyncio
import logging
import os

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

app = FastAPI(
    title="SAAS Hooks API",
    version="1.0.0",
    description="256-skill auto-generated hooks server. POST /hooks/:skill_name to execute.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Specific routes MUST be included before the api catch-all (/hooks/{skill_name})
app.include_router(midi_router)          # GET /hooks/ui/midi, POST /hooks/midi/render
app.include_router(forge_router)         # POST /hooks/forge
app.include_router(github_watch_router)  # GET/POST /hooks/github_watch/{username}
app.include_router(optimiser_router)     # POST /api/optimise
app.include_router(gossip_router)        # /hooks/learnings/gossip/*
app.include_router(ui_router)           # /hooks/ui, /hooks/ui/portal, /hooks/ui/forge, /hooks/ui/forge-entanglement, /hooks/ui/{skill_name}
app.include_router(api_router)          # GET /hooks/, GET /hooks/{name}, POST /hooks/{name}, POST /hooks/batch


_gossip_task: asyncio.Task | None = None


@app.on_event("startup")
async def startup():
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

    from routes.gossip_worker import run_worker
    _gossip_task = asyncio.create_task(run_worker(3600))
    logger.info("Gossip worker started (hourly)")


@app.on_event("shutdown")
async def shutdown():
    if _gossip_task:
        _gossip_task.cancel()
        try:
            await _gossip_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8001, reload=False)
