from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from statistics import fmean, pstdev
from typing import List, Optional


@dataclass
class GCodePoint:
    X: float = 0.0
    Y: float = 0.0
    Z: float = 0.0
    Velocity: float = 0.0


@dataclass
class LlmAttentionResult:
    GatedWeights: list[list[float]] = field(default_factory=list)
    PreservedEntropy: str = ""
    QFactorApplied: float = 0.0
    KneeSlopeApplied: float = 0.0
    ProcessingTimeMs: int = 0


@dataclass
class GCodeResult:
    ProcessedPoints: List[GCodePoint] = field(default_factory=list)
    SmoothingApplied: bool = False
    QFactorApplied: float = 0.0
    KneeSlopeApplied: float = 0.0


@dataclass
class PixelPhaseResult:
    ProcessedImage: list[list[float]] = field(default_factory=list)
    NoiseFloorPreserved: float = 0.0
    QFactorApplied: float = 0.0
    KneeSlopeApplied: float = 0.0


@dataclass
class SteelResonanceResult:
    FilteredFrequencies: List[float] = field(default_factory=list)
    ResonanceDetected: bool = False
    QFactorApplied: float = 0.0
    KneeSlopeApplied: float = 0.0


@dataclass
class VoiceSynthesisResult:
    AudioSamples: List[float] = field(default_factory=list)
    OutputPath: str = ""
    Fingerprint: Optional[dict] = None
    Error: Optional[str] = None


@dataclass
class PersonaResult:
    AudioSamples: List[float] = field(default_factory=list)
    OutputPath: str = ""
    Fingerprint: Optional[dict] = None
    Error: Optional[str] = None


class VanSpectrogram:
    def render(self, title: str, signal: list[float]) -> None:
        mean = fmean(signal) if signal else 0.0
        std = pstdev(signal) if len(signal) > 1 else 0.0
        dr = (max(signal) - min(signal)) if signal else 0.0
        print(f"\n=== Spectrogram: {title} ===")
        print(f"Signal Length: {len(signal)}")
        print(f"Mean: {mean:.4f}")
        print(f"StdDev: {std:.4f}")
        print(f"Dynamic Range: {dr:.4f}")
