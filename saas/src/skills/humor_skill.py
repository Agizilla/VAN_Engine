import functools
import random
import sys
import time
from pathlib import Path

from .base import BaseSkill, register_skill

_SRC_PATH = Path(__file__).resolve().parents[1]
_ARTIFACTS_PATH = _SRC_PATH / "artifacts"
if str(_ARTIFACTS_PATH) not in sys.path:
    sys.path.insert(0, str(_ARTIFACTS_PATH))

from humor.ascii_collection import MEMES, TAGS_INDEX


@functools.lru_cache(maxsize=64)
def _cached_render(lines: tuple[str, ...]) -> str:
    return "\n".join(lines)


def _render(lines: list[str]) -> str:
    return _cached_render(tuple(lines))


_ASCII_COLLECTION_PATH = Path(_ARTIFACTS_PATH) / "humor" / "ascii_collection.py"

_last_meme_times: dict[str, list[float]] = {}


def _check_rate_limit(user_id: str = "default") -> bool:
    now = time.time()
    times = _last_meme_times.setdefault(user_id, [])
    times[:] = [t for t in times if now - t < 60]
    if len(times) >= 10:
        return False
    times.append(now)
    return True


@register_skill("humor_meme", "utility")
class HumorMemeSkill(BaseSkill):
    name = "humor_meme"
    description = "Display ASCII art memes from the Sovereign Slapback Collection"
    category = "utility"
    tags = ["humor", "ascii", "meme", "easter-egg"]

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "random")
        meme_id = kwargs.get("id", "") or kwargs.get("meme_id", "")
        tags = kwargs.get("tags", [])
        user_id = kwargs.get("user_id", "default")

        if action == "add_meme":
            return self._add_meme(kwargs)

        if not _check_rate_limit(user_id):
            return {"error": "Rate limit exceeded: max 10 memes per minute per user", "result": None}

        if action == "list":
            return self._list()

        if action == "by_id":
            return self._by_id(meme_id)

        if action == "by_tags":
            return self._by_tags(tags)

        if action == "tags":
            return self._all_tags()

        return self._random(tags)

    def _list(self) -> dict:
        return {"error": None, "result": {
            "memes": [
                {"id": m["id"], "title": m["title"], "tags": m["tags"]}
                for m in MEMES
            ],
            "count": len(MEMES),
        }}

    def _by_id(self, meme_id: str) -> dict:
        for m in MEMES:
            if m["id"] == meme_id:
                return {"error": None, "result": {
                    "id": m["id"],
                    "title": m["title"],
                    "tags": m["tags"],
                    "ascii": _render(m["lines"]),
                }}
        return {"error": f"Meme '{meme_id}' not found", "result": None}

    def _by_tags(self, tags: list[str]) -> dict:
        if not tags:
            return self._random([])
        indices: set[int] = set()
        for i, m in enumerate(MEMES):
            for t in tags:
                for mt in m["tags"]:
                    if mt.find(t) != -1 or t.find(mt) != -1:
                        indices.add(i)
        if not indices:
            return {"error": f"No memes found with tags: {tags}", "result": None}
        memes = [MEMES[i] for i in sorted(indices)]
        chosen = random.choice(memes)
        return {"error": None, "result": {
            "id": chosen["id"],
            "title": chosen["title"],
            "tags": chosen["tags"],
            "ascii": _render(chosen["lines"]),
        }}

    def _random(self, tags: list[str]) -> dict:
        pool = MEMES
        if tags:
            pool = [m for m in MEMES if any(t in m["tags"] for t in tags)]
            if not pool:
                return self._random([])
        chosen = random.choice(pool)
        return {"error": None, "result": {
            "id": chosen["id"],
            "title": chosen["title"],
            "tags": chosen["tags"],
            "ascii": _render(chosen["lines"]),
        }}

    def _all_tags(self) -> dict:
        all_tags = sorted(set(t for m in MEMES for t in m["tags"]))
        return {"error": None, "result": {"tags": all_tags, "count": len(all_tags)}}

    def _add_meme(self, kwargs: dict) -> dict:
        meme_id = kwargs.get("id", "")
        title = kwargs.get("title", "")
        tags = kwargs.get("tags", [])
        lines = kwargs.get("lines", [])

        if not meme_id or not lines:
            return {"error": "id and lines are required for add_meme", "result": None}

        new_entry = {
            "id": meme_id,
            "title": title or meme_id,
            "tags": tags if isinstance(tags, list) else [tags],
            "lines": lines if isinstance(lines, list) else [lines],
        }

        MEMES.append(new_entry)
        for tag in new_entry["tags"]:
            TAGS_INDEX.setdefault(tag, []).append(len(MEMES) - 1)

        if _ASCII_COLLECTION_PATH.exists():
            try:
                current = _ASCII_COLLECTION_PATH.read_text(encoding="utf-8")
                import re
                # Find the last MEMES entry and append
                lines_start = current.rfind("    },")
                if lines_start == -1:
                    lines_start = current.rfind("    }")
                    if lines_start != -1:
                        lines_start += 4
                else:
                    lines_start += 5

                indent = "\n    "
                entry_text = f",{indent}{{\n        \"id\": \"{meme_id}\",\n        \"title\": \"{title or meme_id}\",\n        \"tags\": {new_entry['tags']},\n        \"lines\": ["
                for line in new_entry["lines"]:
                    entry_text += f"\n            \"{line.replace(chr(34), chr(92) + chr(34))}\","
                entry_text += f"\n        ],\n    }}"
                new_content = current[:lines_start] + entry_text + current[lines_start:]
                _ASCII_COLLECTION_PATH.write_text(new_content, encoding="utf-8")
            except Exception:
                pass

        return {"error": None, "result": {
            "added": meme_id,
            "title": title or meme_id,
            "tags": new_entry["tags"],
            "total": len(MEMES),
        }}


@register_skill("humor_ascii_generator", "utility")
class HumorAsciiGeneratorSkill(BaseSkill):
    name = "humor_ascii_generator"
    description = "Generate simple ASCII art from a text prompt (offline, template-based)"
    category = "utility"
    tags = ["humor", "ascii", "generator", "template"]
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to render as ASCII art"},
            "action": {"type": "string", "enum": ["banner", "figlet"], "default": "banner"},
            "style": {"type": "string", "enum": ["box", "angle", "rounded", "double"], "default": "box"},
        },
        "required": ["text"],
    }

    BORDER_TEMPLATES = [
        ("box", "┌{top}┐\n{body}\n└{bot}┘"),
        ("angle", "╔{top}╗\n{body}\n╚{bot}╝"),
        ("rounded", "╭{top}╮\n{body}\n╰{bot}╯"),
        ("double", "╔{top}╗\n{body}\n╚{bot}╝"),
    ]

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "banner")
        text = kwargs.get("text", "")
        style = kwargs.get("style", "box")
        width = kwargs.get("width", 60)

        if not text:
            return {"error": "No text provided", "result": None}

        if action == "banner":
            return self._make_banner(text, style, width)

        if action == "figlet":
            return self._make_figlet(text)

        return {"error": f"Unknown action: {action}", "result": None}

    def _make_banner(self, text: str, style: str, width: int) -> dict:
        lines = text.split("\n")
        padded = [line.center(width) for line in lines]
        top = "─" * width
        bot = "─" * width
        body = "\n".join(f"│{line}│" for line in padded)

        template_map = {
            "box": ("┌", "┐", "└", "┘"),
            "angle": ("╔", "╗", "╚", "╝"),
            "rounded": ("╭", "╮", "╰", "╯"),
            "double": ("╔", "╗", "╚", "╝"),
        }
        tl, tr, bl, br = template_map.get(style, template_map["box"])

        ascii = f"{tl}{top}{tr}\n{body}\n{bl}{bot}{br}"
        return {"error": None, "result": {"ascii": ascii, "style": style, "width": width}}

    def _make_figlet(self, text: str) -> dict:
        """Simple block-letter rendering — not real figlet."""
        lines = []
        for char in text.upper():
            if char.isalpha():
                lines.append(f" █{char} ")
            else:
                lines.append(f"   ")
        ascii = " ".join(lines) if lines else text
        return {"error": None, "result": {"ascii": ascii, "note": "Simple block render — install pyfiglet for real figlet"}}
