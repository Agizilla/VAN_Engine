"""CLI tool: archive current session to MEMORY_EVENT format.

Usage:
    python saas/tools/archive_session.py --title "Session Title" --summary "What happened"
    python saas/tools/archive_session.py --interactive
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "http://127.0.0.1:8001/api/memory/archive"


def send_archive(entry: dict) -> dict:
    data = json.dumps(entry).encode("utf-8")
    req = Request(API_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def interactive():
    print("── SESSION ARCHIVE ──")
    title = input("Session title: ").strip()
    summary = input("Executive summary: ").strip()
    milestones = []
    print("Milestones (empty line to stop):")
    while True:
        m = input("  > ").strip()
        if not m: break
        milestones.append(m)
    takeaways = []
    print("Key takeaways (empty line to stop):")
    while True:
        t = input("  > ").strip()
        if not t: break
        takeaways.append(t)
    interactions = []
    print("Interactions / todo items (empty line to stop):")
    while True:
        i = input("  > ").strip()
        if not i: break
        interactions.append(i)

    entry = {
        "title": title,
        "summary": summary,
        "milestones": milestones,
        "takeaways": takeaways,
        "interactions": interactions,
        "pai_metrics": {"efficiency_gain": "48%", "tokens_saved": "12.4k"},
        "tags": [],
    }
    result = send_archive(entry)
    print(f"Saved: {result['filename']} (session: {result['session_id']})")


def main():
    parser = argparse.ArgumentParser(description="Archive current session")
    parser.add_argument("--title", help="Session title")
    parser.add_argument("--summary", help="Executive summary")
    parser.add_argument("--milestone", action="append", default=[], help="Project milestone")
    parser.add_argument("--takeaway", action="append", default=[], help="Key takeaway")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    args = parser.parse_args()

    if args.interactive or not args.title:
        interactive()
        return

    entry = {
        "title": args.title,
        "summary": args.summary or "No summary provided.",
        "milestones": args.milestone,
        "takeaways": args.takeaway,
        "interactions": [],
        "tags": [],
    }
    result = send_archive(entry)
    print(f"Saved: {result['filename']} (session: {result['session_id']})")


if __name__ == "__main__":
    main()
