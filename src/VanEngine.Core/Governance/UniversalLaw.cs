using System.Collections.Concurrent;

namespace VanEngine.Core.Governance;

public sealed class UniversalLaw
{
    private readonly ConcurrentQueue<WorkItem> _fairQueue = new();
    private readonly HashSet<string> _transitiveDependencyCache = new();

    public void Enqueue(WorkItem item)
    {
        _fairQueue.Enqueue(item);
    }

    public bool TryDequeue(out WorkItem? item) => _fairQueue.TryDequeue(out item);

    public int QueueLength => _fairQueue.Count;

    public bool ValidateFreeChoice(string module, string dependency)
    {
        if (HasForcedTransitiveDependency(dependency))
        {
            LogViolation($"Law 2: {dependency} forces additional dependencies. Violates free choice.");
            return false;
        }
        return true;
    }

    private bool HasForcedTransitiveDependency(string dependency)
    {
        return _transitiveDependencyCache.Contains(dependency);
    }

    public void RegisterForcedDependency(string dependency)
    {
        _transitiveDependencyCache.Add(dependency);
    }

    private static void LogViolation(string violation)
    {
        Console.WriteLine($"[UNIVERSAL LAW VIOLATION] {violation}");
    }
}

public record WorkItem(string Carrier, Func<object?> Execute, DateTime EnqueuedAt)
{
    public WorkItem(string carrier, Func<object?> execute)
        : this(carrier, execute, DateTime.UtcNow) { }
}
