from typing import Any

from ..skills.base import BaseSkill
from .client import LMStudioClient
from .tools import ToolRegistry
from .loop import AgentLoop


class AgentSkill(BaseSkill):
    def __init__(self):
        super().__init__()
        self.name = "Agent"
        self.description = "Intelligent agent with memory, tools, and reasoning. Can search documents, remember context, and execute other skills."
        self.category = "general"
        self._loop: AgentLoop | None = None
        self._history: list[dict] = []

    def _ensure_loop(self) -> AgentLoop | None:
        if self._loop is not None:
            return self._loop
        client = LMStudioClient()
        if not client.check_available():
            return None
        registry = ToolRegistry()
        self._loop = AgentLoop(client, registry, auto_rag=True, rag_k=3)
        return self._loop

    def ensure_loop(self) -> AgentLoop | None:
        return self._ensure_loop()

    def execute(self, **kwargs: Any) -> dict:
        message = kwargs.get("message", "")
        if not message:
            return {"error": "No message provided", "response": "", "history": []}

        loop = self._ensure_loop()
        if loop is None:
            return {
                "error": "LM Studio not available",
                "response": "ClawDia's brain is offline. Start LM Studio and load a model, then try again.",
                "history": [],
            }

        response, self._history = loop.run(message, self._history)
        return {
            "error": None,
            "response": response,
            "history": self._history,
        }

    def reset(self):
        self._history = []
        return {"status": "conversation reset"}
