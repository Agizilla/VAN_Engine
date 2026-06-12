from unittest.mock import MagicMock, patch

import pytest

from src.agent.client import LLMResponse
from src.agent.loop import AUTO_RAG_PROMPT
from src.agent.loop import AgentLoop
from src.agent.tools import ToolRegistry
from src.skills.rag_skill import RAGSkill
from src.skills.base import SKILL_REGISTRY


class TestRAGSkill:
    def test_skill_registered(self):
        assert "RAG" in SKILL_REGISTRY
        assert SKILL_REGISTRY["RAG"]["category"] == "general"

    def test_search_no_query(self):
        skill = RAGSkill()
        result = skill.execute(action="search", query="")
        assert result["error"] is not None

    def test_search_no_engine(self):
        skill = RAGSkill()
        skill._engine = None
        with patch.object(skill, "_get_engine", return_value=None):
            result = skill.execute(action="search", query="test")
            assert "not available" in result["error"]

    def test_ingest_no_directory(self):
        skill = RAGSkill()
        result = skill.execute(action="ingest", directory="")
        assert result["error"] is not None

    def test_unknown_action(self):
        skill = RAGSkill()
        result = skill.execute(action="nonexistent")
        assert result["error"] is not None


class TestAgentLoopAutoRAG:
    def test_auto_rag_injects_context(self):
        client = MagicMock()
        registry = ToolRegistry()
        loop = AgentLoop(client, registry, auto_rag=True, rag_k=2)

        mock_rag = MagicMock()
        mock_rag.store.count.return_value = 5
        mock_rag.build_context.return_value = (
            [{"chunk_text": "Relevant doc about AI."}],
            "Relevant doc about AI.",
        )
        loop._rag = mock_rag

        client.chat.return_value = LLMResponse(content="Answer with context")

        response, history = loop.run("Tell me about AI")
        assert "Answer with context" in response

        call_args = client.chat.call_args
        system_msg = call_args[1]["messages"][0]
        assert system_msg["role"] == "system"
        assert "Relevant doc about AI." in system_msg["content"]
        assert AUTO_RAG_PROMPT.format(context="")[:20] in system_msg["content"]

    def test_auto_rag_empty_no_injection(self):
        client = MagicMock()
        registry = ToolRegistry()
        loop = AgentLoop(client, registry, auto_rag=True, rag_k=2)

        mock_rag = MagicMock()
        mock_rag.store.count.return_value = 0
        loop._rag = mock_rag

        client.chat.return_value = LLMResponse(content="Direct answer")

        response, history = loop.run("Hello")
        call_args = client.chat.call_args
        system_msg = call_args[1]["messages"][0]
        assert "Relevant documents:" not in system_msg["content"]

    def test_auto_rag_disabled(self):
        client = MagicMock()
        registry = ToolRegistry()
        loop = AgentLoop(client, registry, auto_rag=False)

        client.chat.return_value = LLMResponse(content="No RAG answer")

        response, history = loop.run("Test")
        call_args = client.chat.call_args
        system_msg = call_args[1]["messages"][0]
        assert "Relevant documents:" not in system_msg["content"]
