using System.Net;
using System.Text;
using VanEngine.Game.Core;

namespace VanEngine.Game.Infrastructure;

public sealed class EventWebhook : IDisposable
{
    private readonly SovereignState _state;
    private HttpListener? _listener;
    private CancellationTokenSource? _cts;
    private readonly int _port;

    public bool IsRunning => _listener?.IsListening ?? false;
    public int Port => _port;
    public int EventsReceived { get; private set; }

    public EventWebhook(SovereignState state, int port = 8176)
    {
        _state = state;
        _port = port;
    }

    public void Start()
    {
        if (_listener?.IsListening == true) return;

        _listener = new HttpListener();
        _listener.Prefixes.Add($"http://localhost:{_port}/");
        _cts = new CancellationTokenSource();

        try
        {
            _listener.Start();
            _state.EnqueueLog($"Event webhook listening on http://localhost:{_port}/");
            Task.Run(() => ListenLoop(_cts.Token));
        }
        catch (Exception ex)
        {
            _state.EnqueueLog($"Webhook failed to start: {ex.Message}");
        }
    }

    private async Task ListenLoop(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested && _listener?.IsListening == true)
        {
            try
            {
                var ctx = await _listener.GetContextAsync().WaitAsync(ct);
                await HandleRequest(ctx);
            }
            catch (OperationCanceledException) { break; }
            catch (HttpListenerException) { break; }
            catch { }
        }
    }

    private async Task HandleRequest(HttpListenerContext ctx)
    {
        EventsReceived++;
        var req = ctx.Request;
        var resp = ctx.Response;

        try
        {
            using var reader = new StreamReader(req.InputStream, req.ContentEncoding);
            string body = await reader.ReadToEndAsync();

            string path = req.Url?.AbsolutePath ?? "/";
            string method = req.HttpMethod;

            string summary = $"Webhook {method} {path}";
            if (!string.IsNullOrEmpty(body) && body.Length > 100)
                summary += $" ({body.Length}b)";

            _state.EnqueueLog(summary);

            if (method == "POST" && body.Contains("\"file\""))
            {
                try
                {
                    var doc = System.Text.Json.JsonDocument.Parse(body);
                    string? filePath = null;

                    if (doc.RootElement.TryGetProperty("file", out var fProp))
                        filePath = fProp.GetString();

                    if (doc.RootElement.TryGetProperty("build_status", out var bProp))
                    {
                        string status = bProp.GetString() ?? "unknown";
                        if (status == "success")
                        {
                            _state.AddSovereignty(1, $"CI build success: {filePath ?? "unknown"}");
                            _state.ModifyResources(new ResourcePack { Wealth = 5 });
                        }
                        else if (status == "failure")
                        {
                            _state.AddSovereignty(-2, $"CI build failure: {filePath ?? "unknown"}");
                        }
                        _state.AddTimelineEntry(_state.Year, "house", $"CI {status}: {filePath ?? path}", "webhook");
                    }

                    if (doc.RootElement.TryGetProperty("event", out var eProp))
                    {
                        string eventType = eProp.GetString() ?? "push";
                        if (eventType == "save" && filePath != null)
                        {
                            _state.ModifyResources(new ResourcePack { Food = 2 });
                            _state.AddTimelineEntry(_state.Year, "event", $"Editor save: {Path.GetFileName(filePath)}", "webhook");
                        }
                    }
                }
                catch { }
            }

            byte[] respBytes = Encoding.UTF8.GetBytes("{\"status\":\"ok\"}");
            resp.ContentType = "application/json";
            resp.ContentLength64 = respBytes.Length;
            resp.StatusCode = 200;
            await resp.OutputStream.WriteAsync(respBytes);
            resp.OutputStream.Close();
        }
        catch
        {
            resp.StatusCode = 500;
            resp.OutputStream.Close();
        }
    }

    public void Stop()
    {
        _cts?.Cancel();
        try { _listener?.Stop(); } catch { }
        _state.EnqueueLog("Event webhook stopped");
    }

    public void Dispose()
    {
        Stop();
        _cts?.Dispose();
        _listener?.Close();
    }
}
