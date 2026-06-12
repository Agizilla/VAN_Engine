import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np


BASE_DIR = Path(__file__).resolve().parents[3]
TTS_LOCAL_SCRIPT = BASE_DIR / "tts_local.py"
MODELS_DIR = BASE_DIR / "models"
STYLETTS2_DIR = BASE_DIR / "StyleTTS2"


class PiperTSEngine:
    """Piper TTS — real local voice via ONNX models (from DirtyTalker project)."""

    def __init__(self, model_path: Optional[str] = None):
        self._available = None
        self._voice = None
        self._model_path = model_path or str(
            Path(r"C:\Users\User\Documents\!Deepseek\DirtyTalker\en_US-amy-medium.onnx")
        )

    @property
    def available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            from piper.voice import PiperVoice
            model = Path(self._model_path)
            self._available = model.exists()
            if self._available:
                self._voice = PiperVoice.load(str(model))
            return self._available
        except ImportError:
            self._available = False
            return False

    def speak(self, text: str) -> Optional[bytes]:
        if not self.available:
            return None
        try:
            import io
            import soundfile as sf
            audio_generator = self._voice.synthesize(text)
            wav_bytes = b"".join(audio_generator)
            return wav_bytes
        except Exception:
            return None

    def speak_to_file(self, text: str, output_path: str) -> bool:
        wav = self.speak(text)
        if wav is None:
            return False
        try:
            import io
            import soundfile as sf
            data, sr = sf.read(io.BytesIO(wav), dtype="float32")
            sf.write(output_path, data, sr)
            return True
        except Exception:
            return False

    def play(self, text: str) -> bool:
        wav = self.speak(text)
        if wav is None:
            return False
        try:
            import io
            import sounddevice as sd
            import soundfile as sf
            data, sr = sf.read(io.BytesIO(wav), dtype="float32")
            sd.play(data, sr)
            sd.wait()
            return True
        except Exception:
            return False


class StyleTTS2Engine:
    def __init__(self):
        self._available = None

    @property
    def available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import torch
            has_torch = True
        except ImportError:
            has_torch = False
        self._available = (
            has_torch
            and TTS_LOCAL_SCRIPT.exists()
            and (MODELS_DIR / "Amelia1_ft_StyleTTS2").exists()
        )
        return self._available

    def speak(self, text: str, output_path: Optional[str] = None) -> Optional[str]:
        if not self.available:
            return None

        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

        try:
            result = subprocess.run(
                ["python", str(TTS_LOCAL_SCRIPT), "--text", text, "--output", output_path],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                return None
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return output_path
            return None
        except Exception:
            return None

    def speak_sapi(self, text: str) -> bool:
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(text)
            return True
        except Exception:
            return False
