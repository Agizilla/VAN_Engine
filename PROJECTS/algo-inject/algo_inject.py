"""
Algo Inject — right-click shell extension.
Copies selected text → injects Base64 Algorithm context → puts enhanced prompt on clipboard.
"""
import base64
import os
import re
import sys
import tempfile
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


def load_algorithm_base64() -> str:
    path = ALGORITHM_BUNDLED if ALGORITHM_BUNDLED.exists() else ALGORITHM_USER
    if not path.exists():
        raise FileNotFoundError(f"Algorithm file not found at {path}")
    content = path.read_text(encoding="utf-8")
    return base64.b64encode(content.encode()).decode()


def format_prompt(raw: str) -> str:
    lines = raw.strip().split("\n")
    goal = lines[0] if lines else raw
    constraints = [l for l in lines if "not" in l.lower() or "without" in l.lower()]
    steps = [l for l in lines if re.match(r"^[\d\-]\s", l.strip())]

    parts = []
    parts.append("# Prompt (Algorithm-Enhanced)\n")
    parts.append(f"## Goal\n{goal}")
    if constraints:
        parts.append("\n## Constraints\n" + "\n".join(f"- {c}" for c in constraints))
    if steps:
        parts.append("\n## Steps\n" + "\n".join(steps))
    else:
        parts.append("\n## Steps\n1. Analyse the request\n2. Execute\n3. Verify")

    algo_b64 = load_algorithm_base64()
    parts.append(f"\n\n[SYSTEM_ALGO_B64:{algo_b64}]")
    return "\n".join(parts)


def notify(title: str, message: str):
    if notification:
        try:
            notification.notify(title=title, message=message, timeout=3)
        except Exception:
            print(f"{title}: {message}")
    else:
        print(f"{title}: {message}")


def main():
    if pyperclip is None:
        notify("Algo Inject Error", "pyperclip not installed — run: pip install pyperclip")
        sys.exit(1)

    raw = pyperclip.paste()
    if not raw or not raw.strip():
        notify("Algo Inject", "Clipboard is empty — copy text first, then try again")
        sys.exit(1)

    try:
        enhanced = format_prompt(raw)
        pyperclip.copy(enhanced)
        notify("Algo Inject", f"✓ Enhanced prompt copied ({len(enhanced)} chars)")
    except Exception as e:
        notify("Algo Inject Error", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
