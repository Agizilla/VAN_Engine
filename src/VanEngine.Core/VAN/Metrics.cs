using System.Diagnostics;
using System.Threading;

namespace VanEngine.Core.VAN;

public sealed class Metrics
{
    private long _envelopesProcessed;
    private long _errorsEncountered;
    private long _totalProcessingTicks;
    private int _activeProcessors;

    public long EnvelopesProcessed => Interlocked.Read(ref _envelopesProcessed);
    public long ErrorsEncountered => Interlocked.Read(ref _errorsEncountered);
    public long TotalProcessingTicks => Interlocked.Read(ref _totalProcessingTicks);
    public int ActiveProcessors => Thread.VolatileRead(ref _activeProcessors);

    public double AverageProcessingMs
    {
        get
        {
            long count = EnvelopesProcessed;
            return count > 0 ? (double)TotalProcessingTicks / count / TimeSpan.TicksPerMillisecond : 0;
        }
    }

    public IDisposable BeginProcessing()
    {
        Interlocked.Increment(ref _activeProcessors);
        return new MetricsScope(this, Stopwatch.StartNew());
    }

    public void RecordEnvelope()
    {
        Interlocked.Increment(ref _envelopesProcessed);
    }

    public void RecordError()
    {
        Interlocked.Increment(ref _errorsEncountered);
    }

    public void RecordTicks(long ticks)
    {
        Interlocked.Add(ref _totalProcessingTicks, ticks);
    }

    public Dictionary<string, object> Snapshot()
    {
        return new()
        {
            ["envelopes_processed"] = EnvelopesProcessed,
            ["errors_encountered"] = ErrorsEncountered,
            ["average_processing_ms"] = AverageProcessingMs,
            ["active_processors"] = ActiveProcessors,
            ["total_processing_ticks"] = TotalProcessingTicks
        };
    }

    public void Reset()
    {
        Interlocked.Exchange(ref _envelopesProcessed, 0);
        Interlocked.Exchange(ref _errorsEncountered, 0);
        Interlocked.Exchange(ref _totalProcessingTicks, 0);
        Interlocked.Exchange(ref _activeProcessors, 0);
    }

    private sealed class MetricsScope : IDisposable
    {
        private readonly Metrics _metrics;
        private readonly Stopwatch _sw;

        public MetricsScope(Metrics metrics, Stopwatch sw)
        {
            _metrics = metrics;
            _sw = sw;
        }

        public void Dispose()
        {
            _sw.Stop();
            _metrics.RecordTicks(_sw.ElapsedTicks);
            Interlocked.Decrement(ref _metrics._activeProcessors);
        }
    }
}
