"""Server Manager — launch, monitor, restart child processes from a config.

Usage:
    python saas/server_manager.py          # Start the web UI
    python saas/server_manager.py --serve  # Start in serve mode (API only)
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

CONFIG_PATH = Path(__file__).parent / "servers.json"

processes = {}


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)["servers"]


def check_health(url, timeout=3):
    if not url:
        return "unknown"
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=timeout) as resp:
            return "up" if resp.status < 500 else "down"
    except Exception:
        return "down"


def get_metrics(port):
    if not port:
        return {}
    try:
        req = Request(f"http://127.0.0.1:{port}/")
        with urlopen(req, timeout=3) as resp:
            return json.loads(resp.read())
    except Exception:
        return {}


def start_server(cfg):
    name = cfg["name"]
    if name in processes and processes[name].poll() is None:
        return {"status": "already running", "pid": processes[name].pid}

    cmd = cfg["command"]
    cwd = cfg.get("cwd") or str(Path(__file__).parent.parent)
    if not cmd:
        return {"status": "no command configured"}

    try:
        p = subprocess.Popen(
            cmd.split(),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        processes[name] = p
        return {"status": "started", "pid": p.pid}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def stop_server(name):
    if name not in processes or processes[name].poll() is not None:
        return {"status": "not running"}
    p = processes[name]
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/PID", str(p.pid)], capture_output=True)
    else:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
    del processes[name]
    return {"status": "stopped"}


def restart_server(cfg):
    stop_server(cfg["name"])
    time.sleep(0.5)
    return start_server(cfg)


def get_all_status():
    configs = load_config()
    results = []
    for cfg in configs:
        health = check_health(cfg.get("health_url") or f"http://127.0.0.1:{cfg['port']}/")
        metrics = get_metrics(cfg["port"]) if health == "up" else {}
        running = cfg["name"] in processes and processes[cfg["name"]].poll() is None
        results.append({
            "name": cfg["name"],
            "command": cfg["command"],
            "port": cfg["port"],
            "health": health,
            "running": running,
            "pid": processes[cfg["name"]].pid if running else None,
            "metrics": metrics,
            "color": cfg.get("color", "#00f2fe"),
            "tags": cfg.get("tags", []),
            "notes": cfg.get("notes", ""),
        })
    return results


def web_ui(status_data):
    rows = ""
    for s in status_data:
        dot = "🔴" if s["health"] == "down" else "🟢"
        tags = " ".join(f'<span class="tag">{t}</span>' for t in s["tags"])
        metrics = ""
        if s["metrics"]:
            m = s["metrics"]
            metrics = f'<div class="metric-row"><span>skills: {m.get("skills","?")}</span></div>'
        rows += f"""
        <div class="server-card" style="border-left: 3px solid {s['color']}">
            <div class="card-header">
                <span class="health-dot">{dot}</span>
                <strong>{s["name"]}</strong>
                <span class="pid">{'PID: '+str(s['pid']) if s['pid'] else ''}</span>
            </div>
            <div class="card-body">
                <div class="info-row"><span class="label">port</span><span>{s['port'] or '—'}</span></div>
                <div class="info-row"><span class="label">health</span><span>{s['health']}</span></div>
                <div class="info-row"><span class="label">command</span><span class="cmd">{s['command'] or 'embedded'}</span></div>
                {metrics}
                <div class="tags">{tags}</div>
                <div class="notes">{s['notes']}</div>
                <div class="actions">
                    <button onclick="fetch('/api/server/start?name={s['name']}').then(()=>location.reload())">▶ Start</button>
                    <button onclick="fetch('/api/server/stop?name={s['name']}').then(()=>location.reload())">⏹ Stop</button>
                    <button onclick="fetch('/api/server/restart?name={s['name']}').then(()=>location.reload())">⟳ Restart</button>
                </div>
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><title>Server Manager</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#06080f;color:#c8d0e0;font-family:'Segoe UI',system-ui,monospace;padding:30px 20px}}
h1{{font-size:1.4rem;font-weight:300;letter-spacing:.12em;text-transform:uppercase;color:#6af;margin-bottom:6px}}
.sub{{color:#6a7;font-size:.85rem;margin-bottom:20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
.server-card{{background:#0c1220;border:1px solid #1a2540;border-radius:12px;padding:16px;transition:.2s}}
.server-card:hover{{border-color:#4cf;box-shadow:0 0 20px rgba(60,200,255,0.06)}}
.card-header{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.health-dot{{font-size:14px}}
.pid{{font-size:10px;color:#5a728a;margin-left:auto}}
.card-body{{font-size:12px}}
.info-row{{display:flex;gap:8px;margin:3px 0}}
.label{{color:#5a728a;width:50px;flex-shrink:0}}
.cmd{{color:#88aacc;font-family:monospace;font-size:10px;word-break:break-all}}
.metric-row{{color:#66ff99;margin:3px 0;font-size:11px}}
.tags{{margin:6px 0}}
.tag{{display:inline-block;background:#1a2540;border-radius:10px;padding:1px 8px;font-size:9px;color:#5af;margin:1px}}
.notes{{color:#6a8;font-size:10px;margin:4px 0}}
.actions{{display:flex;gap:6px;margin-top:8px}}
.actions button{{background:#1a2030;border:1px solid #2a4060;border-radius:6px;color:#88bbdd;font-size:10px;padding:4px 10px;cursor:pointer;transition:.15s;font-family:inherit}}
.actions button:hover{{background:#2a4060;color:#aaddff}}
.actions button:nth-child(2):hover{{background:#4a2030;border-color:#a33;color:#ff8888}}
</style></head><body>
<h1>⚙ Server Manager</h1>
<div class="sub">launch · monitor · restart — single pane</div>
<div class="grid">{rows}</div>
<div style="margin-top:20px;font-size:11px;color:#5a728a;text-align:center">
<a href="/" style="color:#5af">← back to SAAS</a> &nbsp;·&nbsp; <a href="/api/server/status" style="color:#5af">JSON status</a>
</div>
</body></html>"""


def run_web_server(host="127.0.0.1", port=9001):
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/server/status":
                data = get_all_status()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2).encode())
            elif self.path.startswith("/api/server/start"):
                name = self._get_name()
                cfg = next((c for c in load_config() if c["name"] == name), None)
                result = start_server(cfg) if cfg else {"status": "not found"}
                self._json_response(result)
            elif self.path.startswith("/api/server/stop"):
                name = self._get_name()
                result = stop_server(name)
                self._json_response(result)
            elif self.path.startswith("/api/server/restart"):
                name = self._get_name()
                cfg = next((c for c in load_config() if c["name"] == name), None)
                result = restart_server(cfg) if cfg else {"status": "not found"}
                self._json_response(result)
            else:
                data = get_all_status()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(web_ui(data).encode())

        def _get_name(self):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            return qs.get("name", [""])[0]

        def _json_response(self, data):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def log_message(self, fmt, *args):
            print(f"[SM] {args[0]} {args[1]} {args[2]}")

    server = HTTPServer((host, port), Handler)
    print(f"Server Manager UI: http://{host}:{port}")
    print(f"JSON status:       http://{host}:{port}/api/server/status")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Server Manager")
    parser.add_argument("--port", type=int, default=9001, help="UI port")
    parser.add_argument("--serve", action="store_true", help="Just start the web UI (don't auto-start servers)")
    args = parser.parse_args()

    for cfg in load_config():
        if cfg["command"] and not args.serve:
            r = start_server(cfg)
            print(f"  {cfg['name']}: {r['status']}")
        elif not cfg["command"]:
            print(f"  {cfg['name']}: embedded (no command)")

    run_web_server(port=args.port)
