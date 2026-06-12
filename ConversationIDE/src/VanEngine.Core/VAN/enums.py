from __future__ import annotations

from enum import Enum


class VanBlockType(str, Enum):
    Transition = "Transition"
    State = "State"


class ProcessingMode(str, Enum):
    Frya = "Frya"
