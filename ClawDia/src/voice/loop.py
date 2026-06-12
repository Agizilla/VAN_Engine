import time
from typing import Optional, Callable

import numpy as np

from .stt import WhisperSTT
from .capture import AudioCapture
from .tts import StyleTTS2Engine, PiperTSEngine
from ..ui.console import ConsoleUI


class VoiceLoop:
    def __init__(self, ui: Optional[ConsoleUI] = None):
        self.ui = ui or ConsoleUI()
        self.stt = WhisperSTT("base")
        self.capture = AudioCapture()
        self.tts = StyleTTS2Engine()
        self.piper = PiperTSEngine()
        self._running = False

    @property
    def mic_available(self) -> bool:
        return self.capture.available

    def warmup(self):
        self.ui.info("Warming up Whisper STT...")
        try:
            self.stt._load_model()
            self.ui.success("Whisper loaded")
        except Exception as e:
            self.ui.warning(f"Whisper unavailable: {e}")

        tts_ready = []
        if self.tts.available:
            tts_ready.append("StyleTTS2")
        if self.piper.available:
            tts_ready.append("Piper (Amy)")
        if tts_ready:
            self.ui.success(f"TTS ready: {', '.join(tts_ready)}")
        else:
            self.ui.info("TTS not available — using SAPI fallback")

        if self.mic_available:
            self.ui.success("Microphone detected")
        else:
            self.ui.warning("No microphone — keyboard input only")

    def listen_and_transcribe(self, timeout: float = 30.0) -> Optional[str]:
        if not self.mic_available:
            return None

        self.ui.info("Listening... (speak now)")
        audio = self.capture.record_until_silence(max_duration=timeout)
        if audio is None:
            self.ui.info("No speech detected")
            return None

        self.ui.info("Transcribing...")
        text = self.stt.transcribe(audio)
        return text

    def speak(self, text: str, use_piper: bool = False) -> bool:
        if use_piper and self.piper.available:
            return self.piper.play(text)
        if self.tts.available:
            path = self.tts.speak(text)
            if path:
                return self._play_audio(path)
        if self.piper.available:
            return self.piper.play(text)
        return self.tts.speak_sapi(text)

    def _play_audio(self, path: str) -> bool:
        try:
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
        except Exception:
            return False

    def run(self, on_command: Callable[[str], Optional[str]], keyboard_input_fn: Callable):
        self._running = True
        while self._running:
            text = self.listen_and_transcribe()
            if text:
                self.ui.echo(f"[dim]You:[/dim] {text}")
                response = on_command(text)
                if response:
                    self.speak(response)
            else:
                self.ui.divider()
                text = keyboard_input_fn()
                if text is None:
                    break
                response = on_command(text)
                if response:
                    self.ui.echo(response)

    def stop(self):
        self._running = False
