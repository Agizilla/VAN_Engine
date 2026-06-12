from typing import Any, Callable, Optional


class Tool:
    def __init__(self, name: str, description: str, parameters: dict,
                 handler: Callable[..., str]):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def execute(self, **kwargs) -> str:
        try:
            result = self.handler(**kwargs)
            return str(result)
        except Exception as e:
            return f"[Error executing {self.name}: {e}]"


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def schemas(self) -> list[dict]:
        return [t.schema() for t in self._tools.values()]

    def execute(self, tool_name: str, **kwargs) -> str:
        tool = self.get(tool_name)
        if tool is None:
            return f"[Unknown tool: {tool_name}]"
        return tool.execute(**kwargs)
