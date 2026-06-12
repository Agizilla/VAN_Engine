import tiktoken
from typing import Optional


DEFAULT_ENCODING = "cl100k_base"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_RESERVE_TOKENS = 1024


class ContextWindow:
    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS, reserve_tokens: int = DEFAULT_RESERVE_TOKENS):
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self._tokenizer = tiktoken.get_encoding(DEFAULT_ENCODING)

    def available_tokens(self) -> int:
        return self.max_tokens - self.reserve_tokens

    def token_count(self, text: str) -> int:
        return len(self._tokenizer.encode(text))

    def fit_to_window(self, texts: list[str], max_tokens: Optional[int] = None) -> list[str]:
        limit = max_tokens or self.available_tokens()
        selected = []
        total = 0
        for t in texts:
            count = self.token_count(t)
            if total + count > limit:
                break
            selected.append(t)
            total += count
        return selected

    def truncate(self, text: str, max_tokens: Optional[int] = None) -> str:
        limit = max_tokens or self.available_tokens()
        tokens = self._tokenizer.encode(text)
        if len(tokens) <= limit:
            return text
        return self._tokenizer.decode(tokens[:limit])
