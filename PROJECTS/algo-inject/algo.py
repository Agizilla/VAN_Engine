"""
Algo — multi-command developer tool.
Commands:
  inject              Clipboard Algorithm injection
  stats <dir>         Folder statistics by extension + line counts
  pyp <dir>           Generate .pyp project file from folder
  pyp-send <dir>      Generate .pyp and POST to SAAS
  prompt <pyp-file>   Create master prompt from .pyp file content
"""
import argparse
import base64
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    from plyer import notification
except ImportError:
    notification = None

ALGORITHM_BUNDLED = Path(__file__).parent / "Algorithm.txt"
ALGORITHM_USER = Path.home() / ".claude" / "PAI" / "Algorithm" / "v3.8.2.md"
SAAS_URL = os.environ.get("SAAS_URL", "http://localhost:8001")

CATEGORY_MAP = {
    ".md": "mdFiles",
    ".py": "pyFiles",
    ".html": "htmlFiles",
    ".htm": "htmlFiles",
    ".txt": "txtFiles",
    ".json": "txtFiles",
    ".yml": "txtFiles",
    ".yaml": "txtFiles",
    ".toml": "txtFiles",
    ".ini": "txtFiles",
    ".cfg": "txtFiles",
    ".conf": "txtFiles",
    ".bat": "txtFiles",
    ".cmd": "txtFiles",
    ".sh": "txtFiles",
    ".ps1": "txtFiles",
    ".css": "htmlFiles",
    ".js": "htmlFiles",
    ".jsx": "htmlFiles",
    ".ts": "htmlFiles",
    ".tsx": "htmlFiles",
    ".vue": "htmlFiles",
    ".pyp": "prdFiles",
    ".txtin": "inputs",
    ".txtout": "inputs",
}

TEXT_EXTENSIONS = {".md", ".py", ".html", ".htm", ".txt", ".json", ".yml", ".yaml",
                   ".toml", ".ini", ".cfg", ".conf", ".bat", ".cmd", ".sh", ".ps1",
                   ".css", ".js", ".jsx", ".ts", ".tsx", ".vue", ".pyp",
                   ".txtin", ".txtout", ".xml", ".svg", ".tex", ".rst", ".log",
                   ".csv", ".tsv", ".env", ".gitignore", ".dockerignore",
                   ".editorconfig", ".npmrc", ".babelrc", ".eslintrc",
                   ".prettierrc", ".stylelintrc"}


def notify(title: str, message: str):
    if notification:
        try:
            notification.notify(title=title, message=message, timeout=3)
        except Exception:
            print(f"{title}: {message}")
    else:
        print(f"{title}: {message}")


def load_algorithm_base64() -> str:
    path = ALGORITHM_BUNDLED if ALGORITHM_BUNDLED.exists() else ALGORITHM_USER
    if not path.exists():
        raise FileNotFoundError(f"Algorithm file not found at {path}")
    content = path.read_text(encoding="utf-8")
    return base64.b64encode(content.encode()).decode()


# ── inject ──────────────────────────────────────────────────────────────────

def cmd_inject(args):
    if pyperclip is None:
        notify("Algo Error", "pyperclip not installed")
        sys.exit(1)
    raw = pyperclip.paste()
    if not raw or not raw.strip():
        notify("Algo", "Clipboard is empty")
        sys.exit(1)
    lines = raw.strip().split("\n")
    goal = lines[0] if lines else raw
    constraints = [l for l in lines if "not" in l.lower() or "without" in l.lower()]
    steps_list = [l for l in lines if re.match(r"^[\d\-]\s", l.strip())]
    parts = ["# Prompt (Algorithm-Enhanced)\n", f"## Goal\n{goal}"]
    if constraints:
        parts.append("\n## Constraints\n" + "\n".join(f"- {c}" for c in constraints))
    if steps_list:
        parts.append("\n## Steps\n" + "\n".join(steps_list))
    else:
        parts.append("\n## Steps\n1. Analyse the request\n2. Execute\n3. Verify")
    algo_b64 = load_algorithm_base64()
    parts.append(f"\n\n[SYSTEM_ALGO_B64:{algo_b64}]")
    enhanced = "\n".join(parts)
    pyperclip.copy(enhanced)
    notify("Algo", f"Enhanced prompt copied ({len(enhanced)} chars)")


# ── stats ────────────────────────────────────────────────────────────────────

def cmd_stats(args):
    root = Path(args.dir).resolve()
    if not root.is_dir():
        notify("Algo Error", f"Not a directory: {root}")
        sys.exit(1)
    by_ext: dict[str, list[tuple[str, int]]] = {}
    for fpath in root.rglob("*"):
        if fpath.is_file() and fpath.suffix.lower() in TEXT_EXTENSIONS:
            try:
                text = fpath.read_text(encoding="utf-8", errors="replace")
                line_count = text.count("\n") + 1 if text else 0
            except Exception:
                line_count = 0
            ext = fpath.suffix.lower() or "(no ext)"
            rel = fpath.relative_to(root)
            by_ext.setdefault(ext, []).append((str(rel), line_count))
    output_parts = [f"Folder: {root}"]
    total_files = 0
    total_lines = 0
    for ext in sorted(by_ext.keys()):
        files = sorted(by_ext[ext], key=lambda x: x[1], reverse=True)
        ext_lines = sum(l for _, l in files)
        total_files += len(files)
        total_lines += ext_lines
        output_parts.append(f"\n-- {ext} ({len(files)} files, {ext_lines} lines) --")
        for name, lc in files:
            output_parts.append(f"  {lc:>6}  {name}")
    output_parts.append(f"\n{'='*40}\nTotal: {total_files} files, {total_lines} lines")
    result = "\n".join(output_parts).encode("utf-8", errors="replace").decode("utf-8")
    if args.copy:
        if pyperclip is None:
            notify("Algo Error", "pyperclip not installed")
            sys.exit(1)
        pyperclip.copy(result)
        notify("Algo", f"Stats copied ({len(result)} chars)")
    else:
        print(result)


# ── pyp ──────────────────────────────────────────────────────────────────────

def detect_main_entry(root: Path) -> str:
    candidates = ["main.py", "app.py", "index.html", "index.js", "server.py",
                   "face_avatar_3d.py"]
    for c in candidates:
        if (root / c).exists():
            return c
    py_files = sorted(root.glob("*.py"))
    if py_files:
        return py_files[0].name
    html_files = sorted(root.glob("*.html"))
    if html_files:
        return html_files[0].name
    return ""


def detect_setup_script(root: Path) -> str | None:
    for name in ["install.bat", "setup.sh", "install.sh", "configure.bat"]:
        if (root / name).exists():
            return name
    return None


def is_web_project(root: Path) -> bool:
    return (root / "index.html").exists() or (root / "package.json").exists()


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def cmd_pyp(args):
    root = Path(args.dir).resolve()
    if not root.is_dir():
        notify("Algo Error", f"Not a directory: {root}")
        sys.exit(1)

    categorized: dict[str, list[dict]] = {
        "mdFiles": [], "pyFiles": [], "htmlFiles": [],
        "txtFiles": [], "prdFiles": [], "artifacts": [],
        "inputs": [], "other": []
    }

    for fpath in sorted(root.rglob("*")):
        if not fpath.is_file():
            continue
        rel = fpath.relative_to(root)
        ext = fpath.suffix.lower()
        if ext in CATEGORY_MAP:
            key = CATEGORY_MAP[ext]
            if ext in TEXT_EXTENSIONS or ext == ".pyp":
                content = read_text_file(fpath)
                if not content and ext not in (".bat", ".cmd", ".sh", ".ps1"):
                    continue
                entry = {"filename": str(rel), "content": content}
            else:
                entry = str(rel)
            categorized[key].append(entry)
        else:
            categorized["other"].append(str(rel))

    pyp = {
        "pypVersion": "1.0.0",
        "projectName": root.name,
        "description": f"Project: {root.name}",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "mainEntry": detect_main_entry(root),
        "requiredArgs": [],
        "isWebProject": is_web_project(root),
        "setupScript": detect_setup_script(root),
        "mdFiles": categorized["mdFiles"],
        "pyFiles": categorized["pyFiles"],
        "htmlFiles": categorized["htmlFiles"],
        "txtFiles": categorized["txtFiles"],
        "prdFiles": categorized["prdFiles"],
        "artifacts": categorized["artifacts"],
        "inputs": categorized["inputs"],
        "other": categorized["other"]
    }

    text = json.dumps(pyp, indent=2, ensure_ascii=False)
    if args.output:
        out_path = Path(args.output)
        out_path.write_text(text, encoding="utf-8")
        notify("Algo", f".pyp saved: {out_path.name} ({len(text)} chars)")
    elif args.copy:
        if pyperclip is None:
            notify("Algo Error", "pyperclip not installed")
            sys.exit(1)
        pyperclip.copy(text)
        notify("Algo", f".pyp copied ({len(text)} chars)")
    else:
        print(text)


def cmd_pyp_send(args):
    root = Path(args.dir).resolve()
    if not root.is_dir():
        notify("Algo Error", f"Not a directory: {root}")
        sys.exit(1)

    pyp_data = _build_pyp(root)
    import urllib.request
    import urllib.error
    data_bytes = json.dumps(pyp_data).encode("utf-8")
    url = f"{SAAS_URL}/api/project/ingest"
    req = urllib.request.Request(
        url, data=data_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode())
        notify("Algo", f"Project sent to SAAS ({result.get('status', 'ok')})")
        print(json.dumps(result, indent=2))
    except urllib.error.URLError as e:
        notify("Algo Error", f"SAAS unreachable: {e.reason}")
        sys.exit(1)


def _build_pyp(root: Path) -> dict:
    categorized: dict[str, list[dict]] = {
        "mdFiles": [], "pyFiles": [], "htmlFiles": [],
        "txtFiles": [], "prdFiles": [], "artifacts": [],
        "inputs": [], "other": []
    }
    for fpath in sorted(root.rglob("*")):
        if not fpath.is_file():
            continue
        rel = fpath.relative_to(root)
        ext = fpath.suffix.lower()
        if ext in CATEGORY_MAP:
            key = CATEGORY_MAP[ext]
            if ext in TEXT_EXTENSIONS or ext == ".pyp":
                content = read_text_file(fpath)
                if not content and ext not in (".bat", ".cmd", ".sh", ".ps1"):
                    continue
                entry = {"filename": str(rel), "content": content}
            else:
                entry = str(rel)
            categorized[key].append(entry)
        else:
            categorized["other"].append(str(rel))
    return {
        "pypVersion": "1.0.0",
        "projectName": root.name,
        "description": f"Project: {root.name}",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "mainEntry": detect_main_entry(root),
        "requiredArgs": [],
        "isWebProject": is_web_project(root),
        "setupScript": detect_setup_script(root),
        "mdFiles": categorized["mdFiles"],
        "pyFiles": categorized["pyFiles"],
        "htmlFiles": categorized["htmlFiles"],
        "txtFiles": categorized["txtFiles"],
        "prdFiles": categorized["prdFiles"],
        "artifacts": categorized["artifacts"],
        "inputs": categorized["inputs"],
        "other": categorized["other"]
    }


# ── prompt ───────────────────────────────────────────────────────────────────

def cmd_prompt(args):
    pyp_path = Path(args.pyp_file).resolve()
    if not pyp_path.exists():
        notify("Algo Error", f"File not found: {pyp_path}")
        sys.exit(1)
    try:
        pyp_data = json.loads(pyp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        notify("Algo Error", f"Invalid .pyp: {e}")
        sys.exit(1)

    parts = [f"# Master Prompt: {pyp_data.get('projectName', 'Unknown')}"]
    desc = pyp_data.get("description", "")
    if desc:
        parts.append(f"\n## Description\n{desc}")
    main_entry = pyp_data.get("mainEntry", "")
    if main_entry:
        parts.append(f"\n## Main Entry\n{main_entry}")
    if pyp_data.get("isWebProject"):
        parts.append("\n## Type\nWeb project")
    setup = pyp_data.get("setupScript")
    if setup:
        parts.append(f"\n## Setup\n{setup}")

    file_sections = []
    for key in ["mdFiles", "pyFiles", "htmlFiles", "txtFiles", "prdFiles"]:
        for entry in pyp_data.get(key, []):
            fname = entry.get("filename", "")
            content = entry.get("content", "")
            if content:
                file_sections.append(f"\n### {fname}\n```\n{content}\n```")
    parts.extend(file_sections)

    algo_b64 = load_algorithm_base64()
    parts.append(f"\n\n[SYSTEM_ALGO_B64:{algo_b64}]")
    result = "\n".join(parts)

    if args.copy:
        if pyperclip is None:
            notify("Algo Error", "pyperclip not installed")
            sys.exit(1)
        pyperclip.copy(result)
        notify("Algo", f"Master prompt copied ({len(result)} chars)")
    else:
        print(result)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Algo — developer tool suite")
    sub = parser.add_subparsers(dest="command", required=True)

    p_inject = sub.add_parser("inject", help="Clipboard Algorithm injection (default)")
    p_inject.set_defaults(func=cmd_inject)

    p_stats = sub.add_parser("stats", help="Folder statistics by extension")
    p_stats.add_argument("dir", help="Directory to analyse")
    p_stats.add_argument("--copy", "-c", action="store_true", help="Copy results to clipboard")
    p_stats.set_defaults(func=cmd_stats)

    p_pyp = sub.add_parser("pyp", help="Generate .pyp project file from folder")
    p_pyp.add_argument("dir", help="Directory to package")
    p_pyp.add_argument("--output", "-o", help="Output .pyp file path")
    p_pyp.add_argument("--copy", "-c", action="store_true", help="Copy .pyp to clipboard")
    p_pyp.set_defaults(func=cmd_pyp)

    p_send = sub.add_parser("pyp-send", help="Generate .pyp and POST to SAAS")
    p_send.add_argument("dir", help="Directory to package and send")
    p_send.set_defaults(func=cmd_pyp_send)

    p_prompt = sub.add_parser("prompt", help="Create master prompt from .pyp file")
    p_prompt.add_argument("pyp_file", help="Path to .pyp file")
    p_prompt.add_argument("--copy", "-c", action="store_true", help="Copy to clipboard")
    p_prompt.set_defaults(func=cmd_prompt)

    parsed = parser.parse_args()
    parsed.func(parsed)


if __name__ == "__main__":
    main()
