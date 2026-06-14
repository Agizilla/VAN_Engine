"""
POST /hooks/emotion_svg
Generate an emotional SVG face from text input — returns Content-Type: image/svg+xml
"""
import json
from .base import BaseSkill, register_skill


# ── Emotion colour palettes ─────────────────────────────────────────
EMO_COLORS = {
    "neutral":  {"p": "#00f2fe", "s": "#4facfe", "a": "#7bf2ff"},
    "joy":      {"p": "#66ff99", "s": "#33cc77", "a": "#99ffbb"},
    "laugh":    {"p": "#88ffbb", "s": "#44dd88", "a": "#bbffdd"},
    "sad":      {"p": "#aa88ff", "s": "#7755dd", "a": "#ccbbff"},
    "surprise": {"p": "#66aaff", "s": "#3388dd", "a": "#99ccff"},
    "anger":    {"p": "#ff6666", "s": "#dd3333", "a": "#ff9999"},
    "fear":     {"p": "#cc66ff", "s": "#9933dd", "a": "#dd99ff"},
    "disgust":  {"p": "#88cc44", "s": "#66aa22", "a": "#aadd66"},
    "contempt": {"p": "#dd8844", "s": "#bb6622", "a": "#eebb66"},
    "tension":  {"p": "#ffaa44", "s": "#dd8822", "a": "#ffcc66"},
    "love":     {"p": "#ff88aa", "s": "#dd5588", "a": "#ffbbcc"},
    "mischief": {"p": "#ff66aa", "s": "#dd3388", "a": "#ff99bb"},
}

# Face-path templates: [mouth, eyes, brows]
FACES = {
    "neutral": [
        "M-12,30 Q0,36 12,30 Q0,42 -12,30",
        "M-20,-35 Q-10,-38 0,-32 Q10,-38 20,-35",
        "M-18,-22 Q-10,-26 0,-22 Q10,-26 18,-22",
    ],
    "smile": [
        "M-14,26 Q0,30 14,26 Q0,42 -14,26",
        "M-20,-36 Q-10,-40 0,-33 Q10,-40 20,-36",
        "M-18,-24 Q-10,-28 0,-24 Q10,-28 18,-24",
    ],
    "open": [
        "M-16,22 Q0,28 16,22 Q0,50 -16,22",
        "M-22,-38 Q-12,-42 0,-35 Q12,-42 22,-38",
        "M-20,-26 Q-10,-30 0,-26 Q10,-30 20,-26",
    ],
    "frown": [
        "M-14,34 Q0,38 14,34 Q0,30 -14,34",
        "M-20,-34 Q-10,-36 0,-31 Q10,-36 20,-34",
        "M-16,-20 Q-10,-24 0,-20 Q10,-24 16,-20",
    ],
    "angry": [
        "M-14,32 Q0,36 14,32 Q0,30 -14,32",
        "M-18,-32 Q-10,-34 0,-30 Q10,-34 18,-32",
        "M-14,-18 Q-8,-14 0,-18 Q8,-14 14,-18",
    ],
    "wide": [
        "M-18,20 Q0,26 18,20 Q0,52 -18,20",
        "M-24,-40 Q-12,-44 0,-36 Q12,-44 24,-40",
        "M-22,-28 Q-10,-32 0,-28 Q10,-32 22,-28",
    ],
}

EMO_TO_FACE = {
    "neutral": "neutral", "joy": "smile", "laugh": "open",
    "sad": "frown", "surprise": "wide", "anger": "angry",
    "fear": "wide", "disgust": "frown", "contempt": "smile",
    "tension": "wide", "love": "smile", "mischief": "smile",
}


def _build_svg(emotion: str) -> str:
    """Return the full SVG string for a given emotion."""
    c = EMO_COLORS.get(emotion, EMO_COLORS["neutral"])
    face_key = EMO_TO_FACE.get(emotion, "neutral")
    f = FACES[face_key]
    mouth, eyes, brows = f[0], f[1], f[2]

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-200 -200 400 400" style="background:#05050a">
<defs>
<filter id="h" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" result="b1"/><feGaussianBlur stdDeviation="3" result="b2"/><feMerge><feMergeNode in="b1"/><feMergeNode in="b2"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="s" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="rg1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{c["s"]}" stop-opacity="0.2"/><stop offset="50%" stop-color="{c["p"]}" stop-opacity="0.8"/><stop offset="100%" stop-color="{c["s"]}" stop-opacity="0.1"/></linearGradient>
<linearGradient id="rg2" x1="100%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="{c["p"]}" stop-opacity="0.7"/><stop offset="100%" stop-color="{c["a"]}" stop-opacity="0"/></linearGradient>
</defs>
<style>.cw{{transform-origin:0 0;animation:sp 25s linear infinite}}.cc{{transform-origin:0 0;animation:sr 35s linear infinite}}.sf{{transform-origin:0 0;animation:sp 12s linear infinite}}.ps{{animation:pu 4s ease-in-out infinite}}@keyframes sp{{to{{transform:rotate(360deg)}}}}@keyframes sr{{to{{transform:rotate(0deg)}}}}@keyframes pu{{0%,100%{{opacity:.75}}50%{{opacity:.95;transform:scale(1.02)}}}}</style>
<g class="cc" opacity="0.35"><rect x="-160" y="-5" width="6" height="6" fill="#cc7a00" opacity="0.7" transform="rotate(15)"/><rect x="155" y="10" width="4" height="4" fill="#ff9933" opacity="0.6" transform="rotate(45)"/><rect x="-10" y="-170" width="5" height="5" fill="#995c00" opacity="0.8" transform="rotate(85)"/><rect x="25" y="165" width="7" height="4" fill="#ffb366" opacity="0.5" transform="rotate(120)"/><rect x="-130" y="-110" width="5" height="5" fill="#b36b00" transform="rotate(200)"/><rect x="120" y="115" width="4" height="6" fill="#ff9933" transform="rotate(290)"/></g>
<g class="cw" opacity="0.4"><rect x="-140" y="20" width="5" height="5" fill="{c["p"]}" transform="rotate(35)"/><rect x="135" y="-30" width="4" height="4" fill="#ffaa44" transform="rotate(75)"/><rect x="-70" y="130" width="6" height="6" fill="#cc7a00" transform="rotate(160)"/><rect x="80" y="-120" width="5" height="5" fill="{c["p"]}" transform="rotate(240)"/></g>
<circle cx="0" cy="0" r="150" fill="none" stroke="url(#rg1)" stroke-width="1.5" stroke-dasharray="200 40 50 40 10 10" class="cw"/>
<circle cx="0" cy="0" r="142" fill="none" stroke="{c["p"]}" stroke-width="0.75" stroke-opacity="0.3" stroke-dasharray="5 5" class="cc"/>
<g class="cc"><circle cx="0" cy="0" r="115" fill="none" stroke="url(#rg2)" stroke-width="2" stroke-dasharray="150 150" filter="url(#s)"/><path d="M-115,0 L-110,0 M115,0 L110,0 M0,-115 L0,-110 M0,115 L0,110" stroke="{c["p"]}" stroke-width="2" opacity="0.6"/></g>
<circle cx="0" cy="0" r="85" fill="none" stroke="{c["p"]}" stroke-width="1" stroke-opacity="0.2" stroke-dasharray="30 10 10 10" class="cw"/>
<g class="cw"><g fill="{c["p"]}" opacity="0.6" filter="url(#s)"><circle cx="0" cy="-75" r="1.5"/><circle cx="0" cy="75" r="1.5"/><circle cx="-75" cy="0" r="1.5"/><circle cx="75" cy="0" r="1.5"/><circle cx="-53" cy="-53" r="1.2"/><circle cx="53" cy="53" r="1.2"/><circle cx="53" cy="-53" r="1.2"/><circle cx="-53" cy="53" r="1.2"/><rect x="-65" y="-20" width="2" height="2" opacity="0.4"/><rect x="65" y="20" width="2" height="2" opacity="0.4"/><rect x="-20" y="65" width="2" height="2" opacity="0.4"/><rect x="20" y="-65" width="2" height="2" opacity="0.4"/><rect x="-45" y="-45" width="3" height="3" fill="#ffaa44" opacity="0.7"/><rect x="45" y="45" width="3" height="3" fill="#ffaa44" opacity="0.7"/></g><ellipse cx="0" cy="0" rx="75" ry="25" fill="none" stroke="{c["p"]}" stroke-width="0.75" stroke-opacity="0.25" transform="rotate(30)"/><ellipse cx="0" cy="0" rx="75" ry="25" fill="none" stroke="{c["p"]}" stroke-width="0.75" stroke-opacity="0.25" transform="rotate(-30)"/><ellipse cx="0" cy="0" rx="75" ry="7" fill="none" stroke="{c["p"]}" stroke-width="0.5" stroke-opacity="0.15" transform="rotate(90)"/></g>
<g class="sf" opacity="0.8"><circle cx="85" cy="0" r="2.5" fill="{c["a"]}" filter="url(#h)"/><circle cx="-85" cy="0" r="2.5" fill="{c["p"]}"/></g>
<g class="ps"><circle cx="0" cy="-10" r="45" fill="{c["p"]}" opacity="0.08" filter="url(#h)"/><g stroke="{c["p"]}" stroke-width="0.5" fill="none" opacity="0.3"><path d="M-55,-10 C-55,-40 -35,-55 0,-55 C35,-55 55,-40 55,-10 C55,20 35,45 0,45 C-35,45 -55,20 -55,-10 Z" stroke-dasharray="2 4"/><path d="M-45,-10 C-45,-30 -25,-42 0,-42 C25,-42 45,-30 45,-10 C45,15 25,32 0,32 C-25,32 -45,15 -45,-10 Z" stroke-opacity="0.5"/></g>
<path d="M-35,-65 C-35,-95 35,-95 35,-65 C35,-45 45,-20 40,15 C36,45 25,65 0,75 C-25,65 -36,45 -40,15 C-45,-20 -35,-45 -35,-65 Z" fill="none" stroke="{c["p"]}" stroke-width="1" stroke-opacity="0.6" filter="url(#s)"/>
<path d="M-35,-65 C-35,-95 35,-95 35,-65 C35,-45 45,-20 40,15 C36,45 25,65 0,75 C-25,65 -36,45 -40,15 C-45,-20 -35,-45 -35,-65 Z" fill="none" stroke="{c["p"]}" stroke-width="2" stroke-opacity="0.3"/>
<path d="{eyes} M-12,-22 Q0,-18 12,-22 {brows} M-4,-32 L-4,-2 L-10,10 L10,10 Z {mouth} M-10,32 Q0,36 10,32" fill="none" stroke="{c["p"]}" stroke-width="1.2" stroke-opacity="0.5" filter="url(#h)"/>
<g fill="{c["p"]}" opacity="0.75"><rect x="-22" y="-23" width="1.5" height="1.5"/><rect x="21" y="-23" width="1.5" height="1.5"/><circle cx="-12" cy="-22" r="0.75"/><circle cx="12" cy="-22" r="0.75"/><polygon points="0,-52 -3,-48 3,-48" opacity="0.6"/></g>
<g filter="url(#s)"><text x="0" y="-3" font-family="monospace" font-size="11" font-weight="900" fill="#ffffff" letter-spacing="5" text-anchor="middle" opacity="0.9">FRYA</text></g>
<text x="0" y="52" font-family="monospace" font-size="5.5" fill="{c["p"]}" letter-spacing="1.5" text-anchor="middle" opacity="0.5">SYS_v2.194_AM</text></g>
<g opacity="0.8"><path d="M-20,100 L20,100 M-10,104 L10,104" stroke="{c["p"]}" stroke-width="1.5" stroke-opacity="0.7"/><polygon points="0,96 -6,100 6,100" fill="{c["p"]}" opacity="0.4"/></g></svg>'''


@register_skill("emotion_svg", "utility")
class EmotionSvgSkill(BaseSkill):
    name = "emotion_svg"
    description = "Generate an emotional SVG face from text input — returns raw SVG with matching facial expression"
    author = "ClawDia"
    version = "1.0.0"
    category = "utility"
    tags = ["svg", "emotion", "face", "generative", "hologram"]
    input_schema = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Input text that sets the emotional context",
                "default": "",
            },
            "emotion": {
                "type": "string",
                "enum": list(EMO_COLORS.keys()),
                "default": "neutral",
                "description": "Emotion to render on the face",
            },
            "raw": {
                "type": "boolean",
                "default": False,
                "description": "If true, return raw SVG string. If false, return JSON with metadata.",
            },
        },
    }

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "")
        emotion = kwargs.get("emotion", "neutral")
        raw = kwargs.get("raw", False)

        if emotion not in EMO_COLORS:
            emotion = "neutral"

        svg = _build_svg(emotion)

        if raw:
            return {"error": None, "result": svg, "_raw_svg": True}

        return {
            "error": None,
            "result": {
                "svg": svg,
                "emotion": emotion,
                "text": text,
                "width": 400,
                "height": 400,
                "format": "svg",
            },
        }
