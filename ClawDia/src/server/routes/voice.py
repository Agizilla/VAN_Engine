from fastapi import APIRouter

from ...voice.stt import WhisperSTT
from ...voice.capture import AudioCapture
from ...voice.tts import StyleTTS2Engine


router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.get("/status")
def status():
    stt_ok = WhisperSTT("base").available
    mic_ok = AudioCapture().available
    tts_ok = StyleTTS2Engine().available
    return {"stt_available": stt_ok, "mic_available": mic_ok, "tts_available": tts_ok}
