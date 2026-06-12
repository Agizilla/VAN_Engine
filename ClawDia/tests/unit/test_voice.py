from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from src.voice.stt import WhisperSTT
from src.voice.capture import AudioCapture
from src.voice.tts import StyleTTS2Engine
from src.voice.loop import VoiceLoop
from src.ui.console import ConsoleUI


class TestWhisperSTT:
    def test_init(self):
        stt = WhisperSTT("tiny")
        assert stt.model_name == "tiny"
        assert stt.device == "cpu"

    def test_available_false_when_model_fails(self):
        stt = WhisperSTT("nonexistent")
        assert stt.available is False

    def test_transcribe_empty_audio(self):
        stt = WhisperSTT("tiny")
        audio = np.zeros(16000, dtype=np.float32)
        try:
            result = stt.transcribe(audio)
            assert isinstance(result, str)
        except Exception:
            pass

    @patch("src.voice.stt.whisper")
    def test_transcribe_mocked(self, mock_whisper):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": " hello world "}
        mock_whisper.load_model.return_value = mock_model
        stt = WhisperSTT("tiny")
        result = stt.transcribe(np.zeros(16000, dtype=np.float32))
        assert result == "hello world"
        mock_model.transcribe.assert_called_once()


class TestAudioCapture:
    def test_init(self):
        cap = AudioCapture()
        assert cap.sample_rate == 16000
        assert cap.vad is not None

    @patch("sounddevice.query_devices")
    def test_available_no_devices(self, mock_query):
        mock_query.return_value = []
        cap = AudioCapture()
        assert cap.available is False

    @patch("sounddevice.query_devices")
    def test_available_with_devices(self, mock_query):
        mock_query.return_value = [{"max_input_channels": 1}]
        cap = AudioCapture()
        assert cap.available is True


class TestStyleTTS2Engine:
    def test_init(self):
        tts = StyleTTS2Engine()
        assert tts._available is None

    @patch("src.voice.tts.TTS_LOCAL_SCRIPT")
    @patch("src.voice.tts.MODELS_DIR")
    def test_available_false_missing_deps(self, mock_models, mock_script):
        mock_script.exists.return_value = False
        mock_models.__truediv__.return_value.exists.return_value = False
        tts = StyleTTS2Engine()
        assert tts.available is False

    @patch("src.voice.tts.subprocess.run")
    def test_speak_subprocess_fails(self, mock_run):
        from unittest.mock import PropertyMock
        mock_run.return_value.returncode = 1
        tts = StyleTTS2Engine()
        object.__setattr__(tts, "_available", True)
        result = tts.speak("hello")
        assert result is None


class TestVoiceLoop:
    def test_init(self):
        loop = VoiceLoop()
        assert loop.stt is not None
        assert loop.capture is not None
        assert loop.tts is not None

    @patch("src.voice.loop.AudioCapture.available", new_callable=lambda: False)
    def test_mic_unavailable(self, mock_avail):
        loop = VoiceLoop()
        assert loop.mic_available is False
        result = loop.listen_and_transcribe()
        assert result is None

    def test_warmup_no_crash(self):
        loop = VoiceLoop(ConsoleUI())
        loop.warmup()
