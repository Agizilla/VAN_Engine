"""CLI tool: generate boot_context.md with archives + manifest.

Usage:
    python saas/tools/generate_boot_context.py
    python saas/tools/generate_boot_context.py --watch  # auto-regenerate every 60s
"""
import argparse
import time
from pathlib import Path
from urllib.request import urlopen

BOOT_CONTEXT_URL = "http://127.0.0.1:8001/api/memory/boot-context"
BOOT_CONTEXT_PATH = Path.home() / ".claude" / "PAI" / "MEMORY" / "ARCHIVES" / "boot_context.md"


def generate():
    try:
        with urlopen(BOOT_CONTEXT_URL) as resp:
            context = resp.read().decode("utf-8")
        BOOT_CONTEXT_PATH.write_text(context, encoding="utf-8")
        print(f"Wrote {BOOT_CONTEXT_PATH} ({len(context)} chars)")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the SAAS server is running on port 8001.")
        # Fallback: generate minimal boot context
        fallback = f"""# BOOT_CONTEXT — Fallback (server unavailable)
Generated: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}

⚠️ SAAS server was not reachable at {BOOT_CONTEXT_URL}.
Make sure `python saas/server.py` is running and try again.

## Quick paths
- SAAS Server: `saas/server.py`
- Simulations API: `saas/routes/simulations.py`
- Memory API: `saas/routes/memory.py`
- TTS Engine: `saas/routes/tts.py`
- Skills Manager: `saas/skills_manager.py`

## Simulations
Open `http://127.0.0.1:8001/hooks/ui/simulations` for the full manifest.
"""
        BOOT_CONTEXT_PATH.write_text(fallback, encoding="utf-8")
        print(f"Wrote fallback to {BOOT_CONTEXT_PATH}")


def watch(interval: int = 60):
    print(f"Watching: regenerating boot context every {interval}s...")
    while True:
        generate()
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate boot context")
    parser.add_argument("--watch", type=int, nargs="?", const=60, metavar="SECONDS", help="Auto-regenerate every N seconds")
    args = parser.parse_args()
    if args.watch:
        watch(args.watch)
    else:
        generate()
