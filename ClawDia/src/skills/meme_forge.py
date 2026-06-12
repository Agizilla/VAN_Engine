import json
import random
import re
import sys
from datetime import datetime
from pathlib import Path

from .base import BaseSkill, register_skill, SkillContext

_SRC_PATH = Path(__file__).resolve().parents[1]
_ARTIFACTS_PATH = _SRC_PATH / "artifacts" / "humor"
if str(_ARTIFACTS_PATH) not in sys.path:
    sys.path.insert(0, str(_ARTIFACTS_PATH))

_LEXICON_PATH = _ARTIFACTS_PATH / "humor_seed_lexicon.json"
_FEEDBACK_PATH = _ARTIFACTS_PATH / "meme_feedback.json"

_RE_ARTICLES = re.compile(r'\b(a|an|the)\b', re.I)


def _load_lexicon() -> dict:
    with open(_LEXICON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_feedback() -> list[dict]:
    if _FEEDBACK_PATH.exists():
        try:
            with open(_FEEDBACK_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_feedback(feedback: list[dict]):
    _FEEDBACK_PATH.write_text(json.dumps(feedback, indent=2), encoding="utf-8")


_EXCLUDED_NOUNS = {"a", "an", "the", "in", "of", "to", "for", "with", "no", "not", "is", "it", "its", "and", "or", "but"}


def _build_noun_pool(lexicon: dict) -> list[str]:
    nouns: set[str] = set()
    for domain_list in lexicon.get("domains", {}).values():
        for item in domain_list:
            parts = item.split()
            for p in parts:
                cleaned = p.strip("-_,.").lower()
                if len(cleaned) >= 3 and cleaned not in _EXCLUDED_NOUNS:
                    nouns.add(p)
            if len(parts) > 1:
                nouns.add(item)
    extras = ["project", "deadline", "repo", "pipeline", "build", "server", "database", "api", "interface", "module", "deploy", "stack", "runtime", "process", "thread"]
    for e in extras:
        nouns.add(e)
    return sorted(nouns)


_IRREGULAR_PAST: dict[str, str] = {
    "catch": "caught", "throw": "threw", "break": "broke", "write": "wrote",
    "speak": "spoke", "take": "took", "run": "ran", "begin": "began",
    "fall": "fell", "forget": "forgot", "give": "gave", "know": "knew",
    "see": "saw", "send": "sent", "spend": "spent", "build": "built",
    "feel": "felt", "keep": "kept", "leave": "left", "lose": "lost",
    "make": "made", "mean": "meant", "meet": "met", "pay": "paid",
    "set": "set", "shut": "shut", "sit": "sat", "stand": "stood",
}


def _past_tense(verb: str) -> str:
    if not verb:
        return "ed"
    lv = verb.lower()
    if lv in _IRREGULAR_PAST:
        return _IRREGULAR_PAST[lv]
    if verb.endswith("e"):
        return verb + "d"
    if verb.endswith("y") and len(verb) > 2 and verb[-2] not in "aeiou":
        return verb[:-1] + "ied"
    if verb.endswith("c"):
        return verb + "ked"
    if len(verb) == 3 and verb[-1] not in "aeiou" and verb[-2] in "aeiou" and verb[-3] not in "aeiou":
        return verb + verb[-1] + "ed"
    return verb + "ed"


VOWEL_LETTERS = frozenset("aeiouAEIOU")


def _fix_articles(text: str) -> str:
    text = re.sub(r"\ba\s+(a|an|the)\b", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\ban\s+(a|an|the)\b", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\bthe\s+(a|an|the)\b", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[aA]\s+([aeiouAEIOU])", r"an \1", text)
    return text


def _no_double_article(text: str, word: str) -> str:
    if word.startswith("a ") or word.startswith("an ") or word.startswith("the "):
        text = text.replace("a " + word, word).replace("an " + word, word)
    return _fix_articles(text)


def _render_ascii_frame(text: str, style: str = "single", width: int = None) -> str:
    lines = text.split("\n")
    max_line = max(len(l) for l in lines) if lines else 40
    w = width or min(max_line + 4, 72)
    pad = w - 2

    try:
        primitives = _load_lexicon().get("ascii_primitives", {})
    except Exception:
        primitives = {}

    def _unpack(pool_key: str, fallback: tuple) -> tuple:
        arr = primitives.get(pool_key, [])
        if len(arr) >= 6:
            return arr[2], arr[3], arr[4], arr[5], arr[0], arr[1]
        if len(arr) >= 4:
            return arr[0], arr[1], arr[2], arr[3], "─", "│"
        return fallback

    if style == "double":
        tl, tr, bl, br, h, v = _unpack("double", ("╔", "╗", "╚", "╝", "═", "║"))
    elif style == "rounded":
        tl, tr, bl, br, h, v = _unpack("rounded", ("╭", "╮", "╰", "╯", "─", "│"))
    else:
        tl, tr, bl, br, h, v = _unpack("single", ("┌", "┐", "└", "┘", "─", "│"))

    top = tl + h * pad + tr
    body = "\n".join(f"{v} {line.ljust(pad - 1)}{v}" for line in lines)
    bot = bl + h * pad + br
    return f"{top}\n{body}\n{bot}"


@register_skill("meme_forge", "utility")
class MemeForgeSkill(BaseSkill):
    name = "meme_forge"
    description = "Generate offline ASCII humour memes from seed lexicon templates"
    author = "DeepSeek / ClawDia"
    version = "1.0.0"
    category = "utility"
    tags = ["humor", "meme", "generator", "offline", "ascii"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["generate", "batch", "feedback", "stats", "list_topics"],
            },
            "topic": {"type": "string", "default": "random"},
            "tone": {"type": "string", "default": "sarcastic"},
            "frame": {"type": "string", "default": "single"},
            "count": {"type": "integer", "default": 1},
            "rate": {"type": "integer", "description": "Rate last meme 1-5"},
            "seed": {"type": "integer", "description": "RNG seed for reproducibility"},
        },
    }

    _LEXICON = None
    _NOUNS = None

    def __init__(self):
        super().__init__()
        if MemeForgeSkill._LEXICON is None:
            MemeForgeSkill._LEXICON = _load_lexicon()
        if MemeForgeSkill._NOUNS is None:
            MemeForgeSkill._NOUNS = _build_noun_pool(self._LEXICON)
        self._lexicon = MemeForgeSkill._LEXICON
        self._nouns = MemeForgeSkill._NOUNS
        self._last_meme: dict | None = None

    def _get_rng(self, seed: int = None) -> random.Random:
        if seed is not None:
            return random.Random(seed)
        return random

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "generate")

        if action == "generate":
            return self._generate(kwargs)
        elif action == "batch":
            return self._batch(kwargs)
        elif action == "feedback":
            return self._record_feedback(kwargs)
        elif action == "stats":
            return self._stats()
        elif action == "list_topics":
            return self._list_topics()
        return {"error": f"Unknown action: {action}", "result": None}

    def _generate(self, kwargs: dict) -> dict:
        topic = kwargs.get("topic", "random")
        tone = kwargs.get("tone", "sarcastic")
        frame = kwargs.get("frame", "none")
        rate = kwargs.get("rate")
        seed = kwargs.get("seed")

        rng = self._get_rng(seed)

        domains = self._lexicon.get("domains", {})
        verbs = self._lexicon.get("action_verbs", [])
        adjectives = self._lexicon.get("adjectives", [])
        templates = self._lexicon.get("punchline_templates", [])
        nonsense = self._lexicon.get("nonsense_items", [])
        outcomes = self._lexicon.get("outcomes", [])
        costs = self._lexicon.get("cost_units", [])
        tones = self._lexicon.get("tone_modes", {})
        tone_opener = rng.choice(tones.get(tone, tones.get("sarcastic", ["Hey."])))

        if topic == "random" or topic not in domains:
            topic = rng.choice(list(domains.keys()))
        domain_items = domains[topic]

        noun = rng.choice(self._nouns)
        verb = rng.choice(verbs)
        adj = rng.choice(adjectives)
        nonsense_item = rng.choice(nonsense)
        outcome = rng.choice(outcomes)
        cost = rng.choice(costs)
        domain_word = rng.choice(domain_items)

        template = rng.choice(templates)
        body = (
            template.replace("{{domain}}", domain_word)
            .replace("{{verb}}ed", _past_tense(verb))
            .replace("{{verb}}", verb)
            .replace("{{noun}}", noun)
            .replace("{{adjective}}", adj)
            .replace("{{nonsense}}", nonsense_item)
            .replace("{{outcome}}", outcome)
            .replace("{{cost}}", cost)
        )
        body = _no_double_article(body, nonsense_item)

        lines = [tone_opener, "", body, ""]
        if frame and frame != "none":
            ascii = _render_ascii_frame("\n".join(l.strip() for l in lines), style=frame)
        else:
            ascii = "\n".join(l for l in lines)

        meme = {
            "topic": topic,
            "tone": tone,
            "frame": frame,
            "body": body,
            "ascii": ascii,
            "generated": datetime.now().isoformat(),
        }
        self._last_meme = meme

        if rate is not None:
            self._record_feedback({"rate": rate})

        self.publish("meme:generated", {"topic": topic, "tone": tone, "body": body[:60]})

        return {"error": None, "result": meme}

    def _batch(self, kwargs: dict) -> dict:
        count = min(kwargs.get("count", 3), 20)
        topic = kwargs.get("topic", "random")
        tone = kwargs.get("tone", "sarcastic")
        frame = kwargs.get("frame", "none")

        memes = []
        for _ in range(count):
            r = self._generate({"topic": topic, "tone": tone, "frame": frame})
            if r.get("result"):
                memes.append(r["result"])

        return {"error": None, "result": {"count": len(memes), "memes": memes}}

    def _record_feedback(self, kwargs: dict) -> dict:
        rating = kwargs.get("rate")
        if rating is None and self._last_meme:
            return {"error": "No rating provided. Use rate=N (1-5)", "result": None}
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return {"error": "Rating must be 1-5", "result": None}

        feedback = _load_feedback()
        entry = {
            "rating": rating,
            "topic": self._last_meme.get("topic", "") if self._last_meme else "",
            "body": self._last_meme.get("body", "") if self._last_meme else "",
            "timestamp": datetime.now().isoformat(),
        }
        feedback.append(entry)
        _save_feedback(feedback)

        return {"error": None, "result": {
            "recorded": True,
            "rating": rating,
            "total_ratings": len(feedback),
        }}

    def _stats(self) -> dict:
        feedback = _load_feedback()
        if not feedback:
            return {"error": None, "result": {"total": 0, "average": 0, "top_topics": []}}

        ratings = [f["rating"] for f in feedback]
        avg = round(sum(ratings) / len(ratings), 2)
        topic_counts: dict[str, int] = {}
        for f in feedback:
            t = f.get("topic", "unknown")
            topic_counts[t] = topic_counts.get(t, 0) + 1
        top = sorted(topic_counts.items(), key=lambda x: -x[1])[:5]

        return {"error": None, "result": {
            "total": len(feedback),
            "average": avg,
            "top_topics": [{"topic": t, "count": c} for t, c in top],
        }}

    def _list_topics(self) -> dict:
        domains = self._lexicon.get("domains", {})
        return {"error": None, "result": {
            "topics": list(domains.keys()),
            "count": len(domains),
        }}

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, dict):
            result = self.execute(**payload)
        else:
            result = self.execute(action="generate", topic=str(payload))
        if result.get("error"):
            return False, result["error"]
        return True, result["result"]
