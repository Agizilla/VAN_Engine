"""GitHub Watchdog — poll user repos, cache, detect new repos."""
import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

_REPO_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_LOCK = threading.Lock()


def _gh_api(endpoint: str) -> list | dict:
    cmd = ["gh", "api", endpoint]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"gh api timed out: {endpoint}")
    if result.returncode != 0:
        raise RuntimeError(f"gh api {endpoint} failed: {result.stderr.strip()}")
    out = result.stdout.strip()
    if not out:
        return []
    return json.loads(out)


def fetch_user_repos(username: str) -> list[dict]:
    repos = _gh_api(f"/users/{username}/repos?per_page=100&sort=created&direction=desc")
    if not isinstance(repos, list):
        repos = []
    return [{
        "name": r.get("name"),
        "full_name": r.get("full_name"),
        "private": r.get("private", False),
        "description": r.get("description", ""),
        "url": r.get("html_url", ""),
        "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0),
        "language": r.get("language", ""),
        "created_at": r.get("created_at", ""),
        "pushed_at": r.get("pushed_at", ""),
    } for r in repos]


def _poll_user_repos(username: str):
    try:
        repos = fetch_user_repos(username)
        repo_names = {r["name"] for r in repos}
        with _CACHE_LOCK:
            cached = _REPO_CACHE.get(username, {})
            prev_names = set(cached.get("repos", []))
            new_repos = repo_names - prev_names

            _REPO_CACHE[username] = {
                "repos": list(repo_names),
                "repo_data": repos,
                "last_fetched": datetime.now(timezone.utc).isoformat(),
                "count": len(repos),
            }

            if new_repos:
                logger.info("Watchdog detected new repos for %s: %s", username, ", ".join(new_repos))
                _REPO_CACHE[username]["new_repos"] = list(new_repos)

            return new_repos
    except Exception as e:
        logger.error("Watchdog poll failed for %s: %s", username, e)
        return set()


def _watchdog_loop(username: str, interval: int = 60):
    while True:
        time.sleep(interval)
        _poll_user_repos(username)


def start_watchdog(username: str, interval: int = 60):
    thread = threading.Thread(target=_watchdog_loop, args=(username, interval), daemon=True)
    thread.start()
    logger.info("Watchdog started for %s (interval=%ds)", username, interval)


@router.get("/hooks/github_watch/{username}")
def get_watch_status(username: str):
    with _CACHE_LOCK:
        cached = _REPO_CACHE.get(username)

    if cached:
        result = dict(cached)
        result.pop("repo_data", None)
        result["new_repos"] = result.get("new_repos", [])
        return {"user": username, "cached": True, **result}

    repos = fetch_user_repos(username)
    repo_names = [r["name"] for r in repos]
    with _CACHE_LOCK:
        _REPO_CACHE[username] = {
            "repos": repo_names,
            "repo_data": repos,
            "last_fetched": datetime.now(timezone.utc).isoformat(),
            "count": len(repos),
        }
    return {"user": username, "cached": False, "repos": repo_names, "count": len(repos), "last_fetched": _REPO_CACHE[username]["last_fetched"]}


@router.post("/hooks/github_watch/{username}/poll")
def trigger_poll(username: str):
    new = _poll_user_repos(username)
    if new:
        return {"user": username, "new_repos": list(new), "new_count": len(new)}
    return {"user": username, "new_repos": [], "new_count": 0}


@router.post("/hooks/github_watch/{username}/start")
def start_watch(username: str, interval: int = 60):
    start_watchdog(username, interval)
    return {"user": username, "interval": interval, "status": "started"}
