import functools
import hashlib
import io
import json
import os
import re as _re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import BaseSkill, register_skill, SkillContext

NARRATIVES_DIR = Path(r"C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\ComicCookCreatorStudio\narratives")
OUTPUT_DIR = Path(__file__).resolve().parent / "comic_output"
OUTPUT_DIR.mkdir(exist_ok=True)
CACHE_DIR = OUTPUT_DIR / "_cache"
CACHE_DIR.mkdir(exist_ok=True)
FONTS_DIR = Path(__file__).resolve().parent / "fonts"

CHAPTER_KEY_RE = _re.compile(r"^chapter_\d+$")

PAGE_W = 6.875
PAGE_H = 10.438
MARGIN = 0.375


def _get_cache_key(data: dict) -> str:
    return hashlib.md5(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


def _check_cache(data: dict, fmt: str) -> Optional[Path]:
    key = _get_cache_key(data)
    cache_path = CACHE_DIR / f"{key}.{fmt}"
    if cache_path.exists():
        return cache_path
    return None


def _write_cache(data: dict, fmt: str, content: bytes):
    key = _get_cache_key(data)
    (CACHE_DIR / f"{key}.{fmt}").write_bytes(content)


def _write_cache_text(data: dict, fmt: str, content: str):
    key = _get_cache_key(data)
    (CACHE_DIR / f"{key}.{fmt}").write_text(content, encoding="utf-8")


@register_skill("comic_compiler", "publishing")
class ComicCompilerSkill(BaseSkill):
    name = "comic_compiler"
    description = "Compile narrative JSON into PDF/HTML with TTS narration"
    author = "ClawDia / DeepSeek"
    version = "1.0.0"
    category = "publishing"
    tags = ["comic", "pdf", "html", "tts", "narration", "compiler"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "list", "load", "compile_pdf", "compile_html",
                    "read_chapter", "read_all",
                ],
                "default": "list",
            },
            "narrative": {"type": "string", "default": ""},
            "chapter": {"type": "string", "default": ""},
            "output_format": {"type": "string", "enum": ["pdf", "html"], "default": "html"},
        },
    }

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "list")
        narrative_name = kwargs.get("narrative", "")
        chapter_key = kwargs.get("chapter", "")

        if action == "list":
            return self._list_narratives()

        if not narrative_name:
            return {"error": "narrative name required", "result": None}

        data = self._load_narrative(narrative_name)
        if "error" in data:
            return data

        if action == "load":
            return {"error": None, "result": self._summarize(data)}

        cached = _check_cache(data, "pdf" if action == "compile_pdf" else "html")
        if cached:
            return {"error": None, "result": {"path": str(cached), "format": "pdf" if action == "compile_pdf" else "html", "cached": True}}

        if action == "compile_pdf":
            path = self._compile_pdf(data, narrative_name)
            if path:
                _write_cache(data, "pdf", path.read_bytes())
                return {"error": None, "result": {"path": str(path), "format": "pdf"}}
            return {"error": "PDF compilation failed", "result": None}

        if action == "compile_html":
            path = self._compile_html(data, narrative_name)
            if path:
                _write_cache_text(data, "html", path.read_text(encoding="utf-8"))
                return {"error": None, "result": {"path": str(path), "format": "html"}}
            return {"error": "HTML compilation failed", "result": None}

        if action == "read_chapter":
            narration = self._get_chapter_narration(data, chapter_key)
            if "error" in narration:
                return narration
            return {"error": None, "result": {"narration": narration["narration"], "chapter": chapter_key}}

        if action == "read_all":
            narrations = self._get_all_narrations(data)
            return {"error": None, "result": {"chapters": narrations}}

        return {"error": f"Unknown action: {action}", "result": None}

    def _list_narratives(self) -> dict:
        if not NARRATIVES_DIR.exists():
            return {"error": f"Narratives dir not found: {NARRATIVES_DIR}", "result": None}
        files = sorted(NARRATIVES_DIR.glob("*.json"))
        narratives = []
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                series = data.get("series", {})
                title = series.get("title", f.stem)
                subtitle = series.get("subtitle", "")
                ch_count = len([k for k in data if CHAPTER_KEY_RE.match(k)])
                panel_count = 0
                for k in data:
                    if isinstance(data.get(k), dict) and "panels" in data[k]:
                        panel_count += len(data[k]["panels"])
                narratives.append({
                    "filename": f.name,
                    "title": title,
                    "subtitle": subtitle,
                    "chapters": ch_count,
                    "panels": panel_count,
                })
            except Exception:
                narratives.append({"filename": f.name, "title": f.stem, "error": "parse failed"})
        return {"error": None, "result": {"narratives": narratives, "count": len(narratives)}}

    def _load_narrative(self, name: str) -> dict:
        path = NARRATIVES_DIR / name
        if not path.exists():
            for f in NARRATIVES_DIR.glob("*.json"):
                if name.lower() in f.stem.lower():
                    path = f
                    break
            else:
                all_names = [f.name for f in NARRATIVES_DIR.glob("*.json")]
                return {"error": f"Narrative '{name}' not found. Available: {', '.join(all_names[:10])}", "result": None}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            return {"error": f"Failed to parse {path.name}: {e}", "result": None}

    def _summarize(self, data: dict) -> dict:
        series = data.get("series", {})
        chapters = []
        for k, v in data.items():
            if CHAPTER_KEY_RE.match(k) and isinstance(v, dict):
                chapters.append({
                    "key": k,
                    "title": v.get("title", ""),
                    "page_count": v.get("page_count", 0),
                    "summary": v.get("summary", ""),
                    "panel_count": len(v.get("panels", [])),
                })
        return {
            "title": series.get("title", ""),
            "subtitle": series.get("subtitle", ""),
            "genre": series.get("genre", ""),
            "logline": series.get("logline", ""),
            "chapters": chapters,
        }

    def _get_chapter_panels(self, data: dict, chapter_key: str) -> list:
        ch = data.get(chapter_key)
        if not ch or not isinstance(ch, dict):
            return []
        return ch.get("panels", [])

    def _extract_narration_text(self, panel: dict) -> str:
        lines = []
        cap = panel.get("caption", "")
        if cap:
            lines.append(cap)
        internal = panel.get("internal_thought", "")
        if internal:
            lines.append(internal)
        for k, v in panel.items():
            if k in ("panel", "visual", "style_note", "text_to_image_prompt",
                     "caption", "internal_thought", "sfx", "page"):
                continue
            if isinstance(v, str) and v.strip():
                lines.append(f"{k.title()} says: {v}")
        sfx = panel.get("sfx", "")
        if sfx:
            lines.append(f"[{sfx}]")
        return " ".join(lines)

    def _get_chapter_narration(self, data: dict, chapter_key: str) -> dict:
        panels = self._get_chapter_panels(data, chapter_key)
        if not panels:
            available = [k for k in data if CHAPTER_KEY_RE.match(k)]
            return {"error": f"Chapter '{chapter_key}' not found. Available: {available}", "result": None}
        parts = []
        for i, panel in enumerate(panels):
            visual = panel.get("visual", "")
            text = self._extract_narration_text(panel)
            parts.append(f"Panel {i + 1}: {visual[:100]}. {text}")
        return {"narration": " ".join(parts), "panel_count": len(panels)}

    def _get_all_narrations(self, data: dict) -> list:
        chapters = []
        for k in sorted(data.keys()):
            if CHAPTER_KEY_RE.match(k):
                nar = self._get_chapter_narration(data, k)
                if "error" not in nar:
                    ch_data = data[k]
                    chapters.append({
                        "key": k,
                        "title": ch_data.get("title", k),
                        "narration": nar["narration"],
                        "panel_count": nar["panel_count"],
                    })
        return chapters

    def _compile_pdf(self, data: dict, name: str) -> Optional[Path]:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.pdfgen import canvas
            from reportlab.lib.colors import HexColor
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            return None

        series = data.get("series", {})
        title = series.get("title", name)
        out_path = OUTPUT_DIR / f"{Path(name).stem}.pdf"

        if FONTS_DIR.exists():
            for font_file in sorted(FONTS_DIR.glob("*.ttf")):
                try:
                    pdfmetrics.registerFont(TTFont(font_file.stem, str(font_file)))
                except Exception:
                    pass

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        pw, ph = letter

        def wrap_text(text, max_w, font_size):
            c.setFont("Helvetica", font_size)
            words = text.split()
            lines, cur = [], ""
            for w in words:
                test = f"{cur} {w}".strip()
                if c.stringWidth(test, "Helvetica", font_size) < max_w:
                    cur = test
                else:
                    lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            return lines

        y = ph - MARGIN * inch
        c.setFillColor(HexColor("#0D0D1A"))
        c.rect(0, 0, pw, ph, fill=1, stroke=0)

        c.setFillColor(HexColor("#C9A84C"))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(pw / 2, y - 20, title)
        c.bookmarkPage("cover")
        c.addOutlineEntry("Cover", "cover", level=0)
        y -= 50

        chapter_keys = sorted([k for k in data if CHAPTER_KEY_RE.match(k)],
                               key=lambda k: int(k.split("_")[1]))
        for ck in chapter_keys:
            if y < 100:
                c.showPage()
                y = ph - MARGIN * inch
                c.setFillColor(HexColor("#0D0D1A"))
                c.rect(0, 0, pw, ph, fill=1, stroke=0)

            ch = data[ck]
            ch_title = ch.get("title", ck)
            c.bookmarkPage(ck)
            c.addOutlineEntry(ch_title, ck, level=0)
            c.setFillColor(HexColor("#C9A84C"))
            c.setFont("Helvetica-Bold", 14)
            c.drawString(MARGIN * inch, y, ch_title)
            y -= 20

            panels = ch.get("panels", [])
            for i, panel in enumerate(panels):
                if y < 60:
                    c.showPage()
                    y = ph - MARGIN * inch
                    c.setFillColor(HexColor("#0D0D1A"))
                    c.rect(0, 0, pw, ph, fill=1, stroke=0)
                    c.setFillColor(HexColor("#C9A84C"))
                    c.setFont("Helvetica-Bold", 14)
                    c.drawString(MARGIN * inch, y, f"{ch_title} (cont.)")
                    y -= 20

                c.setFillColor(HexColor("#4A4A6A"))
                c.setFont("Helvetica-Bold", 9)
                c.drawString(MARGIN * inch + 4, y, f"Panel {panel.get('panel', i + 1)}")
                y -= 14

                t2i = panel.get("text_to_image_prompt", "")
                if t2i:
                    try:
                        from .vision_skills import vision_skills as _vs
                        img_path = _vs._generate_from_prompt(t2i)
                        if img_path:
                            c.drawImage(str(img_path), MARGIN * inch + 4, y - 120, width=3 * inch, height=2 * inch, preserveAspectRatio=True)
                            y -= 130
                    except Exception:
                        pass

                visual = panel.get("visual", "")
                c.setFillColor(HexColor("#8888AA"))
                c.setFont("Helvetica-Oblique", 8)
                for line in wrap_text(visual, pw - 2 * MARGIN * inch - 8, 8):
                    c.drawString(MARGIN * inch + 4, y, line)
                    y -= 11

                cap = panel.get("caption", "")
                if cap:
                    c.setFillColor(HexColor("#F0CC70"))
                    c.setFont("Helvetica-Oblique", 8)
                    for line in wrap_text(cap, pw - 2 * MARGIN * inch - 8, 8):
                        c.drawString(MARGIN * inch + 4, y, line)
                        y -= 11

                for k, v in panel.items():
                    if k in ("panel", "visual", "style_note", "text_to_image_prompt",
                             "caption", "internal_thought", "sfx", "page"):
                        continue
                    if isinstance(v, str) and v.strip():
                        c.setFillColor(HexColor("#F7F7F7"))
                        c.setFont("Helvetica", 8)
                        for line in wrap_text(f"{k}: {v}", pw - 2 * MARGIN * inch - 8, 8):
                            c.drawString(MARGIN * inch + 4, y, line)
                            y -= 11

                y -= 6

        c.save()
        buf.seek(0)
        out_path.write_bytes(buf.getvalue())
        return out_path

    def _compile_html(self, data: dict, name: str) -> Optional[Path]:
        series = data.get("series", {})
        title = series.get("title", Path(name).stem)
        out_path = OUTPUT_DIR / f"{Path(name).stem}.html"

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
                visual = panel.get("visual", "")
                cap = panel.get("caption", "")
                internal = panel.get("internal_thought", "")
                t2i = panel.get("text_to_image_prompt", "")
                sfx = panel.get("sfx", "")

                img_html = ""
                if t2i:
                    try:
                        from .vision_skills import vision_skills as _vs
                        img_path = _vs._generate_from_prompt(t2i)
                        if img_path:
                            img_html = f'<img src="{img_path}" alt="Generated panel art" style="max-width:100%;border-radius:4px;margin:8px 0;">'
                    except Exception:
                        pass

                dialogue_lines = []
                for k, v in panel.items():
                    if k in ("panel", "visual", "style_note", "text_to_image_prompt",
                             "caption", "internal_thought", "sfx", "page"):
                        continue
                    if isinstance(v, str) and v.strip():
                        dialogue_lines.append(f'<div class="dialogue"><span class="speaker">{k}:</span> {v}</div>')

                caps = []
                if cap:
                    caps.append(f'<div class="caption">{cap}</div>')
                if internal:
                    caps.append(f'<div class="caption internal">{internal}</div>')
                if sfx:
                    caps.append(f'<div class="sfx">[{sfx}]</div>')

                panels_html.append(f"""
            <div class="panel">
              <div class="panel-header">Panel {panel.get('panel', i + 1)}</div>
              <div class="panel-visual">{visual}</div>
              {img_html}
              {''.join(caps)}
              {''.join(dialogue_lines)}
            </div>""")

            chapters_html.append(f"""
          <section class="chapter" id="{ck}">
            <div class="chapter-header">
              <h2>{ch_title}</h2>
              <button class="speak-btn" onclick="speakChapter('{ck}')">Speak</button>
              <div class="summary">{summary}</div>
            </div>
            <div class="panels">
              {''.join(panels_html)}
            </div>
          </section>""")

        narration_json = json.dumps(self._get_all_narrations(data))

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0D0D1A; color: #F7F7F7; font-family: Georgia, serif; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
  h1 {{ color: #C9A84C; text-align: center; font-size: 1.8em; margin: 20px 0 4px; }}
  .subtitle {{ color: #8888AA; text-align: center; font-style: italic; margin-bottom: 20px; }}
  .chapter {{ margin: 30px 0; background: #141428; border: 1px solid #2A2A4A; border-radius: 8px; padding: 20px; }}
  .chapter-header h2 {{ color: #C9A84C; font-size: 1.3em; margin-bottom: 8px; display: inline; }}
  .speak-btn {{ float: right; background: #C9A84C; color: #0D0D1A; border: none; padding: 6px 16px; border-radius: 4px; font-weight: bold; cursor: pointer; }}
  .speak-btn:hover {{ background: #F0CC70; }}
  .summary {{ color: #8888AA; font-style: italic; margin: 10px 0; font-size: 0.9em; }}
  .panel {{ background: #1A1A30; border: 1px solid #2A2A4A; border-radius: 6px; margin: 10px 0; padding: 12px; }}
  .panel-header {{ color: #4A4A6A; font-size: 0.75em; font-weight: bold; letter-spacing: 0.08em; margin-bottom: 6px; }}
  .panel-visual {{ color: #8888AA; font-style: italic; font-size: 0.85em; margin-bottom: 8px; line-height: 1.5; }}
  .caption {{ color: #F0CC70; font-style: italic; padding: 2px 0 2px 8px; border-left: 3px solid #C9A84C; margin: 4px 0; }}
  .caption.internal {{ color: #8888FF; }}
  .sfx {{ color: #D93535; font-weight: bold; font-size: 1.05em; }}
  .dialogue {{ margin: 3px 0; font-size: 0.9em; line-height: 1.5; }}
  .speaker {{ color: #C9A84C; font-weight: bold; }}
  .controls {{ text-align: center; margin: 20px 0; }}
  .global-speak {{ background: #2B6CB0; color: white; border: none; padding: 10px 24px; border-radius: 6px; font-weight: bold; cursor: pointer; margin: 0 8px; }}
  .global-speak:hover {{ background: #63B3ED; }}
  .stop-btn {{ background: #9B1C1C; color: white; border: none; padding: 10px 24px; border-radius: 6px; font-weight: bold; cursor: pointer; }}
  #status {{ color: #4A4A6A; text-align: center; font-style: italic; margin: 10px 0; }}
</style>
</head>
<body>
<div class="container">
  <h1>{title}</h1>
  <div class="subtitle">{series.get("subtitle", "")} &middot; {series.get("genre", "")}</div>

  <div class="controls">
    <button class="global-speak" onclick="speakAll()">Read All</button>
    <button class="stop-btn" onclick="stopSpeaking()">Stop</button>
  </div>
  <div id="status">Ready</div>

  {''.join(chapters_html)}
</div>

<script>
const NARRATIONS = {narration_json};
let currentUtterance = null;
let isSpeaking = false;

function setStatus(msg) {{ document.getElementById('status').textContent = msg; }}

function speakChapter(chapterKey) {{
  if (isSpeaking) {{ window.speechSynthesis.cancel(); }}
  const ch = NARRATIONS.find(n => n.key === chapterKey);
  if (!ch) {{ setStatus('Chapter not found'); return; }}
  const text = ch.title + '. ' + ch.narration;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.9;
  utterance.pitch = 1.0;
  currentUtterance = utterance;
  isSpeaking = true;
  setStatus('Reading: ' + ch.title);
  utterance.onend = () => {{ isSpeaking = false; setStatus('Done: ' + ch.title); }};
  utterance.onerror = () => {{ isSpeaking = false; setStatus('Error'); }};
  window.speechSynthesis.speak(utterance);
}}

function speakAll() {{
  if (isSpeaking) {{ window.speechSynthesis.cancel(); }}
  const allText = NARRATIONS.map(ch => ch.title + '. ' + ch.narration).join('. ');
  const utterance = new SpeechSynthesisUtterance(allText);
  utterance.rate = 0.9;
  currentUtterance = utterance;
  isSpeaking = true;
  setStatus('Reading all chapters...');
  utterance.onend = () => {{ isSpeaking = false; setStatus('Finished reading all chapters.'); }};
  utterance.onerror = () => {{ isSpeaking = false; setStatus('Error'); }};
  window.speechSynthesis.speak(utterance);
}}

function stopSpeaking() {{
  if (isSpeaking) {{
    window.speechSynthesis.cancel();
    isSpeaking = false;
    setStatus('Stopped.');
  }}
}}

document.addEventListener('keydown', (e) => {{
  if (e.key === 'Escape' && isSpeaking) {{
    window.speechSynthesis.cancel();
    isSpeaking = false;
    setStatus('Stopped.');
  }}
}});
</script>
</body>
</html>"""
        out_path.write_text(html, encoding="utf-8")
        return out_path

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, str):
            return True, self.execute(action="load", narrative=payload)
        if isinstance(payload, dict):
            r = self.execute(**payload)
            if r.get("error"):
                return False, r["error"]
            return True, r["result"]
        return True, self.execute(action="list")
