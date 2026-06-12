using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using VAN_Engine.Core.Storage;

namespace VAN_Engine.Core.WebSocket
{
    public class QueryHandlers
    {
        private readonly ISubstrateStorage _storage;

        public QueryHandlers(ISubstrateStorage storage)
        {
            _storage = storage;
        }

        public async Task<string> HandleQuery(string rawMessage)
        {
            try
            {
                var query = JsonSerializer.Deserialize<WebSocketQuery>(rawMessage);
                if (query == null)
                    return JsonSerializer.Serialize(new { error = "Invalid query format" });

                switch (query.Type?.ToLower())
                {
                    case "lookup":
                        var (found, w, x, y, z) = await _storage.LookupTokenAsync(query.Token);
                        return JsonSerializer.Serialize(new { found, quaternion = found ? new { w, x, y, z } : null });

                    case "store":
                        var success = await _storage.StoreTokenAsync(query.Token, query.W, query.X, query.Y, query.Z, query.AppliesTo ?? Array.Empty<string>());
                        return JsonSerializer.Serialize(new { success });

                    case "nearest":
                        var nearest = await _storage.FindNearestAsync(query.W, query.X, query.Y, query.Z, query.Limit ?? 5);
                        return JsonSerializer.Serialize(new { results = nearest });

                    case "stats":
                        var stats = await _storage.GetStatsAsync();
                        return JsonSerializer.Serialize(new { stats });

                    case "audit":
                        var audit = await _storage.GetAuditTrailAsync(query.Limit ?? 50);
                        return JsonSerializer.Serialize(new { entries = audit });

                    default:
                        return JsonSerializer.Serialize(new { error = $"Unknown type: {query.Type}" });
                }
            }
            catch (Exception ex)
            {
                return JsonSerializer.Serialize(new { error = ex.Message });
            }
        }
    }
}
