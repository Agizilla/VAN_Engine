using Microsoft.Data.Sqlite;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace VAN_Engine.Core.Storage
{
    public sealed class SQLiteStorage : ISubstrateStorage
    {
        private readonly string _connectionString;
        private readonly SemaphoreSlim _lock = new SemaphoreSlim(1, 1);
        private bool _disposed = false;
        private const int SCHEMA_VERSION = 2;

        public SQLiteStorage(string databasePath)
        {
            var directory = Path.GetDirectoryName(databasePath);
            if (!string.IsNullOrEmpty(directory))
                Directory.CreateDirectory(directory);

            _connectionString = new SqliteConnectionStringBuilder
            {
                DataSource = databasePath,
                Mode = SqliteOpenMode.ReadWriteCreate,
                Cache = SqliteCacheMode.Private,
                Pooling = true
            }.ToString();

            InitializeDatabase();
        }

        private void InitializeDatabase()
        {
            using var conn = new SqliteConnection(_connectionString);
            conn.Open();

            using var versionCmd = conn.CreateCommand();
            versionCmd.CommandText = @"
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )";
            versionCmd.ExecuteNonQuery();

            using var checkCmd = conn.CreateCommand();
            checkCmd.CommandText = "SELECT MAX(version) FROM schema_version";
            var currentVersion = Convert.ToInt32(checkCmd.ExecuteScalar() ?? 0);

            if (currentVersion < SCHEMA_VERSION)
            {
                for (int v = currentVersion + 1; v <= SCHEMA_VERSION; v++)
                    MigrateToVersion(v, conn);
            }

            using var tokensCmd = conn.CreateCommand();
            tokensCmd.CommandText = @"
                CREATE TABLE IF NOT EXISTS tokens (
                    token TEXT PRIMARY KEY,
                    w REAL NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    z REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )";
            tokensCmd.ExecuteNonQuery();

            using var appliesCmd = conn.CreateCommand();
            appliesCmd.CommandText = @"
                CREATE TABLE IF NOT EXISTS applies_to (
                    token TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    PRIMARY KEY (token, domain),
                    FOREIGN KEY (token) REFERENCES tokens(token) ON DELETE CASCADE
                )";
            appliesCmd.ExecuteNonQuery();

            using var vectorIdx = conn.CreateCommand();
            vectorIdx.CommandText = "CREATE INDEX IF NOT EXISTS idx_tokens_vector ON tokens(w, x, y, z)";
            vectorIdx.ExecuteNonQuery();

            using var auditCmd = conn.CreateCommand();
            auditCmd.CommandText = @"
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    component TEXT NOT NULL,
                    action TEXT NOT NULL,
                    before_w REAL, before_x REAL, before_y REAL, before_z REAL,
                    after_w REAL, after_x REAL, after_y REAL, after_z REAL,
                    metadata TEXT
                )";
            auditCmd.ExecuteNonQuery();
        }

        private void MigrateToVersion(int targetVersion, SqliteConnection conn)
        {
            using var transaction = conn.BeginTransaction();
            if (targetVersion == 2)
            {
                using var alterCmd = conn.CreateCommand();
                alterCmd.CommandText = "ALTER TABLE tokens ADD COLUMN magnitude REAL";
                try { alterCmd.ExecuteNonQuery(); } catch { }
            }
            using var versionInsert = conn.CreateCommand();
            versionInsert.CommandText = "INSERT INTO schema_version (version) VALUES (@version)";
            versionInsert.Parameters.AddWithValue("@version", targetVersion);
            versionInsert.ExecuteNonQuery();
            transaction.Commit();
        }

        public async Task<bool> StoreTokenAsync(string token, double w, double x, double y, double z,
                                                string[] appliesTo, CancellationToken ct = default)
        {
            await _lock.WaitAsync(ct);
            try
            {
                using var conn = new SqliteConnection(_connectionString);
                await conn.OpenAsync(ct);
                using var cmd = conn.CreateCommand();
                cmd.CommandText = @"
                    INSERT INTO tokens (token, w, x, y, z, updated_at)
                    VALUES (@token, @w, @x, @y, @z, CURRENT_TIMESTAMP)
                    ON CONFLICT(token) DO UPDATE SET
                        w = excluded.w, x = excluded.x, y = excluded.y, z = excluded.z,
                        updated_at = CURRENT_TIMESTAMP";
                cmd.Parameters.AddWithValue("@token", token);
                cmd.Parameters.AddWithValue("@w", w); cmd.Parameters.AddWithValue("@x", x);
                cmd.Parameters.AddWithValue("@y", y); cmd.Parameters.AddWithValue("@z", z);
                await cmd.ExecuteNonQueryAsync(ct);

                using var deleteCmd = conn.CreateCommand();
                deleteCmd.CommandText = "DELETE FROM applies_to WHERE token = @token";
                deleteCmd.Parameters.AddWithValue("@token", token);
                await deleteCmd.ExecuteNonQueryAsync(ct);

                foreach (var domain in appliesTo)
                {
                    using var insertCmd = conn.CreateCommand();
                    insertCmd.CommandText = "INSERT INTO applies_to (token, domain) VALUES (@token, @domain)";
                    insertCmd.Parameters.AddWithValue("@token", token);
                    insertCmd.Parameters.AddWithValue("@domain", domain);
                    await insertCmd.ExecuteNonQueryAsync(ct);
                }
                return true;
            }
            finally { _lock.Release(); }
        }

        public async Task<(bool found, double w, double x, double y, double z)> LookupTokenAsync(string token, CancellationToken ct = default)
        {
            using var conn = new SqliteConnection(_connectionString);
            await conn.OpenAsync(ct);
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT w, x, y, z FROM tokens WHERE token = @token";
            cmd.Parameters.AddWithValue("@token", token);
            using var reader = await cmd.ExecuteReaderAsync(ct);
            if (await reader.ReadAsync(ct))
                return (true, reader.GetDouble(0), reader.GetDouble(1), reader.GetDouble(2), reader.GetDouble(3));
            return (false, 0, 0, 0, 0);
        }

        public async Task<List<(string token, double w, double x, double y, double z, double similarity)>> 
            FindNearestAsync(double targetW, double targetX, double targetY, double targetZ, int limit = 10, CancellationToken ct = default)
        {
            using var conn = new SqliteConnection(_connectionString);
            await conn.OpenAsync(ct);
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"
                SELECT token, w, x, y, z,
                       (w * @tw + x * @tx + y * @ty + z * @tz) / 
                       (MAX(sqrt(w*w + x*x + y*y + z*z), 1e-10) * MAX(sqrt(@tw*@tw + @tx*@tx + @ty*@ty + @tz*@tz), 1e-10)) as similarity
                FROM tokens
                ORDER BY similarity DESC LIMIT @limit";
            cmd.Parameters.AddWithValue("@tw", targetW); cmd.Parameters.AddWithValue("@tx", targetX);
            cmd.Parameters.AddWithValue("@ty", targetY); cmd.Parameters.AddWithValue("@tz", targetZ);
            cmd.Parameters.AddWithValue("@limit", limit);
            var results = new List<(string, double, double, double, double, double)>();
            using var reader = await cmd.ExecuteReaderAsync(ct);
            while (await reader.ReadAsync(ct))
                results.Add((reader.GetString(0), reader.GetDouble(1), reader.GetDouble(2), reader.GetDouble(3), reader.GetDouble(4), reader.GetDouble(5)));
            return results;
        }

        public async Task LogAuditAsync(string component, string action,
            double? beforeW, double? beforeX, double? beforeY, double? beforeZ,
            double? afterW, double? afterX, double? afterY, double? afterZ,
            string metadata = null, CancellationToken ct = default)
        {
            using var conn = new SqliteConnection(_connectionString);
            await conn.OpenAsync(ct);
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"INSERT INTO audit (component, action, before_w, before_x, before_y, before_z,
                after_w, after_x, after_y, after_z, metadata) VALUES (@comp, @action, @bw, @bx, @by, @bz, @aw, @ax, @ay, @az, @meta)";
            cmd.Parameters.AddWithValue("@comp", component);
            cmd.Parameters.AddWithValue("@action", action);
            cmd.Parameters.AddWithValue("@bw", (object?)beforeW ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@bx", (object?)beforeX ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@by", (object?)beforeY ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@bz", (object?)beforeZ ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@aw", (object?)afterW ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@ax", (object?)afterX ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@ay", (object?)afterY ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@az", (object?)afterZ ?? DBNull.Value);
            cmd.Parameters.AddWithValue("@meta", metadata ?? "");
            await cmd.ExecuteNonQueryAsync(ct);
        }

        public async Task<List<AuditEntry>> GetAuditTrailAsync(int limit = 100, CancellationToken ct = default)
        {
            using var conn = new SqliteConnection(_connectionString);
            await conn.OpenAsync(ct);
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT id, timestamp, component, action, before_w, before_x, before_y, before_z, after_w, after_x, after_y, after_z, metadata FROM audit ORDER BY timestamp DESC LIMIT @limit";
            cmd.Parameters.AddWithValue("@limit", limit);
            var entries = new List<AuditEntry>();
            using var reader = await cmd.ExecuteReaderAsync(ct);
            while (await reader.ReadAsync(ct))
                entries.Add(new AuditEntry {
                    Id = reader.GetInt64(0), Timestamp = reader.GetDateTime(1),
                    Component = reader.GetString(2), Action = reader.GetString(3),
                    BeforeW = reader.IsDBNull(4) ? null : reader.GetDouble(4),
                    BeforeX = reader.IsDBNull(5) ? null : reader.GetDouble(5),
                    BeforeY = reader.IsDBNull(6) ? null : reader.GetDouble(6),
                    BeforeZ = reader.IsDBNull(7) ? null : reader.GetDouble(7),
                    AfterW = reader.IsDBNull(8) ? null : reader.GetDouble(8),
                    AfterX = reader.IsDBNull(9) ? null : reader.GetDouble(9),
                    AfterY = reader.IsDBNull(10) ? null : reader.GetDouble(10),
                    AfterZ = reader.IsDBNull(11) ? null : reader.GetDouble(11),
                    Metadata = reader.IsDBNull(12) ? null : reader.GetString(12)
                });
            return entries;
        }

        public async Task<StorageStats> GetStatsAsync(CancellationToken ct = default)
        {
            using var conn = new SqliteConnection(_connectionString);
            await conn.OpenAsync(ct);
            using var countCmd = conn.CreateCommand();
            countCmd.CommandText = "SELECT COUNT(*) FROM tokens";
            var tokenCount = Convert.ToInt64(await countCmd.ExecuteScalarAsync(ct));
            using var auditCmd = conn.CreateCommand();
            auditCmd.CommandText = "SELECT COUNT(*) FROM audit";
            var auditCount = Convert.ToInt64(await auditCmd.ExecuteScalarAsync(ct));
            var fileInfo = new FileInfo(conn.DataSource);
            return new StorageStats { TotalTokens = tokenCount, StorageSizeBytes = fileInfo.Length, AuditEntryCount = auditCount, LastVacuum = DateTime.UtcNow, StorageType = "SQLite" };
        }

        public Task VacuumAsync(CancellationToken ct = default) { using var conn = new SqliteConnection(_connectionString); conn.Open(); using var cmd = conn.CreateCommand(); cmd.CommandText = "VACUUM"; cmd.ExecuteNonQuery(); return Task.CompletedTask; }

        public async Task<string[]> GetAppliesToAsync(string token, CancellationToken ct = default)
        {
            using var conn = new SqliteConnection(_connectionString);
            await conn.OpenAsync(ct);
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT domain FROM applies_to WHERE token = @token";
            cmd.Parameters.AddWithValue("@token", token);
            var domains = new List<string>();
            using var reader = await cmd.ExecuteReaderAsync(ct);
            while (await reader.ReadAsync(ct)) domains.Add(reader.GetString(0));
            return domains.ToArray();
        }

        public async Task<bool> TokenExistsAsync(string token, CancellationToken ct = default)
        {
            using var conn = new SqliteConnection(_connectionString);
            await conn.OpenAsync(ct);
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT 1 FROM tokens WHERE token = @token LIMIT 1";
            cmd.Parameters.AddWithValue("@token", token);
            return await cmd.ExecuteScalarAsync(ct) != null;
        }

        public async Task<int> GetTokenCountAsync(CancellationToken ct = default)
        {
            using var conn = new SqliteConnection(_connectionString);
            await conn.OpenAsync(ct);
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT COUNT(*) FROM tokens";
            return Convert.ToInt32(await cmd.ExecuteScalarAsync(ct));
        }

        public void Dispose() { if (_disposed) return; _lock.Dispose(); _disposed = true; }
    }
}
