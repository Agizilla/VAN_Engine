using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace VAN_Engine.Core.Storage
{
    public interface ISubstrateStorage : IDisposable
    {
        Task<bool> StoreTokenAsync(string token, double w, double x, double y, double z, 
                                   string[] appliesTo, CancellationToken ct = default);
        Task<(bool found, double w, double x, double y, double z)> LookupTokenAsync(string token, CancellationToken ct = default);
        Task<string[]> GetAppliesToAsync(string token, CancellationToken ct = default);
        Task<bool> TokenExistsAsync(string token, CancellationToken ct = default);
        Task<int> GetTokenCountAsync(CancellationToken ct = default);
        Task<List<(string token, double w, double x, double y, double z, double similarity)>> 
            FindNearestAsync(double targetW, double targetX, double targetY, double targetZ, 
                            int limit = 10, CancellationToken ct = default);
        Task LogAuditAsync(string component, string action, 
                          double? beforeW, double? beforeX, double? beforeY, double? beforeZ,
                          double? afterW, double? afterX, double? afterY, double? afterZ,
                          string metadata = null, CancellationToken ct = default);
        Task<List<AuditEntry>> GetAuditTrailAsync(int limit = 100, CancellationToken ct = default);
        Task VacuumAsync(CancellationToken ct = default);
        Task<StorageStats> GetStatsAsync(CancellationToken ct = default);
    }

    public struct StorageStats
    {
        public long TotalTokens;
        public long StorageSizeBytes;
        public long AuditEntryCount;
        public DateTime LastVacuum;
        public string StorageType;
    }

    public struct AuditEntry
    {
        public long Id;
        public DateTime Timestamp;
        public string Component;
        public string Action;
        public double? BeforeW, BeforeX, BeforeY, BeforeZ;
        public double? AfterW, AfterX, AfterY, AfterZ;
        public string Metadata;
    }
}
