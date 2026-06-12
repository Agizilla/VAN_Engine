"""Learning Gossip Protocol — peer-to-peer learning exchange between agents.

Endpoints:
  GET  /hooks/learnings/gossip/peers      — list known peers
  POST /hooks/learnings/gossip/peers      — add a peer
  POST /hooks/learnings/gossip/receive    — receive learnings from peer
  POST /hooks/learnings/gossip/broadcast  — manual gossip broadcast
  GET  /hooks/learnings/gossip/status     — worker + peer status
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/hooks/learnings/gossip", tags=["learning-gossip"])

_PEERS_FILE = Path.home() / ".claude" / "PAI" / "LEARNINGS" / "peers.json"
_LEARNINGS_FILE = Path.home() / ".claude" / "PAI" / "LEARNINGS" / "algorithm_learnings.jsonl"

gossip_worker_running = False
last_gossip_run: str | None = None


class PeerAddRequest(BaseModel):
    url: str


class GossipReceiveRequest(BaseModel):
    learnings: list[dict[str, Any]]
    sender: str


def _load_peers() -> list[str]:
    if _PEERS_FILE.exists():
        data = json.loads(_PEERS_FILE.read_text(encoding="utf-8"))
        return data.get("peers", [])
    return []


def _save_peers(peers: list[str]):
    _PEERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PEERS_FILE.write_text(json.dumps(
        {"peers": peers, "updated_at": datetime.now(timezone.utc).isoformat()},
        indent=2,
    ), encoding="utf-8")


def _append_learning(entry: dict):
    _LEARNINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(str(_LEARNINGS_FILE), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _list_learnings(limit: int = 200) -> list[dict]:
    if not _LEARNINGS_FILE.exists():
        return []
    entries = []
    for line in _LEARNINGS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


@router.get("/peers")
async def list_peers():
    return {"peers": _load_peers()}


@router.post("/peers")
async def add_peer(req: PeerAddRequest):
    peers = _load_peers()
    if req.url not in peers:
        peers.append(req.url)
        _save_peers(peers)
    return {"status": "added", "peers": peers}


def _is_duplicate(new_l: dict, existing: list[dict]) -> bool:
    cutoff = datetime.now() - timedelta(days=7)
    for ex in existing:
        if ex.get("learning") != new_l.get("learning") or ex.get("author") != new_l.get("author"):
            continue
        ts_str = ex.get("timestamp")
        if ts_str:
            try:
                if datetime.fromisoformat(ts_str) > cutoff:
                    return True
            except (ValueError, TypeError):
                return True
        else:
            return True
    return False


@router.post("/receive")
async def receive_gossip(req: GossipReceiveRequest):
    existing = _list_learnings(limit=200)
    new_count = 0
    for learning in req.learnings:
        if _is_duplicate(learning, existing):
            continue
        learning["gossip_source"] = req.sender
        learning["gossip_received"] = datetime.now(timezone.utc).isoformat()
        if "id" not in learning:
            all_ids = [e.get("id", 0) for e in existing]
            learning["id"] = max(all_ids + [0]) + 1
        _append_learning(learning)
        existing.append(learning)
        new_count += 1
    return {"status": "received", "total": len(req.learnings), "new": new_count}


@router.post("/broadcast")
async def broadcast_gossip():
    peers = _load_peers()
    if not peers:
        return {"status": "no_peers"}
    learnings = _list_learnings(limit=50)
    if not learnings:
        return {"status": "no_learnings", "peers": len(peers)}
    self_url = os.getenv("SAAS_PUBLIC_URL", "http://localhost:8001")
    results = []
    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        for peer in peers:
            try:
                resp = await client.post(
                    f"{peer}/hooks/learnings/gossip/receive",
                    json={"learnings": learnings, "sender": self_url},
                )
                resp.raise_for_status()
                results.append({"peer": peer, "status": "success"})
            except Exception as e:
                results.append({"peer": peer, "status": "failed", "error": str(e)})
    return {"status": "broadcast_complete", "results": results}


@router.get("/status")
async def gossip_status():
    return {
        "worker_running": gossip_worker_running,
        "last_run": last_gossip_run,
        "peers_count": len(_load_peers()),
        "learnings_count": len(_list_learnings(limit=99999)),
    }
