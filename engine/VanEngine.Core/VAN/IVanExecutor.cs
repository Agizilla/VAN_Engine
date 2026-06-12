namespace VanEngine.Core.VAN;

public interface IVanExecutor
{
    bool TryExecute(VanEnvelope envelope, Dictionary<string, object> state, out object? result);
}
