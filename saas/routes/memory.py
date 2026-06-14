"""Memory & Session Archive API — boot context generation + archive CRUD."""
import json
import re
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

router = APIRouter()

ARCHIVE_DIR = Path.home() / ".claude" / "PAI" / "MEMORY" / "ARCHIVES"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

BOOT_CONTEXT_PATH = ARCHIVE_DIR / "boot_context.md"
DEFAULT_LIMIT = 5


class ArchiveEntry(BaseModel):
    title: str
    summary: str
    milestones: list[str] = []
    takeaways: list[str] = []
    interactions: list[str] = []
    pai_metrics: dict = {}
    tags: list[str] = []
    slug: str = ""


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower().strip()).strip("-")
    return s[:48] or "archive"


def format_archive_md(entry: ArchiveEntry, timestamp: str, session_id: str) -> str:
    m = entry.pai_metrics or {}
    return f"""── MEMORY_EVENT // {entry.title.upper()} // SESSION_{session_id[:8]} ──
── {timestamp[:19].replace("T", " // ")} ──

── 0.1 // EXECUTIVE SUMMARY
{entry.summary}

── 0.2 // PROJECT MILESTONES
""" + "\n".join(f"{'- ' + m if m.startswith('-') else '- ' + m}" for m in entry.milestones) + f"""

── 0.3 // REGISTRY OF KEY TAKEAWAYS
""" + "\n".join(f"{'- ' + t if t.startswith('-') else '- ' + t}" for t in entry.takeaways) + f"""

── 0.4 // TO-DO // DEVELOPMENT PIPELINE
""" + "\n".join(f"{'- ' + i if i.startswith('-') else '- ' + i}" for i in entry.interactions if "todo" in i.lower() or "pipeline" in i.lower() or "next" in i.lower()) + f"""

── 0.5 // SUMMARY OF INTERACTIONS
""" + "\n".join(f"{'- ' + i if i.startswith('-') else '- ' + i}" for i in entry.interactions if not ("todo" in i.lower() or "pipeline" in i.lower())) + f"""

── 0.6 // PAI_SUPPORT_SIGNAL
╔════════════════════════════════════════════════════════════════╗
║ PAI // METRICS: {m.get('efficiency_gain', 'N/A')} | Tokens Saved: {m.get('tokens_saved', 'N/A')}     ║
╠════════════════════════════════════════════════════════════════╣
║ SAAS MANIFEST: VAN_Engine Stack // PAI_Algorithm v3.8.2       ║
║ Repo: https://github.com/Agizilla/VAN_Engine                  ║
╠════════════════════════════════════════════════════════════════╣
║ COLLABORATION // DONATION:                                     ║
║ [PayPal/Collab-Contact Info]                                   ║
╚════════════════════════════════════════════════════════════════╝
"""


def scan_simulations_manifest() -> list[dict]:
    """Extract simulations from the inline HTML index in simulations.py."""
    sim_path = Path(__file__).parent / "simulations.py"
    if not sim_path.exists():
        return []
    text = sim_path.read_text(encoding="utf-8")
    cards = []

    # Match card blocks: <div class="card" onclick="window.location='...'"> ... </div>
    card_pattern = re.compile(
        r'<div class="card"[^>]*onclick=\'window\.location=[\'"](/hooks/ui/simulations/[^\'"]+)[\'"]\'[^>]*>'
        r'(.*?)</div>',
        re.DOTALL,
    )
    tag_pattern = re.compile(r'<span class="tag">([^<]+)</span>')

    for match in card_pattern.finditer(text):
        route = match.group(1)
        body = match.group(2)
        title_m = re.search(r"<h2>(.+?)</h2>", body)
        desc_m = re.search(r"<p>(.+?)</p>", body)
        tags = tag_pattern.findall(body)
        cards.append({
            "route": route.replace("/hooks/ui/simulations/", ""),
            "title": title_m.group(1).strip() if title_m else "Untitled",
            "description": re.sub(r"<[^>]+>", "", desc_m.group(1)).strip()[:160] if desc_m else "",
            "tags": tags,
        })
    return cards


def build_boot_context() -> str:
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# BOOT_CONTEXT — Generated {now}",
        "",
        "## SESSION ARCHIVES",
        "",
    ]

    # Recent archives
    archives = sorted(ARCHIVE_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    archives = [p for p in archives if p.name != "boot_context.md"]
    for a_path in archives[:DEFAULT_LIMIT]:
        content = a_path.read_text(encoding="utf-8")
        title_match = re.search(r"^── MEMORY_EVENT // (.+?) //", content)
        title = title_match.group(1) if title_match else a_path.stem
        summary_match = re.search(r"── 0\.1 // EXECUTIVE SUMMARY\n(.+?)\n\n──", content, re.DOTALL)
        summary = summary_match.group(1).strip()[:200] if summary_match else "(no summary)"
        lines.append(f"- **{title}** — {a_path.name}")
        lines.append(f"  {summary}")
        lines.append("")

    # Simulations manifest
    lines.append("## SIMULATIONS MANIFEST")
    lines.append("")
    sims = scan_simulations_manifest()
    for s in sims:
        lines.append(f"- **{s['title']}** → `/hooks/ui/simulations/{s['route']}`")
        lines.append(f"  {s['description']}")
        lines.append("")

    # File path index
    lines.append("## FILE PATH INDEX")
    lines.append("")
    lines.append("| Component | Path |")
    lines.append("|-----------|------|")
    lines.append("| SAAS Server | `saas/server.py` |")
    lines.append("| Simulations Routes | `saas/routes/simulations.py` |")
    lines.append("| TTS Engine | `saas/routes/tts.py` |")
    lines.append("| Memory API | `saas/routes/memory.py` |")
    lines.append("| Vector CD Player | `saas/static/simulations/aras/ara-vector-comic-cd-player.html` |")
    lines.append("| Vector Landscape | `saas/static/simulations/aras/ara-vector-landscape-v4.html` |")
    lines.append("| FRYA SVG | `saas/static/simulations/aras/ara-frya-hologram.html` |")
    lines.append("| FRYA Canvas | `saas/static/simulations/aras/ara-frya-canvas-v5.html` |")
    lines.append("| Mesh Dashboard | `saas/static/simulations/aras/ara-mesh-dashboard.html` |")
    lines.append("| Prime Companion | `deepseek_html_20260613_6374ca.html` |")
    lines.append("| Skills Manager | `saas/skills_manager.py` |")
    lines.append("")
    lines.append("*Boot context auto-generated. Refresh with `/api/memory/boot-context` or run `generate_boot_context.py`*")

    return "\n".join(lines)


@router.post("/api/memory/archive")
async def create_archive(entry: ArchiveEntry):
    timestamp = datetime.utcnow().isoformat() + "Z"
    session_id = hex(hash(timestamp + entry.title))[2:12]
    slug = entry.slug or slugify(entry.title)
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{slug}.md"
    filepath = ARCHIVE_DIR / filename

    md = format_archive_md(entry, timestamp, session_id)
    filepath.write_text(md, encoding="utf-8")

    json_path = filepath.with_suffix(".json")
    json_path.write_text(
        json.dumps({
            "session_id": session_id,
            "timestamp": timestamp,
            "title": entry.title,
            "slug": slug,
            "summary": entry.summary,
            "milestones": entry.milestones,
            "takeaways": entry.takeaways,
            "interactions": entry.interactions,
            "pai_metrics": entry.pai_metrics,
            "tags": entry.tags,
        }, indent=2),
        encoding="utf-8",
    )

    return {"status": "saved", "filename": filename, "session_id": session_id}


@router.get("/api/memory/archives")
async def list_archives(limit: int = DEFAULT_LIMIT):
    files = sorted(ARCHIVE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    archives = []
    for f in files[:limit]:
        data = json.loads(f.read_text(encoding="utf-8"))
        archives.append(data)
    return {"archives": archives}


@router.get("/api/memory/archives/{filename}")
async def get_archive(filename: str):
    fpath = ARCHIVE_DIR / filename
    if not fpath.exists():
        fpath = ARCHIVE_DIR / (filename + ".md")
    if not fpath.exists():
        raise HTTPException(404, "Archive not found")
    return PlainTextResponse(fpath.read_text(encoding="utf-8"))


@router.get("/api/memory/boot-context")
async def get_boot_context():
    context = build_boot_context()
    BOOT_CONTEXT_PATH.write_text(context, encoding="utf-8")
    return PlainTextResponse(context)
