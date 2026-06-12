#!/usr/bin/env python3
import sys, io, json, asyncio, uuid, time
from pathlib import Path
from typing import Dict, List, Set, Any
from dataclasses import dataclass, field
from aiohttp import web, web_ws
import aiohttp

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

@dataclass
class StepExecution:
    id: str
    action: str
    status: str = "pending"
    start_time: float = 0
    end_time: float = 0
    output: Any = None
    error: str = ""

@dataclass
class PipelineExecution:
    id: str
    agent: str
    pipeline: str
    status: str = "pending"
    current_step: str = ""
    steps: List[StepExecution] = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0
    result: Any = None
    error: str = ""

class PipelineMonitorServer:
    def __init__(self, port: int = 8765):
        self.port = port
        self.executions: Dict[str, PipelineExecution] = {}
        self.clients: Set[web_ws.WebSocketResponse] = set()
        self.app = None
        self.runner = None

    async def start(self):
        self.app = web.Application()
        self.app.router.add_get('/ws', self._handle_websocket)
        self.app.router.add_post('/api/start', self._handle_start)
        self.app.router.add_post('/api/update', self._handle_update)
        self.app.router.add_post('/api/step', self._handle_step)
        self.app.router.add_get('/api/executions', self._handle_list)
        self.app.router.add_get('/', self._handle_ui)
        self.app.router.add_get('/health', self._handle_health)
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, 'localhost', self.port)
        await site.start()
        print(f"[PipelineMonitor] Started on port {self.port}")

    async def stop(self):
        for client in self.clients:
            await client.close()
        if self.runner:
            await self.runner.cleanup()

    async def _broadcast(self, event: str, data: Any):
        message = json.dumps({"event": event, "data": data, "timestamp": int(time.time() * 1000)})
        dead_clients = set()
        for client in self.clients:
            try:
                await client.send_str(message)
            except:
                dead_clients.add(client)
        for dead in dead_clients:
            self.clients.discard(dead)

    async def _handle_websocket(self, request: web.Request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.clients.add(ws)
        await ws.send_str(json.dumps({"event": "init",
            "data": {"executions": [self._execution_to_dict(e) for e in self.executions.values()]},
            "timestamp": int(time.time() * 1000)}))
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.CLOSE:
                    break
        finally:
            self.clients.discard(ws)
        return ws

    async def _handle_start(self, request: web.Request):
        data = await request.json()
        execution_id = str(uuid.uuid4())
        steps = [StepExecution(id=s.get('id', str(uuid.uuid4())[:8]),
                 action=s.get('action', 'unknown')) for s in data.get('steps', [])]
        execution = PipelineExecution(id=execution_id, agent=data.get('agent', 'unknown'),
            pipeline=data.get('pipeline', 'unknown'), steps=steps,
            start_time=time.time() * 1000)
        self.executions[execution_id] = execution
        await self._broadcast("pipeline:start", self._execution_to_dict(execution))
        return web.json_response({"id": execution_id})

    async def _handle_update(self, request: web.Request):
        data = await request.json()
        exec_id = data.get('id')
        if exec_id not in self.executions:
            return web.json_response({"error": "Not found"}, status=404)
        exec_obj = self.executions[exec_id]
        if 'status' in data:
            exec_obj.status = data['status']
            if exec_obj.status in ('completed', 'failed'):
                exec_obj.end_time = time.time() * 1000
        if 'current_step' in data:
            exec_obj.current_step = data['current_step']
        if 'result' in data:
            exec_obj.result = data['result']
        if 'error' in data:
            exec_obj.error = data['error']
        await self._broadcast("pipeline:update", self._execution_to_dict(exec_obj))
        return web.json_response({"ok": True})

    async def _handle_step(self, request: web.Request):
        data = await request.json()
        exec_id = data.get('executionId')
        if exec_id not in self.executions:
            return web.json_response({"error": "Not found"}, status=404)
        exec_obj = self.executions[exec_id]
        step = next((s for s in exec_obj.steps if s.id == data.get('stepId')), None)
        if not step:
            return web.json_response({"error": "Step not found"}, status=404)
        if 'status' in data:
            step.status = data['status']
            if step.status == 'running':
                step.start_time = time.time() * 1000
            if step.status in ('completed', 'failed'):
                step.end_time = time.time() * 1000
        if 'output' in data:
            step.output = data['output']
        if 'error' in data:
            step.error = data['error']
        await self._broadcast(f"step:{data['status']}",
            {"executionId": exec_id, "stepId": step.id, "status": step.status})
        return web.json_response({"ok": True})

    async def _handle_list(self, request: web.Request):
        return web.json_response({"executions": [self._execution_to_dict(e) for e in self.executions.values()]})

    async def _handle_health(self, request: web.Request):
        return web.json_response({"status": "ok", "port": self.port})

    async def _handle_ui(self, request: web.Request):
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>VAN_Engine Pipeline Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: monospace; background: #0a0a0a; color: #e0e0e0; padding: 20px; }
        h1 { color: #00ffcc; margin-bottom: 20px; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
        .stat { background: #1a1a1a; padding: 10px 20px; border-radius: 8px; border: 1px solid #333; }
        .stat-value { font-size: 28px; font-weight: bold; color: #00ffcc; }
        .stat-label { font-size: 11px; color: #888; }
        .executions { display: flex; flex-direction: column; gap: 10px; }
        .execution { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 15px; }
        .execution.running { border-color: #00ffcc; }
        .execution.completed { border-color: #00ffaa; }
        .execution.failed { border-color: #ff4444; }
        .execution-header { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .execution-id { font-weight: bold; color: #00ffcc; }
        .steps { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
        .step { font-size: 10px; padding: 4px 8px; border-radius: 4px; background: #2a2a2a; }
        .step.completed { background: #00ffaa20; color: #00ffaa; }
        .step.running { background: #00ffcc20; color: #00ffcc; animation: pulse 1s infinite; }
        .step.failed { background: #ff444420; color: #ff4444; }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <h1>VAN_Engine Pipeline Monitor</h1>
    <div class="stats" id="stats"></div>
    <div class="executions" id="executions"></div>
    <script>
        let ws;
        function connect() {
            ws = new WebSocket('ws://' + location.host + '/ws');
            ws.onmessage = (e) => {
                const msg = JSON.parse(e.data);
                if (msg.event === 'init') render(msg.data.executions);
                else if (msg.event === 'pipeline:start' || msg.event === 'pipeline:update') fetchExecutions();
            };
            ws.onclose = () => setTimeout(connect, 2000);
        }
        async function fetchExecutions() {
            const res = await fetch('/api/executions'); const data = await res.json(); render(data.executions);
        }
        function render(executions) {
            const stats = { total: executions.length, running: executions.filter(e => e.status === 'running').length, completed: executions.filter(e => e.status === 'completed').length, failed: executions.filter(e => e.status === 'failed').length };
            document.getElementById('stats').innerHTML = `<div class='stat'><div class='stat-value'>${stats.total}</div><div class='stat-label'>Total</div></div><div class='stat'><div class='stat-value'>${stats.running}</div><div class='stat-label'>Running</div></div><div class='stat'><div class='stat-value'>${stats.completed}</div><div class='stat-label'>Completed</div></div><div class='stat'><div class='stat-value'>${stats.failed}</div><div class='stat-label'>Failed</div></div>`;
            document.getElementById('executions').innerHTML = executions.map(e => `<div class='execution ${e.status}'><div class='execution-header'><span class='execution-id'>${e.id.substring(0,8)}</span><span class='execution-status ${e.status}'>${e.status}</span></div><div><strong>${e.pipeline}</strong> (${e.agent})</div><div class='steps'>${e.steps.map(s => `<div class='step ${s.status}'>${s.action}</div>`).join('')}</div></div>`).join('');
        }
        connect(); fetchExecutions(); setInterval(fetchExecutions, 2000);
    </script>
</body>
</html>'''
        return web.Response(text=html, content_type='text/html')

    def _execution_to_dict(self, exec_obj: PipelineExecution) -> dict:
        return {"id": exec_obj.id, "agent": exec_obj.agent, "pipeline": exec_obj.pipeline,
            "status": exec_obj.status, "current_step": exec_obj.current_step,
            "steps": [{"id": s.id, "action": s.action, "status": s.status} for s in exec_obj.steps],
            "start_time": exec_obj.start_time, "end_time": exec_obj.end_time, "error": exec_obj.error}

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765, help="WebSocket port")
    args = parser.parse_args()
    server = PipelineMonitorServer(args.port)
    await server.start()
    print(f"Pipeline Monitor running on http://localhost:{args.port}")
    print("Press Ctrl+C to stop")
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
