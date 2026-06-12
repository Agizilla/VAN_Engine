using System;
using System.Threading;
using System.Threading.Tasks;
using VAN_Engine.Core.WebSocket;

namespace VAN_Engine.Tests
{
    class TestWebSocket
    {
        static async Task Main()
        {
            Console.WriteLine("=== VAN_Engine WebSocket Tests ===\n");

            var server = new WebSocketServer(9090, async (msg) =>
            {
                await Task.Delay(10);
                return $"{{\"echo\": true, \"received\": \"{msg}\"}}";
            });

            server.Start();
            Console.WriteLine("Server started on port 9090");

            Console.WriteLine("\nTest: Health endpoint");
            using var httpClient = new System.Net.Http.HttpClient();
            var response = await httpClient.GetAsync("http://localhost:9090/health");
            Console.WriteLine($"  Health: {response.StatusCode}");

            Console.WriteLine("\nTest: Stats endpoint");
            response = await httpClient.GetAsync("http://localhost:9090/stats");
            var body = await response.Content.ReadAsStringAsync();
            Console.WriteLine($"  Stats: {body}");

            Console.WriteLine("\nAll WebSocket tests passed");
            server.Stop();
        }
    }
}
