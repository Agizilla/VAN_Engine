namespace VanEngine.Core.VAN.Audit;

public sealed class AuditLog : IDisposable
{
    private readonly string _logPath;
    private readonly object _lock = new();
    private readonly int _maxEntries;
    private readonly List<AuditEntry> _entries;
    private StreamWriter? _writer;

    public AuditLog(string logPath, int maxEntries = 10000)
    {
        _logPath = logPath;
        _maxEntries = maxEntries;
        _entries = new List<AuditEntry>(maxEntries);
        EnsureWriter();
    }

    public int Count => _entries.Count;

    public void Record(string category, string message, AuditSeverity severity = AuditSeverity.Info)
    {
        var entry = new AuditEntry
        {
            Timestamp = DateTime.UtcNow,
            Category = category,
            Message = message,
            Severity = severity
        };

        lock (_lock)
        {
            _entries.Add(entry);
            _writer?.WriteLine(entry.ToString());
            _writer?.Flush();

            if (_entries.Count > _maxEntries)
            {
                _entries.RemoveRange(0, _entries.Count - _maxEntries);
            }
        }
    }

    public void RecordEnvelope(string carrier, string modulation, string status)
    {
        Record("Envelope", $"Carrier={carrier} Mod={modulation} Status={status}", AuditSeverity.Debug);
    }

    public void RecordError(string context, string error)
    {
        Record("Error", $"[{context}] {error}", AuditSeverity.Error);
    }

    public void RecordWarning(string context, string warning)
    {
        Record("Warning", $"[{context}] {warning}", AuditSeverity.Warning);
    }

    public List<AuditEntry> Query(string? category = null, AuditSeverity? minSeverity = null, int maxResults = 50)
    {
        lock (_lock)
        {
            var query = _entries.AsEnumerable();

            if (!string.IsNullOrEmpty(category))
                query = query.Where(e => e.Category.Equals(category, StringComparison.OrdinalIgnoreCase));

            if (minSeverity.HasValue)
                query = query.Where(e => e.Severity >= minSeverity.Value);

            return query
                .OrderByDescending(e => e.Timestamp)
                .Take(maxResults)
                .ToList();
        }
    }

    public List<AuditEntry> GetRecent(int count = 20)
    {
        lock (_lock)
        {
            return _entries
                .OrderByDescending(e => e.Timestamp)
                .Take(count)
                .ToList();
        }
    }

    public void Clear()
    {
        lock (_lock)
        {
            _entries.Clear();
        }
    }

    public async Task FlushAsync()
    {
        lock (_lock)
        {
            _writer?.Flush();
        }
        await Task.CompletedTask;
    }

    private void EnsureWriter()
    {
        try
        {
            var dir = Path.GetDirectoryName(_logPath);
            if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
                Directory.CreateDirectory(dir);
            _writer = new StreamWriter(_logPath, append: true);
        }
        catch
        {
            _writer = null;
        }
    }

    public void Dispose()
    {
        lock (_lock)
        {
            _writer?.Dispose();
            _writer = null;
            _entries.Clear();
        }
    }
}

public sealed class AuditEntry
{
    public DateTime Timestamp { get; set; }
    public string Category { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public AuditSeverity Severity { get; set; } = AuditSeverity.Info;

    public override string ToString()
    {
        return $"[{Timestamp:O}] [{Severity}] [{Category}] {Message}";
    }
}

public enum AuditSeverity
{
    Debug = 0,
    Info = 1,
    Warning = 2,
    Error = 3,
    Critical = 4
}
