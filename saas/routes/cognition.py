"""
Cognition — real-time thinking dashboard.
POST /api/cognition/event   — submit a thinking event (type, message, status)
GET  /api/cognition/stream  — SSE stream of events (since server start or ?after=ID)
GET  /hooks/ui/cognition    — HTML dashboard
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

events: list[dict] = []
subscribers: list[asyncio.Queue] = []
next_id = 0

EVENT_TYPES = {"thinking", "tool_call", "tool_result", "decision", "learning", "status", "error"}

HTML_PATH = Path(__file__).parent.parent / "static" / "cognition.html"


class CognEvent(BaseModel):
    type: str = "thinking"
    message: str = ""
    tool: str = ""
    description: str = ""
    status: str = ""  # running | completed | failed
    summary: str = ""
    options: list[str] = []
    tags: list[str] = []


def add_event(ev: CognEvent) -> int:
    global next_id
    next_id += 1
    entry = {
        "id": next_id,
        "type": ev.type if ev.type in EVENT_TYPES else "thinking",
        "message": ev.message,
        "tool": ev.tool,
        "description": ev.description,
        "status": ev.status,
        "summary": ev.summary,
        "options": ev.options,
        "tags": ev.tags,
        "ts": datetime.now(timezone.utc).isoformat(),
        "t": time.time(),
    }
    events.append(entry)
    # notify SSE subscribers
    for q in subscribers:
        q.put_nowait(entry)
    return next_id


@router.post("/api/cognition/event")
async def post_event(ev: CognEvent):
    eid = add_event(ev)
    return {"id": eid, "type": ev.type}


@router.get("/api/cognition/stream")
async def stream_events(request: Request, after: int = Query(0, description="Only events after this ID")):
    queue: asyncio.Queue = asyncio.Queue()
    subscribers.append(queue)

    async def generate():
        try:
            # replay past events
            for ev in events:
                if ev["id"] > after:
                    yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            # stream new events
            while True:
                if await request.is_disconnected():
                    break
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        finally:
            if queue in subscribers:
                subscribers.remove(queue)

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/hooks/ui/cognition")
async def cognition_ui():
    if HTML_PATH.exists():
        return HTMLResponse(HTML_PATH.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Cognition Dashboard</h1><p>cognition.html not found</p>", status_code=200)


@router.get("/api/cognition/events")
async def get_events(limit: int = 200, after: int = 0):
    filtered = [ev for ev in events if ev["id"] > after]
    return {"events": filtered[-limit:], "total": len(events)}
