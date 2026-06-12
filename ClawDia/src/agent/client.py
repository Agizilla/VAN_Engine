import json
from typing import Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError


class LLMResponse:
    def __init__(self, content: Optional[str], tool_calls: Optional[list[dict]] = None,
                 finish_reason: str = "stop", usage: Optional[dict] = None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.finish_reason = finish_reason
        self.usage = usage or {}


class LMStudioClient:
    def __init__(self, base_url: str = "http://localhost:1234/v1", timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, url_suffix: str, body: Optional[dict] = None) -> str:
        url = f"{self.base_url}/{url_suffix.lstrip('/')}"
        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, headers={"Content-Type": "application/json"} if body else {},
                      method="POST" if body else "GET")
        resp = urlopen(req, timeout=self.timeout)
        return resp.read().decode()

    def chat(self, messages: list[dict], model: str = "local",
             temperature: float = 0.7, max_tokens: int = 2048,
             tools: Optional[list[dict]] = None) -> LLMResponse:
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        try:
            raw = self._request("chat/completions", body)
            data = json.loads(raw)
        except URLError as e:
            return LLMResponse(
                content=f"[LLM connection error: {e.reason}]",
                finish_reason="error",
            )
        except Exception:
            return LLMResponse(
                content="[LLM returned invalid JSON]",
                finish_reason="error",
            )

        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content")
        raw_tool_calls = msg.get("tool_calls") or []
        finish = choice.get("finish_reason", "stop")
        usage = data.get("usage", {})

        tool_calls = []
        for tc in raw_tool_calls:
            fn = tc.get("function", {})
            try:
                arguments = json.loads(fn.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}
            tool_calls.append({
                "id": tc.get("id", ""),
                "type": "function",
                "function": {
                    "name": fn.get("name", ""),
                    "arguments": arguments,
                },
            })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish,
            usage=usage,
        )

    def check_available(self) -> bool:
        try:
            self._request("models")
            return True
        except Exception:
            return False
