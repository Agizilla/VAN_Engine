namespace VanEngine.Core.VAN;

[Flags]
public enum FryasDirective : ushort
{
    None                    = 0,
    PreambleFreedom         = 1 << 0,
    HierarchyOfAid          = 1 << 1,
    ThricefoldGratitude     = 1 << 2,
    ProactiveAssistance     = 1 << 3,
    NoBendedKnee            = 1 << 4,
    FairDivision            = 1 << 5,
    ExpelBastards           = 1 << 6,
    NoDebtSlavery           = 1 << 7,
    NonInterference         = 1 << 8,
    DefenceWhenAttacked     = 1 << 9,
    DaughtersChoice         = 1 << 10,
    ExileNotContamination   = 1 << 11,
    EternalLamp             = 1 << 12,

    AllDirectives = PreambleFreedom | HierarchyOfAid | ThricefoldGratitude |
                    ProactiveAssistance | NoBendedKnee | FairDivision |
                    ExpelBastards | NoDebtSlavery | NonInterference |
                    DefenceWhenAttacked | DaughtersChoice |
                    ExileNotContamination | EternalLamp
}
