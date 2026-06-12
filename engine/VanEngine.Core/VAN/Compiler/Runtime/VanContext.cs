namespace VanEngine.Core.VAN.Compiler.Runtime;

public sealed class VanContext
{
    public Dictionary<string, object> State { get; set; } = new();
    public AstEnvelope? Envelope { get; set; }

    public T? Get<T>(string key)
    {
        if (State.TryGetValue(key, out var value) && value is T typed)
            return typed;
        return default;
    }

    public T? GetOrDefault<T>(string key, T? defaultValue = default)
    {
        return State.TryGetValue(key, out var value) && value is T typed ? typed : defaultValue;
    }

    public void Set<T>(string key, T value)
    {
        State[key] = value!;
    }

    public bool Contains(string key) => State.ContainsKey(key);
    public void Clear() => State.Clear();
    public int Count => State.Count;
}
