import json
import random
from datetime import datetime
from pathlib import Path

from .base import BaseSkill, register_skill, SkillContext

SETTINGS_PATH = Path(__file__).resolve().parents[2] / "config" / "Settings.json"

SENTIMENT_CATEGORIES = {
    "positive": ["openers", "positive_verbs", "objects", "closers"],
    "neutral": ["openers", "objects", "closers", "meta_comments"],
    "coaching": ["openers", "qualifiers", "closers"],
}

AFFIRMATIONS = {
    "openers": [
        "You are", "Remember that", "Take a breath,", "It's okay to", "Today, you",
        "Your code", "Debugging is", "Every bug fixed", "This moment,", "Your future self",
    ],
    "positive_verbs": [
        "write", "build", "refactor", "test", "ship", "learn", "teach", "share", "fix", "improve",
        "document", "review", "merge", "deploy", "celebrate", "rest", "ask for help",
    ],
    "objects": [
        "clean code", "meaningful tests", "gentle comments", "working software", "team culture",
        "your mental model", "local offline tools", "open source contributions", "a sustainable pace",
        "knowledge that compounds",
    ],
    "qualifiers": [
        "without burning out", "one commit at a time", "even when it's hard", "with curiosity",
        "without comparing to AI slop", "for yourself, not for metrics", "and that is enough",
    ],
    "closers": [
        "You've got this.", "Trust the process.", "Progress, not perfection.",
        "Your value is not measured in tokens.", "Offline first, forever.",
        "Real engineers review code \u2013 you are one.", "The vessel is sovereign.",
    ],
    "meta_comments": [
        " (This affirmation generated offline, with zero carbon footprint.)",
        " (No API calls were harmed in the making of this message.)",
        " (Your local compute thanks you.)",
    ],
}


def _load_user_name() -> str:
    if SETTINGS_PATH.exists():
        try:
            s = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            return s.get("user_name", "")
        except Exception:
            return ""
    return ""


@register_skill("vibe_affirmations", "wellness")
class VibeAffirmationsSkill(BaseSkill):
    name = "vibe_affirmations"
    description = "Wholesome token-recombined developer affirmations \u2014 zero API calls"
    author = "DeepSeek / ARC / ClawDia"
    version = "1.1.0"
    category = "wellness"
    tags = ["affirmations", "wholesome", "motivation", "offline"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["generate", "batch", "info"], "default": "generate"},
            "count": {"type": "integer", "default": 1},
            "sentiment": {"type": "string", "enum": ["positive", "neutral", "coaching"], "default": "positive"},
            "show_author": {"type": "boolean", "default": False},
        },
    }

    def __init__(self):
        super().__init__()
        self._recent: list[str] = []
        self._user_name = _load_user_name()

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "generate")
        if action == "info":
            return self._info()
        if action == "batch":
            return self._batch(kwargs.get("count", 3), kwargs.get("sentiment", "positive"), kwargs.get("show_author", False))
        return self._generate(sentiment=kwargs.get("sentiment", "positive"), show_author=kwargs.get("show_author", False))

    def _generate(self, sentiment: str = "positive", show_author: bool = False) -> dict:
        cats = SENTIMENT_CATEGORIES.get(sentiment, SENTIMENT_CATEGORIES["positive"])
        pool = {k: AFFIRMATIONS[k] for k in cats if k in AFFIRMATIONS}

        opener = random.choice(pool.get("openers", AFFIRMATIONS["openers"]))
        verb = random.choice(pool.get("positive_verbs", AFFIRMATIONS["positive_verbs"]))
        obj = random.choice(pool.get("objects", AFFIRMATIONS["objects"]))
        qualifier = random.choice(pool.get("qualifiers", AFFIRMATIONS["qualifiers"]))
        closer = random.choice(pool.get("closers", AFFIRMATIONS["closers"]))
        meta = random.choice(pool.get("meta_comments", AFFIRMATIONS["meta_comments"]))

        if random.random() > 0.5:
            body = f"{opener} {verb} {obj} {qualifier}"
        else:
            body = f"{verb.capitalize()} {obj} {qualifier}. {opener}"

        emoji = random.choice(["\U0001f9d8", "\U0001f4bb", "\U0001f31f", "\U0001f527", "\U0001f331", "\u2615", "\U0001f4da", "\U0001f91d"])
        phrase = f"{emoji} {body}. {closer}{meta}"

        if show_author:
            phrase += f" \u2014 {self.author}"

        name = self._user_name
        if name:
            phrase = f"Hey {name}, {phrase}"

        if phrase in self._recent:
            random.shuffle(self._recent)
            return self._generate(sentiment, show_author)
        self._recent.append(phrase)
        if len(self._recent) > 10:
            self._recent.pop(0)

        self.publish("affirmation_generated", {"text": phrase[:80]})
        return {
            "error": None,
            "result": {
                "affirmation": phrase,
                "generated": datetime.now().isoformat(),
                "sentiment": sentiment,
            },
        }

    def _batch(self, count: int, sentiment: str = "positive", show_author: bool = False) -> dict:
        count = max(1, min(count, 20))
        affirmations = []
        for _ in range(count):
            r = self._generate(sentiment=sentiment, show_author=show_author)
            affirmations.append(r["result"]["affirmation"])
        return {"error": None, "result": {"count": len(affirmations), "affirmations": affirmations}}

    def _info(self) -> dict:
        return {
            "error": None,
            "result": {
                "categories": list(AFFIRMATIONS.keys()),
                "total_tokens": sum(len(v) for v in AFFIRMATIONS.values()),
                "version": self.version,
                "user_name": self._user_name or "(not set)",
            },
        }

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, int):
            result = self.execute(action="batch", count=payload)
        else:
            result = self.execute(action="generate")
        if result.get("error"):
            return False, result["error"]
        return True, result["result"]["affirmation"]
