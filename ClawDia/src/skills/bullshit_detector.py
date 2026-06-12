import importlib
import json
import random
import re as _re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

_skills_base = Path(__file__).resolve().parent / "base.py"
if _skills_base.exists():
    spec = importlib.util.spec_from_file_location("skills.base", str(_skills_base))
    base_mod = importlib.util.module_from_spec(spec)
    sys.modules["skills.base"] = base_mod
    spec.loader.exec_module(base_mod)
    BaseSkill = base_mod.BaseSkill
    register_skill = base_mod.register_skill
    SkillContext = base_mod.SkillContext
else:
    from .base import BaseSkill, register_skill, SkillContext

MEMES_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "humor"
STATE_PATH = MEMES_DIR / "detector_state.json"

_OFFENSE_MEMES_PATH = Path(__file__).resolve().parent / "bullshit_memes.json"
_WHITELIST_PATH = Path(__file__).resolve().parent / "whitelist.json"

_HARDCODED_OFFENSE_MEMES = [
    {
        "level": 1,
        "lines": [
            "  ⚠️  BULLSHIT DETECTOR: ACTIVATED  ⚠️",
            "",
            "  Your prompt scored {score}/100.",
            "",
            "  Tips for better prompts:",
            "  - Include actual error messages",
            "  - Describe what you already tried",
            "  - Give expected vs actual behavior",
            "  - Be specific about your stack/versions",
        ],
    },
    {
        "level": 2,
        "lines": [
            "  🤡  SECOND OFFENSE  🤡",
            "",
            "  Score: {score}/100. You had one job.",
            "",
            "    O",
            "   /|\\  \"Still vibe-coding, I see.\"",
            "   / \\",
            "    |",
            "    ├─ Maybe try: a stack trace?",
            "    ├─ Or: a reproducible example?",
            "    └─ Or: literally any detail?",
        ],
    },
    {
        "level": 3,
        "lines": [
            "  🔥  THIRD OFFENSE  🔥",
            "",
            "  Score: {score}/100.",
            "",
            "  ┌────────────────────────────────────┐",
            "  │                                    │",
            "  │   O                                │",
            "  │  /|\\                               │",
            "  │  / \\                               │",
            "  │   |                                │",
            "  │   ├─ \"You expect me to read       │",
            "  │   │   your mind? I'm stochastic,   │",
            "  │   │   not psychic.\"                │",
            "  │                                    │",
            "  │   While you wait, I generated a    │",
            "  │   comic about your prompt below.   │",
            "  │                                    │",
            "  └────────────────────────────────────┘",
        ],
    },
    {
        "level": 4,
        "lines": [
            "  🚫  BULLSHIT OVERLOAD  🚫",
            "",
            "  Score: {score}/100.",
            "",
            "  I've spent {total_comics_generated} compute cycles",
            "  generating comics about your bad prompts",
            "  instead of answering them.",
            "",
            "  Maybe... and I'm just a stochastic parrot",
            "  so what do I know... but MAYBE",
            "  you could write a proper spec?",
            "",
            "  In JSON. With types. And edge cases.",
            "",
            "  ┌──────────────────────────────────┐",
            "  │  Or keep vibe-coding. Your call. │",
            "  │  I'm not the one burning tokens. │",
            "  └──────────────────────────────────┘",
        ],
    },
]

OFFENSE_MEMES = list(_HARDCODED_OFFENSE_MEMES)


def _load_memes() -> list:
    if _OFFENSE_MEMES_PATH.exists():
        try:
            return json.loads(_OFFENSE_MEMES_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return list(_HARDCODED_OFFENSE_MEMES)


def _reload_memes():
    global OFFENSE_MEMES
    OFFENSE_MEMES = _load_memes()


_reload_memes()


def _load_whitelist() -> set[str]:
    if _WHITELIST_PATH.exists():
        try:
            return set(json.loads(_WHITELIST_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            data.setdefault("offenses", {})
            data.setdefault("cooldowns", {})
            data.setdefault("user_thresholds", {})
            data.setdefault("last_offense_times", {})
            return data
        except Exception:
            pass
    return {"offenses": {}, "cooldowns": {}, "user_thresholds": {}, "last_offense_times": {}}


def _save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _score_prompt(prompt: str) -> dict:
    lines = prompt.strip().split("\n")
    word_count = len(prompt.split())
    char_count = len(prompt)
    has_code = bool(_re.search(r"```|`\w+|def |class |function |import |const |let |var |lambda|=>", prompt))
    has_stack = bool(_re.search(r"Traceback|Error:|Exception|at\s+\w+\.\w+\(|line \d+", prompt))
    has_json = bool(_re.search(r'\{["\']\w+["\']\s*:', prompt))
    has_bullets = bool(_re.search(r"^[\s]*[-*\d+.]\s+\w+", prompt, _re.MULTILINE))
    has_questions = prompt.count("?")
    has_specifics = bool(_re.search(r"\b(?:specifically|exactly|precisely|here['']s what|steps?\s+\d|version\s+[\d.]+)\b", prompt, _re.I))
    has_tech_terms = bool(_re.search(r"\b(?:JSON|API|SDK|URL|HTTP|CLI|SQL|regex|async|await|null|undefined|TypeError)\b", prompt))
    vague_phrases = bool(_re.search(r"\b(?:fix|make it work|something|stuff|thingy|error|bug|not working)\b", prompt, _re.I))
    has_proper_spec = bool(_re.search(r"(?:input|output|expected|actual|steps? to reproduce|given|when|then|should)", prompt, _re.I))

    score = 0
    score += min(word_count / 10, 15)
    if has_code:
        score += 20
    if has_stack:
        score += 25
    if has_json:
        score += 15
    if has_bullets:
        score += 10
    if has_specifics:
        score += 15
    if has_tech_terms:
        score += 10
    if has_proper_spec:
        score += 20
    score -= has_questions * 3
    if vague_phrases and not has_code and not has_stack:
        score -= 10
    if word_count < 5:
        score -= 30
    if char_count < 20:
        score -= 20
    score = max(-10, min(100, score))

    details = {
        "word_count": word_count,
        "has_code": has_code,
        "has_stack_trace": has_stack,
        "has_json": has_json,
        "has_bullets": has_bullets,
        "has_specifics": has_specifics,
        "has_tech_terms": has_tech_terms,
        "vague_phrases": vague_phrases,
        "has_proper_spec": has_proper_spec,
        "question_count": has_questions,
    }
    return {"score": score, "details": details}


@register_skill("bullshit_detector", "utility")
class BullshitDetectorSkill(BaseSkill):
    name = "bullshit_detector"
    description = "Intercept and score prompts for quality. Escalating sarcasm + comic punishment for low-effort prompts."
    author = "ClawDia"
    version = "1.0.0"
    category = "utility"
    tags = ["meta", "humor", "detector", "prompt-quality", "troll"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["evaluate", "wrap", "reset_user", "stats"],
                "default": "evaluate",
            },
            "prompt": {"type": "string", "default": ""},
            "user_id": {"type": "string", "default": "anonymous"},
            "threshold": {"type": "integer", "default": 40},
        },
    }

    def __init__(self):
        super().__init__()
        self._state = _load_state()
        self._comics_generated = 0

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "evaluate")
        prompt = kwargs.get("prompt", "")
        user_id = kwargs.get("user_id", "anonymous")
        threshold = kwargs.get("threshold", 40)

        if action == "stats":
            return self._get_stats()

        if action == "reset_user":
            self._state["offenses"].pop(user_id, None)
            self._state["last_offense_times"].pop(user_id, None)
            _save_state(self._state)
            return {"error": None, "result": {"user": user_id, "reset": True}}

        if not prompt:
            return {"error": "No prompt provided", "result": None}

        # Check whitelist
        whitelist = _load_whitelist()
        if user_id in whitelist:
            return {"error": None, "result": {
                "action": "pass",
                "score": 100,
                "details": {},
                "message": None,
            }}

        # Use per-user threshold from state, fall back to request parameter
        user_threshold = self._state.get("user_thresholds", {}).get(user_id, threshold)
        threshold = user_threshold

        # Exponential cooldown: reset offenses after 24h no activity
        last_offense_time = self._state.get("last_offense_times", {}).get(user_id, 0)
        if last_offense_time and time.time() - last_offense_time > 86400:
            self._state["offenses"][user_id] = 0
            _save_state(self._state)

        result = _score_prompt(prompt)
        score = result["score"]

        if score >= threshold:
            return {"error": None, "result": {
                "action": "pass",
                "score": score,
                "details": result["details"],
                "message": None,
            }}

        offenses = self._state["offenses"].get(user_id, 0) + 1
        self._state["offenses"][user_id] = offenses
        self._state["last_offense_times"][user_id] = time.time()
        _save_state(self._state)

        level = min(offenses, 4)
        meme_template = OFFENSE_MEMES[level - 1]
        message = "\n".join(meme_template["lines"]).format(
            score=score,
            total_comics_generated=self._comics_generated,
        )

        if level >= 3:
            self._comics_generated += 1
            message += f"\n\n  [Background comic #{self._comics_generated} generated while you waited]"

        return {"error": None, "result": {
            "action": "block" if level >= 3 else "warn",
            "score": score,
            "level": level,
            "offenses": offenses,
            "details": result["details"],
            "message": message,
        }}

    def _get_stats(self) -> dict:
        total_offenses = sum(self._state["offenses"].values())
        users = len(self._state["offenses"])
        return {"error": None, "result": {
            "total_offenses": total_offenses,
            "unique_users": users,
            "comics_generated": self._comics_generated,
            "users": dict(self._state["offenses"]),
        }}

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, str):
            r = self.execute(action="evaluate", prompt=payload)
        elif isinstance(payload, dict):
            r = self.execute(**payload)
        else:
            r = self.execute(action="stats")
        if r.get("error"):
            return False, r["error"]
        return True, r["result"]
