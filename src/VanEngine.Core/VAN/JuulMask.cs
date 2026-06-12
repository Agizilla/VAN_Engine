namespace VanEngine.Core.VAN;

[Flags]
public enum JuulMask : byte
{
    None     = 0b000000,
    Spoke0   = 1 << 0,
    Spoke60  = 1 << 1,
    Spoke120 = 1 << 2,
    Spoke180 = 1 << 3,
    Spoke240 = 1 << 4,
    Spoke300 = 1 << 5,
    OuterRim = 1 << 6
}
