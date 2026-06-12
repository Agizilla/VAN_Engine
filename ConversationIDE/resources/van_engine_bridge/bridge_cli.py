"""
VAN_Engine Bridge CLI — Persistent JSON-RPC over stdin/stdout
ISO_019: Privacy by Default — No external calls unless enabled
"""

import sys
import io
import json
import math
from pathlib import Path

if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from client import get_bridge


def handle_request(method: str, params: dict) -> dict:
    bridge = get_bridge()
    result = {"success": True, "method": method}

    try:
        if method == "ping":
            result["pong"] = True

        elif method == "status":
            rules = bridge.get_iso_rules()
            result["available"] = True
            result["engine_root"] = str(bridge.engine_root)
            result["iso_count"] = len(rules.get("rules", []))
            result["token_count"] = bridge.get_token_count()

        elif method == "quaternion_lookup":
            token = params.get("token", "")
            q = bridge.quaternion_lookup(token)
            if q:
                result["found"] = True
                result["w"], result["x"], result["y"], result["z"] = q
            else:
                result["found"] = False

        elif method == "quaternion_store":
            bridge.quaternion_store(
                params.get("token", ""),
                params.get("w", 0), params.get("x", 0),
                params.get("y", 0), params.get("z", 0),
                params.get("applies_to", "general")
            )
            result["stored"] = True

        elif method == "iso_rules":
            rules = bridge.get_iso_rules()
            result["rules"] = rules.get("rules", [])

        elif method == "token_count":
            result["count"] = bridge.get_token_count()

        elif method == "drift_check":
            q = params.get("quaternion", (0, 0, 0, 0))
            threshold = params.get("threshold", 0.85)
            g = bridge.drift_gate(tuple(q), threshold)
            result.update(g)

        elif method == "audit_log":
            bridge.log_audit(
                params.get("component", "unknown"),
                params.get("action", "unknown"),
                tuple(params.get("quaternion_before")) if params.get("quaternion_before") else None,
                tuple(params.get("quaternion_after")) if params.get("quaternion_after") else None
            )
            result["logged"] = True

        else:
            result["success"] = False
            result["error"] = f"Unknown method: {method}"

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)

    return result


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            req_id = request.get("id", 0)
            method = request.get("method", "")
            params = request.get("params", {})

            response = handle_request(method, params)
            response["id"] = req_id
            print(json.dumps(response), flush=True)

        except json.JSONDecodeError:
            print(json.dumps({"id": 0, "success": False, "error": "Invalid JSON"}), flush=True)
        except Exception as e:
            print(json.dumps({"id": 0, "success": False, "error": str(e)}), flush=True)


if __name__ == "__main__":
    print(json.dumps({"id": 0, "ready": True}), flush=True)
    main()
