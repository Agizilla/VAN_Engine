import os
import tempfile
from pathlib import Path
from typing import Optional

import whisper
import numpy as np


class WhisperSTT:
    def __init__(self, model_name: str = "base", device: Optional[str] = None):
        self.model_name = model_name
        self.device = device or ("cuda" if whisper.torch.cuda.is_available() else "cpu")
        self._model = None

    def _load_model(self):
        if self._model is None:
            self._model = whisper.load_model(self.model_name, device=self.device)
        return self._model

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        model = self._load_model()
        audio = audio.astype(np.float32)
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))
        result = model.transcribe(audio, fp16=False, language="en")
        return result.get("text", "").strip()

    def transcribe_file(self, path: str) -> str:
        model = self._load_model()
        result = model.transcribe(str(path), fp16=False, language="en")
        return result.get("text", "").strip()

    @property
    def available(self) -> bool:
        try:
            self._load_model()
            return True
        except Exception:
            return False
