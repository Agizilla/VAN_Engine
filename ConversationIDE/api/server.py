from __future__ import annotations

import json
import os
import sys
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# ============================================================================
# PATH CONFIGURATION - Fix Python imports
# ============================================================================

# Get the absolute path to the VAN directory containing brain.py
SCRIPT_DIR = Path(__file__).parent.absolute()  # .../ConversationIDE/api
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # .../VAN_Engine
VAN_PATH = PROJECT_ROOT / "ConversationIDE" / "src" / "VanEngine.Core" / "VAN"

# Also try alternative path (if files are directly under VAN_Engine/VAN)
ALT_VAN_PATH = PROJECT_ROOT / "VAN"

# Add paths to Python sys.path
if VAN_PATH.exists():
    sys.path.insert(0, str(VAN_PATH))
    print(f"[Server] Added VAN path: {VAN_PATH}")
else:
    print(f"[Server] Warning: VAN path not found: {VAN_PATH}")

if ALT_VAN_PATH.exists():
    sys.path.insert(0, str(ALT_VAN_PATH))
    print(f"[Server] Added alt VAN path: {ALT_VAN_PATH}")

# Print debug info
print(f"[Server] Script dir: {SCRIPT_DIR}")
print(f"[Server] Project root: {PROJECT_ROOT}")
print(f"[Server] Python sys.path[0]: {sys.path[0]}")

# ============================================================================
# Import VAN_Engine modules
# ============================================================================

HOST = os.environ.get("VAN_API_HOST", "127.0.0.1")
# Port from config/ports.json, overridable via env
with open(PROJECT_ROOT / "config" / "ports.json") as _f:
    _portscfg = json.load(_f)
PORT = int(os.environ.get("VAN_API_PORT", _portscfg.get("ide_api", 44444)))
MODEL = os.environ.get("VAN_API_MODEL", "van_engine-brain")

_brain = None
_engine = None

try:
    # Try different import patterns
    from brain import VANEngineBrain
    _brain = VANEngineBrain.Instance()
    print("[Brain] Loaded successfully from brain.py")
except ImportError as e:
    print(f"[Brain] Import error (brain): {e}")
    try:
        from VAN.brain import VANEngineBrain
        _brain = VANEngineBrain.Instance()
        print("[Brain] Loaded successfully from VAN.brain")
    except ImportError as e2:
        print(f"[Brain] Import error (VAN.brain): {e2}")
        print("[Brain] Running in mock mode")

try:
    from engine import VanEngine
    _engine = VanEngine()
    print("[Engine] Loaded successfully from engine.py")
except ImportError as e:
    print(f"[Engine] Import error (engine): {e}")
    try:
        from VAN.engine import VanEngine
        _engine = VanEngine()
        print("[Engine] Loaded successfully from VAN.engine")
    except ImportError as e2:
        print(f"[Engine] Import error (VAN.engine): {e2}")
        print("[Engine] Running in mock mode")

MEMORY_EVENTS_ROOT = PROJECT_ROOT / "memoryEvents"
MEMORY_EVENTS_ROOT.mkdir(parents=True, exist_ok=True)


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _extract_last_user_message(messages: List[Dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content", "")
            if isinstance(content, str):
                return content.strip()
    return ""


def _export_session(session_id: str, user_text: str, assistant_text: str, action: str, audit_entries: list) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = MEMORY_EVENTS_ROOT / f"session_{timestamp}.md"
    
    iso_list = []
    if _brain:
        try:
            stats = _brain.GetStats()
            iso_list = getattr(stats, 'ActiveISO', [])
        except:
            pass
    
    lines = [
        "# Session Memory Event",
        "",
        "## Metadata",
        f"- **Session ID:** {session_id}",
        f"- **Timestamp:** {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"- **Model:** {MODEL}",
        f"- **Action:** {action}",
        "",
        "## User Prompt",
        user_text,
        "",
        "## Brain Response",
        assistant_text,
        "",
        "## ISO State",
        ", ".join(iso_list) if iso_list else "None",
        "",
        "## Audit Trail",
    ]
    for entry in audit_entries[-10:]:
        lines.append(f"- {entry}")
    lines.extend(["", "## Diagnostics", f"Action: {action}", "", "## Next Actions", ""])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def _get_brain_response(user_text: str) -> tuple[str, str, list]:
    action = "EXECUTE"
    assistant_text = ""
    
    if _brain:
        try:
            result = _brain.ExecuteQuery(user_text)
            assistant_text = getattr(result, 'Message', '')
            action = getattr(result, 'Action', 'EXECUTE')
        except Exception as e:
            assistant_text = f"Brain error: {e}"
            action = "ERROR"
    else:
        # Mock response when brain not available
        user_lower = user_text.lower()
        if "status" in user_lower:
            assistant_text = """VAN_Engine is online (mock mode).
            
Active ISO rules: ISO_001-020
Tokens: 0
Uptime: running"""
        elif "help" in user_lower:
            assistant_text = """Available commands:
- status: System status
- help: This message
- lookup <token>: Find token
- store <token> (w,x,y,z): Store token
- algorithm: Run 7-phase Algorithm"""
        elif "lookup" in user_lower:
            assistant_text = "Token not found in index."
        elif "store" in user_lower:
            assistant_text = "Token stored successfully."
        elif "algorithm" in user_lower:
            assistant_text = """Running 7-Phase Algorithm:
1. OBSERVE - Understanding request
2. THINK - Analyzing options
3. PLAN - Designing approach
4. BUILD - Implementing solution
5. EXECUTE - Running tests
6. VERIFY - Checking criteria
7. LEARN - Capturing insights"""
        else:
            assistant_text = f"I received: \"{user_text}\"\n\n[VAN_Engine mock mode - Connect the actual brain for full functionality]"
        action = "MOCK"
    
    audit = []
    if _brain:
        try:
            audit_events = _brain.GetAuditTrail(10)
            audit = [f"[{getattr(e, 'Timestamp', '?')}] {getattr(e, 'Kind', '?')}: {getattr(e, 'Payload', '?')}" for e in audit_events]
        except:
            pass
    
    return assistant_text, action, audit


def _chat_completion_payload(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    user_text = _extract_last_user_message(messages)
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    created_ts = int(datetime.now().timestamp())

    if not user_text:
        return {
            "id": f"chatcmpl_{created_ts}",
            "object": "chat.completion",
            "created": created_ts,
            "model": MODEL,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "I am online and ready for chat."}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 5, "total_tokens": 5},
            "metadata": {"server_time": now, "brain_action": "STATUS", "session_id": session_id},
        }

    # Safely record envelope
    if _engine and hasattr(_engine, 'Metrics'):
        try:
            if hasattr(_engine.Metrics, 'RecordEnvelope'):
                _engine.Metrics.RecordEnvelope()
            else:
                if not hasattr(_engine.Metrics, 'envelopes'):
                    _engine.Metrics.envelopes = 0
                _engine.Metrics.envelopes += 1
        except:
            pass

    assistant_text, action, audit = _get_brain_response(user_text)
    export_path = _export_session(session_id, user_text, assistant_text, action, audit)

    return {
        "id": f"chatcmpl_{created_ts}",
        "object": "chat.completion",
        "created": created_ts,
        "model": MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": assistant_text},
                "finish_reason": "stop" if action != "HALT_AND_CLARIFY" else "length",
            }
        ],
        "usage": {
            "prompt_tokens": max(1, len(json.dumps(messages).split())),
            "completion_tokens": max(1, len(assistant_text.split())),
            "total_tokens": max(2, len(json.dumps(messages).split()) + len(assistant_text.split())),
        },
        "metadata": {
            "server_time": now,
            "brain_action": action,
            "session_id": session_id,
            "export_path": export_path,
        },
    }


class VANApiHandler(BaseHTTPRequestHandler):
    server_version = "ConversationIDEAPI/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[VAN_API] {self.address_string()} - {format % args}")

    def do_GET(self) -> None:
        if self.path in {"/", "/health"}:
            _json_response(self, 200, {"status": "ok", "model": MODEL})
            return
        if self.path == "/status":
            if _brain:
                try:
                    stats = _brain.GetStats()
                    self_test = _brain.SelfTest()
                    payload = {
                        "brain": self_test.IsValid,
                        "diagnostics": self_test.Diagnostics,
                        "model": MODEL,
                        "uptime": stats.Uptime,
                        "token_count": stats.TokenCount,
                        "audit_count": stats.AuditEventCount,
                        "active_iso": stats.ActiveISO if stats.ActiveISO else [],
                    }
                except Exception as e:
                    payload = {"brain": False, "diagnostics": str(e), "model": MODEL}
            else:
                payload = {
                    "brain": False,
                    "diagnostics": "Brain not loaded (mock mode)",
                    "model": MODEL,
                    "uptime": 0,
                    "token_count": 0,
                    "audit_count": 0,
                    "active_iso": ["ISO_001", "ISO_002", "ISO_003", "ISO_004", "ISO_005",
                                   "ISO_006", "ISO_007", "ISO_008", "ISO_009", "ISO_010",
                                   "ISO_011", "ISO_012", "ISO_013", "ISO_014", "ISO_015",
                                   "ISO_016", "ISO_017", "ISO_018", "ISO_019", "ISO_020"],
                }
            _json_response(self, 200, payload)
            return
        _json_response(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            _json_response(self, 404, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            _json_response(self, 400, {"error": {"message": "Invalid JSON"}})
            return

        messages = payload.get("messages", [])
        if not isinstance(messages, list):
            _json_response(self, 400, {"error": {"message": "messages must be a list"}})
            return

        _json_response(self, 200, _chat_completion_payload(messages))


def main() -> None:
    print("=" * 60)
    print("VAN_Engine ConversationIDE API Server")
    print("=" * 60)
    print(f"Script directory: {SCRIPT_DIR}")
    print(f"VAN path: {VAN_PATH}")
    print(f"VAN path exists: {VAN_PATH.exists()}")
    print(f"Brain loaded: {_brain is not None}")
    print(f"Engine loaded: {_engine is not None}")
    print("=" * 60)
    
    server = ThreadingHTTPServer((HOST, PORT), VANApiHandler)
    print(f"[VAN_API] Listening on http://{HOST}:{PORT}")
    
    if _brain is None:
        print("[VAN_API] Running in MOCK mode - VAN_Engine brain not loaded")
        print("[VAN_API] To load the brain, ensure brain.py is in the Python path")
    else:
        print("[VAN_API] Running with actual VAN_Engine brain")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[VAN_API] Shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()