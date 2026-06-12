import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class PRDSkill:
    __meta__ = {
        "description": "Master PRD Catalog Skill — scan, parse, categorize, and produce professional PRD catalogs across project directories",
        "how_to": "from tools.master_skills.prdSkill import PRDSkill",
        "version": "1.0.0",
        "dateCreated": "2026-06-07",
        "dateLastModified": "2026-06-07",
        "countPublicMethods": 14,
        "countLineNumbers": 0,
        "mergedProjects": 0,
        "update_list": "Initial release — PRD scanning, parsing, categorization, catalog generation",
        "capabilities": [
            "Scan directories for PRD files",
            "Parse YAML frontmatter",
            "Extract sections (Context, Criteria, Decisions, Verification, Artifacts)",
            "Extract artifact file paths",
            "Categorize PRDs by effort, phase, status",
            "Sort by date (timeline)",
            "Generate timeline JSON data",
            "Search PRDs by keyword",
            "Export to JSON catalog",
            "Render PRD to HTML",
            "Detect orphaned/outdated PRDs"
        ]
    }

    PRD_PATTERNS = [
        "**/PRD.md",
        "**/PRD_*.md",
        "**/*.prd",
        "**/*PRD*.md"
    ]

    def __init__(self, scan_root: Optional[Path] = None):
        self._scan_root = scan_root or Path.cwd()
        self._prds: list[dict] = []
        self._artifacts_index: dict[str, list[str]] = {}

    def _parse_frontmatter(self, content: str) -> dict:
        fm = {}
        m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if m:
            for line in m.group(1).strip().split('\n'):
                mo = re.match(r'^(\w+):\s*(.*)', line)
                if mo:
                    key = mo.group(1)
                    val = mo.group(2).strip()
                    fm[key] = val
        return fm

    def _parse_sections(self, content: str) -> dict[str, str]:
        sections = {}
        pattern = re.compile(r'^##\s+(.+)$', re.MULTILINE)
        matches = list(pattern.finditer(content))
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            title = m.group(1).strip()
            body = content[start:end].strip()
            sections[title] = body
        return sections

    def _extract_artifacts(self, content: str) -> list[str]:
        artifacts = []
        patterns = [
            r'`([^`]+\.[a-zA-Z]+)`',
            r'\*\*File:\*\*\s*`([^`]+)`',
            r'\|?\s*`([^`]+\.(py|ts|js|tsx|jsx|html|css|json|yaml|yml|md|toml|cfg|ini))`',
            r'`([^`]+/(?:src|lib|tools|skills|ipc|preload|renderer)/[^`]+)`'
        ]
        for pat in patterns:
            for m in re.finditer(pat, content):
                p = m.group(1)
                if len(p) > 5 and p not in artifacts:
                    artifacts.append(p)
        return artifacts

    def scan(self, root: Optional[Path] = None) -> list[dict]:
        root = Path(root) if root else self._scan_root
        if not root.exists():
            return []
        self._prds = []
        self._artifacts_index = {}
        seen = set()
        for pat in self.PRD_PATTERNS:
            for fp in sorted(root.glob(pat)):
                try:
                    rp = str(fp.relative_to(root))
                except ValueError:
                    rp = str(fp)
                if rp in seen:
                    continue
                seen.add(rp)
                try:
                    raw = fp.read_text(encoding='utf-8', errors='replace')
                except Exception:
                    continue
                fm = self._parse_frontmatter(raw)
                sections = self._parse_sections(raw)
                arts = self._extract_artifacts(raw)
                slug = fm.get('slug', fp.stem)
                phase = fm.get('phase', 'unknown')
                effort = fm.get('effort', 'standard')
                progress = fm.get('progress', '0/0')
                started = fm.get('started', '')
                updated = fm.get('updated', '')
                task = fm.get('task', fp.stem)

                self._artifacts_index[slug] = arts
                self._prds.append({
                    "slug": slug,
                    "task": task,
                    "effort": effort,
                    "phase": phase,
                    "progress": progress,
                    "started": started,
                    "updated": updated,
                    "file_path": rp,
                    "artifact_count": len(arts),
                    "artifacts": arts,
                    "char_count": len(raw),
                    "sections": list(sections.keys()),
                    "section_content": sections,
                    "frontmatter": fm,
                    "raw": raw
                })
        self._prds.sort(key=lambda p: p.get('started', ''), reverse=True)
        return self._prds

    def get_timeline(self, prds: Optional[list[dict]] = None) -> list[dict]:
        items = prds if prds is not None else self._prds
        timeline = []
        for p in items:
            started = p.get('started', '')
            if not started:
                continue
            try:
                dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                ts = int(dt.timestamp())
            except Exception:
                try:
                    dt = datetime.strptime(started[:10], '%Y-%m-%d')
                    ts = int(dt.timestamp())
                except Exception:
                    ts = 0
            timeline.append({
                "timestamp": ts,
                "date": dt.strftime('%Y-%m-%d %H:%M') if 'dt' in dir() else started[:10],
                "slug": p["slug"],
                "task": p["task"],
                "phase": p["phase"],
                "effort": p["effort"],
                "progress": p["progress"],
                "artifact_count": p["artifact_count"]
            })
        timeline.sort(key=lambda t: t["timestamp"])
        return timeline

    def get_catalog(self, prds: Optional[list[dict]] = None) -> dict:
        items = prds if prds is not None else self._prds
        by_effort: dict[str, list[dict]] = {}
        by_phase: dict[str, list[dict]] = {}
        for p in items:
            eff = p.get('effort', 'unknown')
            ph = p.get('phase', 'unknown')
            by_effort.setdefault(eff, []).append(p["slug"])
            by_phase.setdefault(ph, []).append(p["slug"])
        return {
            "total": len(items),
            "by_effort": by_effort,
            "by_phase": by_phase,
            "timeline": self.get_timeline(items),
            "artifacts_total": sum(p["artifact_count"] for p in items)
        }

    def search(self, query: str, prds: Optional[list[dict]] = None) -> list[dict]:
        q = query.lower()
        items = prds if prds is not None else self._prds
        results = []
        for p in items:
            if q in p["task"].lower() or q in p["slug"].lower() or q in p.get('raw', '').lower():
                results.append(p)
        return results

    def render_html(self, slug: str, prds: Optional[list[dict]] = None) -> str:
        items = prds if prds is not None else self._prds
        prd = next((p for p in items if p["slug"] == slug), None)
        if not prd:
            return "<div class='error'>PRD not found</div>"
        fm = prd["frontmatter"]
        sections = prd.get("section_content", {})
        arts = prd.get("artifacts", [])
        html_parts = [
            "<div class='prd-render'>",
            "<div class='prd-header'>",
            f"<h1>{fm.get('task', 'Untitled')}</h1>",
            "<div class='prd-meta-bar'>",
            *[f"<span class='prd-tag tag-{v}'>{k}: {v}</span>" for k, v in
              [("effort", fm.get('effort', '?')), ("phase", fm.get('phase', '?')),
               ("progress", fm.get('progress', '?')), ("mode", fm.get('mode', '?'))]],
            "</div></div>"
        ]
        for title, body in sections.items():
            html_parts.append(f"<div class='prd-section'><h2>{title}</h2><div class='prd-body'>{self._md_to_html(body)}</div></div>")
        if arts:
            html_parts.append("<div class='prd-section artifacts'><h2>Artifacts</h2><ul class='artifact-list'>")
            for a in arts:
                html_parts.append(f"<li><code>{a}</code></li>")
            html_parts.append("</ul></div>")
        html_parts.append("</div>")
        return '\n'.join(html_parts)

    def _md_to_html(self, text: str) -> str:
        text = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code>\2</code></pre>', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
        text = re.sub(r'\n\n', r'</p><p>', text)
        text = f'<p>{text}</p>'
        return text

    def get_artifacts_for(self, slug: str) -> list[str]:
        return self._artifacts_index.get(slug, [])

    def get_all_artifacts(self) -> dict[str, list[str]]:
        return dict(self._artifacts_index)

    def detect_orphaned(self, prds: Optional[list[dict]] = None) -> list[dict]:
        items = prds if prds is not None else self._prds
        orphans = []
        for p in items:
            try:
                dt = datetime.fromisoformat(p.get('updated', '').replace('Z', '+00:00'))
                age_days = (datetime.now().astimezone() - dt).days
            except Exception:
                age_days = 0
            if age_days > 90 and p.get('phase') != 'complete':
                orphans.append({"slug": p["slug"], "age_days": age_days, "phase": p["phase"]})
        return orphans

    def get_capabilities(self) -> list[str]:
        return list(self.__meta__["capabilities"])

    def get_meta(self) -> dict:
        meta = dict(self.__meta__)
        if self._prds:
            meta["cached_prds"] = len(self._prds)
            meta["cached_artifacts"] = sum(len(v) for v in self._artifacts_index.values())
        return meta

    def export_json(self, prds: Optional[list[dict]] = None) -> str:
        items = prds if prds is not None else self._prds
        return json.dumps(self.get_catalog(items), indent=2, default=str)
