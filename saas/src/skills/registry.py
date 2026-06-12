import importlib
import importlib.metadata
import shutil
import subprocess


SKILL_LIBRARY_MAP = {
    "librosa": {"pip": "librosa", "import": "librosa"},
    "soundfile": {"pip": "soundfile", "import": "soundfile"},
    "demucs": {"pip": "demucs", "import": "demucs"},
    "music21": {"pip": "music21", "import": "music21"},
    "opencv": {"pip": "opencv-python", "import": "cv2"},
    "pillow": {"pip": "pillow", "import": "PIL"},
    "ultralytics": {"pip": "ultralytics", "import": "ultralytics"},
    "mediapipe": {"pip": "mediapipe", "import": "mediapipe"},
    "ffmpeg": {"pip": "ffmpeg-python", "import": "ffmpeg"},
    "moviepy": {"pip": "moviepy", "import": "moviepy"},
    "scenedetect": {"pip": "scenedetect", "import": "scenedetect"},
    "pytorch": {"pip": "torch", "import": "torch"},
    "whisper": {"pip": "openai-whisper", "import": "whisper"},
    "piper_tts": {"pip": "piper-tts", "import": "piper"},
    "sentence_transformers": {"pip": "sentence-transformers", "import": "sentence_transformers"},
    "faiss": {"pip": "faiss-cpu", "import": "faiss"},
}


class CapabilityReport:
    def __init__(self, available: dict):
        self._available = available

    @property
    def audio(self) -> bool:
        return self._available.get("librosa", False)

    @property
    def vision(self) -> bool:
        return self._available.get("opencv", False)

    @property
    def video(self) -> bool:
        return self._available.get("ffmpeg", False)

    @property
    def ml(self) -> bool:
        return self._available.get("pytorch", False)

    def __getitem__(self, key):
        val = self._available.get(key, False)
        if isinstance(val, tuple):
            return val[0]
        return val

    def to_dict(self):
        return dict(self._available)

    def summary(self) -> str:
        parts = []
        if self.audio:
            parts.append("Audio")
        if self.vision:
            parts.append("Vision")
        if self.video:
            parts.append("Video")
        if self.ml:
            parts.append("ML")
        return ", ".join(parts) if parts else "None"

    def get_version(self, name: str) -> str:
        val = self._available.get(name)
        if isinstance(val, tuple) and len(val) > 1:
            return val[1]
        return ""


def _check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _get_ffmpeg_version() -> str:
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        first_line = result.stdout.split("\n")[0] if result.stdout else ""
        return first_line.strip()
    except Exception:
        return ""


def _get_import_version(import_name: str, pip_name: str = None) -> str:
    try:
        return importlib.metadata.version(pip_name or import_name)
    except importlib.metadata.PackageNotFoundError:
        return ""


class _CapabilityCache:
    _capabilities_cache: dict = {}
    _cache_valid = False


def detect_capabilities(recompute: bool = False) -> CapabilityReport:
    if _CapabilityCache._cache_valid and not recompute:
        return CapabilityReport(_CapabilityCache._capabilities_cache)

    available = {}
    for name, info in SKILL_LIBRARY_MAP.items():
        if name == "ffmpeg":
            ff_avail = _check_ffmpeg()
            ff_ver = _get_ffmpeg_version() if ff_avail else ""
            available[name] = (ff_avail, ff_ver)
        else:
            try:
                importlib.import_module(info["import"])
                ver = _get_import_version(info["import"], info.get("pip"))
                available[name] = (True, ver)
            except ImportError:
                available[name] = (False, "")
    _CapabilityCache._capabilities_cache = available
    _CapabilityCache._cache_valid = True
    return CapabilityReport(available)


def get_missing_libs() -> list[str]:
    report = detect_capabilities()
    missing = []
    for name in SKILL_LIBRARY_MAP:
        if not report[name]:
            missing.append(name)
    return missing
