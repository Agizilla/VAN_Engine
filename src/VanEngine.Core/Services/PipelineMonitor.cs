using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;

namespace VanEngine.Core.Services;

public class PipelineMonitor : IDisposable
{
    private IWebHost? _host;
    private readonly int _port;
    private readonly ConcurrentDictionary<string, PipelineExecution> _executions = new();
    private readonly HashSet<WebSocket> _clients = new();
    private readonly object _clientLock = new();
    private bool _isRunning;

    public PipelineMonitor(int port = 8765)
    {
        _port = port;
    }

    public void Start()
    {
        if (_isRunning) return;

        _host = new WebHostBuilder()
            .UseKestrel()
            .UseUrls($"http://*:{_port}")
            .ConfigureServices(services =>
            {
                services.AddCors();
                services.AddRouting();
            })
            .Configure(app =>
            {
                app.UseCors(builder => builder.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());
                app.UseWebSockets();
                app.Use(async (context, next) =>
                {
                    if (context.WebSockets.IsWebSocketRequest)
                    {
                        var webSocket = await context.WebSockets.AcceptWebSocketAsync();
                        await HandleWebSocket(webSocket);
                    }
                    else { await next(); }
                });
                app.Map("/api/start", branch => branch.Run(HandleStartPipeline));
                app.Map("/api/update", branch => branch.Run(HandleUpdatePipeline));
                app.Map("/api/step", branch => branch.Run(HandleUpdateStep));
                app.Map("/", branch => branch.Run(HandleUI));
            })
            .Build();

        _host.Start();
        _isRunning = true;
        Console.WriteLine($"[PipelineMonitor] Started on port {_port}");
    }

    private async Task HandleWebSocket(WebSocket webSocket)
    {
        lock (_clientLock) { _clients.Add(webSocket); }
        try
        {
            await SendToClient(webSocket, "init", new { executions = _executions.Values });
            var buffer = new byte[4096];
            while (webSocket.State == WebSocketState.Open)
            {
                var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);
                if (result.MessageType == WebSocketMessageType.Close) break;
            }
        }
        finally
        {
            lock (_clientLock) { _clients.Remove(webSocket); }
            await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
            webSocket.Dispose();
        }
    }

    private void Broadcast(string eventType, object data)
    {
        var message = JsonSerializer.Serialize(new { @event = eventType, data, timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() });
        var bytes = Encoding.UTF8.GetBytes(message);
        lock (_clientLock)
        {
            var dead = _clients.Where(c => c.State != WebSocketState.Open).ToList();
            foreach (var d in dead) _clients.Remove(d);
            foreach (var client in _clients)
            {
                try { client.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None).GetAwaiter().GetResult(); }
                catch { _clients.Remove(client); }
            }
        }
    }

    private static async Task SendToClient(WebSocket client, string eventType, object data)
    {
        var message = JsonSerializer.Serialize(new { @event = eventType, data, timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() });
        var bytes = Encoding.UTF8.GetBytes(message);
        await client.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
    }

    private async Task HandleStartPipeline(HttpContext context)
    {
        if (!context.Request.HasJsonContentType()) { context.Response.StatusCode = 400; return; }
        var body = await JsonSerializer.DeserializeAsync<StartPipelineRequest>(context.Request.Body);
        if (body == null) { context.Response.StatusCode = 400; return; }

        var executionId = Guid.NewGuid().ToString();
        var execution = new PipelineExecution
        {
            Id = executionId,
            Agent = body.Agent ?? "unknown",
            Pipeline = body.Pipeline,
            Status = "pending",
            Steps = body.Steps?.Select(s => new StepExecution { Id = s.Id, Action = s.Action, Status = "pending" }).ToList() ?? new List<StepExecution>(),
            StartTime = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
        };
        _executions[executionId] = execution;
        Broadcast("pipeline:start", execution);
        await context.Response.WriteAsJsonAsync(new { id = executionId });
    }

    private async Task HandleUpdatePipeline(HttpContext context)
    {
        if (!context.Request.HasJsonContentType()) { context.Response.StatusCode = 400; return; }
        var body = await JsonSerializer.DeserializeAsync<UpdatePipelineRequest>(context.Request.Body);
        if (body?.Id == null || !_executions.TryGetValue(body.Id, out var execution)) { context.Response.StatusCode = 404; return; }

        if (!string.IsNullOrEmpty(body.Status)) execution.Status = body.Status;
        if (!string.IsNullOrEmpty(body.CurrentStep)) execution.CurrentStep = body.CurrentStep;
        if (body.Result != null) execution.Result = body.Result;
        if (!string.IsNullOrEmpty(body.Error)) execution.Error = body.Error;
        if (execution.Status is "completed" or "failed") execution.EndTime = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

        Broadcast("pipeline:update", execution);
        await context.Response.WriteAsJsonAsync(new { ok = true });
    }

    private async Task HandleUpdateStep(HttpContext context)
    {
        if (!context.Request.HasJsonContentType()) { context.Response.StatusCode = 400; return; }
        var body = await JsonSerializer.DeserializeAsync<UpdateStepRequest>(context.Request.Body);
        if (body?.ExecutionId == null || !_executions.TryGetValue(body.ExecutionId, out var execution)) { context.Response.StatusCode = 404; return; }

        var step = execution.Steps.FirstOrDefault(s => s.Id == body.StepId);
        if (step == null) { context.Response.StatusCode = 404; return; }

        if (!string.IsNullOrEmpty(body.Status))
        {
            step.Status = body.Status;
            if (body.Status == "running") step.StartTime = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            if (body.Status is "completed" or "failed") step.EndTime = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        }
        if (body.Output != null) step.Output = body.Output;
        if (!string.IsNullOrEmpty(body.Error)) step.Error = body.Error;

        Broadcast($"step:{body.Status}", new { executionId = body.ExecutionId, stepId = body.StepId, status = body.Status });
        await context.Response.WriteAsJsonAsync(new { ok = true });
    }

    private static async Task HandleUI(HttpContext context)
    {
        context.Response.ContentType = "text/html";
        await context.Response.WriteAsync(GetHtmlUI());
    }

    private static string GetHtmlUI()
    {
        return """
<!DOCTYPE html>
<html>
<head>
    <title>VAN_Engine Pipeline Monitor</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:monospace; background:#0a0a0a; color:#e0e0e0; padding:20px; }
        h1 { color:#00ffcc; margin-bottom:20px; }
        .stats { display:flex; gap:20px; margin-bottom:20px; }
        .stat { background:#1a1a1a; padding:10px 20px; border-radius:8px; border:1px solid #333; }
        .stat-value { font-size:28px; font-weight:bold; color:#00ffcc; }
        .stat-label { font-size:11px; color:#888; }
        .executions { display:flex; flex-direction:column; gap:10px; }
        .execution { background:#1a1a1a; border:1px solid #333; border-radius:8px; padding:15px; }
        .execution.running { border-color:#00ffcc; }
        .execution.completed { border-color:#00ffaa; }
        .execution.failed { border-color:#ff4444; }
        .execution-header { display:flex; justify-content:space-between; margin-bottom:10px; }
        .execution-id { font-weight:bold; color:#00ffcc; }
        .execution-status { font-size:12px; padding:2px 8px; border-radius:4px; background:#333; }
        .execution-status.running { background:#00ffcc20; color:#00ffcc; }
        .execution-status.completed { background:#00ffaa20; color:#00ffaa; }
        .execution-status.failed { background:#ff444420; color:#ff4444; }
        .steps { display:flex; gap:8px; margin-top:10px; flex-wrap:wrap; }
        .step { font-size:10px; padding:4px 8px; border-radius:4px; background:#2a2a2a; }
        .step.completed { background:#00ffaa20; color:#00ffaa; }
        .step.running { background:#00ffcc20; color:#00ffcc; animation:pulse 1s infinite; }
        .step.failed { background:#ff444420; color:#ff4444; }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }
    </style>
</head>
<body>
    <h1>VAN_Engine Pipeline Monitor</h1>
    <div class='stats' id='stats'></div>
    <div class='executions' id='executions'></div>
    <script>
        const ws = new WebSocket('ws://' + location.host);
        ws.onmessage = (e) => { const msg = JSON.parse(e.data); if (msg.event === 'init') render(msg.data.executions); else if (msg.event === 'pipeline:start' || msg.event === 'pipeline:update') fetchExecutions(); };
        async function fetchExecutions() { const res = await fetch('/api/executions'); const data = await res.json(); render(data); }
        function render(executions) {
            const stats = { total: executions.length, running: executions.filter(e => e.status === 'running').length, completed: executions.filter(e => e.status === 'completed').length, failed: executions.filter(e => e.status === 'failed').length };
            document.getElementById('stats').innerHTML = `<div class='stat'><div class='stat-value'>${stats.total}</div><div class='stat-label'>Total</div></div><div class='stat'><div class='stat-value'>${stats.running}</div><div class='stat-label'>Running</div></div><div class='stat'><div class='stat-value'>${stats.completed}</div><div class='stat-label'>Completed</div></div><div class='stat'><div class='stat-value'>${stats.failed}</div><div class='stat-label'>Failed</div></div>`;
            document.getElementById('executions').innerHTML = executions.map(e => `<div class='execution ${e.status}'><div class='execution-header'><span class='execution-id'>${e.id.substring(0,8)}</span><span class='execution-status ${e.status}'>${e.status}</span></div><div><strong>${e.pipeline}</strong> (${e.agent})</div><div class='steps'>${e.steps.map(s => `<div class='step ${s.status}'>${s.action}</div>`).join('')}</div></div>`).join('');
        }
        fetchExecutions();
        setInterval(fetchExecutions, 2000);
    </script>
</body>
</html>
""";
    }

    public PipelineExecution? GetExecution(string id) =>
        _executions.TryGetValue(id, out var execution) ? execution : null;

    public List<PipelineExecution> GetAllExecutions() => _executions.Values.ToList();

    public void Stop()
    {
        if (!_isRunning) return;
        _host?.StopAsync().Wait();
        _host?.Dispose();
        _isRunning = false;
    }

    public void Dispose() => Stop();
}

public class PipelineExecution
{
    public string Id { get; set; } = "";
    public string Agent { get; set; } = "";
    public string Pipeline { get; set; } = "";
    public string Status { get; set; } = "pending";
    public string? CurrentStep { get; set; }
    public List<StepExecution> Steps { get; set; } = new();
    public long StartTime { get; set; }
    public long? EndTime { get; set; }
    public object? Result { get; set; }
    public string? Error { get; set; }
}

public class StepExecution
{
    public string Id { get; set; } = "";
    public string Action { get; set; } = "";
    public string Status { get; set; } = "pending";
    public long? StartTime { get; set; }
    public long? EndTime { get; set; }
    public object? Output { get; set; }
    public string? Error { get; set; }
}

public class StartPipelineRequest
{
    public string? Agent { get; set; }
    public string Pipeline { get; set; } = "";
    public List<StepDefinition>? Steps { get; set; }
}

public class StepDefinition
{
    public string Id { get; set; } = "";
    public string Action { get; set; } = "";
}

public class UpdatePipelineRequest
{
    public string Id { get; set; } = "";
    public string? Status { get; set; }
    public string? CurrentStep { get; set; }
    public object? Result { get; set; }
    public string? Error { get; set; }
}

public class UpdateStepRequest
{
    public string ExecutionId { get; set; } = "";
    public string StepId { get; set; } = "";
    public string? Status { get; set; }
    public object? Output { get; set; }
    public string? Error { get; set; }
}
