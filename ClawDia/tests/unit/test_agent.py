import json
from unittest.mock import MagicMock, patch

import pytest

from src.agent.client import LMStudioClient, LLMResponse
from src.agent.tools import Tool, ToolRegistry
from src.agent.prompts import SYSTEM_PROMPT, TOOL_SCHEMAS
from src.agent.loop import AgentLoop
from src.agent.skill import AgentSkill


class TestLMStudioClient:
    def test_response_no_tool_calls(self):
        client = LMStudioClient()
        mock_data = {
            "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        with patch.object(client, "_request", return_value=json.dumps(mock_data)):
            resp = client.chat([{"role": "user", "content": "hi"}])
            assert resp.content == "Hello!"
            assert resp.tool_calls == []

    def test_response_with_tool_calls(self):
        client = LMStudioClient()
        mock_data = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "test_tool", "arguments": '{"key": "val"}'},
                    }],
                },
                "finish_reason": "tool_calls",
            }],
        }
        with patch.object(client, "_request", return_value=json.dumps(mock_data)):
            resp = client.chat([{"role": "user", "content": "call tool"}])
            assert resp.content is None
            assert len(resp.tool_calls) == 1
            assert resp.tool_calls[0]["function"]["name"] == "test_tool"

    def test_response_error_handling(self):
        client = LMStudioClient()
        with patch.object(client, "_request", side_effect=Exception("connection refused")):
            resp = client.chat([{"role": "user", "content": "hi"}])
            assert resp.finish_reason == "error"

    def test_check_available_success(self):
        client = LMStudioClient()
        with patch.object(client, "_request", return_value="ok"):
            assert client.check_available() is True

    def test_check_available_failure(self):
        client = LMStudioClient()
        with patch.object(client, "_request", side_effect=Exception()):
            assert client.check_available() is False


class TestToolRegistry:
    def test_register_and_execute(self):
        registry = ToolRegistry()
        def handler(name: str) -> str:
            return f"Hello {name}"
        tool = Tool("greet", "Greets someone", {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }, handler)
        registry.register(tool)
        assert registry.get("greet") is tool
        result = registry.execute("greet", name="World")
        assert "Hello World" in result

    def test_unknown_tool(self):
        registry = ToolRegistry()
        result = registry.execute("nope")
        assert "Unknown tool" in result

    def test_schemas_output(self):
        registry = ToolRegistry()
        def handler(): pass
        registry.register(Tool("t1", "desc", {"type": "object", "properties": {}}, handler))
        schemas = registry.schemas()
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "t1"


class TestAgentLoop:
    def test_loop_direct_response(self):
        client = LMStudioClient()
        registry = ToolRegistry()
        loop = AgentLoop(client, registry)

        with patch.object(client, "chat", return_value=LLMResponse(content="Direct answer")):
            response, history = loop.run("hello")
            assert "Direct answer" in response

    def test_loop_tool_call_then_response(self):
        client = LMStudioClient()
        registry = ToolRegistry()

        call_count = [0]
        def mock_handler():
            return "tool result"
        registry.register(Tool("test_tool", "A test", {
            "type": "object", "properties": {}, "required": [],
        }, mock_handler))

        def mock_chat(messages, **kw):
            call_count[0] += 1
            if call_count[0] == 1:
                return LLMResponse(content=None, tool_calls=[{
                    "id": "c1", "type": "function",
                    "function": {"name": "test_tool", "arguments": {}},
                }], finish_reason="tool_calls")
            return LLMResponse(content="Final answer")

        loop = AgentLoop(client, registry)
        with patch.object(client, "chat", mock_chat):
            response, history = loop.run("do something")
            assert "Final answer" in response

    def test_loop_max_iterations(self):
        client = LMStudioClient()
        registry = ToolRegistry()
        registry.register(Tool("loop_tool", "looping", {
            "type": "object", "properties": {}, "required": [],
        }, lambda: "still going"))

        loop = AgentLoop(client, registry)

        def always_tool(messages, **kw):
            return LLMResponse(content=None, tool_calls=[{
                "id": "c1", "type": "function",
                "function": {"name": "loop_tool", "arguments": {}},
            }], finish_reason="tool_calls")

        with patch.object(client, "chat", always_tool):
            response, history = loop.run("loop forever")
            assert "max reasoning depth" in response


class TestAgentSkill:
    def test_skill_offline(self):
        skill = AgentSkill()
        result = skill.execute(message="hello")
        assert result["error"] is not None
        assert "offline" in result["response"].lower()

    def test_skill_reset(self):
        skill = AgentSkill()
        result = skill.reset()
        assert result["status"] == "conversation reset"
