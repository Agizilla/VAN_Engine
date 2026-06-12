using System.Collections.Concurrent;

namespace VanEngine.Core.Governance;

public sealed class ForestGuardian
{
    private long _totalAllocated;
    private readonly ConcurrentDictionary<string, long> _moduleAllocations = new();
    private readonly long _maxForestSize;

    public ForestGuardian(long maxForestSize = 1024L * 1024 * 1024)
    {
        _maxForestSize = maxForestSize;
    }

    public long TotalAllocated => _totalAllocated;
    public long MaxForestSize => _maxForestSize;
    public long Available => _maxForestSize - _totalAllocated;

    public bool RequestTreeFelling(long bytesRequested, string moduleName)
    {
        if (bytesRequested < 0)
            return false;

        if (_totalAllocated + bytesRequested > _maxForestSize)
        {
            LogViolation($"Law 7: {moduleName} attempted to allocate {bytesRequested} bytes without community consent. Forest at capacity ({_totalAllocated}/{_maxForestSize}).");
            return false;
        }

        Interlocked.Add(ref _totalAllocated, bytesRequested);
        _moduleAllocations.AddOrUpdate(moduleName, bytesRequested, (_, existing) => existing + bytesRequested);
        return true;
    }

    public void Release(long bytesReleased, string moduleName)
    {
        if (bytesReleased < 0)
            return;

        Interlocked.Add(ref _totalAllocated, -bytesReleased);
        _moduleAllocations.AddOrUpdate(moduleName, 0, (_, existing) => Math.Max(0, existing - bytesReleased));
    }

    public long GetAllocation(string moduleName) =>
        _moduleAllocations.TryGetValue(moduleName, out var val) ? val : 0;

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[UNIVERSAL LAW VIOLATION] {violation}");
    }
}
