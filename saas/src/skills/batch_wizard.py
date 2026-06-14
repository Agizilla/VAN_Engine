import json
import os
from pathlib import Path
from typing import Any, Optional


AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aiff", ".aac", ".wma"}
MIDI_EXTS = {".mid", ".midi"}
TEXT_EXTS = {".txt", ".md", ".rst", ".log"}
DATA_EXTS = {".json", ".yaml", ".yml", ".csv", ".xml", ".toml"}

_HARDCODED_MATRIX = {
    ".wav":   [("transcribe", "Transcribe to MIDI/notes"), ("analyze",  "Analyze tempo/spectral/chroma"), ("split",    "Split or trim segments"), ("chords",  "Detect chord progression"), ("key",     "Estimate musical key")],
    ".mp3":   [("transcribe", "Transcribe to MIDI/notes"), ("analyze",  "Analyze tempo/spectral/chroma"), ("split",    "Split or trim segments"), ("chords",  "Detect chord progression"), ("key",     "Estimate musical key")],
    ".flac":  [("transcribe", "Transcribe to MIDI/notes"), ("analyze",  "Analyze tempo/spectral/chroma"), ("split",    "Split or trim segments"), ("chords",  "Detect chord progression"), ("key",     "Estimate musical key")],
    ".m4a":   [("transcribe", "Transcribe to MIDI/notes"), ("analyze",  "Analyze tempo/spectral/chroma"), ("chords",  "Detect chord progression"), ("key",     "Estimate musical key")],
    ".ogg":   [("transcribe", "Transcribe to MIDI/notes"), ("analyze",  "Analyze tempo/spectral/chroma"), ("chords",  "Detect chord progression"), ("key",     "Estimate musical key")],
    ".mid":   [("playback",   "Play through system synth"), ("info",    "Show MIDI note info")],
    ".midi":  [("playback",   "Play through system synth"), ("info",    "Show MIDI note info")],
    ".txt":   [("summarize",  "Summarize content"), ("count",  "Count words/lines")],
    ".md":    [("summarize",  "Summarize content"), ("count",  "Count words/lines")],
    ".json":  [("validate",   "Validate JSON syntax"), ("count",  "Count entries")],
    ".yaml":  [("validate",   "Validate YAML syntax")],
    ".csv":   [("info",       "Show column headers and row count")],
}

_CAPABILITY_MATRIX_PATH = Path(__file__).resolve().parent / "batch_wizard_matrix.json"
_CHECKPOINT_PATH = Path(__file__).resolve().parent / ".batch_checkpoint.json"

CAPABILITY_MATRIX = dict(_HARDCODED_MATRIX)

def _load_capability_matrix() -> dict:
    if _CAPABILITY_MATRIX_PATH.exists():
        try:
            loaded = json.loads(_CAPABILITY_MATRIX_PATH.read_text(encoding="utf-8"))
            return {k: [tuple(i) for i in v] for k, v in loaded.items()}
        except Exception:
            pass
    return dict(_HARDCODED_MATRIX)

def _reload_matrix():
    global CAPABILITY_MATRIX
    CAPABILITY_MATRIX = _load_capability_matrix()

_reload_matrix()

PROMPT_TEMPLATES = {
    "welcome": "Ok babes, you pointed me at {path}. I found {file_count} files in there.",
    "file_type_breakdown": "Here's what I found: {breakdown}. What file type do you want to work with?",
    "action_prompt": "You selected {ext} files. What do you want me to do with them? Options: {options}. Or say 'all' to run everything possible.",
    "processing": "Alright, processing {count} {ext} files with action '{action}'. Sit tight.",
    "progress": "Finished {done} of {total}. Progress: {pct}%.",
    "complete": "All done! Processed {total} {ext} files with '{action}'. {results}",
    "final_summary": "Session complete. Total files processed: {processed}. Any errors: {errors}. Want me to process something else?",
    "no_action": "Sorry, I don't have anything I can do with {ext} files yet.",
    "cancelled": "Cancelled batch processing. Nothing was done.",
    "error": "Ran into a problem: {error}",
}


def _human_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _speakable_breakdown(grouped: dict[str, int]) -> str:
    parts = [f"{count} {ext} files" for ext, count in sorted(grouped.items())]
    return _human_list(parts)


def _load_checkpoint() -> set[str]:
    if _CHECKPOINT_PATH.exists():
        try:
            return set(json.loads(_CHECKPOINT_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()


def _save_checkpoint(file_path: str):
    processed = _load_checkpoint()
    processed.add(file_path)
    _CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CHECKPOINT_PATH.write_text(json.dumps(list(processed)), encoding="utf-8")


def _clear_checkpoint():
    if _CHECKPOINT_PATH.exists():
        _CHECKPOINT_PATH.unlink()


def scan_directory(path: str, max_depth: int = -1) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"error": f"Path not found: {path}", "files": [], "grouped": {}}
    if not p.is_dir():
        return {"error": f"Not a directory: {path}", "files": [], "grouped": {}}

    files = []

    def _walk(current: Path, depth: int):
        if max_depth >= 0 and depth > max_depth:
            return
        for f in sorted(current.iterdir()):
            if f.is_dir() and not f.name.startswith("."):
                _walk(f, depth + 1)
            elif f.is_file() and not f.name.startswith("."):
                ext = f.suffix.lower()
                files.append({"name": f.name, "ext": ext, "size": f.stat().st_size, "path": str(f)})

    _walk(p, 0)

    grouped: dict[str, int] = {}
    for f in files:
        ext = f["ext"] or "(no ext)"
        grouped[ext] = grouped.get(ext, 0) + 1

    return {"error": None, "files": files, "grouped": grouped, "total": len(files)}


def build_welcome_script(path: str, scan: dict[str, Any]) -> dict[str, Any]:
    if scan["error"]:
        return {"script": PROMPT_TEMPLATES["error"].format(error=scan["error"]), "state": "error"}

    if scan["total"] == 0:
        return {"script": f"I scanned {path} but didn't find any files. Try another directory?",
                "state": "empty"}

    breakdown = _speakable_breakdown(scan["grouped"])
    script = PROMPT_TEMPLATES["welcome"].format(path=path, file_count=scan["total"])
    script += " " + PROMPT_TEMPLATES["file_type_breakdown"].format(breakdown=breakdown)

    return {
        "script": script,
        "state": "choose_type",
        "grouped": scan["grouped"],
        "total": scan["total"],
        "choices": sorted(scan["grouped"].keys()),
        "spoken_breakdown": breakdown,
    }


def build_action_prompt(ext: str, count: int) -> dict[str, Any]:
    caps = CAPABILITY_MATRIX.get(ext, [])
    if not caps:
        return {
            "script": PROMPT_TEMPLATES["no_action"].format(ext=ext),
            "state": "no_action",
            "options": [],
        }

    option_names = [c[0] for c in caps]
    option_descriptions = [f"'{c[0]}': {c[1]}" for c in caps]
    options_script = "; ".join(option_descriptions)
    script = PROMPT_TEMPLATES["action_prompt"].format(
        ext=ext, options=options_script
    )
    return {
        "script": script,
        "state": "choose_action",
        "ext": ext,
        "count": count,
        "options": option_names,
        "option_details": caps,
    }


def build_params_prompt(ext: str, action: str, caps: list[tuple[str, str]]) -> dict[str, Any]:
    if action == "all":
        actions_to_run = [c[0] for c in caps]
        return {
            "script": f"Running all {len(actions_to_run)} actions on your {ext} files.",
            "state": "confirm_all",
            "ext": ext,
            "actions": actions_to_run,
        }

    valid = [c for c in caps if c[0] == action]
    if not valid:
        return {"script": f"Sorry, '{action}' is not supported for {ext} files.", "state": "error"}

    params = {}
    script = ""
    if action in ("transcribe", "analyze", "chords", "key"):
        params["hop_length"] = 512
        script = f"Processing {ext} files with {action}. Using default settings. Starting now."
    elif action == "split":
        params["segments"] = 4
        script = f"Splitting each {ext} file into 4 segments. Starting now."
    elif action == "playback":
        script = f"Playing {ext} files through the system synth. Sit back and listen."

    return {
        "script": script,
        "state": "running",
        "ext": ext,
        "action": action,
        "params": params,
    }


def build_progress_update(done: int, total: int, ext: str, action: str, errors: list[str]) -> dict[str, Any]:
    pct = round(done / total * 100) if total > 0 else 0
    script = PROMPT_TEMPLATES["progress"].format(done=done, total=total, pct=pct)
    return {
        "script": script,
        "state": "progress",
        "done": done,
        "total": total,
        "pct": pct,
        "errors": errors,
    }


def build_complete(total: int, ext: str, action: str, errors: list[str]) -> dict[str, Any]:
    results = f"Processed {total} files."
    if errors:
        results += f" {len(errors)} had errors: {'; '.join(errors[:3])}."
    script = PROMPT_TEMPLATES["complete"].format(total=total, ext=ext, action=action, results=results)
    script += " " + PROMPT_TEMPLATES["final_summary"].format(processed=total, errors=len(errors))
    return {
        "script": script,
        "state": "done",
        "processed": total,
        "errors": errors,
        "total": total,
    }


def _execute_action(file_path: str, ext: str, action: str, params: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        return {"error": None, "result": {"dry_run": True, "would_execute": action, "file": file_path}}
    try:
        import librosa
        import soundfile as sf

        if action in ("transcribe", "analyze", "chords", "key"):
            from transcribe.core import transcribe_file
            from transcribe.exporters import export as export_transcription, format_note_table
            from transcribe.chord_detection import detect_chords, detect_key

        result_path = None
        info = {}

        if action == "analyze":
            y, sr = librosa.load(file_path, sr=None, mono=True)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            spectral = librosa.feature.spectral_centroid(y=y, sr=sr)
            import numpy as np
            info = {
                "tempo": round(float(tempo), 1),
                "spectral_centroid": round(float(np.mean(spectral)), 1),
                "duration": round(len(y) / sr, 2),
            }

        elif action == "transcribe":
            result = transcribe_file(file_path)
            out_path = str(Path(file_path).parent / f"{Path(file_path).stem}_transcribed.mid")
            result_path = export_transcription(result, out_path)
            info = {"note_count": result.note_count, "midi_output": result_path}

        elif action == "chords":
            result = detect_chords(file_path)
            info = {"chord_count": result["chord_count"], "summary": result["chord_summary"]}

        elif action == "key":
            result = detect_key(file_path)
            info = {"key": result["estimated_key"]}

        elif action == "split":
            segments = params.get("segments", 4)
            y, sr = librosa.load(file_path, sr=None, mono=True)
            total = len(y) / sr
            seg_dur = total / segments
            outputs = []
            for i in range(segments):
                s = int(i * seg_dur * sr)
                e = int((i + 1) * seg_dur * sr)
                seg = y[s:e]
                out = str(Path(file_path).parent / f"{Path(file_path).stem}_seg{i+1}.wav")
                sf.write(out, seg, sr)
                outputs.append(out)
            info = {"segments": segments, "outputs": outputs}

        elif action == "playback":
            from transcribe.midi_playback import MIDIPlayer
            player = MIDIPlayer()
            result = player.play_midi_file(file_path)
            player.close()
            info = {"played": True, "notes": result.get("note_count", 0)}

        return {"error": None, "result": info}

    except Exception as e:
        return {"error": str(e), "result": None}


def process_batch(
    files: list[dict[str, Any]],
    ext: str,
    action: str,
    params: dict[str, Any],
    on_progress=None,
    dry_run: bool = False,
) -> dict[str, Any]:
    target_files = [f for f in files if f["ext"] == ext]
    if not target_files:
        return {"error": f"No {ext} files found", "results": [], "errors": []}

    checkpoint = _load_checkpoint()
    results = []
    errors = []
    processed = 0
    skipped = 0

    for i, f in enumerate(target_files):
        if f["path"] in checkpoint:
            skipped += 1
            continue

        if dry_run:
            import sys as _sys
            _sys.stdout.write(f"[DRY RUN] Would process {f['name']} with action '{action}'\n")
            results.append({"file": f["name"], "result": {"dry_run": True}})
            _save_checkpoint(f["path"])
            processed += 1
            if on_progress:
                on_progress(processed, len(target_files) - len(checkpoint), errors)
            continue

        r = _execute_action(f["path"], ext, action, params)
        if r["error"]:
            errors.append(f"{f['name']}: {r['error']}")
        else:
            results.append({"file": f["name"], "result": r["result"]})
        _save_checkpoint(f["path"])
        processed += 1
        if on_progress:
            on_progress(processed, len(target_files) - len(checkpoint), errors)

    _clear_checkpoint()

    return {
        "error": None,
        "results": results,
        "errors": errors,
        "processed": processed,
        "success_count": len(results),
        "error_count": len(errors),
        "skipped": skipped,
    }


from .base import BaseSkill, register_skill


@register_skill("batch_wizard", "utility")
class BatchWizardSkill(BaseSkill):
    name = "batch_wizard"
    description = "Voice-driven batch processing wizard - scan dirs, choose file types and actions"
    category = "utility"
    tags = ["batch", "wizard", "directory", "processing"]
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path to scan for batch processing"},
            "action": {"type": "string", "enum": ["scan", "choose_type", "choose_action", "run", "reset"], "default": "scan"},
            "ext": {"type": "string", "default": "", "description": "File extension filter (e.g. .py, .txt)"},
            "max_depth": {"type": "integer", "default": -1},
            "dry_run": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    }
    required_libs = []

    def execute(self, **kwargs: Any) -> dict:
        action = kwargs.get("action", "scan")
        path = kwargs.get("path", "")
        dry_run = kwargs.get("dry_run", False)

        if action == "scan":
            if not path:
                return {"error": "No directory path provided", "result": None}
            max_depth = kwargs.get("max_depth", -1)
            scan = scan_directory(path, max_depth=max_depth)
            if scan["error"]:
                return {"error": scan["error"], "result": None}
            wizard = build_welcome_script(path, scan)
            return {"error": None, "result": wizard}

        elif action == "choose_type":
            ext = kwargs.get("ext", "")
            count = kwargs.get("count", 0)
            prompt = build_action_prompt(ext, count)
            return {"error": None, "result": prompt}

        elif action == "choose_action":
            ext = kwargs.get("ext", "")
            action_name = kwargs.get("action_name", "")
            caps = CAPABILITY_MATRIX.get(ext, [])
            prompt = build_params_prompt(ext, action_name, caps)
            return {"error": None, "result": prompt}

        elif action == "run":
            ext = kwargs.get("ext", "")
            action_name = kwargs.get("action_name", "")
            params = kwargs.get("params", {})
            files = kwargs.get("files", [])
            if not files:
                return {"error": "No files provided for batch processing", "result": None}
            result = process_batch(files, ext, action_name, params, dry_run=dry_run)
            return {"error": None, "result": result}

        return {"error": f"Unknown action: {action}", "result": None}
