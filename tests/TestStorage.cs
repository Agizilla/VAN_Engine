using System;
using System.IO;
using System.Threading.Tasks;
using VAN_Engine.Core.Storage;

namespace VAN_Engine.Tests
{
    class TestStorage
    {
        static async Task Main()
        {
            Console.WriteLine("=== VAN_Engine Storage Tests ===\n");

            Console.WriteLine("Test 1: SQLite Storage");
            var sqlitePath = Path.Combine(Path.GetTempPath(), "van_test.db");
            using (var sqlite = new SQLiteStorage(sqlitePath))
            {
                await sqlite.StoreTokenAsync("test_token", 0.8, 0.3, 0.2, 0.1, new[] { "test", "example" });
                var (found, w, x, y, z) = await sqlite.LookupTokenAsync("test_token");
                Console.WriteLine($"  Token found: {found}, quaternion: ({w:F2}, {x:F2}, {y:F2}, {z:F2})");

                var nearest = await sqlite.FindNearestAsync(0.8, 0.3, 0.2, 0.1, 5);
                Console.WriteLine($"  Nearest matches: {nearest.Count}");

                await sqlite.LogAuditAsync("Test", "StorageTest", null, null, null, null, w, x, y, z);
                var audit = await sqlite.GetAuditTrailAsync(10);
                Console.WriteLine($"  Audit entries: {audit.Count}");

                var stats = await sqlite.GetStatsAsync();
                Console.WriteLine($"  Stats: {stats.TotalTokens} tokens, {stats.StorageSizeBytes} bytes");
            }

            Console.WriteLine("\nTest 2: LMDB Storage (mmap)");
            var lmdbPath = Path.Combine(Path.GetTempPath(), "van_test.lmdb");
            try
            {
                using (var lmdb = new LMDBCore(lmdbPath))
                {
                    await lmdb.StoreTokenAsync("test_lmdb", 0.9, 0.2, 0.1, 0.05, null);
                    var (found, w, x, y, z) = await lmdb.LookupTokenAsync("test_lmdb");
                    Console.WriteLine($"  Token found: {found}, quaternion: ({w:F2}, {x:F2}, {y:F2}, {z:F2})");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"  LMDB: {ex.Message}");
            }

            Console.WriteLine("\nTest 3: Hybrid Storage");
            try
            {
                using (var hybrid = new HybridStorage(lmdbPath, sqlitePath))
                {
                    await hybrid.StoreTokenAsync("hybrid_token", 0.7, 0.4, 0.3, 0.2, new[] { "hybrid" });
                    var (found, w, x, y, z) = await hybrid.LookupTokenAsync("hybrid_token");
                    Console.WriteLine($"  Token found: {found}, quaternion: ({w:F2}, {x:F2}, {y:F2}, {z:F2})");
                    var appliesTo = await hybrid.GetAppliesToAsync("hybrid_token");
                    Console.WriteLine($"  Applies to: {string.Join(", ", appliesTo)}");
                    await hybrid.LogAuditAsync("Test", "HybridTest", null, null, w, x, y, z, "hybrid metadata");
                    var audit = await hybrid.GetAuditTrailAsync(10);
                    Console.WriteLine($"  Audit entries: {audit.Count}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"  Hybrid: {ex.Message}");
            }

            Console.WriteLine("\n=== All tests complete ===");
        }
    }
}
