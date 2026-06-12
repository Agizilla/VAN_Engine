import re
import time
from pathlib import Path
from typing import Any
from .base import BaseSkill, register_skill
from ..tools.master_skills.prdSkill import PRDSkill

_prd = PRDSkill()
_DEFAULT_ROOT = Path(__file__).parent.parent.parent.parent


_SLUG_RE = re.compile(r'^[a-zA-Z0-9\-]+$')


def _ensure_loaded(root: Path = None):
    if root is None:
        root = _DEFAULT_ROOT
    if not _prd._prds:
        _prd.scan(root)


class _PRDCache:
    _prds_cache = None
    _last_scan_time = 0.0


@register_skill("prd_scan", "prd")
class PRDScanSkill(BaseSkill):
    name = "prd_scan"
    description = "Scan directories for PRD files and return catalog"
    category = "prd"
    def execute(self, **kwargs) -> dict:
        root = Path(kwargs.get("root", _DEFAULT_ROOT))
        if kwargs.get("use_van_root"):
            from ..tools.master_skills.prdSkill import Path
            root = Path(__file__).parent.parent.parent.parent
        _PRDCache._prds_cache = None
        _PRDCache._last_scan_time = time.time()
        prds = _prd.scan(root)
        catalog = _prd.get_catalog(prds)
        for p in prds:
            p["last_modified"] = _get_mtime(p)
        catalog["last_modified"] = _PRDCache._last_scan_time
        return {"result": {"prds": prds, "catalog": catalog}}


def _get_mtime(prd: dict) -> float:
    try:
        fp = prd.get("filepath") or prd.get("file_path", "")
        if fp:
            return Path(fp).stat().st_mtime
    except OSError:
        pass
    return 0.0


@register_skill("prd_get", "prd")
class PRDGetSkill(BaseSkill):
    name = "prd_get"
    description = "Get a single PRD by slug"
    category = "prd"
    def execute(self, **kwargs) -> dict:
        slug = kwargs.get("slug", "")
        if not slug:
            return {"error": "slug required"}
        if not _SLUG_RE.match(slug):
            return {"error": f"Invalid slug: {slug}"}
        _ensure_loaded(Path(kwargs.get("root", _DEFAULT_ROOT)))
        prd = next((p for p in _prd._prds if p["slug"] == slug), None)
        if not prd:
            return {"error": f"PRD not found: {slug}"}
        result = dict(prd)
        result["last_modified"] = _get_mtime(prd)
        return {"result": result}


@register_skill("prd_search", "prd")
class PRDSearchSkill(BaseSkill):
    name = "prd_search"
    description = "Search PRDs by keyword"
    category = "prd"
    def execute(self, **kwargs) -> dict:
        query = kwargs.get("query", "")
        if not query:
            return {"error": "query required"}
        _ensure_loaded(Path(kwargs.get("root", _DEFAULT_ROOT)))
        results = _prd.search(query)
        for r in results:
            r["last_modified"] = _get_mtime(r)
        return {"result": {"query": query, "count": len(results), "results": results}}


@register_skill("prd_timeline", "prd")
class PRDTimelineSkill(BaseSkill):
    name = "prd_timeline"
    description = "Get timeline data for all PRDs"
    category = "prd"
    def execute(self, **kwargs) -> dict:
        _ensure_loaded(Path(kwargs.get("root", _DEFAULT_ROOT)))
        timeline = _prd.get_timeline()
        return {"result": {"timeline": timeline, "count": len(timeline)}}


@register_skill("prd_catalog", "prd")
class PRDCatalogSkill(BaseSkill):
    name = "prd_catalog"
    description = "Get aggregated PRD catalog with stats"
    category = "prd"
    def execute(self, **kwargs) -> dict:
        _ensure_loaded(Path(kwargs.get("root", _DEFAULT_ROOT)))
        catalog = _prd.get_catalog()
        catalog["last_modified"] = _PRDCache._last_scan_time
        return {"result": catalog}


@register_skill("prd_artifacts", "prd")
class PRDArtifactsSkill(BaseSkill):
    name = "prd_artifacts"
    description = "Get artifacts from a specific PRD"
    category = "prd"
    def execute(self, **kwargs) -> dict:
        slug = kwargs.get("slug", "")
        if not slug:
            return {"error": "slug required"}
        if not _SLUG_RE.match(slug):
            return {"error": f"Invalid slug: {slug}"}
        _ensure_loaded(Path(kwargs.get("root", _DEFAULT_ROOT)))
        artifacts = _prd.get_artifacts_for(slug)
        return {"result": {"slug": slug, "artifacts": artifacts}}


@register_skill("prd_orphans", "prd")
class PRDOrphansSkill(BaseSkill):
    name = "prd_orphans"
    description = "Detect orphaned/outdated PRDs"
    category = "prd"
    def execute(self, **kwargs) -> dict:
        _ensure_loaded(Path(kwargs.get("root", _DEFAULT_ROOT)))
        orphans = _prd.detect_orphaned()
        return {"result": {"orphans": orphans, "count": len(orphans)}}


@register_skill("prd_render_html", "prd")
class PRDRenderHtmlSkill(BaseSkill):
    name = "prd_render_html"
    description = "Render a PRD as HTML"
    category = "prd"
    def execute(self, **kwargs) -> dict:
        slug = kwargs.get("slug", "")
        if not slug:
            return {"error": "slug required"}
        if not _SLUG_RE.match(slug):
            return {"error": f"Invalid slug: {slug}"}
        _ensure_loaded(Path(kwargs.get("root", _DEFAULT_ROOT)))
        html = _prd.render_html(slug)
        return {"result": {"slug": slug, "html": html}}


@register_skill("prd_info", "prd")
class PRDInfoSkill(BaseSkill):
    name = "prd_info"
    description = "Get PRDSkill metadata and capabilities"
    category = "prd"
    def execute(self, **kwargs) -> dict:
        meta = _prd.get_meta()
        caps = _prd.get_capabilities()
        return {"result": {"meta": meta, "capabilities": caps}}
