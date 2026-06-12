from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
from typing import Any

from .compliance import FryasComplianceEngine
from .envelope import VanEnvelope
from .fryas_directive import FryasDirective
from .metrics import Metrics
from .results import (
    GCodePoint,
    GCodeResult,
    LlmAttentionResult,
    PersonaResult,
    PixelPhaseResult,
    SteelResonanceResult,
    VanSpectrogram,
    VoiceSynthesisResult,
)


class VanCompiler:
    def __init__(self, processors=None, external_executor=None):
        self.processors = processors or {}
        self.external_executor = external_executor

    def TryExecute(self, envelope, state, out_result=None):
        fn = self.processors.get(envelope.Carrier)
        if not fn:
            return False
        if out_result is not None:
            out_result = fn(envelope)
        return True


class VanEngine:
    def __init__(self, external_executor=None):
        self._spectrogram = VanSpectrogram()
        self._compiler = VanCompiler()
        self._metrics = Metrics()
        self._compliance = FryasComplianceEngine(FryasDirective.ALL_DIRECTIVES)

    @property
    def Metrics(self):
        return self._metrics

    @property
    def Compliance(self):
        return self._compliance

    def VisualizeSpectrogram(self, envelope: VanEnvelope, signal):
        self._spectrogram.render(envelope.Header, signal)
