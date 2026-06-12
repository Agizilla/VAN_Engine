"""
psychoacousticSkill.py — Master Psychoacoustic Skill for Clawdia
Merged from: Mute (experimental wellness modules)

Categories: Ambient Soundscapes, REM Sleep Detection, Emotional Therapy,
            Emotional Release, Flavor Echo, Tear Trigger, Dream Induction
"""

__meta__ = {
    "name": "psychoacousticSkill.py",
    "description": "Master Psychoacoustic Skill for Clawdia — 4 experimental wellness modules merged from Mute. Handles circadian ambient soundscapes (FlavorEngine), REM sleep detection + lucid dream binaural triggers (DreamProcessor), audio-based grief/emotional distress detection (TherapyEngine), and emotional release assistance (TearTrigger).",
    "how_to": "from psychoacousticSkill import PsychoacousticSkill\nskill = PsychoacousticSkill()\nskill.get_ambient('ocean')\nskill.get_sleep_report()\nskill.get_morning_report()",
    "version": "2.0.0",
    "dateCreated": "2026-06-07",
    "dateLastModified": "2026-06-10",
    "countPublicMethods": 40,
    "countLineNumbers": 1100,
    "mergedProjects": ["Mute"],
    "update_list": [
        "2026-06-07 v1.0.0 — Initial extraction: 4 psychoacoustic modules from Mute project.",
        "2026-06-10 v2.0.0 — Volume normalization, cooldown between sessions, sounddevice playback, sample_rate validation, logging, class-level CONFIG with overrides"
    ]
}

from __future__ import annotations
import asyncio, json, logging, time, random
from pathlib import Path
from typing import Optional
from collections import deque

import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=Path(__file__).parent / "psychoacoustic.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

_PSY_EMO_DICT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'config', 'emotional_dictionary.json')
_PSY_EMOTIONAL_DICT = {}
if os.path.exists(_PSY_EMO_DICT_PATH):
    try:
        with open(_PSY_EMO_DICT_PATH, 'r') as f:
            _PSY_EMOTIONAL_DICT = json.load(f)
    except: pass

ROOT = Path(__file__).parent.resolve()


class SkillError(Exception):
    pass


class PsychoacousticConfig:
    CONFIG = {
        "sample_rate": 16000,
        "output_dir": ROOT / "outputs",
        "cooldown_seconds": 5.0,
        "volume_target_peak": 0.95,
    }

    def __init__(self, config_overrides: dict | None = None):
        self.CONFIG["output_dir"].mkdir(parents=True, exist_ok=True)
        if config_overrides:
            self.CONFIG = {**self.CONFIG, **config_overrides}


# ═══════════════════════════════════════════════════════════════════════════
#  FLAVOR ENGINE — Ambient Mood Enhancement (from Mute)
# ═══════════════════════════════════════════════════════════════════════════

class FlavorEngine(PsychoacousticConfig):
    AVAILABLE_FLAVORS = {
        "ocean": {"base_freq": 110, "amplitude": 0.05, "description": "Ocean waves"},
        "rain": {"base_freq": 200, "amplitude": 0.04, "description": "Gentle rain"},
        "fireplace": {"base_freq": 80, "amplitude": 0.06, "description": "Crackling fire"},
        "forest": {"base_freq": 150, "amplitude": 0.05, "description": "Forest ambiance"},
        "night": {"base_freq": 60, "amplitude": 0.03, "description": "Night sounds"},
        "neutral": {"base_freq": 0, "amplitude": 0, "description": "No flavor"},
    }

    def __init__(self, config_overrides: dict | None = None):
        super().__init__(config_overrides)
        self.current_flavor = "neutral"
        self.circadian_enabled = True
        self.active = False
        self.last_flavor_change: float | None = None

    def get_circadian_flavor(self) -> str:
        from datetime import datetime
        hour = datetime.now().hour
        if hour >= 23 or hour < 5:
            return "night"
        elif 5 <= hour < 9:
            return "forest"
        elif 9 <= hour < 17:
            return "ocean" if hour % 2 == 0 else "rain"
        else:
            return "fireplace"

    def set_flavor(self, flavor: str):
        if flavor not in self.AVAILABLE_FLAVORS:
            raise SkillError(f"Unknown flavor: {flavor}. Choose from {list(self.AVAILABLE_FLAVORS.keys())}")
        self.current_flavor = flavor
        self.last_flavor_change = time.time()
        logger.info(f"Flavor set to: {flavor}")

    def generate_ambient(self, duration_s: float = 0.1) -> np.ndarray:
        flavor_config = self.AVAILABLE_FLAVORS[self.current_flavor]
        sr = self.CONFIG.get("sample_rate", 16000)
        t = np.linspace(0, duration_s, int(sr * duration_s))
        base_freq = flavor_config["base_freq"]
        amplitude = flavor_config["amplitude"]

        if base_freq == 0:
            return np.zeros(len(t))

        if self.current_flavor == "ocean":
            wave = amplitude * np.sin(2 * np.pi * base_freq * 0.1 * t)
            noise = amplitude * 0.5 * np.random.randn(len(t))
            ambient = wave + noise
        elif self.current_flavor == "rain":
            noise = amplitude * np.random.randn(len(t))
            ambient = np.convolve(noise, np.ones(10) / 10, mode="same")
        elif self.current_flavor == "fireplace":
            noise = amplitude * np.random.randn(len(t)) ** 2
            if np.random.random() < 0.01:
                pop_idx = np.random.randint(0, len(t))
                noise[pop_idx] += amplitude * 2
            ambient = noise
        elif self.current_flavor == "forest":
            ambient = amplitude * np.sin(2 * np.pi * base_freq * t)
            ambient += amplitude * 0.3 * np.random.randn(len(t))
        elif self.current_flavor == "night":
            ambient = amplitude * np.sin(2 * np.pi * base_freq * t)
        else:
            ambient = np.zeros(len(t))

        peak = np.max(np.abs(ambient))
        if peak > 0:
            target = self.CONFIG.get("volume_target_peak", 0.95)
            ambient = ambient * (target / peak)

        return ambient.astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════
#  DREAM PROCESSOR — REM Detection + Lucid Triggers (from Mute)
# ═══════════════════════════════════════════════════════════════════════════

class DreamProcessor(PsychoacousticConfig):
    def __init__(self, config_overrides: dict | None = None):
        super().__init__(config_overrides)
        self.rem_detection_enabled = self.CONFIG.get("rem_detection_enabled", True)
        self.min_rem_duration = self.CONFIG.get("min_rem_duration_minutes", 5) * 60
        self.binaural_frequency = self.CONFIG.get("binaural_frequency", 6.0)
        self.trigger_volume = self.CONFIG.get("trigger_volume", 0.15)
        self.reality_check_interval = self.CONFIG.get("reality_check_interval_minutes", 20) * 60
        self.emergency_wake = self.CONFIG.get("emergency_wake_enabled", True)
        self.max_consecutive_triggers = 3

        self.sleep_started: float | None = None
        self.current_stage = "awake"
        self.rem_start_time: float | None = None
        self.last_reality_check: float | None = None
        self.breathing_buffer = deque(maxlen=300)
        self.movement_buffer = deque(maxlen=300)
        self.sleep_cycles: list[dict] = []
        self.current_cycle = 0
        self.rem_episodes = 0
        self.lucid_triggers_sent = 0
        self.consecutive_triggers = 0
        self._last_session_time: float | None = None

    def start_session(self):
        cooldown = self.CONFIG.get("cooldown_seconds", 5.0)
        if self._last_session_time and (time.time() - self._last_session_time < cooldown):
            raise SkillError(f"Cooldown active. Wait {cooldown - (time.time() - self._last_session_time):.1f}s")
        self.sleep_started = time.time()
        self.current_stage = "falling_asleep"
        self._last_session_time = time.time()
        logger.info("DreamProcessor session started")

    def process(self, audio_data: np.ndarray, classification: dict | None = None):
        sr = self.CONFIG["sample_rate"]
        breathing_rate = self._detect_breathing(audio_data, sr)
        movement_detected = self._detect_movement(audio_data, classification)
        if breathing_rate > 0:
            self.breathing_buffer.append(breathing_rate)
        self.movement_buffer.append(1 if movement_detected else 0)
        sleep_stage = self._detect_sleep_stage()
        if sleep_stage != self.current_stage:
            old_stage = self.current_stage
            self.current_stage = sleep_stage
            logger.info(f"Sleep stage change: {old_stage} -> {sleep_stage}")
            if sleep_stage == "rem":
                self.rem_start_time = time.time()
                self.rem_episodes += 1

    def _detect_breathing(self, audio_data: np.ndarray, sr: int) -> float:
        autocorr = np.correlate(audio_data, audio_data, mode="full")
        autocorr = autocorr[len(autocorr) // 2:]
        min_distance = int(sr * 1.0)
        peaks = []
        for i in range(min_distance, len(autocorr) - min_distance):
            if (autocorr[i] > autocorr[i - 1] and
                autocorr[i] > autocorr[i + 1] and
                autocorr[i] > 0.1 * np.max(autocorr)):
                peaks.append(i)
        if len(peaks) >= 2:
            avg_distance = np.mean(np.diff(peaks))
            rate_hz = sr / avg_distance
            return rate_hz * 60
        return 0

    def _detect_movement(self, audio_data: np.ndarray, classification: dict | None = None) -> bool:
        rms = np.sqrt(np.mean(audio_data ** 2))
        if rms > 0.3:
            return True
        if classification and classification.get("class") in ["mechanical_hum", "speech"]:
            return True
        return False

    def _detect_sleep_stage(self) -> str:
        if len(self.breathing_buffer) < 30:
            return "falling_asleep"
        breathing_var = np.var(list(self.breathing_buffer)[-30:])
        avg_breathing = np.mean(list(self.breathing_buffer)[-30:])
        movement_rate = np.mean(list(self.movement_buffer)[-30:])
        elapsed = time.time() - self.sleep_started if self.sleep_started else 0
        cycle_pos = (elapsed % 5400) / 5400 if self.sleep_started else 0
        if movement_rate > 0.3:
            return "awake"
        if elapsed < 300:
            return "falling_asleep"
        if cycle_pos > 0.7 and breathing_var > 5:
            return "rem"
        if breathing_var < 2 and movement_rate < 0.05:
            return "deep_sleep"
        return "light_sleep"

    def should_trigger_lucid(self) -> bool:
        if self.current_stage != "rem" or not self.rem_start_time:
            return False
        rem_duration = time.time() - self.rem_start_time
        if rem_duration < self.min_rem_duration:
            return False
        if self.last_reality_check:
            if time.time() - self.last_reality_check < self.reality_check_interval:
                return False
        if self.consecutive_triggers >= self.max_consecutive_triggers:
            return False
        return True

    def generate_binaural_beat(self, duration_s: float = 5.0) -> np.ndarray:
        sr = self.CONFIG["sample_rate"]
        t = np.linspace(0, duration_s, int(sr * duration_s))
        base_freq = 200
        left = np.sin(2 * np.pi * base_freq * t)
        right = np.sin(2 * np.pi * (base_freq + self.binaural_frequency) * t)
        binaural = np.column_stack([left, right])
        envelope = np.hanning(len(binaural))
        binaural = binaural * envelope[:, np.newaxis] * self.trigger_volume
        return binaural.astype(np.float32)

    def get_sleep_report(self) -> dict:
        if not self.sleep_started:
            return {}
        total = time.time() - self.sleep_started
        return {
            "total_sleep_time_hours": total / 3600,
            "rem_episodes": self.rem_episodes,
            "lucid_triggers_sent": self.lucid_triggers_sent,
            "current_stage": self.current_stage,
            "sleep_cycles_completed": int(total / 5400),
        }


# ═══════════════════════════════════════════════════════════════════════════
#  THERAPY ENGINE — Emotional Distress Detection (from Mute)
# ═══════════════════════════════════════════════════════════════════════════

class TherapyEngine(PsychoacousticConfig):
    @property
    def emotional_dictionary(self) -> dict:
        return _PSY_EMOTIONAL_DICT

    def get_facial_deltas(self, emotion_name: str) -> dict | None:
        if not _PSY_EMOTIONAL_DICT or 'emotions' not in _PSY_EMOTIONAL_DICT:
            return None
        emo = _PSY_EMOTIONAL_DICT['emotions']
        name_lower = emotion_name.lower()
        for key, val in emo.items():
            if key.lower() == name_lower:
                return val.get('deltas')
        return None

    def __init__(self, config_overrides: dict | None = None):
        super().__init__(config_overrides)
        self.grief_detection_enabled = self.CONFIG.get("grief_detection_enabled", True)
        self.empathy_volume = self.CONFIG.get("empathy_response_volume", 0.2)
        self.silence_period = self.CONFIG.get("silence_period_seconds", 30)
        self.morning_report_enabled = self.CONFIG.get("morning_report_enabled", True)
        self.emotional_log_retention = self.CONFIG.get("emotional_log_retention_days", 7)
        self.emotional_events: list[dict] = []
        self.last_grief_event: float | None = None
        self.last_response_time: float | None = None
        self.in_silence_period = False
        self.emotion_buffer = deque(maxlen=100)
        self.grief_events_detected = 0
        self.empathy_responses_sent = 0
        self.emotional_log: list[dict] = []
        self.sample_rate = self.CONFIG.get("sample_rate", 16000)
        self._last_session_time: float | None = None

    def detect_emotion(self, audio_data: np.ndarray, classification: dict | None = None) -> str:
        if classification:
            cls = classification.get("class", "")
            if cls == "baby_cry":
                logger.info("Emotion detected: crying (from classification)")
                return "crying"
            if cls == "laughter":
                logger.info("Emotion detected: laughter (from classification)")
                return "laughter"
        rms = np.sqrt(np.mean(audio_data ** 2))
        zcr = np.sum(np.abs(np.diff(np.sign(audio_data)))) / (2 * len(audio_data))
        fft = np.fft.rfft(audio_data)
        freqs = np.fft.rfftfreq(len(audio_data), 1 / self.sample_rate)
        magnitude = np.abs(fft)
        dom_freq = freqs[np.argmax(magnitude)]
        if rms > 0.15 and zcr > 0.05 and 200 < dom_freq < 800:
            if len(self.emotion_buffer) > 10:
                recent = [e for e in list(self.emotion_buffer)[-10:] if isinstance(e, float)]
                if recent and np.var(recent) > 0.01:
                    logger.info("Emotion detected: crying (from audio features)")
                    return "crying"
        if rms > 0.3 and len(self.emotion_buffer) > 5:
            recent = list(self.emotion_buffer)[-5:]
            if recent.count("crying") >= 3:
                logger.info("Emotion detected: distress")
                return "distress"
        return "neutral"

    def process(self, audio_data: np.ndarray, classification: dict | None = None) -> dict | None:
        try:
            fr = FlavorEngine()
            if self.sample_rate != fr.CONFIG.get("sample_rate"):
                logger.warning(f"Sample rate mismatch: TherapyEngine={self.sample_rate}, FlavorEngine={fr.CONFIG.get('sample_rate')}")
        except Exception:
            pass
        emotion = self.detect_emotion(audio_data, classification)
        self.emotion_buffer.append(emotion)
        if emotion in ("crying", "sobbing", "distress"):
            logger.info(f"Emotional event triggered: {emotion}")
            return self._handle_emotional_event(emotion, audio_data)
        return None

    def _handle_emotional_event(self, emotion: str, audio_data: np.ndarray) -> dict:
        cooldown = self.CONFIG.get("cooldown_seconds", 5.0)
        if self._last_session_time and (time.time() - self._last_session_time < cooldown):
            return {"error": f"Cooldown active. Wait {cooldown - (time.time() - self._last_session_time):.1f}s"}
        now = time.time()
        if self.in_silence_period and self.last_response_time:
            if now - self.last_response_time < self.silence_period:
                return None
            self.in_silence_period = False
        event = {"timestamp": now, "emotion": emotion, "intensity": float(np.sqrt(np.mean(audio_data ** 2)))}
        facial_deltas = self.get_facial_deltas(emotion)
        if facial_deltas:
            event['facial_deltas'] = facial_deltas
        self.emotional_events.append(event)
        self.grief_events_detected += 1
        response = self._generate_empathy_response(emotion)
        self.last_response_time = now
        self.in_silence_period = True
        self.emotional_log.append(event)
        self._last_session_time = now
        logger.info(f"Empathy response sent for emotion: {emotion}")
        return {"event": event, "response": response}

    def _generate_empathy_response(self, emotion: str) -> dict:
        self.empathy_responses_sent += 1
        duration = 3
        sr = self.sample_rate
        t = np.linspace(0, duration, int(sr * duration))
        fundamental = 396
        tone = (0.5 * np.sin(2 * np.pi * fundamental * t) +
                0.3 * np.sin(2 * np.pi * fundamental * 2 * t) +
                0.2 * np.sin(2 * np.pi * fundamental * 3 * t))
        envelope = np.hanning(len(tone))
        tone = tone * envelope * self.empathy_volume
        breathing_freq = 1 / 8
        breathing = 0.1 * np.sin(2 * np.pi * breathing_freq * t)
        response = tone + breathing
        return {
            "emotion": emotion,
            "frequency_hz": fundamental,
            "duration_s": duration,
            "waveform": response.astype(np.float32),
            "facial_delta_available": self.get_facial_deltas(emotion) is not None,
        }

    def generate_morning_report(self) -> dict:
        if not self.morning_report_enabled:
            return {}
        cutoff = time.time() - (8 * 3600)
        recent = [e for e in self.emotional_log if e.get("timestamp", 0) > cutoff]
        if not recent:
            return {"status": "peaceful", "message": "No emotional events detected. Hope you slept well!"}
        emotions = [e["emotion"] for e in recent]
        intensities = [e["intensity"] for e in recent]
        grief_count = emotions.count("crying") + emotions.count("distress")
        messages = {
            0: "Your night was peaceful. Take care of yourself today.",
            1: "I noticed some emotional moments last night. It's okay to feel your feelings.",
            2: "Last night was heavy. Processing grief takes time. Be gentle with yourself.",
        }
        if grief_count >= 6:
            msg = "Last night was very difficult. Please consider reaching out to someone you trust."
        else:
            msg = messages.get(grief_count, messages[2])
        return {
            "total_events": len(recent),
            "emotions": emotions,
            "average_intensity": float(np.mean(intensities)),
            "grief_events": grief_count,
            "status": "processed",
            "message": msg,
        }


# ═══════════════════════════════════════════════════════════════════════════
#  TEAR TRIGGER — Emotional Release Assistance (from Mute)
# ═══════════════════════════════════════════════════════════════════════════

class TearTrigger(PsychoacousticConfig):
    def __init__(self, config_overrides: dict | None = None):
        super().__init__(config_overrides)
        self.enabled = False
        self.max_intensity = self.CONFIG.get("max_intensity", 0.3)
        self.cooldown_hours = self.CONFIG.get("cooldown_hours", 24)
        self.max_duration_minutes = self.CONFIG.get("max_duration_minutes", 15)
        self.session_active = False
        self.session_start_time: float | None = None
        self.last_session_time: float | None = None
        self.suppression_score = 0.0
        self.suppression_threshold = self.CONFIG.get("suppression_threshold", 0.7)
        self.sessions_triggered = 0
        self.total_release_events = 0
        self.sample_rate = self.CONFIG.get("sample_rate", 16000)

    def detect_suppression(self, audio_data: np.ndarray, classification: dict | None = None) -> float:
        rms = np.sqrt(np.mean(audio_data ** 2))
        shallow_breathing = 0.3 if 0.05 < rms < 0.15 else 0.0
        zcr = np.sum(np.abs(np.diff(np.sign(audio_data)))) / (2 * len(audio_data))
        tension = min(zcr / 0.15, 1.0) * 0.4
        incongruence = 0.2
        return min(shallow_breathing + tension + incongruence, 1.0)

    def process(self, audio_data: np.ndarray, classification: dict | None = None) -> float:
        suppression = self.detect_suppression(audio_data, classification)
        alpha = 0.1
        self.suppression_score = alpha * suppression + (1 - alpha) * self.suppression_score
        return self.suppression_score

    def can_start_session(self) -> bool:
        if not self.enabled:
            return False
        if self.session_active:
            return False
        if self.suppression_score < self.suppression_threshold:
            return False
        if self.last_session_time:
            elapsed = time.time() - self.last_session_time
            if elapsed < self.cooldown_hours * 3600:
                return False
        return True

    def start_release_session(self) -> bool:
        if not self.can_start_session():
            return False
        cooldown = self.CONFIG.get("cooldown_seconds", 5.0)
        if self.last_session_time and (time.time() - self.last_session_time < cooldown):
            return False
        self.session_active = True
        self.session_start_time = time.time()
        self.sessions_triggered += 1
        logger.info("TearTrigger release session started")
        return True

    def generate_opening_phase(self, duration_s: float = 60.0) -> np.ndarray:
        sr = self.sample_rate
        t = np.linspace(0, duration_s, int(sr * duration_s))
        tone1 = 0.3 * np.sin(2 * np.pi * 396 * t)
        tone2 = 0.2 * np.sin(2 * np.pi * 417 * t)
        envelope = np.linspace(0, 1, len(t))
        return ((tone1 + tone2) * envelope * 0.1).astype(np.float32)

    def generate_deepening_phase(self, duration_s: float = 180.0) -> np.ndarray:
        sr = self.sample_rate
        t = np.linspace(0, duration_s, int(sr * duration_s))
        tone = 0.4 * np.sin(2 * np.pi * 528 * t)
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t)
        return (tone * envelope * 0.15).astype(np.float32)

    def generate_release_phase(self, duration_s: float = 120.0) -> np.ndarray:
        sr = self.sample_rate
        t = np.linspace(0, duration_s, int(sr * duration_s))
        tone = 0.6 * np.sin(2 * np.pi * 432 * t)
        noise = 0.3 * np.random.randn(len(t))
        envelope = 0.3 + 0.7 * np.sin(2 * np.pi * 0.15 * t) ** 2
        return ((tone + noise) * envelope * 0.2).astype(np.float32)

    def generate_integration_phase(self, duration_s: float = 120.0) -> np.ndarray:
        sr = self.sample_rate
        t = np.linspace(0, duration_s, int(sr * duration_s))
        tone = 0.2 * np.sin(2 * np.pi * 852 * t)
        envelope = np.linspace(1, 0, len(t))
        return (tone * envelope * 0.1).astype(np.float32)

    def end_session(self) -> dict | None:
        if not self.session_active:
            return None
        duration = time.time() - self.session_start_time
        self.session_active = False
        self.last_session_time = time.time()
        self.suppression_score = 0.0
        logger.info(f"TearTrigger session ended (duration: {duration/60:.1f}min)")
        return {
            "duration_minutes": duration / 60,
            "sessions_triggered": self.sessions_triggered,
            "total_release_events": self.total_release_events,
        }


# ═══════════════════════════════════════════════════════════════════════════
#  MASTER PSYCHOACOUSTIC SKILL — Clawdia integration
# ═══════════════════════════════════════════════════════════════════════════

class PsychoacousticSkill:
    def __init__(self, config_overrides: dict | None = None):
        self._config = PsychoacousticConfig(config_overrides)
        self._flavor: FlavorEngine | None = None
        self._dream: DreamProcessor | None = None
        self._therapy: TherapyEngine | None = None
        self._tear: TearTrigger | None = None

    def _play_audio(self, waveform: np.ndarray, sample_rate: int):
        try:
            import sounddevice as sd
            sd.play(waveform, sample_rate)
            logger.info(f"Playing audio via sounddevice ({len(waveform)} samples @ {sample_rate}Hz)")
        except ImportError:
            logger.warning("sounddevice not available for audio playback")

    # ── Flavor Engine ───────────────────────────────────────────────────

    @property
    def flavor(self) -> FlavorEngine:
        if self._flavor is None:
            self._flavor = FlavorEngine(self._config.CONFIG)
        return self._flavor

    def get_ambient(self, flavor: str = "neutral", duration_s: float = 0.1, play: bool = False) -> np.ndarray:
        self.flavor.set_flavor(flavor)
        waveform = self.flavor.generate_ambient(duration_s)
        if play:
            self._play_audio(waveform, self.flavor.CONFIG.get("sample_rate", 16000))
        return waveform

    def get_circadian_flavor(self) -> str:
        return self.flavor.get_circadian_flavor()

    # ── Dream Processor ────────────────────────────────────────────────

    @property
    def dream(self) -> DreamProcessor:
        if self._dream is None:
            self._dream = DreamProcessor(self._config.CONFIG)
        return self._dream

    def start_sleep_session(self):
        self.dream.start_session()
        logger.info("Sleep session started")

    def process_sleep_audio(self, audio_data: np.ndarray, classification: dict | None = None):
        self.dream.process(audio_data, classification)

    def get_sleep_report(self) -> dict:
        return self.dream.get_sleep_report()

    def generate_binaural_beat(self, duration_s: float = 5.0, play: bool = False) -> np.ndarray:
        waveform = self.dream.generate_binaural_beat(duration_s)
        if play:
            self._play_audio(waveform, self.dream.CONFIG.get("sample_rate", 16000))
        return waveform

    # ── Therapy Engine ─────────────────────────────────────────────────

    @property
    def therapy(self) -> TherapyEngine:
        if self._therapy is None:
            self._therapy = TherapyEngine(self._config.CONFIG)
        return self._therapy

    def detect_emotion(self, audio_data: np.ndarray, classification: dict | None = None) -> str:
        return self.therapy.detect_emotion(audio_data, classification)

    def process_therapy_audio(self, audio_data: np.ndarray, classification: dict | None = None) -> dict | None:
        return self.therapy.process(audio_data, classification)

    def get_morning_report(self) -> dict:
        return self.therapy.generate_morning_report()

    # ── Tear Trigger ───────────────────────────────────────────────────

    @property
    def tear(self) -> TearTrigger:
        if self._tear is None:
            self._tear = TearTrigger(self._config.CONFIG)
        return self._tear

    def enable_tear_trigger(self):
        self.tear.enabled = True
        logger.info("TearTrigger enabled")

    def process_tear_audio(self, audio_data: np.ndarray, classification: dict | None = None) -> float:
        return self.tear.process(audio_data, classification)

    def start_release_session(self) -> bool:
        return self.tear.start_release_session()

    def generate_opening(self, duration_s: float = 60.0, play: bool = False) -> np.ndarray:
        waveform = self.tear.generate_opening_phase(duration_s) if self.tear.session_active else np.array([])
        if play and len(waveform):
            self._play_audio(waveform, self.tear.sample_rate)
        return waveform

    def generate_deepening(self, duration_s: float = 180.0, play: bool = False) -> np.ndarray:
        waveform = self.tear.generate_deepening_phase(duration_s) if self.tear.session_active else np.array([])
        if play and len(waveform):
            self._play_audio(waveform, self.tear.sample_rate)
        return waveform

    def generate_release(self, duration_s: float = 120.0, play: bool = False) -> np.ndarray:
        waveform = self.tear.generate_release_phase(duration_s) if self.tear.session_active else np.array([])
        if play and len(waveform):
            self._play_audio(waveform, self.tear.sample_rate)
        return waveform

    def generate_integration(self, duration_s: float = 120.0, play: bool = False) -> np.ndarray:
        waveform = self.tear.generate_integration_phase(duration_s) if self.tear.session_active else np.array([])
        if play and len(waveform):
            self._play_audio(waveform, self.tear.sample_rate)
        return waveform

    def end_release_session(self) -> dict | None:
        return self.tear.end_session()

    # ── Meta ───────────────────────────────────────────────────────────

    def get_capabilities(self) -> list[str]:
        return [
            "ambient_soundscapes",
            "circadian_flavors",
            "rem_detection",
            "lucid_triggers",
            "sleep_reporting",
            "grief_detection",
            "empathetic_response",
            "morning_reports",
            "emotional_release",
            "suppression_detection",
        ]

    def get_feature_matrix(self) -> dict[str, bool]:
        return {c: True for c in self.get_capabilities()}

    def get_meta(self) -> dict:
        return __meta__
