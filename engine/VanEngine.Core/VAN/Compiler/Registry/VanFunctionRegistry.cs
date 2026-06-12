using VanEngine.Core.VAN.Compiler.Runtime;

namespace VanEngine.Core.VAN.Compiler.Registry;

public sealed class VanFunctionRegistry : IVanExecutor
{
    private readonly Dictionary<string, Dictionary<string, Func<VanContext, AstEnvelope, Task<object>>>> _map;

    public VanFunctionRegistry()
    {
        _map = new Dictionary<string, Dictionary<string, Func<VanContext, AstEnvelope, Task<object>>>>();
        RegisterCoreFunctions();
    }

    public void Register(string carrier, string modulation,
                         Func<VanContext, AstEnvelope, Task<object>> executor)
    {
        if (!_map.ContainsKey(carrier))
            _map[carrier] = new Dictionary<string, Func<VanContext, AstEnvelope, Task<object>>>();

        _map[carrier][modulation] = executor;
    }

    public bool TryGetExecutor(AstEnvelope envelope, out Func<VanContext, AstEnvelope, Task<object>>? executor)
    {
        executor = null;
        if (_map.TryGetValue(envelope.Carrier, out var modMap))
            return modMap.TryGetValue(envelope.Modulation, out executor);
        return false;
    }

    public bool TryExecute(VanEnvelope envelope, Dictionary<string, object> state, out object? result)
    {
        result = null;
        var astEnv = new AstEnvelope
        {
            Carrier = envelope.Carrier,
            Modulation = envelope.Modulation,
            QFactor = envelope.QFactor,
            Dither = envelope.Dither,
            Data = envelope.Data,
            DataTypes = envelope.DataTypes
        };

        if (TryGetExecutor(astEnv, out var executor) && executor != null)
        {
            var ctx = new VanContext { State = state, Envelope = astEnv };
            try
            {
                result = executor(ctx, astEnv).GetAwaiter().GetResult();
                return true;
            }
            catch
            {
                return false;
            }
        }

        return false;
    }

    private void RegisterCoreFunctions()
    {
        Register("VanEngine", "Soft-Knee-Expander", async (ctx, env) =>
        {
            return new { result = "Expanded" };
        });

        Register("SCADA", "ModbusWrite", async (ctx, env) =>
        {
            return new { written = true };
        });

        Register("Audio", "GeckoShift", async (ctx, env) =>
        {
            return new { shifted = true };
        });
    }
}
