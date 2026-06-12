from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from .enums import ProcessingMode, VanBlockType


@dataclass
class VanEnvelope:
    BlockType: VanBlockType = VanBlockType.Transition
    Mode: ProcessingMode = ProcessingMode.Frya
    Header: str = ""
    Carrier: str = ""
    Modulation: str = ""
    QFactor: float = 0.95
    Dither: str = ""
    Data: List[Any] = field(default_factory=list)
    DataTypes: List[str] = field(default_factory=list)
    DitherProfile2D: Optional[list[list[float]]] = None
