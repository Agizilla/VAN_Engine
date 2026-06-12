import functools
import importlib
import json
import math
import os
import random
import re as _re
import sys
from pathlib import Path
from typing import Optional

from .base import BaseSkill, register_skill, SkillContext

CHAPTER_KEY_RE = _re.compile(r"^chapter_\d+$")
NARRATIVES_DIR = Path(r"C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\ComicCookCreatorStudio\narratives")
OUTPUT_DIR = Path(__file__).resolve().parent / "comic_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Character sets (configurable via ascii_comic.json) ────────────

_CONFIG_PATH = Path(__file__).resolve().parent / "ascii_comic.json"

_DEFAULT_BODY = {
    "head":       " O ",
    "head_woman": " O ",
    "torso":      "/|\\",
    "torso_walk": "/|\\",
    "legs":       "/ \\",
    "legs_walk":  "/ \\",
    "arm_l":      "/",
    "arm_r":      "\\",
    "arm_up_l":   "╱",
    "arm_up_r":   "╲",
}

_DEFAULT_SIT = {
    "head":  " O ",
    "head_woman": " O ",
    "torso": "/|\\",
    "legs":  " | ",
    "arm_l": "/",
    "arm_r": "\\",
}

BODY = dict(_DEFAULT_BODY)
SIT = dict(_DEFAULT_SIT)

def _load_character_sets():
    if not _CONFIG_PATH.exists():
        return
    try:
        config = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        custom = config.get("character_sets", {})
        if "BODY" in custom:
            BODY.update(custom["BODY"])
        if "SIT" in custom:
            SIT.update(custom["SIT"])
    except Exception:
        pass

_load_character_sets()

# ── ANSI color support ────────────────────────────────────────────

_USE_COLOR = (
    os.environ.get("TERM") is not None
    and os.environ.get("TERM") != "dumb"
)

# ── Panel dimensions ──────────────────────────────────────────────

PANEL_W = 66
PANEL_H_MIN = 8
STICK_H = 4  # head + torso + legs + ground line
MARGIN = 1


def _make_stickigure(col: int, variants: dict = None) -> list[str]:
    v = variants or BODY
    lines = [
        v["head"].center(5),
        v["torso"].center(5),
        v["legs"].center(5),
    ]
    return [l.rstrip() for l in lines]


def _render_stick(row: int, col: int, canvas: list[list[str]], variant: str = "stand", panel_width: int = PANEL_W):
    h, t, ll = _make_stickigure(col)
    for offset, line in enumerate([h, t, ll]):
        cy = row + offset
        for ci, ch in enumerate(line):
            if ch != " ":
                canvas[cy][col + ci] = ch
    connector_col = col + int(panel_width * 0.08)
    if connector_col < len(canvas[0]):
        canvas[row + 1][connector_col] = "│"


@functools.lru_cache(maxsize=128)
def _wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if len(test) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines if lines else [""]


def _render_speech_bubble(text: str, col: int, row: int, canvas: list[list[str]], align: str = "left"):
    wrapped = _wrap_text(text, PANEL_W - col - 8)
    for i, line in enumerate(wrapped):
        cy = row + i
        prefix = "├─ " if align == "left" else " ─┤"
        if align == "right":
            for j, ch in enumerate(prefix[::-1]):
                if ch != " ":
                    canvas[cy][col - j] = ch
            for j, ch in enumerate(line):
                canvas[cy][col - len(prefix) - len(line) + j] = ch
        else:
            for j, ch in enumerate(prefix):
                if ch != " ":
                    canvas[cy][col + j] = ch
            for j, ch in enumerate(line):
                canvas[cy][col + len(prefix) + j] = ch


def _blank_canvas(h: int, w: int) -> list[list[str]]:
    return [[" "] * w for _ in range(h)]


def _canvas_to_str(canvas: list[list[str]]) -> str:
    result = "\n".join("".join(row).rstrip() for row in canvas)
    if _USE_COLOR:
        result = "\033[33m" + result + "\033[0m"
    return result


def _draw_box(canvas: list[list[str]], y1: int, x1: int, y2: int, x2: int, style: str = "single"):
    if style == "double":
        tl, tr, bl, br, h, v = "╔", "╗", "╚", "╝", "═", "║"
    elif style == "rounded":
        tl, tr, bl, br, h, v = "╭", "╮", "╰", "╯", "─", "│"
    elif style == "thick":
        tl, tr, bl, br, h, v = "┏", "┓", "┗", "┛", "━", "┃"
    else:
        tl, tr, bl, br, h, v = "┌", "┐", "└", "┘", "─", "│"
    for x in range(x1 + 1, x2):
        canvas[y1][x] = h
        canvas[y2][x] = h
    for y in range(y1 + 1, y2):
        canvas[y][x1] = v
        canvas[y][x2] = v
    canvas[y1][x1] = tl
    canvas[y1][x2] = tr
    canvas[y2][x1] = bl
    canvas[y2][x2] = br


def _render_panel(
    scene_desc: str,
    dialogue: list[tuple[str, str]],
    caption: str,
    internal: str,
    sfx: str,
    panel_num: int,
    width: int = PANEL_W,
) -> str:
    # ---- pass 1: calculate required height ----
    req = 2  # top margin before scene
    if scene_desc:
        req += len(_wrap_text(f"Scene: {scene_desc}", width - 6)) + 1
    has_stick = len(dialogue) >= 1
    if has_stick:
        req += STICK_H + 1
    max_di_lines = 0
    for _, t in dialogue:
        n = len(_wrap_text(t, width - 16))
        max_di_lines = max(max_di_lines, n)
    if max_di_lines:
        req += max_di_lines + 1
    if caption:
        req += len(_wrap_text(caption, width - 6)) + 1
    if internal:
        req += len(_wrap_text(f"({internal})", width - 6)) + 1
    if sfx:
        req += 2
    req = max(req, PANEL_H_MIN)

    canvas = _blank_canvas(req + 2, width + 2)
    _draw_box(canvas, 0, 0, req + 1, width + 1, "single")
    header = f" Panel {panel_num} "
    for i, ch in enumerate(header):
        canvas[0][2 + i] = ch

    cy = 2

    # scene description
    if scene_desc:
        scene_lines = _wrap_text(f"Scene: {scene_desc}", width - 6)
        for line in scene_lines:
            for j, ch in enumerate(line):
                canvas[cy][3 + j] = ch
            cy += 1
        cy += 1

    # stick figures (relative positioning)
    stick_left_col = max(2, int(width * 0.08))
    stick_right_col = width - max(2, int(width * 0.12))
    if has_stick:
        _render_stick(cy, stick_left_col, canvas, panel_width=width)
    if len(dialogue) >= 2:
        _render_stick(cy, stick_right_col, canvas, panel_width=width)

    # dialogue (render below stick figures)
    for i, (speaker, text) in enumerate(dialogue):
        dy = cy + STICK_H + 1
        col = stick_left_col + int(width * 0.08) if i == 0 else stick_right_col - int(width * 0.08)
        prefix = f"{speaker}: "
        full = prefix + text
        wrapped = _wrap_text(full, width - col - 8)
        for j, line in enumerate(wrapped):
            for k, ch in enumerate(line):
                if dy + j < len(canvas) and col + k < width + 2:
                    canvas[dy + j][col + k] = ch

    if has_stick:
        cy += STICK_H + 1 + max_di_lines

    # caption
    if caption:
        cy += 1
        for line in _wrap_text(caption, width - 6):
            for j, ch in enumerate(line):
                if cy < len(canvas) and 4 + j < width + 2:
                    canvas[cy][4 + j] = ch
            cy += 1

    # internal thought
    if internal:
        cy += 1
        for line in _wrap_text(f"({internal})", width - 6):
            if cy < len(canvas):
                for j, ch in enumerate(line):
                    col = 4 + j
                    if col < width + 2:
                        canvas[cy][col] = ch
                if len(canvas[cy]) > 3:
                    canvas[cy][3] = "("
            cy += 1

    # SFX
    if sfx:
        cy += 1
        for line in _wrap_text(f"[{sfx}]", width - 6):
            if cy < len(canvas):
                start_col = max(2, width - len(line) - 2)
                for j, ch in enumerate(line):
                    col = start_col + j
                    if col < width + 2:
                        canvas[cy][col] = ch
            cy += 1

    return _canvas_to_str(canvas)


def _extract_dialogue(panel: dict) -> list[tuple[str, str]]:
    dialogue = []
    for k, v in panel.items():
        if k in ("panel", "visual", "style_note", "text_to_image_prompt",
                 "caption", "internal_thought", "sfx", "page", "narration", "scene_direction"):
            continue
        if isinstance(v, str) and v.strip():
            dialogue.append((k, v))
    return dialogue


def _narrative_to_ascii(data: dict, chapter_key: str = None) -> str:
    output_parts = []
    chapter_keys = sorted([k for k in data if CHAPTER_KEY_RE.match(k)],
                          key=lambda k: int(k.split("_")[1]))
    if chapter_key:
        chapter_keys = [k for k in chapter_keys if k == chapter_key]

    for ck in chapter_keys:
        ch = data[ck]
        ch_title = ch.get("title", ck)
        output_parts.append("")
        output_parts.append(f"  ══ {ch_title} ══")
        output_parts.append("")

        panels = ch.get("panels", [])
        for i, panel in enumerate(panels):
            scene = panel.get("visual", panel.get("scene_direction", ""))
            dialogue = _extract_dialogue(panel)
            cap = panel.get("caption", "")
            internal = panel.get("internal_thought", "")
            sfx = panel.get("sfx", "")
            ascii_panel = _render_panel(
                scene_desc=scene,
                dialogue=dialogue,
                caption=cap,
                internal=internal,
                sfx=sfx,
                panel_num=panel.get("panel", i + 1),
            )
            output_parts.append(ascii_panel)
            output_parts.append("")

    return "\n".join(output_parts)


def _narrative_to_html(data: dict) -> str:
    series = data.get("series", {})
    title = series.get("title", "ASCII Comic")
    subtitle = series.get("subtitle", "")

    chapters_html = []
    chapter_keys = sorted([k for k in data if CHAPTER_KEY_RE.match(k)],
                          key=lambda k: int(k.split("_")[1]))

    for ck in chapter_keys:
        ch = data[ck]
        ch_title = ch.get("title", ck)
        summary = ch.get("summary", "")
        panels = ch.get("panels", [])

        panels_html = []
        for i, panel in enumerate(panels):
            scene = panel.get("visual", panel.get("scene_direction", ""))
            dialogue = _extract_dialogue(panel)
            cap = panel.get("caption", "")
            internal = panel.get("internal_thought", "")
            sfx = panel.get("sfx", "")
            ascii_panel = _render_panel(
                scene_desc=scene,
                dialogue=dialogue,
                caption=cap,
                internal=internal,
                sfx=sfx,
                panel_num=panel.get("panel", i + 1),
            )
            escaped = (ascii_panel
                       .replace("&", "&amp;")
                       .replace("<", "&lt;")
                       .replace(">", "&gt;"))
            panels_html.append(f'<pre class="ascii-panel">{escaped}</pre>')

        chapters_html.append(f"""
        <section class="chapter" id="{ck}">
          <div class="chapter-header">
            <h2>{ch_title}</h2>
            <div class="summary">{summary}</div>
          </div>
          <div class="panels">
            {''.join(panels_html)}
          </div>
        </section>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} — ASCII Edition</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0D0D1A; color: #E0E0E0; font-family: 'Courier New', monospace; }}
  .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
  h1 {{ color: #C9A84C; text-align: center; font-size: 1.4em; margin: 20px 0 4px; }}
  .subtitle {{ color: #8888AA; text-align: center; font-style: italic; margin-bottom: 20px; }}
  .chapter {{ margin: 24px 0; background: #0D0D1A; border: 1px solid #2A2A4A; padding: 16px; }}
  .chapter-header h2 {{ color: #C9A84C; font-size: 1.1em; margin-bottom: 8px; }}
  .summary {{ color: #8888AA; font-style: italic; margin: 10px 0; font-size: 0.8em; }}
  .ascii-panel {{ background: #0A0A14; color: #C0C0D0; padding: 8px; margin: 8px 0;
                  border-left: 2px solid #2A2A4A; font-size: 11px; line-height: 1.15;
                  overflow-x: auto; white-space: pre; }}
  .controls {{ text-align: center; margin: 16px 0; }}
  .toggle {{ background: #2A2A4A; color: #C9A84C; border: 1px solid #4A4A6A;
             padding: 6px 16px; cursor: pointer; font-family: monospace; }}
</style>
</head>
<body>
<div class="container">
  <h1>{title}</h1>
  <div class="subtitle">{subtitle} — ASCII Art Edition</div>
  <div class="controls">
    <button class="toggle" onclick="document.querySelectorAll('.ascii-panel').forEach(p=>p.style.display=p.style.display==='none'?'block':'none')">
      Toggle All Panels
    </button>
  </div>
  {''.join(chapters_html)}
</div>
</body>
</html>"""


@register_skill("ascii_comic", "publishing")
class AsciiComicSkill(BaseSkill):
    name = "ascii_comic"
    description = "Render comic narratives as ASCII art — stick figures, speech bubbles, scene descriptions — pure math, real-time"
    author = "ClawDia"
    version = "1.0.0"
    category = "publishing"
    tags = ["comic", "ascii", "art", "real-time", "renderer", "stick-figure"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["render", "render_chapter", "compile_html", "list"],
                "default": "render",
            },
            "narrative": {"type": "string", "default": ""},
            "chapter": {"type": "string", "default": ""},
        },
    }

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "render")
        narrative_name = kwargs.get("narrative", "")
        chapter = kwargs.get("chapter", "")

        if action == "list":
            return self._list()

        if not narrative_name:
            return {"error": "narrative name required", "result": None}

        data = self._load(narrative_name)
        if "error" in data:
            return data

        if action == "render":
            ascii_text = _narrative_to_ascii(data, chapter if chapter else None)
            return {"error": None, "result": {"format": "text", "content": ascii_text}}

        if action == "render_chapter":
            if not chapter:
                return {"error": "chapter required", "result": None}
            ascii_text = _narrative_to_ascii(data, chapter)
            return {"error": None, "result": {"format": "text", "chapter": chapter, "content": ascii_text}}

        if action == "compile_html":
            html = _narrative_to_html(data)
            out_name = f"{Path(narrative_name).stem}_ascii.html"
            out_path = OUTPUT_DIR / out_name
            out_path.write_text(html, encoding="utf-8")
            return {"error": None, "result": {"format": "html", "path": str(out_path)}}

        return {"error": f"Unknown action: {action}", "result": None}

    def _list(self) -> dict:
        if not NARRATIVES_DIR.exists():
            return {"error": f"Narratives dir not found: {NARRATIVES_DIR}", "result": None}
        files = sorted(NARRATIVES_DIR.glob("*.json"))
        return {"error": None, "result": {
            "narratives": [f.name for f in files],
            "count": len(files),
        }}

    def _load(self, name: str) -> dict:
        path = NARRATIVES_DIR / name
        if not path.exists():
            for f in NARRATIVES_DIR.glob("*.json"):
                if name.lower() in f.stem.lower():
                    path = f
                    break
            else:
                return {"error": f"Narrative '{name}' not found", "result": None}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            return {"error": f"Failed to parse {path.name}: {e}", "result": None}

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, dict):
            r = self.execute(**payload)
        else:
            r = self.execute(action="render", narrative=str(payload))
        if r.get("error"):
            return False, r["error"]
        return True, r["result"]
