import difflib
import json
import re
from pathlib import Path
from typing import Optional

from .base import BaseSkill, SkillManifest, register_skill, SkillContext
from .intent_grid import map_intent, grid_to_label, GRID_AXES

INTENT_CACHE: dict[str, dict] = {}
_context_history: list[str] = []
_mutation_count: int = 0
INTENT_CACHE_PATH = Path(__file__).resolve().parent / "intent_cache.json"


def _save_cache():
    global _mutation_count
    try:
        INTENT_CACHE_PATH.write_text(json.dumps(INTENT_CACHE, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _load_cache():
    global INTENT_CACHE
    try:
        if INTENT_CACHE_PATH.exists():
            data = json.loads(INTENT_CACHE_PATH.read_text(encoding="utf-8"))
            INTENT_CACHE.update(data)
    except Exception:
        pass


def _valid_grid_coords(grid: dict) -> bool:
    x_cat = grid.get("x", {}).get("category")
    y_cat = grid.get("y", {}).get("category")
    z_cat = grid.get("z", {}).get("category")
    if x_cat and x_cat not in GRID_AXES.get("x", {}):
        return False
    if y_cat and y_cat not in GRID_AXES.get("y", {}):
        return False
    if z_cat and z_cat not in GRID_AXES.get("z", {}):
        return False
    return True


_load_cache()


@register_skill("intent_enricher", "intent")
class IntentEnricherSkill(BaseSkill):
    name = "intent_enricher"
    description = "Map raw intent onto 3D Isographic Grid (Action x Domain x Constraint)"
    author = "The Butler / Ara Mascarra"
    version = "1.1.0"
    category = "intent"
    tags = ["intent", "grid", "mapping", "isographic"]
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Cleaned intent text (post signal filter)"},
            "use_cache": {"type": "boolean", "default": True},
            "include_grid": {"type": "boolean", "default": True},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "intent_summary": {"type": "string"},
            "grid": {"type": "object"},
            "grid_label": {"type": "string"},
            "tokens": {"type": "array"},
        },
    }

    def execute(self, **kwargs) -> dict:
        global _mutation_count
        text = kwargs.get("text", "")
        use_cache = kwargs.get("use_cache", True)
        include_grid = kwargs.get("include_grid", True)

        if not text:
            return {"error": "No intent text provided", "result": None}

        cache_key = text.lower().strip()
        if use_cache and cache_key in INTENT_CACHE:
            return {"error": None, "result": dict(INTENT_CACHE[cache_key])}

        grid = map_intent(text) if include_grid else {}
        if include_grid and not _valid_grid_coords(grid):
            x_cat = grid.get("x", {}).get("category")
            known_x = list(GRID_AXES.get("x", {}).keys())
            if x_cat and x_cat not in GRID_AXES.get("x", {}):
                matches = difflib.get_close_matches(x_cat, known_x, n=1)
                if matches:
                    grid["x"]["category"] = matches[0]

            y_cat = grid.get("y", {}).get("category")
            known_y = list(GRID_AXES.get("y", {}).keys())
            if y_cat and y_cat not in GRID_AXES.get("y", {}):
                matches = difflib.get_close_matches(y_cat, known_y, n=1)
                if matches:
                    grid["y"]["category"] = matches[0]

            z_cat = grid.get("z", {}).get("category")
            known_z = list(GRID_AXES.get("z", {}).keys())
            if z_cat and z_cat not in GRID_AXES.get("z", {}):
                matches = difflib.get_close_matches(z_cat, known_z, n=1)
                if matches:
                    grid["z"]["category"] = matches[0]

        label = grid_to_label(grid) if include_grid else ""

        x = grid.get("x", {}).get("category", "?")
        y = grid.get("y", {}).get("category", "?")
        z = grid.get("z", {}).get("category", "?")

        desc_map = {
            "create": "Create", "read": "Read", "update": "Update", "delete": "Delete",
            "query": "Query", "analyze": "Analyze", "transform": "Transform",
            "communicate": "Send", "monitor": "Monitor", "orchestrate": "Orchestrate",
        }
        domain_map = {
            "audio": "audio", "text": "text", "filesystem": "file system",
            "network": "network", "system": "system", "data": "data",
            "code": "code", "image": "image", "time": "time",
        }
        constraint_map = {
            "count": "count", "filter": "filter", "search": "search",
            "sort": "sort", "generate": "generate", "validate": "validate",
            "convert": "convert", "summarize": "summarize", "compare": "compare",
            "notify": "notify",
        }

        action_word = desc_map.get(x, x)
        domain_word = domain_map.get(y, y)
        constraint_word = constraint_map.get(z, z)

        if constraint_word != "unknown" and constraint_word != "?":
            intent_summary = f"{action_word} {domain_word} with {constraint_word}"
        else:
            intent_summary = f"{action_word} {domain_word}"

        result = {
            "intent_summary": intent_summary,
            "grid": grid if include_grid else {},
            "grid_label": label,
            "tokens": grid.get("raw_tokens", []) if include_grid else [],
            "score_summary": grid.get("score_summary", {}) if include_grid else {},
        }

        if use_cache:
            INTENT_CACHE[cache_key] = result
            _mutation_count += 1
            if _mutation_count >= 100:
                _save_cache()
                _mutation_count = 0

        _context_history.append(intent_summary)
        if len(_context_history) > 3:
            _context_history.pop(0)

        return {"error": None, "result": result}

    def _nearest_neighbor_fallback(self, text: str) -> Optional[str]:
        known_keys = list(INTENT_CACHE.keys()) if INTENT_CACHE else []
        if not known_keys:
            return None
        matches = difflib.get_close_matches(text.lower().strip(), known_keys, n=1, cutoff=0.5)
        if matches:
            return matches[0]
        return None

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, str):
            payload = {"text": payload}
        result = self.execute(**payload) if isinstance(payload, dict) else self.execute(text=str(payload))
        if result.get("error"):
            fallback_key = self._nearest_neighbor_fallback(str(payload))
            if fallback_key:
                return True, dict(INTENT_CACHE[fallback_key])
            return False, result["error"]
        return True, result["result"]


@register_skill("intent_cache_clear", "intent")
class IntentCacheClearSkill(BaseSkill):
    name = "intent_cache_clear"
    description = "Clear the intent enrichment cache"
    category = "intent"

    def execute(self, **kwargs) -> dict:
        global _mutation_count
        count = len(INTENT_CACHE)
        INTENT_CACHE.clear()
        _mutation_count = 0
        if INTENT_CACHE_PATH.exists():
            INTENT_CACHE_PATH.unlink()
        return {"error": None, "result": {"cleared": count}}
