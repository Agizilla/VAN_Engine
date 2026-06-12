import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from voice.tts import PiperTSEngine
except ImportError:
    from ..voice.tts import PiperTSEngine

from .base import BaseSkill, register_skill, SkillContext

SETTINGS_PATH = Path(__file__).resolve().parents[2] / "config" / "Settings.json"
_RECORDINGS_DIR = Path(r"C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ClawDia\recordings")
_PIPER_DATASET_DIR = Path(r"C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ClawDia\piper_dataset")
_PIPER_MODELS_DIR = Path(__file__).resolve().parent.parent / "voice" / "models"


def _load_settings() -> dict:
    if SETTINGS_PATH.exists():
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    return {}


def _save_settings(s: dict):
    SETTINGS_PATH.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


def _download_piper_model(url: str, dest: Path) -> bool:
    try:
        import requests
        print(f"Downloading Piper model from {url}...")
        resp = requests.get(url, stream=True, timeout=300)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(str(dest), "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = int(100 * downloaded / total)
                    print(f"\rDownload progress: {pct}%", end="")
        print()
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def _apply_noise_reduction(audio: list, sample_rate: int, cutoff: int = 4000) -> list:
    try:
        from scipy.signal import butter, sosfilt
        nyquist = 0.5 * sample_rate
        normal_cutoff = cutoff / nyquist
        sos = butter(4, normal_cutoff, btype="low", output="sos")
        import numpy as np
        return sosfilt(sos, np.array(audio)).tolist()
    except ImportError:
        return audio


def _resample(audio: list, orig_rate: int, target_rate: int = 22050) -> list:
    try:
        from scipy.signal import resample
        import numpy as np
        num_samples = int(len(audio) * target_rate / orig_rate)
        return resample(np.array(audio), num_samples).tolist()
    except ImportError:
        return audio


@register_skill("voice_trainer", "audio")
class VoiceTrainerSkill(BaseSkill):
    name = "voice_trainer"
    description = "Record audio, speak via Piper TTS, and prepare training datasets"
    author = "DeepSeek / ClawDia"
    version = "1.2.0"
    category = "audio"
    tags = ["voice", "piper", "tts", "recording", "training"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["speak", "record", "train", "status", "speak_file"],
                "default": "status",
            },
            "text": {"type": "string", "default": ""},
            "duration": {"type": "number", "default": 5.0},
            "sample_rate": {"type": "integer", "default": 22050},
            "backend": {"type": "string", "enum": ["piper", "coqui", "edge-tts"], "default": "piper"},
            "noise_reduction": {"type": "boolean", "default": True},
        },
    }

    def __init__(self):
        super().__init__()
        self.piper = PiperTSEngine()
        self._last_text = ""
        self._recordings_dir = _RECORDINGS_DIR
        self._dataset_dir = _PIPER_DATASET_DIR
        self._recordings_dir.mkdir(parents=True, exist_ok=True)
        self._dataset_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_piper_model()

    def _ensure_piper_model(self):
        if not self.piper.available:
            model_files = list(_PIPER_MODELS_DIR.glob("*.onnx"))
            if not model_files:
                url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/amy.onnx"
                dest = _PIPER_MODELS_DIR / "en_US-amy-medium.onnx"
                if _download_piper_model(url, dest):
                    self.piper = PiperTSEngine()

    def warmup(self) -> bool:
        return self.piper.available

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "status")

        if action == "status":
            return self._status()
        if action == "speak":
            backend = kwargs.get("backend", "piper")
            return self._speak(kwargs.get("text", ""), backend=backend)
        if action == "record":
            noise_reduction = kwargs.get("noise_reduction", True)
            return self._record(kwargs.get("duration", 5.0), kwargs.get("sample_rate", 22050), noise_reduction=noise_reduction)
        if action == "train":
            return self._train()
        if action == "speak_file":
            backend = kwargs.get("backend", "piper")
            return self._speak(kwargs.get("text", ""), to_file=True, backend=backend)
        return {"error": f"Unknown action: {action}", "result": None}

    def _status(self) -> dict:
        recordings = list(self._recordings_dir.glob("*.wav"))
        settings = _load_settings()
        backend = settings.get("tts_backend", "piper")
        return {"error": None, "result": {
            "piper_available": self.piper.available,
            "backend": backend,
            "recordings_count": len(recordings),
            "recordings_dir": str(self._recordings_dir),
            "last_text": self._last_text,
        }}

    def _speak(self, text: str, to_file: bool = False, backend: str = "piper") -> dict:
        if not text:
            return {"error": "No text to speak", "result": None}

        self._last_text = text

        if backend == "piper":
            if not self.piper.available:
                return {"error": "Piper TTS not available — check ONNX model path", "result": None}
            if to_file:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                fname = f"tts_{ts}.wav"
                out_path = str(self._recordings_dir / fname)
                ok = self.piper.speak_to_file(text, out_path)
                if ok:
                    self.publish("voice_trainer:tts_file", {"path": out_path, "text": text[:40]})
                    return {"error": None, "result": {"wrote": out_path}}
                return {"error": "Failed to render TTS to file", "result": None}
            ok = self.piper.play(text)
            if ok:
                self.publish("voice_trainer:tts_played", {"text": text[:40]})
                return {"error": None, "result": {"played": text[:60]}}
            return {"error": "Failed to play TTS audio", "result": None}

        elif backend == "edge-tts":
            try:
                import asyncio
                import edge_tts
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_path = str(self._recordings_dir / f"tts_edge_{ts}.mp3")
                asyncio.run(edge_tts.Communicate(text).save(out_path))
                if to_file:
                    return {"error": None, "result": {"wrote": out_path}}
                import sounddevice as sd
                import soundfile as sf
                data, sr = sf.read(out_path)
                sd.play(data, sr)
                sd.wait()
                return {"error": None, "result": {"played": text[:60]}}
            except ImportError:
                return {"error": "edge-tts not installed", "result": None}

        elif backend == "coqui":
            try:
                from TTS.api import TTS
                tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_path = str(self._recordings_dir / f"tts_coqui_{ts}.wav")
                tts.tts_to_file(text=text, file_path=out_path)
                if to_file:
                    return {"error": None, "result": {"wrote": out_path}}
                import sounddevice as sd
                import soundfile as sf
                data, sr = sf.read(out_path)
                sd.play(data, sr)
                sd.wait()
                return {"error": None, "result": {"played": text[:60]}}
            except ImportError:
                return {"error": "TTS (Coqui) not installed", "result": None}

        return {"error": f"Unknown backend: {backend}", "result": None}

    def _record(self, duration: float, sample_rate: int, noise_reduction: bool = True) -> dict:
        try:
            import sounddevice as sd
            import soundfile as sf
        except ImportError:
            return {"error": "sounddevice/soundfile not installed", "result": None}

        duration = max(1.0, min(duration, 30.0))
        self.publish("voice_trainer:recording_start", {"duration": duration})

        try:
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
            sd.wait()
        except Exception as e:
            return {"error": f"Recording failed: {e}", "result": None}

        audio = recording.flatten().tolist()

        if noise_reduction:
            audio = _apply_noise_reduction(audio, sample_rate, cutoff=4000)

        audio = _resample(audio, sample_rate, target_rate=22050)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"recorded_{ts}.wav"
        fpath = self._recordings_dir / fname
        import numpy as np
        sf.write(str(fpath), np.array(audio, dtype=np.float32), 22050)

        self.publish("voice_trainer:recording_done", {"path": str(fpath), "duration": duration})
        return {"error": None, "result": {
            "saved": fname,
            "path": str(fpath),
            "duration": duration,
            "sample_rate": 22050,
            "noise_reduction": noise_reduction,
            "recordings_dir": str(self._recordings_dir),
        }}

    def _train(self) -> dict:
        wavs_dir = self._dataset_dir / "wavs"
        wavs_dir.mkdir(parents=True, exist_ok=True)
        metadata_lines = []

        for wav_path in sorted(self._recordings_dir.glob("*.wav")):
            dest = wavs_dir / wav_path.name
            shutil.copy2(str(wav_path), str(dest))
            label = self._last_text or "unknown"
            metadata_lines.append(f"{wav_path.name}|{label}|voice_trainer")

        meta_path = self._dataset_dir / "metadata.tsv"
        with open(str(meta_path), "w", encoding="utf-8") as f:
            f.write("\n".join(metadata_lines))

        return {"error": None, "result": {
            "samples": len(metadata_lines),
            "dataset_dir": str(self._dataset_dir),
            "wavs_dir": str(wavs_dir),
            "metadata": str(meta_path),
        }}

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        text = payload if isinstance(payload, str) else ""
        action = "speak" if text else "status"
        result = self.execute(action=action, text=text)
        if result.get("error"):
            return False, result["error"]
        return True, result["result"]
