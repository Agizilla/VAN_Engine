"""
voice_emotion_capture_NEEDS-TESTING.py — Real-time mic capture of non-verbal emotional sounds.

STATUS: NEEDS TESTING (cannot be verified without a physical microphone)

Extracted from: VoiceCut.py
Dependencies: pyaudio, librosa, numpy, soundfile, webrtcvad, (optional: matplotlib)

Capabilities:
  - Real-time audio capture via PyAudio
  - WebRTC VAD-based voice activity detection
  - RMS energy silence gating
  - Spectral feature extraction (centroid, ZCR, rolloff)
  - Ring-buffer pre-roll for onset capture
  - Non-blocking session with callback-based labeling
  - Session manifest JSON export

Usage:
    from voice_emotion_capture_NEEDS_TESTING import VoiceEmotionCapture

    def on_capture(wav_path, features):
        print(f"Captured: {wav_path}")
        return "sigh"  # return label string or None to skip

    cap = VoiceEmotionCapture(on_capture=on_capture)
    cap.start(output_dir="labeled_sounds")
    # ... runs until cap.stop() or timeout ...
    manifest = cap.stop()
"""

import os
import json
import time
import queue
import threading
import datetime
import struct
import wave
import warnings
from collections import deque
from pathlib import Path
from typing import Callable, Optional

warnings.filterwarnings("ignore")

import numpy as np

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    import webrtcvad
except ImportError:
    webrtcvad = None

try:
    import librosa
except ImportError:
    librosa = None


VALID_SAMPLE_RATES = {8000, 16000, 32000, 48000}


class SkillError(Exception):
    pass


# ═══════════════════════════════════════════════════════════════════════════
#  VOICE EMOTION CAPTURE
# ═══════════════════════════════════════════════════════════════════════════

class VoiceEmotionCapture:
    """Real-time microphone capture of non-verbal emotional sounds.

    Listens to the default mic in a background thread, detects non-verbal
    sounds (sighs, moans, laughs, gasps, etc.) using WebRTC VAD + RMS
    energy gating, saves 2-second clips, and invokes a callback for labeling.

    Attributes:
        sample_rate: Audio sample rate (Hz). WebRTC VAD supports 8k/16k/32k/48k.
        silence_threshold: RMS below this is treated as silence.
        capture_seconds: Duration of each captured clip.
        vad_aggressiveness: WebRTC VAD mode 0-3 (3=most aggressive).
        on_capture: Callable(wav_path, features_dict) -> str | None.

    Usage:
        def on_capture(wav_path, features):
            return "sigh"  # label

        cap = VoiceEmotionCapture(on_capture=on_capture)
        cap.start("labeled_sounds")
        time.sleep(30)
        manifest = cap.stop()
    """

    CHUNK_MS = 30

    def __init__(
        self,
        sample_rate: int = 16000,
        silence_threshold: float = 0.01,
        vad_aggressiveness: int = 2,
        capture_seconds: float = 2.0,
        vad_trigger_ratio: float = 0.3,
        ring_buffer_chunks: int = 10,
        pre_roll_chunks: int = 5,
        on_capture: Optional[Callable] = None,
        device_index: Optional[int] = None,
        silence_timeout: float = 3.0,
        test_mode: bool = False,
        test_wav_path: Optional[str] = None,
    ):
        if sample_rate not in VALID_SAMPLE_RATES:
            raise ValueError(
                f"Invalid sample_rate {sample_rate}. WebRTC VAD supports: {sorted(VALID_SAMPLE_RATES)}"
            )

        if test_mode and test_wav_path:
            pass
        else:
            if pyaudio is None:
                raise SkillError("pyaudio required: pip install pyaudio")
            if webrtcvad is None:
                raise SkillError("webrtcvad required: pip install webrtcvad")
            if librosa is None:
                raise SkillError("librosa required: pip install librosa")

        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.vad_aggressiveness = vad_aggressiveness
        self.capture_seconds = capture_seconds
        self.vad_trigger_ratio = vad_trigger_ratio
        self.ring_buffer_chunks = ring_buffer_chunks
        self.pre_roll_chunks = pre_roll_chunks
        self.on_capture = on_capture
        self.device_index = device_index
        self.silence_timeout = silence_timeout
        self.test_mode = test_mode
        self.test_wav_path = test_wav_path

        self.chunk_samples = int(sample_rate * self.CHUNK_MS / 1000)
        self.chunk_bytes = self.chunk_samples * 2
        self.capture_chunks = int(capture_seconds * 1000 / self.CHUNK_MS)

        self._gain = 1.0
        self._audio_queue: queue.Queue = queue.Queue()
        self._label_queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._capture_thread: Optional[threading.Thread] = None
        self._session_manifest: dict[str, str] = {}
        self._running = False
        self._output_dir = ""

    # ── public API ─────────────────────────────────────────────────────

    def start(self, output_dir: str | Path = "labeled_sounds") -> None:
        """Start the capture session in a background thread."""
        if self._running:
            raise SkillError("Session already running")
        self._output_dir = str(output_dir)
        os.makedirs(self._output_dir, exist_ok=True)
        self._stop_event.clear()
        self._session_manifest.clear()
        self._running = True
        self._capture_thread = threading.Thread(
            target=self._session_loop, daemon=True
        )
        self._capture_thread.start()

    def stop(self) -> dict[str, str]:
        """Stop the capture session and return the manifest {filename: label}."""
        if not self._running:
            return self._session_manifest
        self._stop_event.set()
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=5.0)
        self._drain_label_queue()
        self._write_manifest()
        self._running = False
        return dict(self._session_manifest)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def manifest(self) -> dict[str, str]:
        return dict(self._session_manifest)

    # ── internal ───────────────────────────────────────────────────────

    def _drain_label_queue(self):
        while not self._label_queue.empty():
            try:
                fname, label = self._label_queue.get_nowait()
                self._session_manifest[fname] = label
            except queue.Empty:
                break

    def _write_manifest(self):
        path = Path(self._output_dir) / "session_manifest.json"
        try:
            path.write_text(json.dumps(self._session_manifest, indent=2))
        except Exception:
            pass

    def _auto_gain(self, samples: np.ndarray) -> np.ndarray:
        peak = np.max(np.abs(samples))
        if peak > 0.95:
            self._gain *= 0.707
        elif peak < 0.1:
            self._gain *= 1.414
        self._gain = max(0.1, min(self._gain, 10.0))
        return samples * self._gain

    def _audio_capture_loop(self):
        """Background thread: reads mic chunks into the audio queue."""
        if self.test_mode and self.test_wav_path:
            try:
                import soundfile as sf
                data, sr = sf.read(self.test_wav_path)
                if sr != self.sample_rate:
                    import librosa
                    data = librosa.resample(data, orig_sr=sr, target_sr=self.sample_rate)
                chunk_frames = self.chunk_samples
                for i in range(0, len(data), chunk_frames):
                    chunk = data[i:i + chunk_frames]
                    if len(chunk) < chunk_frames:
                        chunk = np.pad(chunk, (0, chunk_frames - len(chunk)))
                    chunk_int16 = (chunk * 32767).astype(np.int16)
                    self._audio_queue.put(chunk_int16.tobytes())
                    if self._stop_event.is_set():
                        break
            except ImportError:
                self._stop_event.set()
            return

        pa = pyaudio.PyAudio()
        try:
            if self.device_index is not None:
                dev_info = pa.get_device_info_by_index(self.device_index)
            else:
                dev_info = pa.get_default_input_device_info()
        except IOError:
            self._stop_event.set()
            pa.terminate()
            return

        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk_samples,
        )

        while not self._stop_event.is_set():
            try:
                raw = stream.read(self.chunk_samples, exception_on_overflow=False)
                self._audio_queue.put(raw)
            except OSError:
                break

        stream.stop_stream()
        stream.close()
        pa.terminate()

    @staticmethod
    def _rms_energy(pcm_bytes: bytes) -> float:
        samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return float(np.sqrt(np.mean(samples ** 2)))

    @staticmethod
    def _spectral_features(pcm_bytes: bytes) -> dict:
        y = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        if len(y) < 512:
            return {}
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=16000)))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
        rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=16000)))
        return {
            "spectral_centroid_hz": round(centroid, 1),
            "zero_crossing_rate": round(zcr, 5),
            "spectral_rolloff_hz": round(rolloff, 1),
        }

    @staticmethod
    def _save_wav(pcm_frames: list[bytes], filepath: str):
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"".join(pcm_frames))

    def _label_clip(self, wav_path: str, features: dict) -> str:
        """Invoke the user callback for labeling. Returns label string."""
        if self.on_capture:
            try:
                label = self.on_capture(wav_path, features)
                if label:
                    return str(label).strip().lower()
            except Exception:
                pass
        return "unlabeled"

    def _session_loop(self):
        """Main processing loop running in background thread."""
        if not self.test_mode:
            vad = webrtcvad.Vad(self.vad_aggressiveness)
        else:
            vad = None

        audio_thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
        audio_thread.start()

        ring_buffer = deque(maxlen=self.ring_buffer_chunks)
        pre_roll = deque(maxlen=self.pre_roll_chunks)
        triggered = False
        capture_buf: list[bytes] = []
        capture_count = 0
        last_voice_time = time.time()

        while not self._stop_event.is_set():
            self._drain_label_queue()

            try:
                raw = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                if triggered and (time.time() - last_voice_time > self.silence_timeout):
                    triggered = False
                    capture_buf = []
                    capture_count = 0
                continue

            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            gained = self._auto_gain(samples)
            gained_int16 = (gained * 32767).astype(np.int16)
            raw_gained = gained_int16.tobytes()

            energy = self._rms_energy(raw_gained)

            if not triggered and energy < self.silence_threshold:
                pre_roll.append(raw_gained)
                continue

            if vad is not None:
                try:
                    is_speech = vad.is_speech(raw_gained, self.sample_rate)
                except Exception:
                    is_speech = False
            else:
                is_speech = energy >= self.silence_threshold

            ring_buffer.append((raw_gained, energy, is_speech))
            pre_roll.append(raw_gained)

            if not triggered and len(ring_buffer) == self.ring_buffer_chunks:
                voiced = sum(1 for _, _, sp in ring_buffer if sp) / self.ring_buffer_chunks
                avg_e = np.mean([e for _, e, _ in ring_buffer])
                if voiced >= self.vad_trigger_ratio and avg_e >= self.silence_threshold:
                    triggered = True
                    capture_count = 0
                    capture_buf = list(pre_roll)
                    last_voice_time = time.time()

            if triggered:
                capture_buf.append(raw_gained)
                capture_count += 1

                if energy >= self.silence_threshold:
                    last_voice_time = time.time()
                elif time.time() - last_voice_time > self.silence_timeout:
                    triggered = False
                    capture_buf = []
                    capture_count = 0
                    continue

                if capture_count >= self.capture_chunks:
                    triggered = False
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    wav_name = f"nonverbal_{ts}.wav"
                    wav_path = os.path.join(self._output_dir, wav_name)
                    self._save_wav(capture_buf, wav_path)

                    all_pcm = b"".join(capture_buf)
                    features = self._spectral_features(all_pcm)
                    label = self._label_clip(wav_path, features)

                    if not self.on_capture:
                        print(f"[VoiceEmotionCapture] Captured: {wav_name}")
                        print(f"  Features: {json.dumps(features, indent=2)}")
                        print(f"  Label: {label}")

                    meta = {
                        "label": label,
                        "wav_file": wav_name,
                        "features": features,
                        "captured": datetime.datetime.now().isoformat(),
                    }
                    meta_path = os.path.join(self._output_dir, f"nonverbal_{ts}.json")
                    try:
                        Path(meta_path).write_text(json.dumps(meta, indent=2))
                    except Exception:
                        pass

                    self._label_queue.put((wav_name, label))

                    ring_buffer.clear()
                    pre_roll.clear()
                    capture_buf = []
                    capture_count = 0

        audio_thread.join(timeout=2.0)

    def get_capabilities(self) -> list[str]:
        return [
            "real_time_mic_capture",
            "voice_activity_detection",
            "nonverbal_sound_detection",
            "emotion_labeling",
            "spectral_feature_extraction",
            "session_manifest_export",
        ]
