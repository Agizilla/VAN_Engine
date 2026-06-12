import json
import logging
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import BaseSkill, register_skill, SkillContext
from .replay_audit import ReplayAuditSkill

logger = logging.getLogger(__name__)

# Point to the existing DirtyTokens.json from DeepSeek's DirtyTalker project
_DIRTYTALKER_DIR = Path(r"C:\Users\User\Documents\!Deepseek\DirtyTalker")
_FALLBACK_TOKENS_PATH = _DIRTYTALKER_DIR / "DirtyTokens.json"

_REQUIRED_TOP_KEYS = {"tokens", "categories", "intensities"}


def _validate_schema(data: dict) -> bool:
    if not isinstance(data, dict):
        logger.warning("DirtyTokens.json: root is not a dict")
        return False
    top_keys = set(data.keys())
    if not _REQUIRED_TOP_KEYS.issubset(top_keys):
        missing = _REQUIRED_TOP_KEYS - top_keys
        logger.warning(f"DirtyTokens.json missing required keys: {missing}")
        return False
    if "categories" in data and not isinstance(data["categories"], dict):
        logger.warning("DirtyTokens.json 'categories' is not a dict")
        return False
    if "tokens" in data and not isinstance(data["tokens"], dict):
        logger.warning("DirtyTokens.json 'tokens' is not a dict")
        return False
    if "intensities" in data and not isinstance(data["intensities"], dict):
        logger.warning("DirtyTokens.json 'intensities' is not a dict")
        return False
    return True


def _load_tokens() -> dict:
    path = _FALLBACK_TOKENS_PATH
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _validate_schema(data)
        if "categories" in data:
            return data["categories"]
        return data
    return {}


def _has_dirtytalker() -> bool:
    return _DIRTYTALKER_DIR.exists() and _FALLBACK_TOKENS_PATH.exists()


_PROFANITY_LIST: set[str] = {
    "fuck", "shit", "damn", "ass", "bitch", "cock", "dick", "piss",
    "cunt", "bastard", "slut", "whore", "motherfucker",
}


def _sanitize(phrase: str) -> str:
    import re
    def _replace(m):
        w = m.group(0)
        return w[0] + "*" * (len(w) - 2) + w[-1] if len(w) > 2 else "*" * len(w)
    pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in _PROFANITY_LIST) + r")\b", re.IGNORECASE)
    return pattern.sub(_replace, phrase)


# ── Skill 1: Dirty Talker — token recombination engine ──────────

@register_skill("dirty_talker", "utility")
class DirtyTalkerSkill(BaseSkill):
    name = "dirty_talker"
    description = "Generate NSFW spoken phrases via token recombination (requires DirtyTokens.json)"
    author = "DeepSeek / ClawDia"
    version = "1.0.0"
    category = "utility"
    tags = ["nsfw", "audio", "voice", "token-recomb"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["generate", "batch", "info", "reload"],
                "default": "generate",
            },
            "template": {"type": "string", "default": ""},
            "count": {"type": "integer", "default": 1},
            "category": {"type": "string", "default": ""},
            "seed": {"type": "integer", "default": None},
            "sanitize": {"type": "boolean", "default": False},
        },
    }

    def __init__(self):
        super().__init__()
        self._tokens = {}
        self._default_structure = ""
        self._rng = random.Random()
        self._audit_skill = ReplayAuditSkill()
        self._load()

    def _load(self):
        self._tokens = _load_tokens()
        rules = {}
        try:
            p = _FALLBACK_TOKENS_PATH
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                rules = raw.get("generation_rules", {})
        except Exception:
            pass
        self._default_structure = rules.get(
            "structure",
            "{crying_filler} {begging} {action_verb} my {body_part} {intensifier} till I {emotional_reaction} {cum_related} {human_natural_filler}",
        )

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "generate")

        if not _has_dirtytalker():
            return {"error": f"DirtyTokens.json not found at {_FALLBACK_TOKENS_PATH}", "result": None}

        if action == "info":
            return self._info()
        if action == "reload":
            self._load()
            cats = list(self._tokens.keys())
            return {"error": None, "result": {"reloaded": True, "categories": cats}}
        if action == "batch":
            return self._batch(kwargs)
        return self._generate(kwargs)

    def _generate(self, kwargs: dict) -> dict:
        template = kwargs.get("template", "") or self._default_structure
        category = kwargs.get("category", "")
        sanitize = kwargs.get("sanitize", False)
        seed = kwargs.get("seed")

        if seed is not None:
            self._rng = random.Random(seed)
        else:
            self._rng = random.Random()

        if category:
            if category not in self._tokens:
                return {"error": f"Category '{category}' not found. Options: {list(self._tokens.keys())}", "result": None}
            choice = self._rng.choice(self._tokens[category])
            phrase = choice
        else:
            def _fill(m):
                key = m.group(1).strip()
                pool = self._tokens.get(key, [])
                if not pool:
                    return f"{{{key}}}"
                return self._rng.choice(pool)

            import re
            phrase = re.sub(r"\{(\w+)\}", _fill, template)

            if self._rng.random() > 0.5:
                words = phrase.split()
                if len(words) > 3:
                    idx = self._rng.randint(1, len(words) - 2)
                    w = words[idx]
                    if len(w) > 2:
                        words[idx] = f"{w[0]}-{w.lower()}"
                        phrase = " ".join(words)

        if sanitize:
            phrase = _sanitize(phrase)

        result = {
            "phrase": phrase,
            "template": template,
            "sanitized": sanitize,
            "generated": datetime.now().isoformat(),
        }
        self.publish("dirty_talk:generated", {"phrase": phrase[:60]})

        try:
            self._audit_skill.execute(
                action="log",
                action_type="dirty_talk",
                skill_id=self.name,
                preview=phrase[:120],
            )
        except Exception:
            pass

        return {"error": None, "result": result}

    def _batch(self, kwargs: dict) -> dict:
        count = min(kwargs.get("count", 3), 20)
        phrases = []
        for _ in range(count):
            r = self._generate(kwargs)
            if r.get("result"):
                phrases.append(r["result"]["phrase"])
        return {"error": None, "result": {"count": len(phrases), "phrases": phrases}}

    def _info(self) -> dict:
        cats = {k: len(v) for k, v in self._tokens.items()}
        return {"error": None, "result": {
            "available": _has_dirtytalker(),
            "tokens_path": str(_FALLBACK_TOKENS_PATH),
            "categories": cats,
            "total_tokens": sum(cats.values()),
        }}

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, str):
            result = self.execute(action="generate", category=payload)
        elif isinstance(payload, dict):
            result = self.execute(**payload)
        else:
            result = self.execute(action="generate")
        if result.get("error"):
            return False, result["error"]
        return True, result["result"]
