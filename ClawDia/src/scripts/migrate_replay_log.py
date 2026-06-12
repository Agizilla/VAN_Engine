"""
Migrate replay_event_log.json to SQLite audit (replay_audit.db).
Run once:  python -m src.scripts.migrate_replay_log
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SRC))

from skills.replay_audit import ReplayAuditSkill


def main():
    json_path = str(_SRC.parent / "replay_event_log.json")
    alt_path = "replay_event_log.json"

    audit = ReplayAuditSkill()

    for path in [json_path, alt_path]:
        if Path(path).exists():
            print(f"Found: {path}")
            result = audit.execute(action="migrate", json_path=path)
            if result.get("error"):
                print(f"Error: {result['error']}")
                return 1
            r = result["result"]
            print(f"Migrated {r['migrated']} events from {r['source']}.")
            print("You may now archive or delete the JSON file.")
            return 0

    print("No replay_event_log.json found — nothing to migrate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
