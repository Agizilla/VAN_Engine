"""Essay Skill — unified visual composition generator.
Generates self-contained HTML/CSS visual essays in 10 formats.

Usage:
  POST /hooks/essay_generate  {"text":"...", "format":"timeline", "style":"modern"}
"""

try:
    from .base import BaseSkill, register_skill
except ImportError:
    from skills.base import BaseSkill, register_skill

import html as htmlmod
import json
import random
import re

_THEMES = {
    "modern": {"bg":"#0f172a","fg":"#e2e8f0","accent1":"#3b82f6","accent2":"#8b5cf6","accent3":"#06b6d4","card":"#1e293b","border":"#334155","heading":"#f8fafc"},
    "vintage":{"bg":"#fef3c7","fg":"#78350f","accent1":"#d97706","accent2":"#92400e","accent3":"#b45309","card":"#fffbeb","border":"#fde68a","heading":"#451a03"},
    "minimal":{"bg":"#ffffff","fg":"#1e293b","accent1":"#64748b","accent2":"#94a3b8","accent3":"#475569","card":"#f8fafc","border":"#e2e8f0","heading":"#0f172a"},
    "neon":   {"bg":"#0a0a0a","fg":"#f0f0f0","accent1":"#ff00ff","accent2":"#00ffff","accent3":"#39ff14","card":"#1a1a2e","border":"#333355","heading":"#ffffff"},
    "nature": {"bg":"#f0fdf4","fg":"#166534","accent1":"#22c55e","accent2":"#15803d","accent3":"#4ade80","card":"#dcfce7","border":"#bbf7d0","heading":"#14532d"},
    "dark":   {"bg":"#000000","fg":"#a3a3a3","accent1":"#737373","accent2":"#525252","accent3":"#404040","card":"#171717","border":"#262626","heading":"#fafafa"},
}

_ICONS = {
    "infographic":"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAbwAAAG8B8aLcQwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAEoSURBVDiNpZMxTsNAEEX/rNeOAwUlLVdA4gJcAokLUNDRcAQkLkCBaOgouQIVHZyAgoKSK0QiJI5jr3cohuxarJP8aVfz5s+b0QIAc3MPAET3DwA3cz8HkAPIAOQAzs3cARyauQO4MvNKaw0RyQAszDwDcDH/0VrPD4UNgKnWGkQkAC4BzMx9a60DkH/yRGsNAD3AT60VInIPYFdrHQAMgGmt9aO1fjf3QwAwsxOtdW+1fgLwYu4Hzcz23xu01gCwAPBijxGRFMAUQNJaewXwCqCqte4BpADmnzFEpANwDmAKIKm1vgGYAYi11h5ADOAdQAxgCqCqteYAxgAqEXkCkJn7Q4iIDK31l4jsAJwDaK0PAL4BfAH4/h8GEXkC0FprAC5EJNkf/gF7/k3rvbWe6QAAAABJRU5ErkJggg==",
    "timeline":"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAbwAAAG8B8aLcQwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAEOSURBVDiNpZMxTsNAEEX/rNeOAxUlLVdA4gJcAokLUNDRcAQkLkCBaOgouQIVHZyAgoKSK0QiJI5jr3cohuxarJP8aVfz5s+b0QIAc3MPAET3DwA3cz8HkAPIAOQAzs3cARyauQO4MvNKaw0RyQAszDwDcDH/0VrPD4UNgKnWGkQkAC4BzMx9a60DkH/yRGsNAD3AT60VInIPYFdrHQAMgGmt9aO1fjf3QwAwsxOtdW+1fgLwYu4Hzcz23xu01gCwAPBijxGRFMAUQNJaewXwCqCqte4BpADmnzFEpANwDmAKIKm1vgGYAYi11h5ADOAdQAxgCqCqteYAxgAqEXkCkJn7Q4iIDK31l4jsAJwDaK0PAL4BfAH4/h8GEXkC0FprAC5EJNkf/gF7/k3rvbWe6QAAAABJRU5ErkJggg==",
}


def _t(t: str, theme: str) -> str:
    return _THEMES.get(theme, _THEMES["modern"]).get(t, _THEMES["modern"][t])


def _base_css(theme: str) -> str:
    th = _THEMES.get(theme, _THEMES["modern"])
    return f"""<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:{th['bg']};color:{th['fg']};line-height:1.6}}
.essay{{max-width:960px;margin:0 auto;padding:2rem}}
h1,h2,h3,h4{{color:{th['heading']};font-weight:700;line-height:1.2}}
h1{{font-size:2rem;margin-bottom:0.5rem}}
h2{{font-size:1.5rem;margin-bottom:0.75rem;display:inline-block;border-bottom:3px solid {th['accent1']};padding-bottom:0.25rem}}
p{{margin-bottom:0.75rem}}
.tag{{display:inline-block;padding:0.15rem 0.6rem;border-radius:999px;font-size:0.75rem;font-weight:600;background:{th['accent1']};color:{th['bg']};margin-right:0.3rem;margin-bottom:0.3rem}}
.card{{background:{th['card']};border:1px solid {th['border']};border-radius:0.75rem;padding:1.25rem;margin-bottom:1rem}}
.glow{{box-shadow:0 0 20px {th['accent1']}33}}
</style>"""


def _render_infographic(text: str, theme: str, title: str) -> str:
    lines = [l for l in text.split("\n") if l.strip()]
    sections = []
    current = []
    for l in lines:
        if l.startswith("#") or l.startswith("##") or l.startswith("###"):
            if current: sections.append(" ".join(current)); current=[]
            sections.append(l.lstrip("#").strip())
        else: current.append(l)
    if current: sections.append(" ".join(current))
    if not sections: sections = [text]

    items_html = ""
    for i, s in enumerate(sections):
        words = s.split()
        mid = len(words)//2
        stat = str(len(words)) if words else "0"
        items_html += f"""<div class="card glow" style="border-left:4px solid {_t('accent1',theme) if i%2==0 else _t('accent2',theme)}">
<div style="font-size:2rem;font-weight:800;color:{_t('accent1',theme) if i%2==0 else _t('accent2',theme)};margin-bottom:0.25rem">{stat}</div>
<div>{htmlmod.escape(s)}</div>
</div>"""

    ttl = htmlmod.escape(title or "Infographic")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{ttl}</title>{_base_css(theme)}</head><body>
<div class="essay"><h1>{ttl}</h1><p style="color:{_t('accent1',theme)};font-size:0.9rem">infographic · {theme}</p>
{items_html}
</div></body></html>"""


def _render_timeline(text: str, theme: str, title: str) -> str:
    lines = [l for l in text.split("\n") if l.strip()]
    entries = []
    date = ""
    for l in lines:
        if re.match(r"^[\d]{1,4}[-/][\d]{1,2}[-/][\d]{1,4}$", l.strip()) or re.match(r"^\d{4}$", l.strip()) or re.match(r"^[A-Z][a-z]+ \d{4}", l.strip()):
            if date and entries: entries[-1]["content"] += f" ({l.strip()})"
            else: date = l.strip()
        elif l.startswith("- ") or l.startswith("* "):
            entries.append({"date": date or f"Entry {len(entries)+1}", "content": l[2:].strip()})
            date = ""
        elif entries:
            entries[-1]["content"] += " " + l.strip()
        else:
            entries.append({"date": date or f"Entry {len(entries)+1}", "content": l.strip()})
            date = ""
    if not entries: entries = [{"date":"1","content":text}]
    if date: entries.append({"date":date,"content":"—"})

    items = ""
    for i, e in enumerate(entries):
        side = "left" if i%2==0 else "right"
        items += f"""<div style="display:flex;justify-content:flex-{'end' if side=='right' else 'start'};padding-left:{'50%' if side=='right' else '0'};padding-right:{'50%' if side=='left' else '0'};position:relative;margin-bottom:1.5rem">
<div class="card" style="width:100%;position:relative">
<div style="position:absolute;{'right' if side=='left' else 'left'}:-8px;top:1rem;width:16px;height:16px;border-radius:50%;background:{_t('accent1',theme)};border:3px solid {_t('bg',theme)}"></div>
<div style="font-size:0.8rem;color:{_t('accent1',theme)};font-weight:700;margin-bottom:0.25rem">{htmlmod.escape(e['date'])}</div>
<div>{htmlmod.escape(e['content'])}</div>
</div></div>"""

    ttl = htmlmod.escape(title or "Timeline")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{ttl}</title>{_base_css(theme)}</head><body>
<div class="essay"><h1>{ttl}</h1>
<div style="position:relative;padding-left:0;padding-right:0">
<div style="position:absolute;left:50%;top:0;bottom:0;width:3px;background:{_t('border',theme)};transform:translateX(-50%)"></div>
{items}
</div></div></body></html>"""


def _render_aphorism(text: str, theme: str, title: str) -> str:
    lines = text.strip().split("\n")
    quote = lines[0] if lines else text
    attr = lines[1].strip().lstrip("-—–").strip() if len(lines)>1 else ""
    ttl = htmlmod.escape(title or "Aphorism")
    q = htmlmod.escape(quote)
    a = htmlmod.escape(attr)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{ttl}</title>{_base_css(theme)}</head><body>
<div class="essay" style="display:flex;align-items:center;justify-content:center;min-height:60vh">
<div class="card glow" style="max-width:600px;text-align:center;padding:3rem 2rem">
<div style="font-size:4rem;line-height:1;color:{_t('accent1',theme)};opacity:0.3;margin-bottom:-1rem">&ldquo;</div>
<blockquote style="font-size:1.5rem;font-style:italic;color:{_t('heading',theme)};margin:1rem 0">{q}</blockquote>
<div style="font-size:4rem;line-height:1;color:{_t('accent1',theme)};opacity:0.3;margin-top:-1rem;text-align:right">&rdquo;</div>
{a and f'<div style="margin-top:1rem;font-size:0.9rem;color:{_t("accent1",theme)}">— {a}</div>' or ''}
</div></div></body></html>"""


def _render_frameworks(text: str, theme: str, title: str) -> str:
    lines = [l for l in text.split("\n") if l.strip()]
    items = []
    for l in lines:
        parts = l.split(":", 1)
        items.append((parts[0].strip(), parts[1].strip() if len(parts)>1 else ""))
    if not items: items = [("Concept",text)]

    grid = ""
    for i, (k, v) in enumerate(items):
        grid += f"""<div class="card glow" style="border-top:3px solid {[_t('accent1',theme),_t('accent2',theme),_t('accent3',theme)][i%3]};padding:1rem">
<div style="font-size:1.1rem;font-weight:700;color:{_t('heading',theme)};margin-bottom:0.5rem">{htmlmod.escape(k)}</div>
<div style="font-size:0.9rem">{htmlmod.escape(v)}</div>
</div>"""

    ttl = htmlmod.escape(title or "Framework")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{ttl}</title>{_base_css(theme)}</head><body>
<div class="essay"><h1>{ttl}</h1>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;margin-top:1.5rem">{grid}</div>
</div></body></html>"""


def _render_comics(text: str, theme: str, title: str) -> str:
    panels = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[")]
    if not panels: panels = [text[:100]]
    pan = ""
    for i, p in enumerate(panels):
        pan += f"""<div class="card" style="min-height:120px;display:flex;flex-direction:column;justify-content:center;border:2px solid {_t('border',theme)};border-radius:0.5rem;padding:1rem">
<div style="font-size:0.7rem;text-transform:uppercase;color:{_t('accent1',theme)};margin-bottom:0.5rem">Panel {i+1}</div>
<div style="font-size:0.9rem">{htmlmod.escape(p[:120])}</div>
</div>"""

    ttl = htmlmod.escape(title or "Comic Strip")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{ttl}</title>{_base_css(theme)}</head><body>
<div class="essay"><h1>{ttl}</h1>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0.5rem;margin-top:1.5rem">{pan}</div>
</div></body></html>"""


def _render_comparison(text: str, theme: str, title: str) -> str:
    lines = [l for l in text.split("\n") if l.strip()]
    a_items = []; b_items = []
    mode = "a"
    for l in lines:
        if l.lower().startswith("vs") or l.lower().startswith("vs.") or l=="—" or l=="-":
            mode="b"; continue
        if mode=="a": a_items.append(l)
        else: b_items.append(l)
    if not a_items: a_items=["Option A"]; b_items=["Option B"]

    def col(items, accent, label):
        rows = "".join(f'<div style="padding:0.5rem 0;border-bottom:1px solid {_t("border",theme)};font-size:0.9rem">{htmlmod.escape(i)}</div>' for i in items)
        return f"""<div class="card" style="border-top:3px solid {accent};flex:1"><h3 style="color:{accent};margin-bottom:0.75rem">{label}</h3>{rows}</div>"""

    ttl = htmlmod.escape(title or "Comparison")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{ttl}</title>{_base_css(theme)}</head><body>
<div class="essay"><h1>{ttl}</h1>
<div style="display:flex;gap:1rem;margin-top:1.5rem">
{col(a_items, _t('accent1',theme), "A")}
{col(b_items, _t('accent2',theme), "B")}
</div></div></body></html>"""


def _render_stat(text: str, theme: str, title: str) -> str:
    lines = [l for l in text.split("\n") if l.strip()]
    stats = []
    for l in lines:
        parts = l.split(":", 1)
        if len(parts)==2:
            num = re.sub(r"[^0-9.%]", "", parts[1].strip())
            stats.append((parts[0].strip(), num or parts[1].strip()))
        else:
            words = l.split()
            if words: stats.append((words[0], " ".join(words[1:]) if len(words)>1 else l))
    if not stats: stats = [("Value",text)]

    cards = ""
    for i, (k, v) in enumerate(stats):
        cards += f"""<div class="card glow" style="text-align:center;border-bottom:3px solid {[_t('accent1',theme),_t('accent2',theme),_t('accent3',theme)][i%3]}">
<div style="font-size:2.5rem;font-weight:800;color:{_t('accent1',theme)};letter-spacing:-1px">{htmlmod.escape(v)}</div>
<div style="font-size:0.8rem;text-transform:uppercase;color:{_t('fg',theme)};opacity:0.7">{htmlmod.escape(k)}</div>
</div>"""

    ttl = htmlmod.escape(title or "Statistics")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{ttl}</title>{_base_css(theme)}</head><body>
<div class="essay"><h1>{ttl}</h1>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-top:1.5rem">{cards}</div>
</div></body></html>"""


def _render_poster(text: str, theme: str, title: str) -> str:
    lines = text.split("\n")
    headline = title or (lines[0] if lines else "Poster")
    body = " ".join(l.strip() for l in lines[1:] if l.strip()) if len(lines)>1 else text
    if body == headline: body = ""
    ttl = htmlmod.escape(headline)
    bd = htmlmod.escape(body[:300])
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{ttl}</title>{_base_css(theme)}</head><body>
<div class="essay" style="display:flex;align-items:center;justify-content:center;min-height:80vh">
<div class="card glow" style="text-align:center;padding:4rem 2rem;max-width:700px;border:2px solid {_t('accent1',theme)}">
<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:3px;color:{_t('accent1',theme)};margin-bottom:1.5rem">· {theme} ·</div>
<h1 style="font-size:2.5rem;margin-bottom:1rem;letter-spacing:-1px">{ttl}</h1>
{bd and f'<div style="font-size:1.1rem;opacity:0.85;margin:1.5rem 0;line-height:1.7">{bd}</div>' or ''}
<div style="margin-top:2rem"><span class="tag">EXHIBIT</span></div>
</div></div></body></html>"""


def _render_card(text: str, theme: str, title: str) -> str:
    lines = text.strip().split("\n")
    hd = title or (lines[0] if lines else "Card")
    bd = " ".join(l.strip() for l in lines[1:] if l.strip()) if len(lines)>1 else text
    if bd == hd: bd = ""
    ttl = htmlmod.escape(hd)
    b = htmlmod.escape(bd[:200])

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{ttl}</title>{_base_css(theme)}</head><body>
<div class="essay" style="display:flex;align-items:center;justify-content:center;min-height:50vh">
<div class="card glow" style="max-width:400px;padding:0;overflow:hidden">
<div style="height:6px;background:linear-gradient(90deg,{_t('accent1',theme)},{_t('accent2',theme)})"></div>
<div style="padding:1.5rem">
<div style="width:48px;height:48px;border-radius:12px;background:{_t('accent1',theme)};display:flex;align-items:center;justify-content:center;margin-bottom:1rem;font-size:1.5rem">✦</div>
<h3 style="margin-bottom:0.5rem">{ttl}</h3>
{b and f'<div style="font-size:0.85rem;opacity:0.8">{b}</div>' or ''}
<div style="margin-top:1rem;display:flex;gap:0.5rem"><span class="tag">{htmlmod.escape(theme)}</span><span class="tag" style="background:{_t('accent2',theme)}">card</span></div>
</div></div></div></body></html>"""


def _render_storyboard(text: str, theme: str, title: str) -> str:
    scenes = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("[") and not l.startswith("#")]
    if not scenes: scenes = [text[:100]]
    items = ""
    for i, s in enumerate(scenes):
        items += f"""<div class="card" style="display:flex;gap:1rem;align-items:flex-start">
<div style="min-width:80px;height:60px;background:{_t('accent1',theme)}22;border-radius:0.5rem;display:flex;align-items:center;justify-content:center;font-size:1.5rem;font-weight:800;color:{_t('accent1',theme)}">{i+1}</div>
<div style="flex:1"><div style="font-size:0.8rem;text-transform:uppercase;color:{_t('accent1',theme)};margin-bottom:0.25rem">Scene {i+1}</div>
<div style="font-size:0.9rem">{htmlmod.escape(s[:150])}</div></div></div>"""

    ttl = htmlmod.escape(title or "Storyboard")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{ttl}</title>{_base_css(theme)}</head><body>
<div class="essay"><h1>{ttl}</h1>
<div style="display:flex;flex-direction:column;gap:0.75rem;margin-top:1.5rem">{items}</div>
</div></body></html>"""


_FORMAT_RENDERERS = {
    "infographic": _render_infographic,
    "timeline": _render_timeline,
    "aphorism": _render_aphorism,
    "frameworks": _render_frameworks,
    "comics": _render_comics,
    "comparison": _render_comparison,
    "stat": _render_stat,
    "poster": _render_poster,
    "card": _render_card,
    "storyboard": _render_storyboard,
}
_FORMATS = list(_FORMAT_RENDERERS.keys())
_STYLES = list(_THEMES.keys())


@register_skill("essay_generate", "vision")
class EssaySkill(BaseSkill):
    name = "essay_generate"
    description = "Generate visual essay from text in 10 formats: infographic, timeline, aphorism, frameworks, comics, comparison, stat, poster, card, storyboard"
    category = "vision"
    version = "1.0.0"
    author = "ClawDia"
    tags = ["essay", "visual", "infographic", "timeline", "poster", "comics", "diagram", "composition"]
    required_libs = []
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text content to visualize"},
            "format": {"type": "string", "enum": _FORMATS, "description": "Visual format", "default": "infographic"},
            "style": {"type": "string", "enum": _STYLES, "description": "Color theme", "default": "modern"},
            "title": {"type": "string", "description": "Optional title", "default": ""},
        },
        "required": ["text"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "html": {"type": "string", "description": "Rendered HTML"},
            "format": {"type": "string"},
            "style": {"type": "string"},
            "char_count": {"type": "integer"},
        },
    }

    def execute(self, **kwargs):
        text = kwargs.get("text", "")
        fmt = kwargs.get("format", "infographic")
        style = kwargs.get("style", "modern")
        title = kwargs.get("title", "")

        if not text.strip():
            return {"error": "No text provided"}

        renderer = _FORMAT_RENDERERS.get(fmt)
        if not renderer:
            return {"error": f"Unknown format '{fmt}'. Choose: {', '.join(_FORMATS)}"}

        if style not in _STYLES:
            return {"error": f"Unknown style '{style}'. Choose: {', '.join(_STYLES)}"}

        html = renderer(text, style, title)
        return {
            "result": {
                "html": html,
                "format": fmt,
                "style": style,
                "char_count": len(text),
            }
        }
