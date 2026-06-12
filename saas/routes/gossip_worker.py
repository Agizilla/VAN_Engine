"""Background gossip exchange worker — runs hourly, broadcasts learnings to peers."""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_PEERS_FILE = Path.home() / ".claude" / "PAI" / "LEARNINGS" / "peers.json"
_LEARNINGS_FILE = Path.home() / ".claude" / "PAI" / "LEARNINGS" / "algorithm_learnings.jsonl"

last_run: str | None = None
_running = False


def _load_peers() -> list[str]:
    if _PEERS_FILE.exists():
        data = json.loads(_PEERS_FILE.read_text(encoding="utf-8"))
        return data.get("peers", [])
    return []


def _list_learnings(limit: int = 50) -> list[dict]:
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


async def _gossip_once():
    global last_run
    peers = _load_peers()
    if not peers:
        return
    learnings = _list_learnings(limit=50)
    if not learnings:
        return
    self_url = os.getenv("SAAS_PUBLIC_URL", "http://localhost:8001")
    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        for peer in peers:
            try:
                await client.post(
                    f"{peer}/hooks/learnings/gossip/receive",
                    json={"learnings": learnings, "sender": self_url},
                    timeout=20.0,
                )
                logger.info("Gossiped to %s", peer)
            except Exception as e:
                logger.debug("Gossip to %s failed: %s", peer, e)
    last_run = datetime.now(timezone.utc).isoformat()


async def run_worker(interval_seconds: int = 3600):
    global _running
    _running = True
    while _running:
        await asyncio.sleep(interval_seconds)
        try:
            await _gossip_once()
        except Exception as e:
            logger.error("Gossip worker error: %s", e)
    _running = False


def stop_worker():
    global _running
    _running = False
