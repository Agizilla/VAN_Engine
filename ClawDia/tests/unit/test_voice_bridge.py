from unittest.mock import MagicMock, patch

import pytest

from src.ui.app import ClawDiaApp


class TestVoiceAgentBridge:
    @pytest.fixture
    def app(self):
        a = ClawDiaApp()
        a._agent = None
        a.skills = []
        a._voice = MagicMock()
        return a

    def test_voice_mode_fallback_no_agent(self, app):
        """Without agent, voice mode falls back to keyword matching."""
        app._voice.warmup = MagicMock()
        app._voice.run = MagicMock()

        app._handle_voice_mode(None)

        call_args = app._voice.run.call_args
        on_command = call_args[0][0]

        result = on_command("hello")
        assert "Not sure how to do" in result

    def test_voice_mode_quit_command(self, app):
        app._voice.warmup = MagicMock()
        app._voice.run = MagicMock()

        app._handle_voice_mode(None)

        call_args = app._voice.run.call_args
        on_command = call_args[0][0]

        result = on_command("quit")
        assert "Logging off" in result

    def test_voice_mode_list_skills(self, app):
        app._voice.warmup = MagicMock()
        app._voice.run = MagicMock()

        from src.skills.base import BaseSkill
        mock_skill = MagicMock(spec=BaseSkill)
        mock_skill.name = "audio_transcribe"
        mock_skill.category = "audio"
        app.skills = [mock_skill]

        app._handle_voice_mode(None)
        call_args = app._voice.run.call_args
        on_command = call_args[0][0]

        result = on_command("list skills")
        assert "audio_transcribe" in result

    def test_voice_mode_with_agent(self, app):
        """When agent is available, route through agent."""
        app._voice.warmup = MagicMock()
        app._voice.run = MagicMock()

        mock_agent = MagicMock()
        mock_agent.ensure_loop.return_value = True
        mock_agent.execute.return_value = {"error": None, "response": "Hello from agent!"}
        app._agent = mock_agent

        app._handle_voice_mode(None)
        call_args = app._voice.run.call_args
        on_command = call_args[0][0]

        result = on_command("what's the weather")
        assert result == "Hello from agent!"
        mock_agent.execute.assert_called_once_with(message="what's the weather")

    def test_voice_mode_agent_error(self, app):
        app._voice.warmup = MagicMock()
        app._voice.run = MagicMock()

        mock_agent = MagicMock()
        mock_agent.ensure_loop.return_value = True
        mock_agent.execute.return_value = {"error": "LLM error", "response": ""}
        app._agent = mock_agent

        app._handle_voice_mode(None)
        call_args = app._voice.run.call_args
        on_command = call_args[0][0]

        result = on_command("hello")
        assert "Hit a snag" in result
        assert "LLM error" in result
