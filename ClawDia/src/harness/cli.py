import argparse
import json
import sys
from pathlib import Path

from . import IntentPipeline

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    "\u2550".encode(sys.stdout.encoding)
    USE_UNICODE = True
except (UnicodeEncodeError, UnicodeDecodeError):
    USE_UNICODE = False

if USE_UNICODE:
    H = "\u2550"; V = "\u2551"; TL = "\u2554"; TR = "\u2557"
    BL = "\u255A"; BR = "\u255D"; WARN_SYM = "\u2622"
    BULLET = "\u00b7"; RIGHT = "\u2192"
else:
    H = "="; V = "|"; TL = "+"; TR = "+"
    BL = "+"; BR = "+"; WARN_SYM = "!"; BULLET = "."; RIGHT = "->"


def _boxed(title: str, width: int = 60) -> str:
    pad = width - len(title) - 6
    return H * 3 + title + H * 3


def _sanitize(text: str) -> str:
    if USE_UNICODE:
        return text
    return text.encode("ascii", "replace").decode("ascii")


def _fmt_gate(gate: dict) -> str:
    action = gate.get("action", "?")
    score = gate.get("score", 0)
    level = gate.get("level", 0)
    msg = gate.get("message", "")
    arrow = " %s " % RIGHT

    if action == "pass":
        return "  Score: %d/100 %s PASS" % (score, arrow)
    if action == "warn":
        base = "  Score: %d/100 %s WARN (Level %d)" % (score, arrow, level)
        safe_msg = _sanitize(msg)
        lines = [base] + ["  " + l for l in safe_msg.split("\n") if l.strip()]
        return "\n".join(lines)
    if action == "block":
        base = "  Score: %d/100 %s BLOCKED (Level %d)" % (score, arrow, level)
        safe_msg = _sanitize(msg)
        lines = [base] + ["  " + l for l in safe_msg.split("\n") if l.strip()]
        return "\n".join(lines)
    return "  Score: %d/100 %s %s" % (score, arrow, action)


def _fmt_intent(intent: dict) -> str:
    summary = intent.get("intent_summary", "?")
    grid = intent.get("grid", {})
    label = intent.get("grid_label", "?")
    x = grid.get("x", {})
    y = grid.get("y", {})
    z = grid.get("z", {})
    lines = [
        "  Summary: " + summary,
        "  Grid:    " + label,
        "  Action:   %s  (score: %d)" % (x.get("category", "?"), x.get("score", 0)),
        "  Domain:   %s  (score: %d)" % (y.get("category", "?"), y.get("score", 0)),
        "  Constraint: %s  (score: %d)" % (z.get("category", "?"), z.get("score", 0)),
    ]
    return "\n".join(lines)


def _fmt_output(output: dict) -> str:
    otype = output.get("type", "")
    result = output.get("result", {})
    error = output.get("error")
    hint = output.get("hint", "")

    if error:
        base = "  ERROR: " + error
        nars = output.get("narratives_available", [])
        if nars:
            return base + "\n  Available: " + ", ".join(nars)
        return base
    if hint:
        return "  " + hint
    if otype == "ascii_comic":
        content = _sanitize(result.get("content", ""))
        fmt = result.get("format", "text")
        if fmt == "text" and content:
            lines = content.split("\n")
            preview = "\n".join("  " + l for l in lines[:10])
            more = ""
            if len(lines) > 10:
                more = "  ... (%d lines total)" % len(lines)
            return "  Format: ASCII text\n" + preview + "\n" + more
        if fmt == "text":
            return "  (empty content - check narrative file)"
        return json.dumps(result, indent=2)
    if otype == "comic_compiler":
        path = result.get("path", "")
        fmt = result.get("format", "")
        size = ""
        if path:
            p = Path(path)
            if p.exists():
                size = " (%.1f KB)" % (p.stat().st_size / 1024.0)
        return "  Format: " + fmt + "\n  Path:   " + path + size
    if otype == "meme":
        ascii = result.get("ascii", "")
        title = result.get("title", "")
        mid = result.get("id", "")
        lines = ["  Meme: " + title + " (id: " + mid + ")"] + ["  " + l for l in ascii.split("\n")]
        return "\n".join(lines)
    if otype == "ascii_banner":
        ascii = result.get("ascii", "")
        return "\n".join("  " + l for l in ascii.split("\n"))
    if otype == "svg_animated":
        path = result.get("path", "")
        dur = result.get("duration", 0)
        ch = result.get("characters", [])
        kf = result.get("keyframes", 0)
        sz = result.get("size", 0)
        lines = ["  Path: " + path, "  Duration: %ds  Keyframes: %d  Size: %d bytes" % (dur, kf, sz)]
        if ch:
            lines.append("  Characters: " + ", ".join(ch))
        return "\n".join(lines)
    return json.dumps(output, indent=2)


def _display(result: dict, args):
    status = result.get("status", "error")
    prompt = result.get("prompt", args.prompt)
    gate = result.get("gate", {})
    intent = result.get("intent", {})
    target = result.get("target", "?")
    output = result.get("output", {})

    short = prompt[:60] + "..." if len(prompt) > 60 else prompt
    print()
    print("  " + TL + _boxed("VAN Engine " + BULLET + " CyberSaint Pipeline", 52))
    print("  " + V + "  " + short)
    print("  " + BL + H * 58 + BR)
    print()

    if status == "blocked":
        print("  " + _boxed(" BULLSHIT DETECTOR "))
        print(_fmt_gate(gate))
        print()
        print("  %s  Pipeline halted at bullshit gate." % WARN_SYM)
        print("  Use --no-gate to bypass.")
        return

    if args.no_gate:
        print("  " + _boxed(" 1. BULLSHIT GATE "))
        print("  (bypassed with --no-gate)")
    else:
        print("  " + _boxed(" 1. BULLSHIT GATE "))
        print(_fmt_gate(gate))
    print()

    print("  " + _boxed(" 2. INTENT ENRICHMENT "))
    print(_fmt_intent(intent))
    print()

    print("  " + _boxed(" 3. SKILL ROUTER "))
    print("  " + RIGHT + " " + target)
    if args.narrative:
        print("  Narrative:  " + args.narrative)
    if args.action:
        print("  Action:     " + args.action)
    print()

    print("  " + _boxed(" 4. OUTPUT "))
    print(_fmt_output(output))
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="cvnt",
        description="VAN Engine %s CyberSaint Pipeline - sovereign AI full-stack harness" % BULLET,
    )
    parser.add_argument("prompt", nargs="?", default="",
                        help="Intent prompt")
    parser.add_argument("--skill", "-s", default=None,
                        choices=["ascii_comic", "comic_compiler", "humor_meme", "humor_ascii", "svg_animated"],
                        help="Target skill (bypasses auto-router)")
    parser.add_argument("--narrative", "-n", default=None,
                        help="Narrative name for comic/compiler skills")
    parser.add_argument("--action", "-a", default=None,
                        help="Skill-specific action (render, compile_html, etc.)")
    parser.add_argument("--no-gate", action="store_true",
                        help="Skip the bullshit detector gate")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON instead of formatted display")

    args = parser.parse_args()

    if not args.prompt and not args.skill:
        parser.print_help()
        print("\n  Available narratives:")
        try:
            from skills.comic_compiler import ComicCompilerSkill
            c = ComicCompilerSkill()
            narr_result = c.execute(action="list")
            for nar in narr_result.get("result", {}).get("narratives", []):
                print("    - %s  (%d ch, %d panels)" % (
                    nar["filename"], nar["chapters"], nar["panels"]))
        except Exception as e:
            print("    (could not list: %s)" % e)
        return

    pipeline = IntentPipeline()
    result = pipeline.run(
        prompt=args.prompt,
        skill=args.skill,
        narrative=args.narrative,
        action=args.action,
        no_gate=args.no_gate,
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return

    _display(result, args)


if __name__ == "__main__":
    main()
