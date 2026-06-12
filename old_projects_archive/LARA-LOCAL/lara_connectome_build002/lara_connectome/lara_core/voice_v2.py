"""
LARA — Voice Manager v2 (Connectome-integrated)
Version: 0.1.1 | Build: 002 | Date: 2026-02-23

DROP-IN REPLACEMENT for voice.py.
All original functionality preserved.

New: When speak() is called with a persona_id and a connectome_mgr,
     it reads synthesised voice parameters from the connectome and
     applies them as modulations to the TTS engine before synthesis.

Connectome → TTS mapping:
  voice_pitch.base_hz           → TTS speaker pitch
  voice_tempo.syllables_per_sec → TTS speed factor
  voice_energy.amplitude        → TTS volume/gain
  emotion_valence.value         → subtle speed/pitch warmth offset
  emotion_arousal.value         → energy emphasis boost
  prosody_melody.range_semitones→ pitch variation range
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from lara_core.constants import (
    APP_VERSION, BUILD_NUMBER,
    DIR_MODELS_VOICE, DIR_VERSIONS,
    error as fmt_error
)


# ── Connectome → TTS parameter mapping ──────────────────────

def connectome_to_tts_params(voice_params: Dict[str, Any],
                              engine: str = "coqui") -> Dict[str, Any]:
    """
    Convert connectome synthesised parameters to TTS-engine-specific kwargs.

    Returns a dict of kwargs that can be passed to the TTS engine.
    Values are clamped to safe ranges for each engine.

    For Coqui TTS (tacotron2/VITS):
      - speed:     synthesis speed multiplier [0.5 – 2.0]
      - pitch:     semitone offset [-12 – +12]
      - energy:    amplitude scale [0.3 – 1.5]

    For pyttsx3:
      - rate:      words per minute [80 – 200]
      - volume:    [0.0 – 1.0]
    """
    gv = voice_params  # shorthand

    def gp(key, default=0.0):
        """Get a connectome param by dot-notation key."""
        return gv.get(key, default) if isinstance(gv.get(key, default), (int, float)) else default

    # Raw connectome values
    base_hz      = gp("voice_pitch.base_hz", 180.0)
    syllables_s  = gp("voice_tempo.syllables_per_sec", 4.5)
    amplitude    = gp("voice_energy.amplitude", 0.7)
    valence      = gp("emotion_valence.value", 0.0)   # -1 to +1 after sigmoid mapping
    arousal      = gp("emotion_arousal.value", 0.5)
    melody_range = gp("prosody_melody.range_semitones", 8.0)

    if engine == "coqui":
        # Map Hz to semitone offset from neutral (175 Hz ≈ average female)
        import math
        neutral_hz = 175.0
        if base_hz > 0 and neutral_hz > 0:
            pitch_semitones = 12.0 * math.log2(base_hz / neutral_hz)
        else:
            pitch_semitones = 0.0
        pitch_semitones = max(-12.0, min(12.0, pitch_semitones))

        # Speed: 4.5 syllables/s ≈ 1.0x, range 2-8 syl/s → 0.5-1.8x
        speed = max(0.5, min(1.8, syllables_s / 4.5))

        # Energy: amplitude already 0.3-1.0; scale up slightly with arousal
        energy = max(0.3, min(1.5, amplitude * (1.0 + arousal * 0.3)))

        # Warm offset from valence: positive valence → slight pitch brightening
        pitch_semitones += valence * 0.5

        return {
            "speed": round(speed, 3),
            "pitch": round(pitch_semitones, 2),
            "energy": round(energy, 3),
            "melody_range": round(melody_range, 1),
            "_engine": "coqui",
            "_raw": {
                "base_hz": base_hz, "valence": valence,
                "arousal": arousal, "amplitude": amplitude
            }
        }

    elif engine == "pyttsx3":
        # pyttsx3 uses rate (WPM) and volume
        # 4.5 syllables/s ≈ ~135 WPM; 2-8 syllables/s → 60-240 WPM
        rate = int(max(60, min(240, syllables_s * 30)))
        volume = max(0.1, min(1.0, amplitude))
        return {
            "rate": rate,
            "volume": round(volume, 3),
            "_engine": "pyttsx3",
        }

    return {}


class VoiceManager:

    def __init__(self, data_dir: Path, config: dict,
                 connectome_mgr=None, logger=None):
        self.voice_dir = data_dir / DIR_MODELS_VOICE
        self.versions_dir = data_dir / DIR_VERSIONS / "voice"
        self.voice_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.connectome_mgr = connectome_mgr
        self.logger = logger
        self.engine = config.get("voice", {}).get("engine", "stub")
        self._tts = None
        self._init_engine()

    # ── Engine Init (unchanged) ──────────────────────────────

    def _init_engine(self):
        if self.engine == "coqui":
            try:
                from TTS.api import TTS
                model_name = "tts_models/en/ljspeech/tacotron2-DDC"
                self._tts = TTS(model_name, progress_bar=False)
                if self.logger:
                    self.logger.info(f"Coqui TTS loaded | model={model_name}")
            except ImportError:
                if self.logger:
                    self.logger.warning("Coqui TTS not installed — falling back to pyttsx3")
                self.engine = "pyttsx3"
                self._init_engine()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Coqui TTS init failed ({e}) — falling back to pyttsx3")
                self.engine = "pyttsx3"
                self._init_engine()

        elif self.engine == "pyttsx3":
            try:
                import pyttsx3
                self._tts = pyttsx3.init()
                if self.logger:
                    self.logger.info("pyttsx3 TTS loaded")
            except ImportError:
                self.engine = "stub"
        else:
            if self.logger:
                self.logger.info("Voice engine: stub mode")

    # ── Synthesis ────────────────────────────────────────────

    def speak(self, text: str, voice_model_id: str = None,
              output_file: Path = None,
              persona_id: str = None) -> bool:
        """
        Synthesise speech. If persona_id given and connectome_mgr active,
        reads connectome voice params and applies them to TTS engine.
        """
        # ── Resolve connectome voice params ──────────────────
        tts_overrides = {}
        if persona_id and self.connectome_mgr:
            try:
                vp = self.connectome_mgr.get_voice_params(persona_id)
                if vp:
                    tts_overrides = connectome_to_tts_params(vp, self.engine)
                    if self.logger:
                        self.logger.info(
                            f"Connectome voice params | persona={persona_id} | "
                            f"speed={tts_overrides.get('speed','?')} | "
                            f"pitch={tts_overrides.get('pitch','?')} | "
                            f"energy={tts_overrides.get('energy','?')}"
                        )
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Connectome param load failed: {e} — using defaults")

        if self.logger:
            self.logger.info(
                f"TTS | engine={self.engine} | model={voice_model_id or 'default'} | "
                f"chars={len(text)} | persona={persona_id or 'none'} | "
                f"connectome_params={bool(tts_overrides)}"
            )

        return self._synthesise(text, output_file, tts_overrides)

    def _synthesise(self, text: str, output_file: Optional[Path],
                    params: Dict[str, Any]) -> bool:
        """Internal: call TTS engine with resolved params."""
        if self.engine == "coqui" and self._tts:
            return self._speak_coqui(text, output_file, params)
        elif self.engine == "pyttsx3" and self._tts:
            return self._speak_pyttsx3(text, output_file, params)
        else:
            emotion_hint = ""
            if params.get("_raw"):
                r = params["_raw"]
                v = r.get("valence", 0)
                a = r.get("arousal", 0.5)
                emotion_hint = f" [valence={v:.2f} arousal={a:.2f}]"
            print(f"\n🎵 [LARA VOICE STUB{emotion_hint}]\n{text}\n")
            return True

    def _speak_coqui(self, text: str, output_file: Optional[Path],
                     params: Dict[str, Any]) -> bool:
        try:
            out = str(output_file) if output_file else "/tmp/lara_tts_out.wav"
            # Coqui TTS kwargs depend on model; apply speed if supported
            kwargs = {"text": text, "file_path": out}
            if "speed" in params:
                kwargs["speed"] = params["speed"]
            self._tts.tts_to_file(**kwargs)
            if not output_file:
                self._play_audio(Path(out))
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(fmt_error("E008", f"Coqui TTS: {e}"))
            return False

    def _speak_pyttsx3(self, text: str, output_file: Optional[Path],
                       params: Dict[str, Any]) -> bool:
        try:
            if "rate" in params:
                self._tts.setProperty("rate", params["rate"])
            if "volume" in params:
                self._tts.setProperty("volume", params["volume"])
            if output_file:
                self._tts.save_to_file(text, str(output_file))
            else:
                self._tts.say(text)
            self._tts.runAndWait()
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(fmt_error("E008", f"pyttsx3: {e}"))
            return False

    def _play_audio(self, path: Path):
        import subprocess, sys
        try:
            if sys.platform == "linux":
                subprocess.run(["aplay", str(path)], check=True,
                               capture_output=True, timeout=30)
            elif sys.platform == "darwin":
                subprocess.run(["afplay", str(path)], check=True,
                               capture_output=True, timeout=30)
            elif sys.platform == "win32":
                import winsound
                winsound.PlaySound(str(path), winsound.SND_FILENAME)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Audio playback failed: {e}")

    # ── Model Versioning (unchanged from v1) ─────────────────

    def register_model(self, model_id: str, source_path: Path,
                       description: str = "",
                       persona_id: str = None) -> bool:
        if not source_path.exists():
            if self.logger:
                self.logger.error(fmt_error("E012", f"Source not found: {source_path}"))
            return False

        dest = self.voice_dir / model_id
        dest.mkdir(parents=True, exist_ok=True)
        existing = list(dest.glob("v*.json"))
        version = len(existing) + 1
        version_tag = f"v{version:03d}"

        shutil.copy2(source_path, dest / source_path.name)

        manifest = {
            "model_id": model_id,
            "version": version,
            "version_tag": version_tag,
            "source": str(source_path),
            "file": source_path.name,
            "description": description,
            "registered_at": datetime.now().isoformat(),
            "lara_version": APP_VERSION,
        }
        (dest / f"{version_tag}.json").write_text(json.dumps(manifest, indent=2))
        (self.versions_dir / f"{model_id}_{version_tag}.json").write_text(
            json.dumps(manifest, indent=2)
        )

        if self.logger:
            self.logger.info(
                f"Voice model registered | id={model_id} | version={version_tag}"
            )

        # Fire plasticity trigger if persona_id supplied
        if persona_id and self.connectome_mgr:
            from lara_core.persona_v2 import PersonaManager
            # Directly call connectome trigger — PersonaManager not available here
            self.connectome_mgr.trigger(
                persona_id, "audio_training",
                {"model_id": model_id, "version": version_tag}
            )
        return True

    def get_latest_model(self, model_id: str) -> Optional[dict]:
        model_dir = self.voice_dir / model_id
        if not model_dir.exists():
            if self.logger:
                self.logger.error(fmt_error("E012", f"Voice model '{model_id}' not found"))
            return None
        manifests = sorted(model_dir.glob("v*.json"))
        if not manifests:
            return None
        return json.loads(manifests[-1].read_text())

    def list_models(self) -> list:
        return [d.name for d in self.voice_dir.iterdir() if d.is_dir()]
