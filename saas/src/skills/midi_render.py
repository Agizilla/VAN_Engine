"""MIDI Render Skill — converts note sequences to sheet music + playback data.

Usage:
  POST /hooks/midi_render  {"notes": "C4,E4,G4,C5", "tempo": 120, "instrument": "synth", "format": "json"}

Returns note frequencies, MIDI note numbers, durations, and optional VexFlow HTML.
"""

import json

try:
    from .base import BaseSkill, register_skill
except ImportError:
    from skills.base import BaseSkill, register_skill

NOTE_FREQ = {
    "C4": 261.63, "C#4": 277.18, "Db4": 277.18, "D4": 293.66,
    "D#4": 311.13, "Eb4": 311.13, "E4": 329.63, "F4": 349.23,
    "F#4": 369.99, "Gb4": 369.99, "G4": 392.00, "G#4": 415.30,
    "Ab4": 415.30, "A4": 440.00, "A#4": 466.16, "Bb4": 466.16,
    "B4": 493.88, "C5": 523.25, "C#5": 554.37, "Db5": 554.37,
    "D5": 587.33, "D#5": 622.25, "Eb5": 622.25, "E5": 659.25,
    "F5": 698.46, "F#5": 739.99, "Gb5": 739.99, "G5": 783.99,
    "G#5": 830.61, "Ab5": 830.61, "A5": 880.00, "A#5": 932.33,
    "Bb5": 932.33, "B5": 987.77,
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61,
    "G3": 196.00, "A3": 220.00, "B3": 246.94,
    "C6": 1046.50, "D6": 1174.66, "E6": 1318.51, "F6": 1396.91, "G6": 1567.98,
}

MIDI_NOTE_NUM = {
    "C3": 48, "C#3": 49, "D3": 50, "D#3": 51, "E3": 52, "F3": 53,
    "F#3": 54, "G3": 55, "G#3": 56, "A3": 57, "A#3": 58, "B3": 59,
    "C4": 60, "C#4": 61, "D4": 62, "D#4": 63, "E4": 64, "F4": 65,
    "F#4": 66, "G4": 67, "G#4": 68, "A4": 69, "A#4": 70, "B4": 71,
    "C5": 72, "C#5": 73, "D5": 74, "D#5": 75, "E5": 76, "F5": 77,
    "F#5": 78, "G5": 79, "G#5": 80, "A5": 81, "A#5": 82, "B5": 83,
    "C6": 84, "D6": 86, "E6": 88, "F6": 89, "G6": 91,
}


@register_skill("midi_render", "audio")
class MidiRenderSkill(BaseSkill):
    name = "midi_render"
    description = "Convert note sequences to sheet music HTML + playback data"
    category = "audio"
    version = "1.0.0"
    author = "ClawDia / Mike"
    tags = ["midi", "sheet-music", "vexflow", "audio", "composer"]
    required_libs = []
    input_schema = {
        "type": "object",
        "properties": {
            "notes": {
                "type": "string",
                "description": "Comma-separated note names (e.g., C4,E4,G4,C5)",
                "default": "C4,E4,G4,C5,G4,E4,C4",
            },
            "tempo": {
                "type": "integer",
                "description": "Tempo in BPM",
                "default": 120,
                "minimum": 30,
                "maximum": 300,
            },
            "instrument": {
                "type": "string",
                "enum": ["synth", "piano"],
                "description": "Instrument for playback",
                "default": "synth",
            },
            "format": {
                "type": "string",
                "enum": ["json", "html"],
                "description": "Response format (json=data, html=sheet music page)",
                "default": "json",
            },
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "note_names": {"type": "array", "items": {"type": "string"}},
            "frequencies": {"type": "array", "items": {"type": "number"}},
            "midi_notes": {"type": "array", "items": {"type": "integer"}},
            "durations": {"type": "array", "items": {"type": "number"}},
            "tempo": {"type": "integer"},
            "instrument": {"type": "string"},
            "total_duration": {"type": "number"},
        },
    }

    def execute(self, **kwargs) -> dict:
        notes_str = kwargs.get("notes", "C4,E4,G4")
        tempo = int(kwargs.get("tempo", 120))
        instrument = kwargs.get("instrument", "synth")
        output_format = kwargs.get("format", "json")

        note_names = [n.strip() for n in notes_str.split(",") if n.strip()]
        duration = 60.0 / tempo

        frequencies = []
        midi_notes = []
        durations = []
        valid_names = []

        for n in note_names:
            freq = NOTE_FREQ.get(n)
            if freq is None:
                continue
            frequencies.append(freq)
            midi_notes.append(MIDI_NOTE_NUM.get(n, 60))
            durations.append(duration)
            valid_names.append(n)

        result = {
            "note_names": valid_names,
            "frequencies": frequencies,
            "midi_notes": midi_notes,
            "durations": durations,
            "tempo": tempo,
            "instrument": instrument,
            "total_duration": round(len(valid_names) * duration, 2),
            "note_count": len(valid_names),
        }

        if output_format == "html":
            result["html"] = self._render_vexflow_html(valid_names, midi_notes, tempo)

        return {"error": None, "result": result}

    def _render_vexflow_html(self, note_names: list[str], midi_notes: list[int], tempo: int) -> str:
        vex_notes = []
        for name in note_names:
            letter = name[0].upper()
            accidental = "#" if "#" in name else ("b" if "b" in name else "")
            vex_notes.append(f"{letter}{accidental}/q")

        vex_json = json.dumps(vex_notes)

        return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/vexflow@5.3.0/build/cjs/vexflow.js"></script>
<style>
  body {{ background: #f5efe7; margin: 0; padding: 20px; font-family: system-ui; }}
  #output {{ max-width: 900px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 20px; }}
  h2 {{ color: #4A148C; margin-top: 0; }}
  .info {{ color: #555; font-size: 14px; margin-bottom: 12px; }}
</style>
</head><body>
<div id="output">
  <h2>🎵 Sheet Music</h2>
  <div class="info">Tempo: {tempo} BPM &middot; Notes: {len(vex_notes)}</div>
  <div id="vexflow-container"></div>
  <script>
    VF = VexFlow;
    var vf = new VF.Factory({{renderer: {{elementId: 'vexflow-container', width: 800, height: 180}}}});
    var score = vf.EasyScore();
    var system = vf.System();
    var notes = {vex_json};
    var staveNotes = notes.map(function(n) {{ return score.cleanNote(n); }});
    system.addStave({{voices: [score.voice(staveNotes)]}});
    vf.draw();
  </script>
</div>
</body></html>"""
