import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.skills.audio_skills import (
    AudioTranscribeSkill,
    AudioSplitSkill,
    AudioAnalyzeSkill,
)
from src.skills.base import SKILL_REGISTRY


def _mock_audio_modules():
    return patch.dict("sys.modules", {"librosa": MagicMock(), "soundfile": MagicMock()})


class TestAudioTranscribeSkill:
    def test_skill_registered(self):
        assert "audio_transcribe" in SKILL_REGISTRY

    def test_no_path(self):
        skill = AudioTranscribeSkill()
        result = skill.execute()
        assert result["error"] is not None

    @patch("src.skills.audio_skills._import_transcribe")
    def test_transcribe_action_no_librosa(self, mock_import):
        mock_import.return_value = (None, None, None, None, None)
        skill = AudioTranscribeSkill()
        result = skill.execute(action="transcribe", path="test.wav")
        assert "not available" in result["error"]

    @patch("src.skills.audio_skills._import_transcribe")
    def test_transcribe_action(self, mock_import):
        mock_transcription = MagicMock()
        mock_transcription.note_count = 42
        mock_transcription.duration = 30.0
        mock_transcription.bpm = 120.0
        mock_transcription.pitch_range = (48, 72)

        mock_format_table = MagicMock(return_value="note table")
        mock_import.return_value = (MagicMock, MagicMock, MagicMock(return_value=mock_transcription), MagicMock, mock_format_table)

        skill = AudioTranscribeSkill()
        result = skill.execute(action="transcribe", path="test.wav")
        assert result["error"] is None
        assert result["result"]["note_count"] == 42

    @patch("src.skills.audio_skills._import_transcribe")
    def test_export_action(self, mock_import):
        mock_transcription = MagicMock()
        mock_transcription.note_count = 10
        mock_transcription.duration = 20.0
        mock_transcription.bpm = 100.0

        mock_export = MagicMock(return_value="/out/test.mid")
        mock_import.return_value = (MagicMock, MagicMock, MagicMock(return_value=mock_transcription), mock_export, MagicMock)

        skill = AudioTranscribeSkill()
        result = skill.execute(action="export", path="test.wav", format="mid")
        assert result["error"] is None
        assert "output" in result["result"]

    def test_unknown_action(self):
        skill = AudioTranscribeSkill()
        result = skill.execute(action="nonexistent", path="test.wav")
        assert result["error"] is not None


class TestAudioSplitSkill:
    def test_skill_registered(self):
        assert "audio_split" in SKILL_REGISTRY

    def test_no_path(self):
        skill = AudioSplitSkill()
        result = skill.execute()
        assert result["error"] is not None

    def test_info_action(self):
        with _mock_audio_modules():
            import librosa
            librosa.load.return_value = (MagicMock(), 22050)
            librosa.load.return_value[0].__len__.return_value = 44100
            skill = AudioSplitSkill()
            result = skill.execute(action="info", path="test.wav")
            assert result["error"] is None
            assert result["result"]["duration"] == 2.0

    def test_trim_action(self):
        with _mock_audio_modules():
            import librosa
            y = np.zeros(44100)
            librosa.load.return_value = (y, 22050)
            skill = AudioSplitSkill()
            result = skill.execute(action="trim", path="test.wav", start=0, end=1)
            assert result["error"] is None

    def test_split_action(self):
        with _mock_audio_modules():
            import librosa
            y = np.zeros(88200)
            librosa.load.return_value = (y, 22050)
            skill = AudioSplitSkill()
            result = skill.execute(action="split", path="test.wav", segments=2)
            assert result["error"] is None
            assert len(result["result"]["outputs"]) == 2

    def test_detect_silence(self):
        with _mock_audio_modules():
            import librosa
            y = np.zeros(44100)
            y[11025:33075] = 0.5
            librosa.load.return_value = (y, 22050)
            librosa.feature.rms.return_value = np.array([[0.0] * 10 + [0.5] * 10 + [0.0] * 10])
            librosa.frames_to_time.side_effect = lambda x, **kw: np.array(range(len(x))) * 0.1

            skill = AudioSplitSkill()
            result = skill.execute(action="detect_silence", path="test.wav")
            assert result["error"] is None
            assert "silences" in result["result"]


class TestAudioAnalyzeSkill:
    def test_skill_registered(self):
        assert "audio_analyze" in SKILL_REGISTRY

    def test_no_path(self):
        skill = AudioAnalyzeSkill()
        result = skill.execute()
        assert result["error"] is not None

    def test_analyze_basic(self):
        with _mock_audio_modules():
            import librosa
            y = np.zeros(44100)
            librosa.load.return_value = (y, 22050)
            librosa.beat.beat_track.return_value = (120.0, np.array([0, 10, 20]))
            librosa.feature.spectral_centroid.return_value = np.array([[1000.0]])
            librosa.feature.rms.return_value = np.array([[0.1]])
            librosa.zero_crossings.return_value = np.array([False, True] * 22050)
            librosa.effects.hpss.return_value = (np.zeros(44100), np.zeros(44100))
            librosa.onset.onset_detect.return_value = np.array([10, 20, 30])
            librosa.frames_to_time.return_value = np.array([0.5, 1.0, 1.5])

            skill = AudioAnalyzeSkill()
            result = skill.execute(path="test.wav")
            assert result["error"] is None
            assert result["result"]["duration"] == 2.0
            assert result["result"]["tempo"] == 120.0
