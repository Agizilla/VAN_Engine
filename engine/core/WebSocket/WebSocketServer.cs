using System;
using System.Collections.Generic;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;

namespace VAN_Engine.Core.WebSocket
{
    public sealed class WebSocketServer : IDisposable
    {
        private IWebHost _host;
        private readonly int _port;
        private bool _isRunning = false;
        private readonly List<WebSocket> _activeConnections = new List<WebSocket>();
        private readonly object _connectionLock = new object();
        private readonly Func<string, Task<string>> _queryHandler;

        public WebSocketServer(int port = 8080, Func<string, Task<string>> queryHandler = null)
        {
            _port = port;
            _queryHandler = queryHandler;
        }

        public void Start()
        {
            if (_isRunning) return;

            _host = new WebHostBuilder()
                .UseKestrel()
                .UseUrls($"http://*:{_port}")
                .Configure(app =>
                {
                    app.UseWebSockets();
                    app.Run(HandleRequest);
                })
                .Build();

            _host.Start();
            _isRunning = true;
            Console.WriteLine($"[WebSocket] Server started on port {_port}");
        }

        private async Task HandleRequest(HttpContext context)
        {
            if (context.WebSockets.IsWebSocketRequest)
            {
                var webSocket = await context.WebSockets.AcceptWebSocketAsync();
                lock (_connectionLock) _activeConnections.Add(webSocket);
                try
                {
                    await HandleConnection(webSocket);
                }
                finally
                {
                    lock (_connectionLock) _activeConnections.Remove(webSocket);
                    webSocket.Dispose();
                }
            }
            else if (context.Request.Path == "/health")
            {
                context.Response.StatusCode = 200;
                await context.Response.WriteAsync("OK");
            }
            else if (context.Request.Path == "/stats")
            {
                context.Response.ContentType = "application/json";
                await context.Response.WriteAsync(JsonSerializer.Serialize(new
                {
                    connections = _activeConnections.Count,
                    status = "running"
                }));
            }
            else
            {
                context.Response.StatusCode = 404;
            }
        }

        private async Task HandleConnection(WebSocket webSocket)
        {
            var buffer = new byte[4096];
            while (webSocket.State == WebSocketState.Open)
            {
                var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);
                if (result.MessageType == WebSocketMessageType.Close)
                {
                    await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                    break;
                }
                if (result.MessageType == WebSocketMessageType.Text)
                {
                    var message = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    string response;
                    try
                    {
                        var query = JsonSerializer.Deserialize<WebSocketQuery>(message);
                        if (query == null)
                            response = JsonSerializer.Serialize(new { error = "Invalid query" });
                        else if (_queryHandler != null)
                            response = await _queryHandler(message);
                        else
                            response = JsonSerializer.Serialize(new { success = true, result = $"Echo: {query.Type}" });
                    }
                    catch (Exception ex)
                    {
                        response = JsonSerializer.Serialize(new { error = ex.Message });
                    }
                    var responseBytes = Encoding.UTF8.GetBytes(response);
                    await webSocket.SendAsync(new ArraySegment<byte>(responseBytes), WebSocketMessageType.Text, true, CancellationToken.None);
                }
            }
        }

        public void Stop()
        {
            if (!_isRunning) return;
            lock (_connectionLock)
            {
                foreach (var ws in _activeConnections)
                {
                    try { ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None).Wait(); } catch { }
                    ws.Dispose();
                }
                _activeConnections.Clear();
            }
            _host?.StopAsync().Wait();
            _host?.Dispose();
            _isRunning = false;
            Console.WriteLine("[WebSocket] Server stopped");
        }

        public void Dispose() => Stop();
    }

    public class WebSocketQuery
    {
        public string Type { get; set; }
        public string Content { get; set; }
        public string Token { get; set; }
        public double W { get; set; }
        public double X { get; set; }
        public double Y { get; set; }
        public double Z { get; set; }
        public string[] AppliesTo { get; set; }
        public int? Limit { get; set; }
        public Dictionary<string, object> Context { get; set; }
    }
}
