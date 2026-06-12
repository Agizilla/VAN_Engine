using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace VAN_Engine.Core.Storage
{
    public sealed class HybridStorage : ISubstrateStorage
    {
        private readonly LMDBCore _lmdb;
        private readonly SQLiteStorage _sqlite;

        public HybridStorage(string lmdbPath, string sqlitePath)
        {
            _lmdb = new LMDBCore(lmdbPath);
            _sqlite = new SQLiteStorage(sqlitePath);
        }

        public Task<bool> StoreTokenAsync(string token, double w, double x, double y, double z, string[] appliesTo, CancellationToken ct = default)
        {
            var lmdbTask = _lmdb.StoreTokenAsync(token, w, x, y, z, appliesTo, ct);
            var sqliteTask = _sqlite.StoreTokenAsync(token, w, x, y, z, appliesTo, ct);
            Task.WhenAll(lmdbTask, sqliteTask).Wait(ct);
            return Task.FromResult(lmdbTask.Result && sqliteTask.Result);
        }

        public Task<(bool found, double w, double x, double y, double z)> LookupTokenAsync(string token, CancellationToken ct = default)
            => _lmdb.LookupTokenAsync(token, ct);

        public Task<List<(string token, double w, double x, double y, double z, double similarity)>>
            FindNearestAsync(double targetW, double targetX, double targetY, double targetZ, int limit = 10, CancellationToken ct = default)
            => _lmdb.FindNearestAsync(targetW, targetX, targetY, targetZ, limit, ct);

        public Task<string[]> GetAppliesToAsync(string token, CancellationToken ct = default)
            => _sqlite.GetAppliesToAsync(token, ct);

        public Task LogAuditAsync(string component, string action,
            double? beforeW, double? beforeX, double? beforeY, double? beforeZ,
            double? afterW, double? afterX, double? afterY, double? afterZ,
            string metadata = null, CancellationToken ct = default)
            => _sqlite.LogAuditAsync(component, action, beforeW, beforeX, beforeY, beforeZ, afterW, afterX, afterY, afterZ, metadata, ct);

        public Task<List<AuditEntry>> GetAuditTrailAsync(int limit = 100, CancellationToken ct = default)
            => _sqlite.GetAuditTrailAsync(limit, ct);

        public async Task<StorageStats> GetStatsAsync(CancellationToken ct = default)
        {
            var s = await _sqlite.GetStatsAsync(ct);
            s.StorageType = "Hybrid (LMDB + SQLite)";
            return s;
        }

        public Task VacuumAsync(CancellationToken ct = default) => _sqlite.VacuumAsync(ct);
        public Task<bool> TokenExistsAsync(string token, CancellationToken ct = default) => _sqlite.TokenExistsAsync(token, ct);
        public Task<int> GetTokenCountAsync(CancellationToken ct = default) => _sqlite.GetTokenCountAsync(ct);

        public void Dispose() { _lmdb?.Dispose(); _sqlite?.Dispose(); }
    }
}
