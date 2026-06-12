import re
import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class PRDSkill:
    __meta__ = {
        "description": "Master PRD Catalog Skill — scan, parse, categorize, and produce professional PRD catalogs across project directories",
        "how_to": "from tools.master_skills.prdSkill import PRDSkill",
        "version": "2.0.0",
        "dateCreated": "2026-06-07",
        "dateLastModified": "2026-06-10",
        "countPublicMethods": 14,
        "countLineNumbers": 0,
        "mergedProjects": 0,
        "update_list": "v2.0.0 — frontmatter validation, watch mode, caching, slug normalization, nested sections, artifact existence check",
        "capabilities": [
            "Scan directories for PRD files",
            "Parse YAML frontmatter",
            "Validate YAML frontmatter",
            "Extract sections (Context, Criteria, Decisions, Verification, Artifacts)",
            "Nested section parsing (## Context > Subsection)",
            "Extract artifact file paths",
            "Artifact existence checking",
            "Categorize PRDs by effort, phase, status",
            "Sort by date (timeline)",
            "Generate timeline JSON data",
            "Search PRDs by keyword",
            "Export to JSON catalog",
            "Render PRD to HTML",
            "Detect orphaned/outdated PRDs",
            "Watch mode for directory changes"
        ]
    }

    PRD_PATTERNS = [
        "**/PRD.md",
        "**/PRD_*.md",
        "**/*.prd",
        "**/*PRD*.md"
    ]

    REQUIRED_FRONTMATTER_FIELDS = ["slug", "task", "effort", "phase"]

    def __init__(self, scan_root: Optional[Path] = None, cache_file: Optional[Path] = None):
        self._scan_root = scan_root or Path.cwd()
        self._prds: list[dict] = []
        self._artifacts_index: dict[str, list[str]] = {}
        self._cache_file = cache_file or (self._scan_root / "prd_cache.json")
        self._watcher = None

    def _normalize_slug(self, slug: str) -> str:
        slug = slug.lower().replace(' ', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        return slug

    def validate_frontmatter(self, content: str) -> tuple[bool, list[str]]:
        fm = self._parse_frontmatter(content)
        missing = [f for f in self.REQUIRED_FRONTMATTER_FIELDS if f not in fm]
        return (len(missing) == 0, missing)

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

    def _parse_sections(self, content: str) -> dict[str, str | dict]:
        sections = {}
        pattern = re.compile(r'^##\s+(.+)$', re.MULTILINE)
        matches = list(pattern.finditer(content))
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            title = m.group(1).strip()
            body = content[start:end].strip()

            if ' > ' in title:
                parts = [p.strip() for p in title.split(' > ')]
                current = sections
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    if not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = body
            else:
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

    def _check_artifacts_exist(self, prd: dict, root: Path) -> list[str]:
        warnings = []
        for field in ('artifacts', 'files'):
            items = prd.get(field, [])
            if isinstance(items, list):
                for art in items:
                    art_path = root / art
                    if not os.path.exists(str(art_path)):
                        warnings.append(f"Artifact not found: {art}")
        return warnings

    def _load_cache(self) -> dict:
        try:
            if self._cache_file and self._cache_file.exists():
                return json.loads(self._cache_file.read_text(encoding='utf-8'))
        except Exception:
            pass
        return {}

    def _save_cache(self, cache: dict):
        try:
            if self._cache_file:
                self._cache_file.parent.mkdir(parents=True, exist_ok=True)
                self._cache_file.write_text(json.dumps(cache, indent=2, default=str), encoding='utf-8')
        except Exception:
            pass

    def scan(self, root: Optional[Path] = None) -> list[dict]:
        root = Path(root) if root else self._scan_root
        if not root.exists():
            return []
        self._prds = []
        self._artifacts_index = {}
        seen = set()
        cache = self._load_cache()

        for pat in self.PRD_PATTERNS:
            for fp in sorted(root.glob(pat)):
                try:
                    rp = str(fp.relative_to(root))
                except ValueError:
                    rp = str(fp)
                if rp in seen:
                    continue
                seen.add(rp)

                cache_key = str(fp.resolve())
                mtime = fp.stat().st_mtime
                cached_entry = cache.get(cache_key, {})
                if cached_entry.get('mtime') == mtime:
                    self._prds.append(cached_entry['data'])
                    slug = cached_entry['data']['slug']
                    self._artifacts_index[slug] = cached_entry['data'].get('artifacts', [])
                    continue

                try:
                    raw = fp.read_text(encoding='utf-8', errors='replace')
                except Exception:
                    continue

                fm = self._parse_frontmatter(raw)
                sections = self._parse_sections(raw)
                arts = self._extract_artifacts(raw)
                slug = self._normalize_slug(fm.get('slug', fp.stem))
                phase = fm.get('phase', 'unknown')
                effort = fm.get('effort', 'standard')
                progress = fm.get('progress', '0/0')
                started = fm.get('started', '')
                updated = fm.get('updated', '')
                task = fm.get('task', fp.stem)

                prd_data = {
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
                }

                artifact_warnings = self._check_artifacts_exist(prd_data, root)
                if artifact_warnings:
                    prd_data['artifact_warnings'] = artifact_warnings

                cache[cache_key] = {'mtime': mtime, 'data': prd_data}

                self._artifacts_index[slug] = arts
                self._prds.append(prd_data)

        self._save_cache(cache)
        self._prds.sort(key=lambda p: p.get('started', ''), reverse=True)
        return self._prds

    def start_watch(self, root: Optional[Path] = None, callback: Optional[callable] = None):
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            raise ImportError("watchdog required: pip install watchdog")

        watch_root = Path(root) if root else self._scan_root

        class PRDHandler(FileSystemEventHandler):
            def __init__(self, skill, cb):
                self.skill = skill
                self.cb = cb

            def on_created(self, event):
                if not event.is_dir and event.src_path.endswith(('.md', '.prd')):
                    self.skill.scan()
                    if self.cb:
                        self.cb('created', event.src_path)

            def on_modified(self, event):
                if not event.is_dir and event.src_path.endswith(('.md', '.prd')):
                    self.skill.scan()
                    if self.cb:
                        self.cb('modified', event.src_path)

            def on_deleted(self, event):
                if not event.is_dir and event.src_path.endswith(('.md', '.prd')):
                    self.skill.scan()
                    if self.cb:
                        self.cb('deleted', event.src_path)

        event_handler = PRDHandler(self, callback)
        self._watcher = Observer()
        self._watcher.schedule(event_handler, str(watch_root), recursive=True)
        self._watcher.start()

    def stop_watch(self):
        if self._watcher:
            self._watcher.stop()
            self._watcher.join()
            self._watcher = None

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
