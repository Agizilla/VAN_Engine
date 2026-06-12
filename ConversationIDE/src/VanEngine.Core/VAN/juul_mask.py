from __future__ import annotations

from enum import Flag, auto


class JuulMask(Flag):
    NONE = 0
    SPOKE0 = auto()
    SPOKE60 = auto()
    SPOKE120 = auto()
    SPOKE180 = auto()
    SPOKE240 = auto()
    SPOKE300 = auto()
    OUTER_RIM = auto()
