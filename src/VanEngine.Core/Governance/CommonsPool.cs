using System.Collections.Concurrent;

namespace VanEngine.Core.Governance;

public sealed class CommonsPool<T> where T : class
{
    private readonly ConcurrentBag<T> _pool = new();
    private int _borrowedCount;
    private readonly Func<T> _factory;
    private readonly Func<T, bool> _integrityCheck;
    private readonly int _maxSize;

    public CommonsPool(Func<T> factory, Func<T, bool>? integrityCheck = null, int maxSize = 100)
    {
        _factory = factory;
        _integrityCheck = integrityCheck ?? (_ => true);
        _maxSize = maxSize;
    }

    public T Borrow()
    {
        if (_pool.TryTake(out var item) && _integrityCheck(item))
        {
            Interlocked.Increment(ref _borrowedCount);
            return item;
        }

        var fresh = _factory();
        Interlocked.Increment(ref _borrowedCount);
        return fresh;
    }

    public void Return(T item)
    {
        if (_integrityCheck(item))
        {
            if (_pool.Count < _maxSize)
                _pool.Add(item);
            Interlocked.Decrement(ref _borrowedCount);
        }
        else
        {
            if (item is IDisposable d)
                d.Dispose();
            Interlocked.Decrement(ref _borrowedCount);
        }
    }

    public int Available => _pool.Count;
    public int Borrowed => _borrowedCount;
    public int Total => _pool.Count + _borrowedCount;
}
