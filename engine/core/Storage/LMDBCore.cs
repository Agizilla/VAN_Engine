using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace VAN_Engine.Core.Storage
{
    public sealed class LMDBCore : ISubstrateStorage
    {
        private IntPtr _env;
        private IntPtr _dbi;
        private readonly string _path;
        private readonly object _lock = new object();
        private bool _disposed = false;
        private const int MAX_DATABASE_SIZE = 1024 * 1024 * 1024;

        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern int mdb_env_create(out IntPtr env);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern int mdb_env_open(IntPtr env, string path, uint flags, int mode);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern int mdb_env_set_mapsize(IntPtr env, long size);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern void mdb_env_close(IntPtr env);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern int mdb_txn_begin(IntPtr env, IntPtr parent, uint flags, out IntPtr txn);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern int mdb_txn_commit(IntPtr txn);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern void mdb_txn_abort(IntPtr txn);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern int mdb_dbi_open(IntPtr txn, string name, uint flags, out IntPtr dbi);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern int mdb_put(IntPtr txn, IntPtr dbi, ref MDB_val key, ref MDB_val data, uint flags);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern int mdb_get(IntPtr txn, IntPtr dbi, ref MDB_val key, ref MDB_val data);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern int mdb_cursor_open(IntPtr txn, IntPtr dbi, out IntPtr cursor);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern int mdb_cursor_get(IntPtr cursor, ref MDB_val key, ref MDB_val data, uint op);
        [DllImport("lmdb", CallingConvention = CallingConvention.Cdecl)]
        private static extern void mdb_cursor_close(IntPtr cursor);

        [StructLayout(LayoutKind.Sequential)]
        private struct MDB_val { public IntPtr mv_size; public IntPtr mv_data; }

        private const uint MDB_CREATE = 0x00040000;
        private const uint MDB_RDONLY = 0x00020000;
        private const uint MDB_NOSYNC = 0x00010000;
        private uint _cursorOp = 0;

        public LMDBCore(string databasePath)
        {
            _path = databasePath;
            var dir = System.IO.Path.GetDirectoryName(databasePath);
            if (!string.IsNullOrEmpty(dir)) System.IO.Directory.CreateDirectory(dir);

            int rc = mdb_env_create(out _env);
            if (rc != 0) throw new InvalidOperationException($"mdb_env_create failed: {rc}");
            rc = mdb_env_set_mapsize(_env, MAX_DATABASE_SIZE);
            if (rc != 0) throw new InvalidOperationException($"mdb_env_set_mapsize failed: {rc}");
            rc = mdb_env_open(_env, databasePath, MDB_NOSYNC, 0644);
            if (rc != 0) throw new InvalidOperationException($"mdb_env_open failed at {databasePath}: {rc}");

            var txn = BeginTransaction(false);
            rc = mdb_dbi_open(txn, "tokens", MDB_CREATE, out _dbi);
            if (rc != 0) throw new InvalidOperationException($"mdb_dbi_open failed: {rc}");
            CommitTransaction(txn);
        }

        private IntPtr BeginTransaction(bool readOnly)
        {
            uint flags = readOnly ? MDB_RDONLY : 0;
            int rc = mdb_txn_begin(_env, IntPtr.Zero, flags, out IntPtr txn);
            if (rc != 0) throw new InvalidOperationException($"mdb_txn_begin failed: {rc}");
            return txn;
        }

        private void CommitTransaction(IntPtr txn) { int rc = mdb_txn_commit(txn); if (rc != 0) { mdb_txn_abort(txn); throw new InvalidOperationException($"mdb_txn_commit failed: {rc}"); } }

        private static MDB_val CreateMDBVal(string value) {
            var bytes = Encoding.UTF8.GetBytes(value);
            return new MDB_val { mv_size = (IntPtr)bytes.Length, mv_data = Marshal.AllocHGlobal(bytes.Length) };
        }
        private static MDB_val CreateMDBVal(double[] values) {
            var bytes = new byte[values.Length * 8];
            Buffer.BlockCopy(values, 0, bytes, 0, bytes.Length);
            return new MDB_val { mv_size = (IntPtr)bytes.Length, mv_data = Marshal.AllocHGlobal(bytes.Length) };
        }
        private static void FreeMDBVal(ref MDB_val val) { if (val.mv_data != IntPtr.Zero) Marshal.FreeHGlobal(val.mv_data); val = default; }

        public Task<bool> StoreTokenAsync(string token, double w, double x, double y, double z, string[] appliesTo, CancellationToken ct = default)
        {
            return Task.Run(() => {
                lock (_lock) {
                    var txn = BeginTransaction(false);
                    try {
                        var key = CreateMDBVal(token);
                        var value = CreateMDBVal(new double[] { w, x, y, z });
                        int rc = mdb_put(txn, _dbi, ref key, ref value, 0);
                        FreeMDBVal(ref key); FreeMDBVal(ref value);
                        if (rc != 0) return false;
                        CommitTransaction(txn);
                        return true;
                    } catch { mdb_txn_abort(txn); throw; }
                }
            }, ct);
        }

        public Task<(bool found, double w, double x, double y, double z)> LookupTokenAsync(string token, CancellationToken ct = default)
        {
            return Task.Run(() => {
                lock (_lock) {
                    var txn = BeginTransaction(true);
                    try {
                        var key = CreateMDBVal(token);
                        var value = new MDB_val();
                        int rc = mdb_get(txn, _dbi, ref key, ref value);
                        FreeMDBVal(ref key);
                        if (rc != 0) { mdb_txn_abort(txn); return (false, 0d, 0d, 0d, 0d); }
                        var bytes = new byte[(long)value.mv_size];
                        Marshal.Copy(value.mv_data, bytes, 0, bytes.Length);
                        var doubles = new double[4];
                        Buffer.BlockCopy(bytes, 0, doubles, 0, bytes.Length);
                        CommitTransaction(txn);
                        return (true, doubles[0], doubles[1], doubles[2], doubles[3]);
                    } catch { mdb_txn_abort(txn); throw; }
                }
            }, ct);
        }

        public Task<List<(string token, double w, double x, double y, double z, double similarity)>>
            FindNearestAsync(double targetW, double targetX, double targetY, double targetZ, int limit = 10, CancellationToken ct = default)
        {
            return Task.Run(() => {
                var results = new List<(string, double, double, double, double, double)>();
                lock (_lock) {
                    var txn = BeginTransaction(true);
                    try {
                        int rc = mdb_cursor_open(txn, _dbi, out IntPtr cursor);
                        if (rc != 0) return results;
                        var key = new MDB_val(); var value = new MDB_val();
                        double targetMag = Math.Sqrt(targetW*targetW + targetX*targetX + targetY*targetY + targetZ*targetZ);
                        while (mdb_cursor_get(cursor, ref key, ref value, _cursorOp) == 0) {
                            _cursorOp = 0; // MDB_FIRST only on first call, then MDB_NEXT is implicit through 0
                            var tBytes = new byte[(long)key.mv_size];
                            Marshal.Copy(key.mv_data, tBytes, 0, tBytes.Length);
                            var tok = Encoding.UTF8.GetString(tBytes);
                            var vBytes = new byte[(long)value.mv_size];
                            Marshal.Copy(value.mv_data, vBytes, 0, vBytes.Length);
                            var d = new double[4]; Buffer.BlockCopy(vBytes, 0, d, 0, vBytes.Length);
                            double mag = Math.Sqrt(d[0]*d[0] + d[1]*d[1] + d[2]*d[2] + d[3]*d[3]);
                            double sim = (d[0]*targetW + d[1]*targetX + d[2]*targetY + d[3]*targetZ) / (Math.Max(mag, 1e-10) * Math.Max(targetMag, 1e-10));
                            results.Add((tok, d[0], d[1], d[2], d[3], sim));
                        }
                        mdb_cursor_close(cursor);
                        CommitTransaction(txn);
                    } catch { mdb_txn_abort(txn); throw; }
                }
                return results.OrderByDescending(x => x.similarity).Take(limit).ToList();
            }, ct);
        }

        public Task<string[]> GetAppliesToAsync(string token, CancellationToken ct = default) => throw new NotImplementedException("LMDB: use SQLite for applies_to");
        public Task LogAuditAsync(string component, string action, double? beforeW, double? beforeX, double? beforeY, double? beforeZ, double? afterW, double? afterX, double? afterY, double? afterZ, string metadata = null, CancellationToken ct = default) => throw new NotImplementedException("LMDB: use SQLite for audit");
        public Task<List<AuditEntry>> GetAuditTrailAsync(int limit = 100, CancellationToken ct = default) => throw new NotImplementedException("LMDB: use SQLite for audit");
        public Task<StorageStats> GetStatsAsync(CancellationToken ct = default) => throw new NotImplementedException();
        public Task VacuumAsync(CancellationToken ct = default) => Task.CompletedTask;
        public Task<bool> TokenExistsAsync(string token, CancellationToken ct = default) => throw new NotImplementedException();
        public Task<int> GetTokenCountAsync(CancellationToken ct = default) => throw new NotImplementedException();
        public void Dispose() { if (_disposed) return; if (_dbi != IntPtr.Zero) mdb_env_close(_env); _disposed = true; }
    }
}
