"""
Project ingest endpoint.
POST /api/project/ingest — receive .pyp JSON, extract keywords, write to disk, commit to GitHub, gossip.
GET  /api/projects       — list ingested projects, optional ?keywords= filter.
"""
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent / "data" / "projects"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GIT_REPO = Path(__file__).parent.parent.parent

STOPWORDS = {"the", "a", "an", "and", "or", "of", "to", "for", "in", "on",
             "at", "with", "by", "is", "are", "was", "were", "be", "been",
             "being", "have", "has", "had", "having", "do", "does", "did",
             "doing", "but", "so", "if", "then", "else", "when", "where",
             "which", "while", "who", "whom", "this", "that", "these",
             "those", "such", "as", "into", "through", "during", "before",
             "after", "above", "below", "between", "under", "over", "etc",
             "project", "file", "files", "use", "using", "used", "set"}


class ProjectIngestRequest(BaseModel):
    pypVersion: str = "1.0.0"
    projectName: str
    description: str = ""
    createdAt: str = ""
    mainEntry: str = ""
    requiredArgs: list[str] = []
    isWebProject: bool = False
    setupScript: str | None = None
    mdFiles: list[dict] = []
    pyFiles: list[dict] = []
    htmlFiles: list[dict] = []
    txtFiles: list[dict] = []
    prdFiles: list[dict] = []
    artifacts: list[str] = []
    inputs: list[str] = []
    other: list[str] = []


def extract_keywords(data: dict) -> list[str]:
    kw = set()

    name = data.get("projectName", "")
    kw.update(name.lower().split())

    desc = data.get("description", "")
    kw.update(w for w in desc.lower().split()[:15] if len(w) > 2)

    main_entry = data.get("mainEntry", "")
    if main_entry.endswith(".py"):
        kw.add("python")
    elif main_entry.endswith(".html"):
        kw.add("web")
    elif main_entry.endswith(".js") or main_entry.endswith(".ts"):
        kw.add("javascript")

    if data.get("pyFiles"):
        kw.add("python")
    if data.get("htmlFiles"):
        kw.add("web")

    for md in data.get("mdFiles", []):
        c = md.get("content", "").lower()
        if "opencv" in c or "cv2" in c:
            kw.add("opencv")
        if "mediapipe" in c:
            kw.add("mediapipe")
        if "3d" in c or "mesh" in c or "three.js" in c:
            kw.add("3d")
        if "avatar" in c or "face" in c:
            kw.add("face-avatar")
        if "pygame" in c or "opengl" in c:
            kw.add("graphics")
        if "tensorflow" in c or "pytorch" in c or "keras" in c:
            kw.add("ml")
        if "flask" in c or "fastapi" in c or "django" in c:
            kw.add("backend")
        if "react" in c or "vue" in c or "angular" in c:
            kw.add("frontend")

    for txt in data.get("txtFiles", []):
        fn = txt.get("filename", "").lower()
        c = txt.get("content", "").lower()
        if "requirements.txt" in fn:
            for lib in ["opencv", "mediapipe", "numpy", "pygame", "flask",
                        "fastapi", "django", "torch", "tensorflow", "pillow",
                        "requests", "httpx", "pydantic"]:
                if lib in c:
                    kw.add(lib)
        if "package.json" in fn:
            kw.add("npm")
            kw.add("javascript")

    for art in data.get("artifacts", []):
        if art.endswith(".bat"):
            kw.add("windows")
        elif art.endswith(".sh"):
            kw.add("linux")

    kw = {k for k in kw if k not in STOPWORDS and len(k) > 2}
    return sorted(kw)


def _write_project_files(project_name: str, data: dict) -> tuple[Path, list[str]]:
    project_dir = DATA_DIR / project_name
    if project_dir.exists():
        import shutil
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    category_dirs = {
        "mdFiles": "docs", "pyFiles": "src", "htmlFiles": "ui",
        "txtFiles": "config", "prdFiles": "prd",
    }

    for category, subdir in category_dirs.items():
        for entry in data.get(category, []):
            if isinstance(entry, dict) and "filename" in entry and "content" in entry:
                fpath = project_dir / subdir / entry["filename"]
                fpath.parent.mkdir(parents=True, exist_ok=True)
                fpath.write_text(entry["content"], encoding="utf-8")

    keywords = extract_keywords(data)

    metadata = {
        "pypVersion": data.get("pypVersion", "1.0.0"),
        "projectName": project_name,
        "description": data.get("description", ""),
        "createdAt": data.get("createdAt", datetime.now(timezone.utc).isoformat()),
        "mainEntry": data.get("mainEntry", ""),
        "isWebProject": data.get("isWebProject", False),
        "setupScript": data.get("setupScript"),
        "artifacts": data.get("artifacts", []),
        "inputs": data.get("inputs", []),
        "other": data.get("other", []),
        "keywords": keywords,
        "ingestedAt": datetime.now(timezone.utc).isoformat(),
        "fileCount": sum(len(data.get(c, [])) for c in category_dirs),
    }
    (project_dir / ".metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (project_dir / ".keywords.json").write_text(json.dumps({"keywords": keywords}, indent=2), encoding="utf-8")
    return project_dir, keywords


def _git_commit(project_name: str, keywords: list[str]) -> dict:
    rel_path = f"data/projects/{project_name}"
    try:
        subprocess.run(["git", "add", rel_path], cwd=str(GIT_REPO), capture_output=True, timeout=30, check=False)
        kw_tag = " ".join(keywords[:5])
        result = subprocess.run(
            ["git", "commit", "-m", f"feat(project): {project_name} — {kw_tag}"],
            cwd=str(GIT_REPO), capture_output=True, timeout=30, check=False
        )
        sha_result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(GIT_REPO), capture_output=True, timeout=15, check=False)
        commit_sha = sha_result.stdout.decode("utf-8", errors="replace").strip() if sha_result.returncode == 0 else "unknown"

        if result.returncode == 0:
            return {"committed": True, "sha": commit_sha, "message": result.stdout.decode("utf-8", errors="replace").strip()}
        else:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            if "nothing to commit" in stderr:
                return {"committed": False, "sha": commit_sha, "message": "nothing to commit"}
            return {"committed": False, "sha": commit_sha, "message": stderr}
    except subprocess.TimeoutExpired:
        return {"committed": False, "sha": "", "message": "timeout"}
    except Exception as e:
        return {"committed": False, "sha": "", "message": str(e)}


async def _gossip_project(project_name: str, keywords: list[str]):
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://localhost:8001/hooks/learnings/gossip/receive",
                json={
                    "learnings": [{
                        "learning": f"New project ingested: {project_name} — keywords: {', '.join(keywords[:8])}",
                        "author": "SAAS/ingestor",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "project_ingest",
                        "tags": ["project", project_name] + keywords[:5],
                    }],
                    "sender": "http://localhost:8001",
                },
            )
            resp.raise_for_status()
    except Exception as e:
        logger.debug("Gossip broadcast failed: %s", e)


@router.post("/api/project/ingest")
async def project_ingest(req: ProjectIngestRequest, background: BackgroundTasks):
    project_name = req.projectName.strip().replace(" ", "_").replace("/", "_")
    if not project_name:
        raise HTTPException(status_code=400, detail="projectName is required")

    data = req.model_dump()
    project_dir, keywords = _write_project_files(project_name, data)
    git_result = _git_commit(project_name, keywords)
    background.add_task(_gossip_project, project_name, keywords)

    return {
        "status": "ingested",
        "projectName": project_name,
        "keywords": keywords,
        "path": str(project_dir.relative_to(GIT_REPO) if project_dir.is_relative_to(GIT_REPO) else project_dir),
        "fileCount": metadata["fileCount"] if (metadata := json.loads((project_dir / ".metadata.json").read_text())) else 0,
        "git": git_result,
        "gossip": "queued",
    }


@router.get("/api/projects")
async def list_projects(keywords: str | None = None):
    projects = []
    for pdir in sorted(DATA_DIR.iterdir()):
        if not pdir.is_dir():
            continue
        meta_path = pdir / ".metadata.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            meta = {"projectName": pdir.name, "description": "", "keywords": []}
        if keywords:
            kw_lower = keywords.lower()
            names = [meta.get("projectName", "").lower(), meta.get("description", "").lower()]
            names.extend(meta.get("keywords", []))
            if not any(kw_lower in n for n in names):
                continue
        projects.append(meta)
    return {"projects": projects, "count": len(projects)}
