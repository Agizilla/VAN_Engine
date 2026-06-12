using System;
using System.IO;
using System.Threading.Tasks;
using VAN_Engine.Core.Storage;
using VAN_Engine.Core.WebSocket;
using VAN_Engine.Core.Voice;

namespace VAN_Engine.Core
{
    public class IntegrationExample
    {
        public static async Task RunAsync()
        {
            var dataDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data");
            Directory.CreateDirectory(dataDir);

            Console.WriteLine("=== VAN_Engine Full Integration ===\n");

            Console.WriteLine("1. Initializing Hybrid Storage...");
            var sqlitePath = Path.Combine(dataDir, "van_engine.db");
            var lmdbPath = Path.Combine(dataDir, "index.lmdb");
            ISubstrateStorage storage;
            try
            {
                storage = new HybridStorage(lmdbPath, sqlitePath);
                Console.WriteLine("   Hybrid (LMDB + SQLite) storage active");
            }
            catch
            {
                storage = new SQLiteStorage(sqlitePath);
                Console.WriteLine("   SQLite storage active (LMDB unavailable)");
            }

            Console.WriteLine("\n2. Storing sample tokens...");
            await storage.StoreTokenAsync("sound_wave", 0.8, 0.3, 0.2, 0.1, new[] { "audio", "physics" });
            await storage.StoreTokenAsync("shape_triangle", 0.1, 0.9, 0.3, 0.2, new[] { "geometry", "visual" });
            await storage.StoreTokenAsync("number_pi", 0.2, 0.1, 0.9, 0.3, new[] { "math", "constant" });
            await storage.StoreTokenAsync("time_cycle", 0.3, 0.2, 0.1, 0.9, new[] { "temporal", "physics" });
            Console.WriteLine("   4 tokens stored");

            Console.WriteLine("\n3. Looking up token...");
            var (found, w, x, y, z) = await storage.LookupTokenAsync("sound_wave");
            Console.WriteLine(found ? $"   sound_wave -> ({w:F2}, {x:F2}, {y:F2}, {z:F2})" : "   Not found");

            Console.WriteLine("\n4. Finding nearest vectors...");
            var nearest = await storage.FindNearestAsync(0.8, 0.3, 0.2, 0.1, 3);
            foreach (var (token, nw, nx, ny, nz, sim) in nearest)
                Console.WriteLine($"   {token}: similarity={sim:F4}");

            Console.WriteLine("\n5. Logging audit trail...");
            await storage.LogAuditAsync("Integration", "Startup", null, null, null, null, 1, 0, 0, 0, "System initialized");
            var audit = await storage.GetAuditTrailAsync(10);
            Console.WriteLine($"   {audit.Count} audit entries");

            Console.WriteLine("\n6. Starting WebSocket server...");
            var handlers = new QueryHandlers(storage);
            var wsServer = new WebSocketServer(8080, handlers.HandleQuery);
            wsServer.Start();

            Console.WriteLine("\n7. Initializing Voice parser...");
            var voiceParser = new VoiceCommandParser(
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "models", "whisper_tiny.onnx"),
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "models", "lora_adapter.bin")
            );
            Console.WriteLine("   Voice parser ready");

            Console.WriteLine("\n=== VAN_Engine Fully Operational ===");
            Console.WriteLine("   SQLite: Persistent storage");
            Console.WriteLine("   LMDB: mmap-friendly index (if available)");
            Console.WriteLine("   WebSocket: Listening on port 8080");
            Console.WriteLine("   Voice: ONNX + LoRA ready");
            Console.WriteLine("\nPress Ctrl+C to shutdown...");

            await Task.Delay(-1);
        }
    }
}
