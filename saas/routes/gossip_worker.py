"""Background gossip exchange worker — runs hourly, broadcasts learnings to peers."""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

import httpx

logger = logging.getLogger(__name__)

_PEERS_FILE = Path.home() / ".claude" / "PAI" / "LEARNINGS" / "peers.json"
_LEARNINGS_FILE = Path.home() / ".claude" / "PAI" / "LEARNINGS" / "algorithm_learnings.jsonl"

last_run: str | None = None


def _load_peers() -> List[str]:
    if _PEERS_FILE.exists():
        data = json.loads(_PEERS_FILE.read_text(encoding="utf-8"))
        return data.get("peers", [])
    return []


def _list_recent_learnings(limit: int = 50) -> List[Dict]:
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


async def gossip_broadcast_to_all_peers(self_url: str) -> dict:
    peers = _load_peers()
    if not peers:
        return {"status": "no_peers", "peers": 0}
    learnings = _list_recent_learnings(limit=50)
    if not learnings:
        return {"status": "no_learnings", "peers": len(peers)}
    results = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for peer in peers:
            try:
                resp = await client.post(
                    f"{peer}/hooks/learnings/gossip/receive",
                    json={"learnings": learnings, "sender": self_url},
                    timeout=10.0,
                )
                resp.raise_for_status()
                results.append({"peer": peer, "status": "success"})
                logger.info("Gossiped to %s", peer)
            except Exception as e:
                results.append({"peer": peer, "status": "failed", "error": str(e)})
                logger.debug("Gossip to %s failed: %s", peer, e)
    return {"status": "complete", "total_peers": len(peers), "results": results}


async def background_gossip_worker(interval_seconds: int = 3600, shutdown_event: asyncio.Event = None):
    self_url = os.getenv("SAAS_PUBLIC_URL", "http://localhost:8001")
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            if shutdown_event and shutdown_event.is_set():
                break
            await gossip_broadcast_to_all_peers(self_url)
            global last_run
            last_run = datetime.now(timezone.utc).isoformat()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Gossip worker error: %s", e)
