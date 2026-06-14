"""TTS route — Kokoro ONNX neural voice via sherpa-onnx."""
import logging
import time
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger("tts")

router = APIRouter()

MODEL_DIR = Path(__file__).parent.parent / "tts_models" / "kokoro-int8-en-v0_19"

_tts = None
_audio_buffer = None  # holds last generated WAV bytes for replay


def _load_model():
    global _tts
    if _tts is not None:
        return _tts
    import sherpa_onnx

    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=str(MODEL_DIR / "model.int8.onnx"),
                voices=str(MODEL_DIR / "voices.bin"),
                tokens=str(MODEL_DIR / "tokens.txt"),
                data_dir=str(MODEL_DIR / "espeak-ng-data"),
            ),
            num_threads=4,
        ),
    )
    _tts = sherpa_onnx.OfflineTts(cfg)
    logger.info("Kokoro TTS model loaded (%d speakers)", _tts.num_speakers)
    return _tts


class SpeakRequest(BaseModel):
    text: str
    speaker_id: int = 0
    speed: float = 1.0
    pitch_shift: float = 0.0  # semitones, applied server-side via resampling


class SpeakResponse(BaseModel):
    sample_rate: int
    num_samples: int
    duration_sec: float


@router.post("/api/tts/speak")
async def speak(req: SpeakRequest):
    """Generate speech WAV from text using Kokoro ONNX model."""
    tts = _load_model()
    t0 = time.perf_counter()

    audio = tts.generate(req.text, sid=req.speaker_id, speed=req.speed)

    elapsed = time.perf_counter() - t0
    duration = len(audio.samples) / audio.sample_rate
    logger.info(
        "TTS: %.1fs audio generated in %.2fs (RTF=%.2f) — text=%r",
        duration, elapsed, elapsed / max(duration, 0.01),
        req.text[:60],
    )

    # Convert to 16-bit WAV bytes
    import numpy as np
    import soundfile as sf
    import io

    samples = np.array(audio.samples, dtype=np.float32)

    # Apply pitch shift if requested (via linear resampling, optional scipy dependency)
    if abs(req.pitch_shift) > 0.01:
        try:
            from scipy.signal import resample
            ratio = 2.0 ** (req.pitch_shift / 12.0)
            new_len = int(len(samples) / ratio)
            samples = resample(samples, new_len)
        except ImportError:
            logger.warning("scipy not available — skipping pitch shift of %.1f semitones", req.pitch_shift)

    buf = io.BytesIO()
    sf.write(buf, samples, audio.sample_rate, format="WAV")
    wav_bytes = buf.getvalue()

    global _audio_buffer
    _audio_buffer = wav_bytes

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={
            "X-Duration-Sec": f"{duration:.3f}",
            "X-Sample-Rate": str(audio.sample_rate),
            "X-Num-Samples": str(len(samples)),
        },
    )


@router.get("/api/tts/last")
async def last_audio():
    """Return the last generated WAV (for replay without re-synthesis)."""
    if _audio_buffer is None:
        return Response("No audio generated yet", status_code=404)
    return Response(content=_audio_buffer, media_type="audio/wav")
