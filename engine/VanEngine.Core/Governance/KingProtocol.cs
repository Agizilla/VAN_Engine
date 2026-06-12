using VanEngine.Core.Defence;

namespace VanEngine.Core.Governance;

public sealed class KingProtocol
{
    private readonly DefenceRegistry _defenceRegistry;

    public KingProtocol(DefenceRegistry defenceRegistry)
    {
        _defenceRegistry = defenceRegistry;
    }

    public T ConsultWisdom<T>(Func<T> wisdomFunction)
    {
        return wisdomFunction();
    }

    public void DelegateDefence(IAssailant assailant)
    {
        _defenceRegistry.SignalAttack(assailant);
    }

    public bool MayDirectlyDefend() => false;
}
