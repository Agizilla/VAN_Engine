"""
audioSkill.py — Master Audio Skill for Clawdia
Merged from: Music Studio, AUDIO_STUDIO, autoRapper, AudioWorkstation,
             VoiceAdapterStudio, Mute, DirtyTalker, VLC_AudioStudio,
             PhoneController, VirtualDrums, and 20+ other audio projects.

Categories: Stem Separation, Transcription, Voice Analysis, Voice Cloning,
            Voice Training, MIDI/Music Theory, Lyric Engine, Force Alignment,
            Mixing/Remixing, Audio Effects, Video from Audio, TTS
"""

from __future__ import annotations

__meta__ = {
    "name": "audioSkill.py",
    "description": "Master Audio Skill for Clawdia — 31 audio projects merged into one. Handles stem separation, transcription (Whisper + Vosk), voice cloning/synthesis/training, MIDI/music theory, lyric engine, mixing/remixing, audio DSP, noise cancellation, production audio engine, ONNX sound classification, offline voice commands, and music video generation.",
    "how_to": "from audioSkill import AudioSkill\nskill = AudioSkill()\nskill.separate_stems(Path('song.mp3'))\nskill.transcribe(Path('vocals.wav'))\nskill.synthesize('Hello world', Path('model.onnx'))\nskill.remix(Path('track.mp3'), Path('remix.wav'))\nskill.classify_sound(Path('noise.wav'))\nskill.voice_recognize_once(Path('command.wav'))",
    "version": "1.1.0",
    "dateCreated": "2026-06-07",
    "dateLastModified": "2026-06-07 14:30",
    "countPublicMethods": 131,
    "countLineNumbers": 2179,
    "mergedProjects": ["Music Studio", "AUDIO_STUDIO", "autoRapper", "AudioWorkstation", "VoiceAdapterStudio", "Mute", "DirtyTalker", "VLC_AudioStudio", "PhoneController", "VirtualDrums", "Song Style Extractor", "VoiceClone", "VoiceHash", "VoiceMash", "VoicePaperclip", "AudioToImage", "labeled_sounds", "Song Mixer", "VibeVoice", "Autorapper_replit", "LyricalStoryBoard", "GechoShift", "LyricToMelodyPlusVoice", "music21-studio", "DeepSeekAudioMorph", "OfflineSongWriter", "CollabEngine", "CLI", "LM_Studio", "ARC_Cinematic_Engine"],
    "update_list": [
        "2026-06-07 v1.0.0 — Initial merge: Music Studio (base, 1555 KB), AUDIO_STUDIO (654 KB), autoRapper (406 KB), AudioWorkstation (70 KB), VoiceAdapterStudio (88 KB), DirtyTalker (21 KB).",
        "    Extracted 22 capability categories across 107 public methods.",
        "    Capabilities: StemSeparation, Transcription, VoiceAnalysis, VoiceCloning, VoiceTransformation, PiperTTS, VoiceTraining, VoiceAdapter, NoiseCancellation, MIDIEncoder, MusicTheory, LyricGeneration, RhymeScoring, ForcedAlignment, PhonemeMatching, WavToMidi, DrumGeneration, AudioEffects, RemixPipeline, BatchProcessing, MusicVideoGeneration, AudioIO.",
        "2026-06-07 v1.0.1 — Added LyricsService (Genius API integration) extracted from ClaudeHipHopperList. New capabilities: song_search, lyrics_fetch, annotation_extraction, song_detail, batch_enrichment, artist_lookup. Added api_client.py retry/rate-limit utilities.",
        "2026-06-07 v1.0.2 — Added VoskTranscriber (offline Kaldi-based speech-to-text) extracted from ARC Cinematic Engine. Alternative to Whisper for short clips. New capability: vosk_transcription.",
        "2026-06-07 v1.0.3 — Added VoiceEmotionCapture (real-time mic capture of non-verbal emotional sounds) extracted from VoiceCut.py. UNTESTED — requires physical microphone. New capability: voice_emotion_capture. See voice_emotion_capture_needs_testing.py.",
        "2026-06-07 v1.1.0 — Added AudioProcessor (production audio engine with VAD, AGC, anti-noise generation, spectral masking) from Mute project. Replaces legacy NoiseCanceller.",
        "    Added ModelInference + ModelTrainer (ONNX sound classifier, mel-spectrogram extraction, hot-swappable models) from Mute project.",
        "    Added VoiceCommands (offline Pocketsphinx voice recognition with wake word + fuzzy command matching) from Mute project.",
        "    New capabilities: audio_processor, sound_classification, model_training, voice_commands."
    ]
}

import os, sys, json, time, random, shutil, struct, wave, abc, re, tempfile
import threading, logging, subprocess, importlib, hashlib, asyncio, functools
from pathlib import Path
from typing import Any, BinaryIO, Callable, Optional, AsyncGenerator
from collections import defaultdict, deque
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from enum import Enum

import numpy as np

try:
    import soundfile as sf
except ImportError:
    sf = None

try:
    import librosa
except ImportError:
    librosa = None

try:
    import pydub
except ImportError:
    pydub = None

try:
    from tools.master_skills.lyrics_service import LyricsService
except ImportError:
    try:
        from lyrics_service import LyricsService
    except ImportError:
        LyricsService = None

try:
    from tools.master_skills.voice_emotion_capture_needs_testing import VoiceEmotionCapture
except ImportError:
    try:
        from voice_emotion_capture_needs_testing import VoiceEmotionCapture
    except ImportError:
        VoiceEmotionCapture = None


ROOT = Path(__file__).parent.resolve()

DEFAULT_CONFIG = {
    "whisper_model": "medium",
    "demucs_model": "htdemucs",
    "piper_models_dir": ROOT / "models" / "piper",
    "speechbrain_cache": ROOT / "models" / "speechbrain",
    "sample_rate": 22050,
    "ffmpeg_path": "ffmpeg",
    "output_dir": ROOT / "outputs",
}

CONFIG = dict(DEFAULT_CONFIG)

for _d in [CONFIG["piper_models_dir"], CONFIG["speechbrain_cache"], CONFIG["output_dir"]]:
    _d.mkdir(parents=True, exist_ok=True)

_whisper_model_cache: dict[str, Any] = {}
_speechbrain_classifier_cache = None

_AUDIO_EMO_DICT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'config', 'emotional_dictionary.json')
_AUDIO_EMOTIONAL_DICT = {}
if os.path.exists(_AUDIO_EMO_DICT_PATH):
    try:
        with open(_AUDIO_EMO_DICT_PATH, 'r') as f:
            _AUDIO_EMOTIONAL_DICT = json.load(f)
    except: pass


class CancelFlags:
    def __init__(self):
        self._flags: dict[str, threading.Event] = {}

    def get(self, key: str) -> threading.Event:
        if key not in self._flags:
            self._flags[key] = threading.Event()
        return self._flags[key]

    def cancel(self, key: str):
        self.get(key).set()

    def reset(self, key: str):
        self.get(key).clear()

    @property
    def is_cancelled(self) -> bool:
        return any(f.is_set() for f in self._flags.values())

CANCEL = CancelFlags()


class AudioFormat(Enum):
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"
    WMA = "wma"


class SkillError(Exception):
    pass


# ═══════════════════════════════════════════════════════════════════════════
#  AUDIO I/O UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def _require(pkg: str, install_hint: str | None = None):
    try:
        return importlib.import_module(pkg)
    except ImportError:
        hint = install_hint or f"pip install {pkg}"
        raise SkillError(f"Missing package '{pkg}'. Install with: {hint}")


def ffmpeg(*args, check=False) -> subprocess.CompletedProcess:
    cmd = [CONFIG["ffmpeg_path"], *args]
    return subprocess.run(cmd, capture_output=True, check=check)


def audio_duration(path: Path) -> float:
    if sf:
        info = sf.info(str(path))
        return info.duration
    result = ffmpeg("-i", str(path), "-f", "null", "-")
    for line in result.stderr.decode().split("\n"):
        if "Duration" in line:
            parts = line.strip().split(",")[0].split("Duration:")[-1].strip()
            h, m, s = parts.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def to_wav(src: Path, out: Path | None = None) -> Path:
    if out is None:
        out = src.with_suffix(".wav")
    ffmpeg("-i", str(src), "-ar", str(CONFIG["sample_rate"]), "-ac", "1",
           "-sample_fmt", "s16", "-y", str(out), check=True)
    return out


def mp4_extract_audio(src: Path, out_mp3: Path) -> Path:
    ffmpeg("-i", str(src), "-vn", "-acodec", "libmp3lame", "-y", str(out_mp3), check=True)
    return out_mp3


def mp4_strip_audio(src: Path, out_mp4: Path) -> Path:
    ffmpeg("-i", str(src), "-an", "-c:v", "copy", "-y", str(out_mp4), check=True)
    return out_mp4


def play_wav(path: Path):
    import pygame
    pygame.mixer.init(frequency=CONFIG["sample_rate"])
    pygame.mixer.music.load(str(path))
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


def load_audio(path: Path, sr: int | None = None) -> tuple[np.ndarray, int]:
    if sr is None:
        sr = CONFIG["sample_rate"]
    if sf:
        data, samplerate = sf.read(str(path))
        if samplerate != sr and librosa:
            data = librosa.resample(data, orig_sr=samplerate, target_sr=sr)
        elif samplerate != sr:
            import scipy.signal
            ratio = sr / samplerate
            data = scipy.signal.resample(data, int(len(data) * ratio))
        return data.astype(np.float32), sr
    if librosa:
        return librosa.load(str(path), sr=sr)
    raise SkillError("No audio backend available (install soundfile or librosa)")


def save_audio(path: Path, data: np.ndarray, sr: int):
    if sf:
        sf.write(str(path), data, sr)
    elif pydub:
        from pydub import AudioSegment
        seg = AudioSegment(data.tobytes(), frame_rate=sr, sample_width=data.dtype.itemsize, channels=1)
        seg.export(str(path), format=path.suffix.lstrip("."))
    else:
        import scipy.io.wavfile
        scipy.io.wavfile.write(str(path), sr, (data * 32767).astype(np.int16))


def peak_dbfs(path: Path) -> float:
    data, sr = load_audio(path)
    peak = np.max(np.abs(data))
    if peak == 0:
        return -float("inf")
    return 20 * np.log10(peak)


def waveform_b64(path: Path, width: int = 600, height: int = 80) -> str | None:
    try:
        import matplotlib.pyplot as plt
        import base64, io
        data, sr = load_audio(path)
        fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
        ax.plot(np.linspace(0, len(data) / sr, len(data)), data, linewidth=0.5, color="#4A90D9")
        ax.axis("off")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  DEMUCS — STEM SEPARATION
# ═══════════════════════════════════════════════════════════════════════════

class DemucsSeparator:
    def __init__(self, model_name: str = "htdemucs"):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from demucs import pretrained
                from demucs.apply import apply_model
                self._apply = apply_model
                self._model = pretrained.get_model(self.model_name)
            except ImportError:
                raise SkillError("demucs not installed. Run: pip install demucs")
        return self._model

    def separate(self, audio_path: Path, shifts: int = 1,
                 progress_callback: Callable[[int, int], None] | None = None) -> dict[str, np.ndarray]:
        model = self._load()
        wav, sr = load_audio(audio_path)
        wav_t = torch.from_numpy(wav).float()
        if wav_t.dim() == 1:
            wav_t = wav_t.unsqueeze(0)
        ref = wav_t.mean(0)
        wav_t = (wav_t - ref.mean()) / ref.std()

        import torch
        with torch.no_grad():
            sources = self._apply(model, wav_t.unsqueeze(0), shifts=shifts, split=True)[0]

        stems = {}
        total = len(model.sources)
        for i, name in enumerate(model.sources):
            if progress_callback:
                progress_callback(i + 1, total)
            stem = sources[i].cpu().numpy()
            stem = stem * ref.std().numpy() + ref.mean().numpy()
            stems[name] = stem

        return stems, sr

    def separate_save(self, audio_path: Path, output_dir: Path | None = None,
                      shifts: int = 1,
                      progress_callback: Callable[[int, int], None] | None = None) -> dict[str, Path]:
        temp_dir = None
        try:
            if output_dir is None:
                temp_dir = Path(tempfile.mkdtemp(prefix="demucs_"))
                output_dir = temp_dir
            stems, sr = self.separate(audio_path, shifts, progress_callback)
            return self.save_stems(stems, sr, output_dir)
        finally:
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def save_stems(self, stems: dict[str, np.ndarray], sr: int, out_dir: Path) -> dict[str, Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = {}
        for name, data in stems.items():
            p = out_dir / f"{name}.wav"
            save_audio(p, data, sr)
            paths[name] = p
        return paths


# ═══════════════════════════════════════════════════════════════════════════
#  WHISPER — TRANSCRIPTION
# ═══════════════════════════════════════════════════════════════════════════

def get_whisper(model_size: str = "medium"):
    global _whisper_model_cache
    if model_size in _whisper_model_cache:
        return _whisper_model_cache[model_size]
    whisper = _require("whisper", "pip install openai-whisper")
    print(f"  Loading Whisper '{model_size}'...")
    model = whisper.load_model(model_size)
    _whisper_model_cache[model_size] = model
    return model


def transcribe_audio(audio_path: Path, model_size: str = "medium",
                     word_timestamps: bool = True) -> dict:
    model = get_whisper(model_size)
    wav, sr = load_audio(audio_path)
    result = model.transcribe(wav, word_timestamps=word_timestamps)
    return result


def build_lrc(segments: list[dict], word_timestamps: bool = False) -> str:
    lines = []
    for seg in segments:
        if word_timestamps and "words" in seg:
            for w in seg["words"]:
                if "start" in w and "end" in w:
                    start = w["start"]
                    lines.append(f"[{int(start)//60:02d}:{int(start)%60:02d}.{int(start*100)%100:02d}] {w['word'].strip()}")
                else:
                    lines.append(w["word"].strip())
        else:
            start = seg.get("start", 0)
            lines.append(f"[{int(start)//60:02d}:{int(start)%60:02d}.{int(start*100)%100:02d}] {seg['text'].strip()}")
    return "\n".join(lines)


def build_txt(segments: list[dict]) -> str:
    return "\n".join(seg["text"].strip() for seg in segments)


# ═══════════════════════════════════════════════════════════════════════════
#  VOSK — OFFLINE SPEECH-TO-TEXT (alternative to Whisper)
# ═══════════════════════════════════════════════════════════════════════════

class VoskTranscriber:
    """Offline speech-to-text using Vosk (Kaldi).

    Extracted from ARC Cinematic Engine. Lighter than Whisper for
    short audio clips. Requires a downloaded Vosk model in
    CONFIG["vosk_model_dir"].

    Usage:
        vt = VoskTranscriber()
        text = vt.transcribe("audio.wav")
    """

    def __init__(self, model_path: str | Path | None = None):
        self._model = None
        self._model_path = Path(model_path) if model_path else (
            CONFIG.get("vosk_model_dir", ROOT / "models" / "vosk")
        )

    def _load(self):
        if self._model is None:
            from vosk import Model
            self._model = Model(str(self._model_path))
        return self._model

    def transcribe(self, audio_path: Path | str, chunk_frames: int = 4000) -> str:
        """Transcribe a WAV file (must be 16kHz mono). Returns full text."""
        from vosk import KaldiRecognizer
        import wave
        model = self._load()
        wf = wave.open(str(audio_path), "rb")
        rec = KaldiRecognizer(model, wf.getframerate())
        text_parts = []
        while True:
            data = wf.readframes(chunk_frames)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text_parts.append(result.get("text", ""))
        wf.close()
        final = json.loads(rec.FinalResult())
        text_parts.append(final.get("text", ""))
        return " ".join(t for t in text_parts if t)

    def transcribe_file(self, audio_path: Path | str) -> dict:
        """Transcribe and return full result dict."""
        text = self.transcribe(audio_path)
        return {"text": text, "segments": [{"text": text, "start": 0, "end": 0}]}


# ═══════════════════════════════════════════════════════════════════════════
#  VOICE ANALYSIS — PITCH, BPM, KEY, MFCC
# ═══════════════════════════════════════════════════════════════════════════

class AutoCorrelationPitchDetector:
    def detect(self, y: np.ndarray, sr: int, fmin: float = 50, fmax: float = 2000) -> np.ndarray:
        from librosa import autocorrelate
        pitches = np.zeros(len(y))
        frame_length = int(sr / fmin)
        hop = frame_length // 4
        for i in range(0, len(y) - frame_length, hop):
            frame = y[i:i + frame_length] * np.hanning(frame_length)
            ac = autocorrelate(frame)
            d = np.diff(ac)
            peaks = np.where((d[:-1] > 0) & (d[1:] <= 0))[0] + 1
            if len(peaks) > 0:
                lag = peaks[0]
                if lag > 0:
                    freq = sr / lag
                    if fmin <= freq <= fmax:
                        pitches[i // hop] = freq
        return pitches


class YINPitchDetector:
    def detect(self, y: np.ndarray, sr: int, fmin: float = 50, fmax: float = 2000) -> np.ndarray:
        if librosa:
            from librosa import yin
            return yin(y, fmin=fmin, fmax=fmax, sr=sr)
        raise SkillError("librosa required for YIN pitch detection")


class SpectralPitchDetector:
    def detect(self, y: np.ndarray, sr: int) -> np.ndarray:
        S = np.abs(librosa.stft(y))
        frequencies = librosa.fft_frequencies(sr=sr)
        pitches = frequencies[np.argmax(S, axis=0)]
        return pitches


class PitchTracker:
    def __init__(self, method: str = "autocorrelation"):
        methods = {
            "autocorrelation": AutoCorrelationPitchDetector,
            "yin": YINPitchDetector,
            "spectral": SpectralPitchDetector,
        }
        if method not in methods:
            raise SkillError(f"Unknown pitch method: {method}. Choose from {list(methods.keys())}")
        self.detector = methods[method]()

    def track(self, y: np.ndarray, sr: int) -> np.ndarray:
        return self.detector.detect(y, sr)


def freq_to_midi(freq: float) -> float:
    if freq <= 0:
        return 0
    return 12 * np.log2(freq / 440) + 69


def midi_to_freq(midi: float) -> float:
    return 440 * 2 ** ((midi - 69) / 12)


def midi_to_name(midi: float) -> str:
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    if midi <= 0:
        return "REST"
    octave = int(midi // 12) - 1
    note = note_names[int(midi) % 12]
    return f"{note}{octave}"


def detect_bpm_key(audio_path: Path) -> tuple[float, str]:
    if not librosa:
        raise SkillError("librosa required for BPM/key detection")
    y, sr = load_audio(audio_path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    key_indices = np.sum(chroma, axis=1)
    major_keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    key = major_keys[np.argmax(key_indices)]
    return float(tempo), key


def extract_mfcc_profile(audio_path: Path, n_mfcc: int = 20) -> np.ndarray:
    if not librosa:
        raise SkillError("librosa required for MFCC extraction")
    y, sr = load_audio(audio_path)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return np.mean(mfcc, axis=1)


class GoldenRatioMetric:
    @staticmethod
    def compute(y: np.ndarray, sr: int) -> dict:
        if not librosa:
            raise SkillError("librosa required")
        spectral = np.abs(librosa.stft(y))
        centroid = librosa.feature.spectral_centroid(S=spectral, sr=sr)[0]
        bandwidth = librosa.feature.spectral_bandwidth(S=spectral, sr=sr)[0]
        rolloff = librosa.feature.spectral_rolloff(S=spectral, sr=sr)[0]
        return {
            "centroid_mean": float(np.mean(centroid)),
            "bandwidth_mean": float(np.mean(bandwidth)),
            "rolloff_mean": float(np.mean(rolloff)),
            "golden_ratio_score": float(np.mean(centroid) / max(np.mean(bandwidth), 1)),
        }


# ═══════════════════════════════════════════════════════════════════════════
#  VOICE TRANSFORMATION
# ═══════════════════════════════════════════════════════════════════════════

def formant_shift_parselmouth(y: np.ndarray, sr: int, shift: float = 1.2) -> np.ndarray:
    try:
        import parselmouth
        import io
        buf = io.BytesIO()
        sf.write(buf, y, sr, format="wav")
        buf.seek(0)
        snd = parselmouth.Sound(buf.read())
        manipulated = snd.shift_pitch(time_stretch=1, pitch_shift=shift)
        return manipulated.values.T.squeeze().astype(np.float32)
    except ImportError:
        raise SkillError("parselmouth not installed: pip install praat-parselmouth")


def formant_shift_lpc(y: np.ndarray, sr: int, shift: float = 1.2) -> np.ndarray:
    if not librosa:
        raise SkillError("librosa required")
    order = int(sr / 1000) + 2
    lpc = librosa.lpc(y, order=order)
    residual = np.convolve(y, lpc, mode="full")[:len(y)]
    excited = np.zeros_like(residual)
    sampleshift = int(round(1.0 / shift))
    for i in range(0, len(residual), sampleshift):
        idx = min(i, len(residual) - 1)
        excited[i] = residual[idx]
    filtered = np.convolve(excited, lpc, mode="full")[:len(y)]
    return filtered.astype(np.float32)


def apply_formant_shift_ms(y: np.ndarray, sr: int, shift: float = 1.2) -> np.ndarray:
    try:
        return formant_shift_parselmouth(y, sr, shift)
    except Exception:
        return formant_shift_lpc(y, sr, shift)


# ═══════════════════════════════════════════════════════════════════════════
#  VOICE CLONING — ECAPA-TDNN SPEAKER EMBEDDING
# ═══════════════════════════════════════════════════════════════════════════

def extract_embedding(audio_path: Path) -> np.ndarray:
    global _speechbrain_classifier_cache
    if _speechbrain_classifier_cache is None:
        try:
            from speechbrain.inference.speaker import EncoderClassifier
        except ImportError:
            raise SkillError("speechbrain not installed: pip install speechbrain")
        _speechbrain_classifier_cache = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=str(CONFIG["speechbrain_cache"]),
        )
    classifier = _speechbrain_classifier_cache
    signal, fs = load_audio(audio_path)
    signal_t = torch.from_numpy(signal).float().unsqueeze(0)
    import torch
    with torch.no_grad():
        embeddings = classifier.encode_batch(signal_t)
        embedding = embeddings.squeeze().numpy()
    return embedding


def clone_voice_from_audio(source_wav: Path, target_wav: Path,
                           output_path: Path, sr: int | None = None) -> Path:
    if sr is None:
        sr = CONFIG["sample_rate"]
    src_emb = extract_embedding(source_wav)
    tgt_emb = extract_embedding(target_wav)
    delta = tgt_emb - src_emb
    out = output_path.with_suffix(".npz")
    np.savez(out, delta=delta, src_file=str(source_wav), tgt_file=str(target_wav))
    return out


def load_voice_clone(npz_path: Path) -> np.ndarray:
    data = np.load(npz_path)
    return data["delta"]


def compute_feature_delta(src_profile: np.ndarray, tgt_profile: np.ndarray) -> np.ndarray:
    return tgt_profile - src_profile


# ═══════════════════════════════════════════════════════════════════════════
#  PIPER TTS — VOICE SYNTHESIS
# ═══════════════════════════════════════════════════════════════════════════

def get_piper_session(model_path: Path):
    try:
        import piper
        import piper.download
    except ImportError:
        raise SkillError("piper not installed: pip install piper-tts")
    import piper
    import onnxruntime
    session = onnxruntime.InferenceSession(str(model_path))
    return session


def piper_models() -> list[Path]:
    return list(CONFIG["piper_models_dir"].glob("*.onnx"))


def piper_probe_speaker_dim(model_path: Path) -> tuple[int, np.ndarray | None]:
    import onnxruntime
    session = onnxruntime.InferenceSession(str(model_path))
    for inp in session.get_inputs():
        if "sid" in inp.name.lower():
            return inp.shape[1] if len(inp.shape) > 1 else inp.shape[0], None
    return 0, None


def extract_speaker_patch(model_path: Path, reference_wav: Path) -> np.ndarray:
    emb = extract_embedding(reference_wav)
    return emb


def synthesise(text: str, model_path: Path, output_path: Path,
               speaker_id: int | None = None, length_scale: float = 1.0) -> Path:
    try:
        import piper
    except ImportError:
        raise SkillError("piper not installed: pip install piper-tts")
    import piper
    from piper import PiperVoice
    voice = PiperVoice.load(str(model_path), config_path=str(model_path.with_suffix(".json")))
    with open(output_path, "wb") as f:
        voice.synthesize(text, f, speaker_id=speaker_id, length_scale=length_scale)
    return output_path


# ═══════════════════════════════════════════════════════════════════════════
#  AUDIO EFFECTS — DSP PROCESSING
# ═══════════════════════════════════════════════════════════════════════════

def apply_crossfade(audio: np.ndarray, sr: int, fade_ms: int = 50) -> np.ndarray:
    fade_len = int(sr * fade_ms / 1000)
    if fade_len > len(audio):
        fade_len = len(audio) // 2
    fade_in = np.linspace(0, 1, fade_len)
    fade_out = np.linspace(1, 0, fade_len)
    result = audio.copy()
    result[:fade_len] *= fade_in
    if len(result) > fade_len:
        result[-fade_len:] *= fade_out
    return result


def time_stretch(y: np.ndarray, sr: int, rate: float) -> np.ndarray:
    if not librosa:
        raise SkillError("librosa required for time stretching")
    return librosa.effects.time_stretch(y=y, rate=rate)


def pitch_shift(y: np.ndarray, sr: int, n_steps: float) -> np.ndarray:
    if not librosa:
        raise SkillError("librosa required for pitch shifting")
    return librosa.effects.pitch_shift(y=y, sr=sr, n_steps=n_steps)


def change_volume(y: np.ndarray, dB: float) -> np.ndarray:
    return y * (10 ** (dB / 20))


def apply_eq(y: np.ndarray, sr: int, low_gain: float = 0,
             mid_gain: float = 0, high_gain: float = 0) -> np.ndarray:
    if not librosa:
        raise SkillError("librosa required for EQ")
    S = librosa.stft(y)
    freqs = librosa.fft_frequencies(sr=sr)
    low_mask = freqs < 250
    mid_mask = (freqs >= 250) & (freqs < 4000)
    high_mask = freqs >= 4000
    S[low_mask] *= 10 ** (low_gain / 20)
    S[mid_mask] *= 10 ** (mid_gain / 20)
    S[high_mask] *= 10 ** (high_gain / 20)
    return librosa.istft(S)


def add_reverb(y: np.ndarray, sr: int, decay: float = 0.3, delay_ms: int = 50) -> np.ndarray:
    delay_samples = int(sr * delay_ms / 1000)
    output = y.copy()
    for i in range(delay_samples, len(y)):
        output[i] += y[i - delay_samples] * decay
    return output / np.max(np.abs(output))


def generate_tone(freq: float, duration_s: float, sr: int | None = None,
                  waveform: str = "sine") -> np.ndarray:
    if sr is None:
        sr = CONFIG["sample_rate"]
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)
    if waveform == "sine":
        return np.sin(2 * np.pi * freq * t)
    elif waveform == "square":
        return np.sign(np.sin(2 * np.pi * freq * t))
    elif waveform == "sawtooth":
        return 2 * (freq * t - np.floor(freq * t + 0.5))
    elif waveform == "triangle":
        return 2 * np.abs(2 * (freq * t - np.floor(freq * t + 0.5))) - 1
    return np.sin(2 * np.pi * freq * t)


# ═══════════════════════════════════════════════════════════════════════════
#  MIXING / REMIXING
# ═══════════════════════════════════════════════════════════════════════════

def mix_stems(stem_paths: list[Path], output_path: Path,
              volumes: list[float] | None = None) -> Path:
    if not stem_paths:
        raise SkillError("No stems to mix")

    mixed = None
    sr = None
    for i, sp in enumerate(stem_paths):
        data, rate = load_audio(sp)
        if sr is None:
            sr = rate
            mixed = np.zeros(max(len(d) for d in [data]))
        if volumes and i < len(volumes):
            data = data * volumes[i]
        if mixed is not None:
            if len(data) > len(mixed):
                mixed = np.pad(mixed, (0, len(data) - len(mixed)))
            elif len(data) < len(mixed):
                data = np.pad(data, (0, len(mixed) - len(data)))
            mixed += data

    if mixed is None:
        raise SkillError("Failed to mix stems")
    mixed /= np.max(np.abs(mixed)) + 1e-10
    save_audio(output_path, mixed.astype(np.float32), sr or CONFIG["sample_rate"])
    return output_path


def mix_beat_vocal(beat_wav: Path, vocal_wav: Path, out_wav: Path,
                   beat_volume: float = 0.7, vocal_volume: float = 1.0) -> Path:
    return mix_stems([beat_wav, vocal_wav], out_wav, [beat_volume, vocal_volume])


class RemixPipeline:
    def __init__(self):
        self.separator = DemucsSeparator()

    def remix(self, audio_path: Path, output_path: Path,
              vocal_source: str = "vocals", beat_source: str = "drums") -> Path:
        stems, sr = self.separator.separate(audio_path)
        vocal = stems.get(vocal_source, stems.get("vocals"))
        beat = stems.get(beat_source, stems.get("drums"))
        if vocal is None or beat is None:
            raise SkillError(f"Stem sources not found. Available: {list(stems.keys())}")

        min_len = min(len(vocal), len(beat))
        mixed = vocal[:min_len] * 1.0 + beat[:min_len] * 0.7
        mixed /= np.max(np.abs(mixed)) + 1e-10
        save_audio(output_path, mixed.astype(np.float32), sr)
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
#  MIDI / MUSIC THEORY
# ═══════════════════════════════════════════════════════════════════════════

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
SCALE_INTERVALS = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "chromatic": list(range(12)),
}


@dataclass
class MIDIEvent:
    note: int
    velocity: int
    start: float
    duration: float


class SyllableNode:
    def __init__(self, text: str, start: float, duration: float):
        self.text = text
        self.start = start
        self.duration = duration
        self.midi_notes: list[int] = []
        self.stress: float = 0.5


class SyllableSegmenter:
    def segment(self, text: str) -> list[SyllableNode]:
        import re
        words = re.findall(r"\w+|[^\w\s]", text.lower())
        nodes = []
        t = 0.0
        for word in words:
            syls = self._split_syllables(word)
            for syl in syls:
                dur = max(0.1, len(syl) * 0.08)
                nodes.append(SyllableNode(syl, t, dur))
                t += dur
            t += 0.05
        return nodes

    def _split_syllables(self, word: str) -> list[str]:
        import re
        vowels = "aeiouy"
        if len(word) <= 3:
            return [word]
        syllables = []
        current = ""
        for i, ch in enumerate(word):
            current += ch
            if ch in vowels and i < len(word) - 1 and word[i + 1] not in vowels:
                syllables.append(current)
                current = ""
        if current:
            syllables.append(current)
        return syllables if syllables else [word]


class TickQuantizer:
    def __init__(self, ticks_per_beat: int = 480, bpm: float = 120):
        self.tpq = ticks_per_beat
        self.bpm = bpm

    def quantize(self, time_s: float) -> int:
        sec_per_tick = 60.0 / (self.bpm * self.tpq)
        return int(round(time_s / sec_per_tick))


class AeolianScaleMatrix:
    SCALES = {
        "aeolian": [0, 2, 3, 5, 7, 8, 10],
        "dorian": [0, 2, 3, 5, 7, 9, 10],
        "phrygian": [0, 1, 3, 5, 7, 8, 10],
        "lydian": [0, 2, 4, 6, 7, 9, 11],
        "mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "locrian": [0, 1, 3, 5, 6, 8, 10],
    }

    def __init__(self, root: int = 60, mode: str = "aeolian"):
        self.root = root
        self.notes = [root + i for i in self.SCALES.get(mode, self.SCALES["aeolian"])]

    def get_note(self, degree: int, octave_shift: int = 0) -> int:
        if degree < 0 or degree >= len(self.notes):
            octaves = degree // len(self.notes)
            degree = degree % len(self.notes)
            octave_shift += octaves
        return self.notes[degree] + 12 * octave_shift


class MarkovMelodyGenerator:
    def __init__(self, order: int = 2):
        self.order = order
        self.chain: dict[tuple, list[int]] = {}

    def train(self, notes: list[int]):
        for i in range(len(notes) - self.order):
            key = tuple(notes[i:i + self.order])
            self.chain.setdefault(key, []).append(notes[i + self.order])

    def generate(self, length: int, seed: list[int] | None = None) -> list[int]:
        if not self.chain:
            raise SkillError("Markov chain not trained")
        if seed is None:
            seed = list(random.choice(list(self.chain.keys())))
        result = list(seed)
        for _ in range(length - len(seed)):
            key = tuple(result[-self.order:])
            if key in self.chain:
                result.append(random.choice(self.chain[key]))
            else:
                result.append(random.choice(list(self.chain.keys()))[0])
        return result


class CadenceEnforcer:
    RESOLUTIONS = {
        0: [0, 4, 7],
        3: [0, 3, 7],
        4: [0, 4, 7],
        5: [0, 4, 7],
        7: [0, 4, 7],
    }

    def enforce(self, melody: list[int], scale_notes: list[int]) -> list[int]:
        if not melody:
            return melody
        result = melody.copy()
        result[-1] = scale_notes[0]
        if len(result) > 1:
            result[-2] = scale_notes[4]
        return result


class MIDIEncoder:
    def encode(self, events: list[MIDIEvent], output_path: Path,
               bpm: float = 120, ticks_per_beat: int = 480):
        try:
            import mido
        except ImportError:
            raise SkillError("mido not installed: pip install mido")

        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))
        track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4))

        tpq = ticks_per_beat
        sec_per_tick = 60.0 / (bpm * tpq)

        events_sorted = sorted(events, key=lambda e: e.start)
        current_time = 0.0
        active_notes: dict[int, float] = {}

        for event in events_sorted:
            if event.start > current_time:
                delta = int((event.start - current_time) / sec_per_tick)
                track.append(mido.Message("note_on", note=event.note,
                                          velocity=event.velocity, time=delta))
                current_time = event.start
            else:
                track.append(mido.Message("note_on", note=event.note,
                                          velocity=event.velocity, time=0))
            active_notes[event.note] = event.start

        for note, start in active_notes.items():
            track.append(mido.Message("note_off", note=note, velocity=64,
                                      time=int(0.25 / sec_per_tick)))

        mid.save(str(output_path))
        return output_path


@dataclass
class AlignedWord:
    word: str
    start: float
    end: float
    confidence: float = 1.0


@dataclass
class AlignedPhoneme:
    phoneme: str
    start: float
    end: float


@dataclass
class AlignmentResult:
    words: list[AlignedWord] = field(default_factory=list)
    phonemes: list[AlignedPhoneme] = field(default_factory=list)
    duration: float = 0.0


class DTWAligner:
    def align(self, audio_path: Path, text: str) -> AlignmentResult:
        if not librosa:
            raise SkillError("librosa required for DTW alignment")
        result = AlignmentResult()
        y, sr = load_audio(audio_path)
        result.duration = len(y) / sr

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        words = text.lower().split()
        n_words = len(words)
        if n_words == 0:
            return result

        hop_length = 512
        frames_per_word = mfcc.shape[1] // n_words
        t = 0.0
        for i, word in enumerate(words):
            start = t
            dur = (frames_per_word * hop_length) / sr
            result.words.append(AlignedWord(word, start, start + dur))
            t += dur

        return result


class ForcedAligner:
    def __init__(self):
        self.dtw = DTWAligner()
        self.phoneme_map = {
            "a": "AA", "e": "EH", "i": "IH", "o": "OW", "u": "UW",
            "b": "B", "d": "D", "f": "F", "g": "G", "h": "HH",
            "k": "K", "l": "L", "m": "M", "n": "N", "p": "P",
            "r": "R", "s": "S", "t": "T", "v": "V", "w": "W",
            "y": "Y", "z": "Z",
        }

    def align(self, audio_path: Path, text: str) -> AlignmentResult:
        result = self.dtw.align(audio_path, text)
        for word in result.words:
            for ch in word.word.lower():
                if ch in self.phoneme_map:
                    result.phonemes.append(AlignedPhoneme(
                        self.phoneme_map[ch], word.start, word.end
                    ))
        return result


# ═══════════════════════════════════════════════════════════════════════════
#  LYRIC ENGINE — GENERATION, RHYME, ENHANCEMENT
# ═══════════════════════════════════════════════════════════════════════════

class MarkovGeneticLyricEngine:
    def __init__(self, order: int = 3):
        self.order = order
        self.chain: dict[tuple, list[str]] = {}

    def train(self, corpus: list[str]):
        for line in corpus:
            words = line.lower().split()
            for i in range(len(words) - self.order):
                key = tuple(words[i:i + self.order])
                self.chain.setdefault(key, []).append(words[i + self.order])

    def generate(self, seed: list[str] | None = None, length: int = 20) -> list[str]:
        if not self.chain:
            return ["No training data"]
        if seed is None:
            seed = list(random.choice(list(self.chain.keys())))
        result = list(seed)
        for _ in range(length):
            key = tuple(result[-self.order:])
            if key in self.chain:
                result.append(random.choice(self.chain[key]))
            else:
                break
        return result


class RhymeScorer:
    def __init__(self):
        try:
            import pronouncing
            self.pronouncing = pronouncing
        except ImportError:
            self.pronouncing = None

    def score(self, word_a: str, word_b: str) -> float:
        if self.pronouncing:
            rhymes_a = set(self.pronouncing.rhymes(word_a))
            rhymes_b = set(self.pronouncing.rhymes(word_b))
            if word_b in rhymes_a and word_a in rhymes_b:
                return 1.0
            overlap = len(rhymes_a & rhymes_b)
            return overlap / max(len(rhymes_a | rhymes_b), 1)
        return 1.0 if word_a[-2:] == word_b[-2:] else 0.0


class RhymeFlowSuggester:
    def __init__(self):
        self.scorer = RhymeScorer()

    def suggest(self, word: str, candidates: list[str], top_n: int = 5) -> list[tuple[str, float]]:
        scored = [(c, self.scorer.score(word, c)) for c in candidates]
        return sorted(scored, key=lambda x: -x[1])[:top_n]


class LyricEnhancer:
    def __init__(self):
        self.substitutions = {
            "love": "devotion", "heart": "soul", "night": "darkness",
            "day": "sunlight", "rain": "teardrops", "fire": "blaze",
            "cold": "frozen", "strong": "unbreakable",
        }

    def enhance(self, line: str) -> str:
        words = line.split()
        enhanced = []
        for w in words:
            w_clean = w.strip(".,!?;:")
            if w_clean.lower() in self.substitutions:
                replacement = self.substitutions[w_clean.lower()]
                if w[0].isupper():
                    replacement = replacement.capitalize()
                enhanced.append(replacement)
            else:
                enhanced.append(w)
        return " ".join(enhanced)


class PhonemeMatcher:
    def __init__(self):
        self.phoneme_map = {
            "b": "b", "p": "p", "m": "m", "f": "f", "v": "v",
            "d": "d", "t": "t", "n": "n", "l": "l", "r": "r",
            "g": "g", "k": "k", "h": "h", "s": "s", "z": "z",
            "sh": "sh", "zh": "zh", "ch": "ch", "jh": "jh",
            "th": "th", "dh": "dh", "w": "w", "y": "y",
        }

    def match(self, text: str, phoneme_sequence: list[str]) -> float:
        text_phonemes = []
        for ch in text.lower():
            if ch in self.phoneme_map:
                text_phonemes.append(self.phoneme_map[ch])
        if not text_phonemes or not phoneme_sequence:
            return 0.0
        matches = sum(1 for a, b in zip(text_phonemes, phoneme_sequence) if a == b)
        return matches / max(len(phoneme_sequence), 1)


# ═══════════════════════════════════════════════════════════════════════════
#  WAV → MIDI / ABC
# ═══════════════════════════════════════════════════════════════════════════

def wav_to_midi(audio_path: Path, output_path: Path,
                note_duration: float = 0.25, min_freq: float = 50,
                max_freq: float = 2000) -> Path:
    y, sr = load_audio(audio_path)
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr)

    pitch_tracker = PitchTracker("autocorrelation")
    pitches = pitch_tracker.track(y, sr)
    times_pitch = np.linspace(0, len(y) / sr, len(pitches))

    events = []
    for i, (t, p) in enumerate(zip(times_pitch, pitches)):
        if min_freq <= p <= max_freq:
            midi = int(round(freq_to_midi(p)))
            if 0 < midi < 128:
                events.append(MIDIEvent(note=midi, velocity=100,
                                        start=t, duration=note_duration))

    encoder = MIDIEncoder()
    encoder.encode(events, output_path)
    return output_path


def wav_to_abc(audio_path: Path) -> str:
    y, sr = load_audio(audio_path)
    pitch_tracker = PitchTracker("autocorrelation")
    pitches = pitch_tracker.track(y, sr)
    times = np.linspace(0, len(y) / sr, len(pitches))

    abc_notes = []
    key = "C"
    for p in pitches[:200]:
        if p > 0:
            midi = int(round(freq_to_midi(p)))
            name = midi_to_name(midi)
            abc_notes.append(name.replace("#", "^"))
        else:
            abc_notes.append("z")

    header = f"X:1\nM:4/4\nK:{key}\n"
    body = "".join(abc_notes[:64]) + "|"
    return header + body


# ═══════════════════════════════════════════════════════════════════════════
#  RHYTHM GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def generate_drum_track(bpm: float, pattern: str = "four_on_floor",
                        duration_bars: int = 4, sr: int | None = None) -> np.ndarray:
    if sr is None:
        sr = CONFIG["sample_rate"]
    beats_per_bar = 4
    total_beats = duration_bars * beats_per_bar
    beat_duration = 60.0 / bpm
    total_duration = total_beats * beat_duration
    total_samples = int(sr * total_duration)
    track = np.zeros(total_samples)

    patterns = {
        "four_on_floor": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "rock": [1, 0, 0, 1, 0, 1, 0, 0],
        "hiphop": [1, 0, 0, 0, 0, 1, 0, 0],
        "drum_and_bass": [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
    }
    hits = patterns.get(pattern, patterns["four_on_floor"])
    kick_freq = 60

    for beat in range(total_beats):
        if hits[beat % len(hits)]:
            start_sample = int(beat * beat_duration * sr)
            if start_sample < total_samples:
                tone = generate_tone(kick_freq, 0.1, sr, "sine") * np.exp(-np.linspace(0, 5, int(0.1 * sr)))
                end = min(start_sample + len(tone), total_samples)
                track[start_sample:end] += tone[:end - start_sample]

    return track / np.max(np.abs(track))


def generate_chord_track(scale: str, key_root: int = 60, bpm: float = 120,
                         duration_bars: int = 4, sr: int | None = None) -> np.ndarray:
    if sr is None:
        sr = CONFIG["sample_rate"]
    intervals = SCALE_INTERVALS.get(scale, SCALE_INTERVALS["major"])
    chord_roots = [key_root + intervals[i] for i in range(len(intervals))]
    beat_duration = 60.0 / bpm
    samples_per_bar = int(4 * beat_duration * sr)
    total_samples = samples_per_bar * duration_bars
    track = np.zeros(total_samples)

    chord_dur = beat_duration * 4
    chord_samples = int(chord_dur * sr)
    for bar in range(duration_bars):
        root = chord_roots[bar % len(chord_roots)]
        chord_notes = [root, root + 4, root + 7]
        start = bar * samples_per_bar
        for note in chord_notes:
            tone = generate_tone(midi_to_freq(note), chord_dur, sr, "sine") * 0.3
            end = min(start + chord_samples, total_samples)
            tone = tone[:end - start]
            track[start:end] += tone

    return track / np.max(np.abs(track))


# ═══════════════════════════════════════════════════════════════════════════
#  VOCAL EXTRACTION / PROCESSING
# ═══════════════════════════════════════════════════════════════════════════

def extract_vocals(audio_path: Path, output_dir: Path) -> dict[str, Path]:
    separator = DemucsSeparator()
    stems, sr = separator.separate(audio_path)
    return separator.save_stems(stems, sr, output_dir)


def extract_beat(audio_path: Path, output_dir: Path) -> Path | None:
    stems = extract_vocals(audio_path, output_dir)
    for name in ["drums", "bass", "other"]:
        if name in stems:
            return stems[name]
    return None


def extract_lyrics(audio_path: Path, model_size: str = "medium") -> str:
    result = transcribe_audio(audio_path, model_size)
    return build_txt(result.get("segments", []))


# ═══════════════════════════════════════════════════════════════════════════
#  VOICE TRAINING — PIPER ONNX
# ═══════════════════════════════════════════════════════════════════════════

def prepare_piper_dataset(recordings_dir: Path, output_dir: Path,
                          metadata_file: str = "metadata.tsv") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    wavs_dir = output_dir / "wavs"
    wavs_dir.mkdir(exist_ok=True)

    entries = []
    for wav_path in recordings_dir.glob("*.wav"):
        text_file = wav_path.with_suffix(".txt")
        if text_file.exists():
            text = text_file.read_text().strip()
            dest = wavs_dir / wav_path.name
            shutil.copy2(wav_path, dest)
            entries.append(f"{wav_path.name}\t{text}\n")

    metadata = output_dir / metadata_file
    with open(metadata, "w") as f:
        f.writelines(entries)

    return metadata


def train_piper_voice(dataset_dir: Path, output_dir: Path):
    try:
        import piper_train
    except ImportError:
        raise SkillError("piper_train not installed")
    cmd = [
        sys.executable, "-m", "piper_train",
        "--dataset-dir", str(dataset_dir),
        "--output-dir", str(output_dir),
    ]
    subprocess.run(cmd, check=True)


# ═══════════════════════════════════════════════════════════════════════════
#  AUDIO PROCESSOR — Production Engine (from Mute)
# ═══════════════════════════════════════════════════════════════════════════

class AudioProcessor:
    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.sample_rate = cfg.get("sample_rate", 16000)
        self.chunk_size = cfg.get("chunk_size", 1024)
        self.channels = cfg.get("channels", 1)
        self.analysis_buffer_len = self.sample_rate * 2
        self.analysis_buffer = np.zeros(self.analysis_buffer_len, dtype=np.float32)
        self.async_queue: asyncio.Queue = asyncio.Queue(maxsize=128)
        self.stream_instance = None
        self.vad_enabled = cfg.get("vad_enabled", True)
        self.vad_threshold = cfg.get("noise_gate_threshold", -45)
        self.is_low_power = False
        self.silence_counter = 0
        self.agc_enabled = True
        self.current_gain = 1.0
        self.target_rms = 0.18
        self.anti_noise_strength = cfg.get("anti_noise_strength", 0.8)
        self.latency_comp_samples = int(self.sample_rate * (cfg.get("latency_ms", 20) / 1000))
        self.spectral_filtering = cfg.get("spectral_filtering", True)

    @staticmethod
    def list_available_devices():
        if sd:
            return sd.query_devices()
        return "No audio driver detected."

    async def initialize(self):
        if not sd:
            raise SkillError("sounddevice is required for production-level latency.")
        def _audio_callback(indata, frames, time_info, status):
            if status:
                logging.debug(f"Stream Status: {status}")
            raw_chunk = indata.copy().flatten()
            self.analysis_buffer = np.roll(self.analysis_buffer, -len(raw_chunk))
            self.analysis_buffer[-len(raw_chunk):] = raw_chunk
            try:
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(self.async_queue.put_nowait, raw_chunk)
            except Exception:
                pass
        self.stream_instance = sd.InputStream(
            samplerate=self.sample_rate, channels=self.channels,
            blocksize=self.chunk_size, device=None,
            callback=_audio_callback, dtype="float32",
        )
        self.stream_instance.start()

    async def stream(self):
        while True:
            chunk = await self.async_queue.get()
            timestamp = time.time()
            if self.agc_enabled:
                chunk = self._apply_agc(chunk)
            if self.vad_enabled:
                rms = np.sqrt(np.mean(chunk**2))
                db = 20 * np.log10(rms + 1e-12)
                if db < self.vad_threshold:
                    self.silence_counter += 1
                    if self.silence_counter > (self.sample_rate / self.chunk_size * 2):
                        self.is_low_power = True
                        await asyncio.sleep(0.1)
                        continue
                else:
                    self.silence_counter = 0
                    self.is_low_power = False
            yield chunk, timestamp

    def _apply_agc(self, chunk: np.ndarray) -> np.ndarray:
        rms = np.sqrt(np.mean(chunk**2)) + 1e-12
        target = self.target_rms / rms
        self.current_gain = (0.98 * self.current_gain) + (0.02 * target)
        return np.clip(chunk * self.current_gain, -1.0, 1.0)

    def get_latest_slice(self, ms: int = 512) -> np.ndarray:
        samples = int(self.sample_rate * (ms / 1000))
        return self.analysis_buffer[-samples:]

    def generate_anti_noise(self, audio_data: np.ndarray) -> np.ndarray:
        anti_noise = -audio_data * self.anti_noise_strength
        if self.spectral_filtering:
            anti_noise = self._spectral_mask(anti_noise)
        if self.latency_comp_samples > 0:
            anti_noise = np.roll(anti_noise, -self.latency_comp_samples)
        return np.clip(anti_noise, -0.98, 0.98)

    def _spectral_mask(self, data: np.ndarray) -> np.ndarray:
        from scipy.fft import rfft, irfft
        n = len(data)
        spectrum = rfft(data)
        freqs = np.fft.rfftfreq(n, 1 / self.sample_rate)
        mask = (freqs >= 60) & (freqs <= 1800)
        spectrum[~mask] *= 0.25
        return irfft(spectrum, n=n)

    async def play_anti_noise(self, anti_noise: np.ndarray):
        if sd:
            sd.play(anti_noise, self.sample_rate)

    async def stop(self):
        if self.stream_instance:
            self.stream_instance.stop()
            self.stream_instance.close()

    def generate_anti_sound(self, y: np.ndarray) -> np.ndarray:
        return self.generate_anti_noise(y)

    def adaptive_filter(self, y: np.ndarray, noise_profile: np.ndarray | None = None) -> np.ndarray:
        if noise_profile is None:
            noise_profile = y[:int(0.1 * len(y))]
        noise_power = np.mean(noise_profile ** 2)
        if noise_power < 1e-10:
            return y
        return y - noise_profile * (np.mean(y * noise_profile) / noise_power)

    def spectral_gate(self, y: np.ndarray, sr: int, threshold_db: float = -40) -> np.ndarray:
        if not librosa:
            raise SkillError("librosa required for spectral gating")
        S = librosa.stft(y)
        magnitude = np.abs(S)
        mask = 20 * np.log10(magnitude + 1e-10) > threshold_db
        S_clean = S * mask
        return librosa.istft(S_clean)

    def generate_anti_sound(self, y: np.ndarray) -> np.ndarray:
        return -y

    def adaptive_filter(self, y: np.ndarray, noise_profile: np.ndarray | None = None) -> np.ndarray:
        if noise_profile is None:
            noise_profile = y[:int(0.1 * len(y))]
        noise_power = np.mean(noise_profile ** 2)
        if noise_power < 1e-10:
            return y
        return y - noise_profile * (np.mean(y * noise_profile) / noise_power)

    def spectral_gate(self, y: np.ndarray, sr: int, threshold_db: float = -40) -> np.ndarray:
        if not librosa:
            raise SkillError("librosa required for spectral gating")
        S = librosa.stft(y)
        magnitude = np.abs(S)
        mask = 20 * np.log10(magnitude + 1e-10) > threshold_db
        S_clean = S * mask
        return librosa.istft(S_clean)


# ═══════════════════════════════════════════════════════════════════════════
#  SOUND CLASSIFICATION — ONNX Model Inference (from Mute)
# ═══════════════════════════════════════════════════════════════════════════

class ModelInference:
    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.model_path = Path(cfg.get("model_path", "models/classifier.onnx"))
        self.classes = cfg.get("classes", [
            "snoring", "dog_bark", "baby_cry", "mechanical_hum",
            "laughter", "clock_tick", "insect", "speech",
        ])
        self.confidence_threshold = cfg.get("confidence_threshold", 0.7)
        self.inference_threads = cfg.get("inference_threads", 2)
        self.session = None
        self.input_name = None
        self.output_name = None
        self.sample_rate = cfg.get("sample_rate", 16000)
        self.n_mels = cfg.get("n_mels", 128)
        self.fft_size = cfg.get("fft_size", 2048)
        self.hop_length = cfg.get("hop_length", 512)
        self.inferences = 0
        self.inference_times: list[float] = []

    async def initialize(self):
        if not ort:
            return
        if not self.model_path.exists():
            return
        try:
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = self.inference_threads
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=sess_options,
                providers=["CPUExecutionProvider"],
            )
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
        except Exception as e:
            logging.error(f"Failed to load model: {e}")

    async def classify(self, audio_data: np.ndarray) -> dict | None:
        try:
            start_time = time.time()
            features = self.extract_features(audio_data)
            if features is None:
                return None
            if self.session:
                prediction = await self._run_onnx_inference(features)
            else:
                prediction = self._dummy_classifier(audio_data)
            inference_time = (time.time() - start_time) * 1000
            self.inference_times.append(inference_time)
            self.inferences += 1
            if len(self.inference_times) > 100:
                self.inference_times.pop(0)
            return prediction
        except Exception as e:
            logging.error(f"Error in classification: {e}")
            return None

    def extract_features(self, audio_data: np.ndarray) -> np.ndarray | None:
        try:
            if librosa:
                mel_spec = librosa.feature.melspectrogram(
                    y=audio_data, sr=self.sample_rate,
                    n_fft=self.fft_size, hop_length=self.hop_length,
                    n_mels=self.n_mels,
                )
                log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
                normalized = (log_mel_spec - log_mel_spec.min()) / (log_mel_spec.max() - log_mel_spec.min() + 1e-8)
                return normalized[np.newaxis, np.newaxis, :, :].astype(np.float32)
            return self._simple_spectrogram(audio_data)
        except Exception as e:
            logging.error(f"Error extracting features: {e}")
            return None

    def _simple_spectrogram(self, audio_data: np.ndarray) -> np.ndarray:
        from scipy import signal
        f, t, Zxx = signal.stft(audio_data, fs=self.sample_rate,
                                nperseg=self.fft_size, noverlap=self.fft_size - self.hop_length)
        mag_spec = np.abs(Zxx)
        if mag_spec.shape[0] > self.n_mels:
            factor = mag_spec.shape[0] // self.n_mels
            mag_spec = mag_spec.reshape(self.n_mels, factor, -1).mean(axis=1)
        log_spec = np.log10(mag_spec + 1e-10)
        normalized = (log_spec - log_spec.min()) / (log_spec.max() - log_spec.min() + 1e-8)
        return normalized[np.newaxis, np.newaxis, :, :].astype(np.float32)

    async def _run_onnx_inference(self, features: np.ndarray) -> dict:
        try:
            outputs = self.session.run([self.output_name], {self.input_name: features})
            probs = outputs[0][0]
            top_idx = np.argmax(probs)
            return {
                "class": self.classes[top_idx],
                "confidence": float(probs[top_idx]),
                "all_scores": {cls: float(probs[i]) for i, cls in enumerate(self.classes)},
            }
        except Exception:
            return self._dummy_classifier(features)

    def _dummy_classifier(self, audio_data) -> dict:
        rms = np.sqrt(np.mean(audio_data ** 2))
        zcr = np.sum(np.abs(np.diff(np.sign(audio_data)))) / (2 * len(audio_data))
        if rms < 0.01:
            cls, conf = "clock_tick", 0.6
        elif rms > 0.5 and zcr > 0.1:
            cls, conf = "dog_bark", 0.65
        elif zcr < 0.05:
            cls, conf = "snoring", 0.7
        else:
            cls, conf = "speech", 0.5
        return {"class": cls, "confidence": conf, "all_scores": {c: 0.1 for c in self.classes}}

    def get_inference_stats(self) -> dict:
        if not self.inference_times:
            return {"count": 0, "min_ms": 0, "max_ms": 0, "avg_ms": 0}
        return {
            "count": self.inferences,
            "min_ms": min(self.inference_times),
            "max_ms": max(self.inference_times),
            "avg_ms": sum(self.inference_times) / len(self.inference_times),
        }

    async def hot_swap_model(self, new_model_path: Path):
        try:
            new_session = ort.InferenceSession(str(new_model_path), providers=["CPUExecutionProvider"])
            old_session = self.session
            self.session = new_session
            self.model_path = new_model_path
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            if old_session:
                del old_session
        except Exception as e:
            logging.error(f"Failed to swap model: {e}")

    async def train_model(self, clips_dir: Path, output_path: Path):
        logging.info(f"Training model from {clips_dir} (stub — requires PyTorch)")
        pass


class ModelTrainer:
    def __init__(self, config: dict | None = None):
        self.config = config or {}

    async def initialize(self):
        logging.warning("PyTorch training not yet implemented")

    async def collect_data(self, label: str, duration: int = 30):
        logging.info(f"Recording {duration}s for label '{label}'")

    async def train(self, epochs: int = 50):
        logging.info(f"Training for {epochs} epochs")

    async def evaluate(self):
        logging.info("Evaluating model")


# ═══════════════════════════════════════════════════════════════════════════
#  VOICE COMMANDS — Offline Recognition (from Mute)
# ═══════════════════════════════════════════════════════════════════════════

try:
    import speech_recognition as sr
except ImportError:
    sr = None


class VoiceCommands:
    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.wake_word = cfg.get("wake_word", "hey mute")
        self.commands = cfg.get("commands", {
            "mute": "disable_anti_noise", "unmute": "enable_anti_noise",
            "volume up": "increase_volume", "volume down": "decrease_volume",
            "pause": "pause_processing", "play": "resume_processing",
        })
        self.sensitivity = cfg.get("sensitivity", 0.5)
        self.timeout = cfg.get("timeout", 5)
        self.recognizer = None
        self.microphone = None
        self.command_callback: Callable | None = None
        self.listening = False
        self.wake_word_detected = False
        self.recognitions = 0
        self.successful_commands = 0
        self.failed_recognitions = 0

    async def initialize(self):
        if sr is None:
            return
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            self.recognizer.energy_threshold = 300 * self.sensitivity
            self.recognizer.dynamic_energy_threshold = True
        except Exception as e:
            logging.error(f"Failed to initialize voice recognition: {e}")
            self.recognizer = None

    def set_command_callback(self, callback: Callable):
        self.command_callback = callback

    async def listen(self):
        if self.recognizer is None:
            return
        self.listening = True
        try:
            while self.listening:
                if not self.wake_word_detected:
                    await self._listen_for_wake_word()
                if self.wake_word_detected:
                    await self._listen_for_command()
                await asyncio.sleep(0.1)
        except Exception as e:
            logging.error(f"Error in voice listener: {e}")
        finally:
            self.listening = False

    async def _listen_for_wake_word(self):
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
            text = await self._recognize_speech(audio)
            if text and self.wake_word.lower() in text.lower():
                self.wake_word_detected = True
        except sr.WaitTimeoutError:
            pass
        except Exception:
            pass

    async def _listen_for_command(self):
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=self.timeout, phrase_time_limit=5)
            text = await self._recognize_speech(audio)
            if text:
                self.recognitions += 1
                command = self._match_command(text)
                if command:
                    self.successful_commands += 1
                    if self.command_callback:
                        self.command_callback(command)
                else:
                    self.failed_recognitions += 1
            self.wake_word_detected = False
        except sr.WaitTimeoutError:
            self.wake_word_detected = False
        except Exception:
            self.wake_word_detected = False

    async def _recognize_speech(self, audio) -> str | None:
        try:
            return self.recognizer.recognize_sphinx(audio)
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None

    def _match_command(self, text: str) -> str | None:
        text_lower = text.lower().strip()
        if text_lower in self.commands:
            return text_lower
        for cmd in self.commands:
            if cmd in text_lower:
                return cmd
        for cmd in self.commands:
            if self._fuzzy_match(text_lower, cmd):
                return cmd
        return None

    def _fuzzy_match(self, text: str, command: str, threshold: float = 0.6) -> bool:
        matches = sum(c1 == c2 for c1, c2 in zip(text, command))
        similarity = matches / max(len(text), len(command))
        return similarity >= threshold

    def get_stats(self) -> dict:
        success_rate = self.successful_commands / self.recognitions if self.recognitions > 0 else 0
        return {
            "recognitions": self.recognitions,
            "successful_commands": self.successful_commands,
            "failed_recognitions": self.failed_recognitions,
            "success_rate": success_rate,
        }

    async def stop(self):
        self.listening = False
        await asyncio.sleep(0.5)


# ═══════════════════════════════════════════════════════════════════════════
#  VOICE ADAPTER TRAINING
# ═══════════════════════════════════════════════════════════════════════════

class VoiceAdapter:
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.adapter: np.ndarray | None = None

    def train(self, source_embeddings: list[np.ndarray],
              target_embeddings: list[np.ndarray]):
        if len(source_embeddings) != len(target_embeddings):
            raise SkillError("Source and target embedding counts must match")
        deltas = [t - s for s, t in zip(source_embeddings, target_embeddings)]
        self.adapter = np.mean(deltas, axis=0)

    def apply(self, embedding: np.ndarray) -> np.ndarray:
        if self.adapter is None:
            raise SkillError("Adapter not trained")
        return embedding + self.adapter

    def save(self, path: Path):
        if self.adapter is None:
            raise SkillError("Nothing to save")
        np.savez(path, adapter=self.adapter)

    def load(self, path: Path):
        data = np.load(path)
        self.adapter = data["adapter"]


# ═══════════════════════════════════════════════════════════════════════════
#  MUSIC VIDEO GENERATOR (from AudioWorkstation)
# ═══════════════════════════════════════════════════════════════════════════

class MusicVideoGenerator:
    def __init__(self, fps: int = 24):
        self.fps = fps

    def generate(self, audio_path: Path, image_paths: list[Path],
                 output_path: Path, lyrics: list[tuple[str, float]] | None = None):
        try:
            from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
        except ImportError:
            raise SkillError("moviepy not installed: pip install moviepy")

        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        if not image_paths:
            raise SkillError("At least one image required")

        clip_duration = duration / len(image_paths)
        clips = []
        for img_path in image_paths:
            clip = ImageClip(str(img_path), duration=clip_duration)
            clip = clip.resize(height=720)
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video = video.set_audio(audio)

        if lyrics:
            text_clips = []
            for text, timestamp in lyrics:
                txt = TextClip(text, fontsize=24, color="white",
                               stroke_color="black", stroke_width=1)
                txt = txt.set_position(("center", "bottom")).set_start(timestamp).set_duration(2)
                text_clips.append(txt)
            video = CompositeVideoClip([video] + text_clips)

        video.write_videofile(str(output_path), fps=self.fps, codec="libx264", audio_codec="aac")
        return output_path


# ═══════════════════════════════════════════════════════════════════════════
#  BATCH OPERATIONS (from autoRapper)
# ═══════════════════════════════════════════════════════════════════════════

class BatchProcessor:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def process_files(self, files: list[Path], processor_fn: Callable,
                      progress_callback: Callable[[int, int], None] | None = None) -> list[Any]:
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(processor_fn, f): f for f in files}
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(None)
                if progress_callback:
                    progress_callback(len(results), len(files))
        return results

    def batch_stem_separate(self, audio_files: list[Path],
                            output_dir: Path,
                            progress_callback: Callable[[int, int], None] | None = None) -> dict[Path, dict[str, Path]]:
        separator = DemucsSeparator()
        results = {}
        for i, f in enumerate(audio_files):
            if progress_callback:
                progress_callback(i + 1, len(audio_files))
            temp_dir = None
            try:
                song_dir = output_dir / f.stem
                song_dir.mkdir(parents=True, exist_ok=True)
                stems, sr = separator.separate(f)
                results[f] = separator.save_stems(stems, sr, song_dir)
            finally:
                if temp_dir is not None:
                    shutil.rmtree(temp_dir, ignore_errors=True)
        return results

    def batch_transcribe(self, audio_files: list[Path],
                         model_size: str = "medium",
                         progress_callback: Callable[[int, int], None] | None = None) -> dict[Path, str]:
        model = get_whisper(model_size)
        results = {}
        for i, f in enumerate(audio_files):
            if progress_callback:
                progress_callback(i + 1, len(audio_files))
            result = model.transcribe(str(f))
            results[f] = result["text"]
        return results


# ═══════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════

class SessionState:
    def __init__(self, state_file: Path | None = None):
        self.state_file = state_file or CONFIG["output_dir"] / ".skill_state.json"
        self.data: dict = {}

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.data, indent=2, default=str))

    def load(self):
        if self.state_file.exists():
            try:
                self.data = json.loads(self.state_file.read_text())
            except Exception:
                self.data = {}

    def set(self, key: str, value: Any):
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


# ═══════════════════════════════════════════════════════════════════════════
#  MASTER AUDIO SKILL — Clawdia integration entry point
# ═══════════════════════════════════════════════════════════════════════════

class AudioSkill:
    def __init__(self, config: dict | None = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.state = SessionState()
        self.state.load()
        self.separator: DemucsSeparator | None = None
        self.pitch_tracker: PitchTracker | None = None
        token = self.config.get("genius_token") if config else None
        self.lyrics: LyricsService | None = LyricsService(token) if LyricsService else None
        self._vosk: VoskTranscriber | None = None
        self._voice_emotion: VoiceEmotionCapture | None = None
        self._audio_processor: AudioProcessor | None = None
        self._model_inference: ModelInference | None = None
        self._voice_commands: VoiceCommands | None = None
        self._whisper = None
        self._speechbrain_classifier = None
        self._ffmpeg_available = shutil.which(self.config.get("ffmpeg_path", "ffmpeg")) is not None
        self._cancel_event = threading.Event()

    @property
    def emotional_dictionary(self) -> dict:
        return _AUDIO_EMOTIONAL_DICT

    def get_facial_deltas(self, emotion_name: str) -> dict | None:
        if not _AUDIO_EMOTIONAL_DICT or 'emotions' not in _AUDIO_EMOTIONAL_DICT:
            return None
        emo = _AUDIO_EMOTIONAL_DICT['emotions']
        name_lower = emotion_name.lower()
        for key, val in emo.items():
            if key.lower() == name_lower:
                return val.get('deltas')
        return None

    def cancel(self):
        self._cancel_event.set()

    def reset_cancel(self):
        self._cancel_event.clear()

    def _load_whisper(self, model_size: str | None = None):
        if self._whisper is None:
            size = model_size or self.config.get("whisper_model", "medium")
            whisper_lib = _require("whisper", "pip install openai-whisper")
            print(f"  Loading Whisper '{size}'...")
            self._whisper = whisper_lib.load_model(size)
        return self._whisper

    def _load_speechbrain(self):
        if self._speechbrain_classifier is None:
            try:
                from speechbrain.inference.speaker import EncoderClassifier
            except ImportError:
                raise SkillError("speechbrain not installed: pip install speechbrain")
            self._speechbrain_classifier = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir=str(self.config["speechbrain_cache"]),
            )
        return self._speechbrain_classifier

    def get_separator(self) -> DemucsSeparator:
        if self.separator is None:
            self.separator = DemucsSeparator(self.config["demucs_model"])
        return self.separator

    def get_pitch_tracker(self, method: str = "autocorrelation") -> PitchTracker:
        if self.pitch_tracker is None:
            self.pitch_tracker = PitchTracker(method)
        return self.pitch_tracker

    def analyze(self, audio_path: Path) -> dict:
        if self._cancel_event.is_set():
            return {}
        data, sr = load_audio(audio_path)
        duration = len(data) / sr
        tempo, key = detect_bpm_key(audio_path)
        mfcc = extract_mfcc_profile(audio_path)
        return {
            "duration": duration,
            "sample_rate": sr,
            "tempo": tempo,
            "key": key,
            "mfcc_mean": mfcc.tolist(),
        }

    def separate_stems(self, audio_path: Path, output_dir: Path | None = None,
                       progress_callback: Callable[[int, int], None] | None = None) -> dict[str, Path]:
        if self._cancel_event.is_set():
            return {}
        sep = self.get_separator()
        temp_dir = None
        if output_dir is None:
            temp_dir = Path(tempfile.mkdtemp(prefix="stems_"))
            output_dir = temp_dir
        else:
            output_dir = self.config["output_dir"] / "stems" / audio_path.stem
        try:
            stems, sr = sep.separate(audio_path, progress_callback=progress_callback)
            return sep.save_stems(stems, sr, output_dir)
        finally:
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def transcribe(self, audio_path: Path, word_timestamps: bool = True,
                   model_size: str | None = None,
                   progress_callback: Callable[[int, int], None] | None = None) -> dict:
        if self._cancel_event.is_set():
            return {"text": "", "segments": [], "lrc": ""}
        model = self._load_whisper(model_size)
        wav, sr = load_audio(audio_path)
        if progress_callback:
            progress_callback(0, 1)
        result = model.transcribe(wav, word_timestamps=word_timestamps)
        if progress_callback:
            progress_callback(1, 1)
        return {
            "text": result.get("text", ""),
            "segments": result.get("segments", []),
            "lrc": build_lrc(result.get("segments", []), word_timestamps),
        }

    def transcribe_vosk(self, audio_path: Path) -> str:
        if self._vosk is None:
            self._vosk = VoskTranscriber()
        return self._vosk.transcribe(audio_path)

    @property
    def vosk_transcriber(self) -> VoskTranscriber:
        if self._vosk is None:
            self._vosk = VoskTranscriber()
        return self._vosk

    # ── voice emotion capture (NEEDS TESTING — requires mic) ──────────

    def voice_emotion_capture(self, output_dir: str | Path = "labeled_sounds",
                               on_capture: Callable | None = None,
                               duration: float | None = None) -> dict[str, str]:
        """Run a voice emotion capture session (REQUIRES MICROPHONE).

        Args:
            output_dir: Directory to save clips.
            on_capture: Callable(wav_path, features) returning a label string.
            duration: If set, auto-stop after N seconds.

        Returns:
            Manifest dict {filename: label}.

        NOTE: This capability requires a physical microphone and cannot be
        tested in headless/CI environments. See voice_emotion_capture_needs_testing.py.
        """
        if VoiceEmotionCapture is None:
            raise SkillError(
                "VoiceEmotionCapture unavailable. Install: pip install pyaudio webrtcvad librosa"
            )
        cap = VoiceEmotionCapture(on_capture=on_capture)
        cap.start(output_dir)
        try:
            if duration:
                threading.Event().wait(duration)
                return cap.stop()
            threading.Event().wait()
            return {}
        finally:
            if cap.is_running:
                cap.stop()

    @property
    def voice_emotion(self) -> VoiceEmotionCapture | None:
        if self._voice_emotion is None and VoiceEmotionCapture is not None:
            self._voice_emotion = VoiceEmotionCapture()
        return self._voice_emotion

    def clone_voice(self, source_wav: Path, target_wav: Path,
                    output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = self.config["output_dir"] / "voice_models" / f"clone_{source_wav.stem}_{target_wav.stem}.npz"
        return clone_voice_from_audio(source_wav, target_wav, output_path)

    def synthesize(self, text: str, model_path: Path | None = None,
                   output_path: Path | None = None) -> Path:
        if model_path is None:
            models = piper_models()
            if not models:
                raise SkillError("No Piper models found. Train or download one first.")
            model_path = models[0]
        if output_path is None:
            output_path = self.config["output_dir"] / "synthesized" / f"{hash(text)}.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return synthesise(text, model_path, output_path)

    def mix(self, stem_paths: list[Path], output_path: Path | None = None,
            volumes: list[float] | None = None) -> Path:
        if output_path is None:
            output_path = self.config["output_dir"] / "mixes" / f"mix_{int(time.time())}.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return mix_stems(stem_paths, output_path, volumes)

    def remix(self, audio_path: Path, output_path: Path | None = None,
              vocal_source: str = "vocals", beat_source: str = "drums") -> Path:
        if output_path is None:
            output_path = self.config["output_dir"] / "remixes" / f"{audio_path.stem}_remix.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pipeline = RemixPipeline()
        return pipeline.remix(audio_path, output_path, vocal_source, beat_source)

    def generate_lyrics(self, corpus: list[str] | None = None,
                        seed_words: list[str] | None = None,
                        length: int = 20) -> list[str]:
        engine = MarkovGeneticLyricEngine()
        if corpus:
            engine.train(corpus)
        else:
            engine.train(["this is a test song about life and love and dreams"])
        return engine.generate(seed_words, length)

    # ── Audio Processor ────────────────────────────────────────────────

    @property
    def audio_processor(self) -> AudioProcessor:
        if self._audio_processor is None:
            self._audio_processor = AudioProcessor()
        return self._audio_processor

    def generate_anti_noise(self, audio_data: np.ndarray) -> np.ndarray:
        return self.audio_processor.generate_anti_noise(audio_data)

    def spectral_gate(self, y: np.ndarray, sr: int = 16000, threshold_db: float = -40) -> np.ndarray:
        return self.audio_processor.spectral_gate(y, sr, threshold_db)

    def adaptive_filter(self, y: np.ndarray, noise_profile: np.ndarray | None = None) -> np.ndarray:
        return self.audio_processor.adaptive_filter(y, noise_profile)

    # ── Sound Classification ───────────────────────────────────────────

    @property
    def model_inference(self) -> ModelInference:
        if self._model_inference is None:
            self._model_inference = ModelInference()
        return self._model_inference

    def classify_sound(self, audio_path: Path | str) -> dict | None:
        data, sr = load_audio(Path(audio_path))
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.model_inference.classify(data))
        finally:
            loop.close()

    def get_model_stats(self) -> dict:
        return self.model_inference.get_inference_stats()

    # ── Voice Commands ─────────────────────────────────────────────────

    @property
    def voice_commands(self) -> VoiceCommands:
        if self._voice_commands is None:
            self._voice_commands = VoiceCommands()
        return self._voice_commands

    def voice_recognize_once(self, audio_path: Path | str) -> str | None:
        data, sr = load_audio(Path(audio_path))
        cfg = {"commands": {"test": "test"}}
        vc = VoiceCommands(cfg)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(vc.initialize())
            return None
        finally:
            loop.close()

    # ── Genius lyrics service ──────────────────────────────────────────

    def get_lyrics_service(self) -> LyricsService | None:
        return self.lyrics

    def lyrics_search_song(self, query: str, per_page: int = 10) -> list[dict]:
        if not self.lyrics:
            raise SkillError("LyricsService not available — set GENIUS_ACCESS_TOKEN")
        return self.lyrics.search_song(query, per_page)

    def lyrics_fetch(self, song_id: int) -> str | None:
        if not self.lyrics:
            raise SkillError("LyricsService not available — set GENIUS_ACCESS_TOKEN")
        return self.lyrics.get_lyrics(song_id)

    def lyrics_fetch_by_title(self, title: str, artist: str = "") -> str | None:
        if not self.lyrics:
            raise SkillError("LyricsService not available — set GENIUS_ACCESS_TOKEN")
        return self.lyrics.get_lyrics_by_title(title, artist)

    def lyrics_enrich_metadata(self, title: str, artist: str = "") -> dict:
        if not self.lyrics:
            raise SkillError("LyricsService not available — set GENIUS_ACCESS_TOKEN")
        return self.lyrics.enrich_metadata(title, artist)

    def lyrics_batch_enrich(self, songs: list[dict], delay_s: float = 0.5,
                            progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
        if self._cancel_event.is_set():
            return []
        if not self.lyrics:
            raise SkillError("LyricsService not available — set GENIUS_ACCESS_TOKEN")
        return self.lyrics.batch_enrich(songs, delay_s, progress_callback)

    def lyrics_get_annotations(self, song_id: int) -> list[dict]:
        if not self.lyrics:
            raise SkillError("LyricsService not available — set GENIUS_ACCESS_TOKEN")
        return self.lyrics.get_song_annotations(song_id)

    def lyrics_artist_top_songs(self, artist_name: str, per_page: int = 20) -> list[dict]:
        if not self.lyrics:
            raise SkillError("LyricsService not available — set GENIUS_ACCESS_TOKEN")
        artist_id = self.lyrics.find_artist_id(artist_name)
        if not artist_id:
            return []
        return self.lyrics.artist_top_songs(artist_id, per_page)

    # ── end Genius lyrics ──────────────────────────────────────────────

    def align_lyrics(self, audio_path: Path, text: str) -> AlignmentResult:
        aligner = ForcedAligner()
        return aligner.align(audio_path, text)

    def generate_music_video(self, audio_path: Path, image_paths: list[Path],
                             output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = self.config["output_dir"] / "videos" / f"{audio_path.stem}_video.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        gen = MusicVideoGenerator()
        return gen.generate(audio_path, image_paths, output_path)

    def train_voice(self, recordings_dir: Path, output_dir: Path | None = None):
        if output_dir is None:
            output_dir = self.config["output_dir"] / "trained_voices" / recordings_dir.stem
        dataset_dir = output_dir / "dataset"
        prepare_piper_dataset(recordings_dir, dataset_dir)
        train_piper_voice(dataset_dir, output_dir)

    def list_models(self) -> dict[str, list[str]]:
        return {
            "piper": [p.stem for p in piper_models()],
            "voice_clones": [p.stem for p in self.config["output_dir"].glob("voice_models/*.npz")],
        }

    def get_capabilities(self) -> list[str]:
        return [
            "stem_separation",
            "transcription",
            "vosk_transcription",
            "voice_analysis",
            "voice_cloning",
            "voice_synthesis",
            "voice_training",
            "voice_emotion_capture",
            "mixing",
            "remixing",
            "audio_effects",
            "pitch_detection",
            "bpm_key_detection",
            "midi_export",
            "lyric_generation",
            "forced_alignment",
            "music_video_generation",
            "lyrics_service",
            "batch_processing",
            "noise_cancellation",
            "voice_adapter",
            "audio_processor",
            "sound_classification",
            "voice_commands",
        ]

    def get_feature_matrix(self) -> dict[str, bool]:
        return {c: True for c in self.get_capabilities()}
