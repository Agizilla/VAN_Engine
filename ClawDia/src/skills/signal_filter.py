import re

from .base import BaseSkill, register_skill, SkillContext

FILLER_TOKENS: set[str] = {
    "anyway", "dunno", "like", "um", "uh", "hmm", "ah", "oh", "well",
    "basically", "actually", "literally", "honestly", "sort of", "kind of",
    "i mean", "you know", "you see", "thing is", "so yeah", "right",
    "i guess", "i suppose", "just", "maybe", "perhaps", "probably",
    "totally", "definitely", "seriously", "obviously", "essentially",
    "anyways", "alright", "okay", "ok", "so", "yeah", "nah",
    "don't", "can't", "won't", "it's", "that's",
}

FILLER_CONTRACTIONS: dict[str, int] = {
    "don't": 2, "can't": 2, "won't": 2, "it's": 2, "that's": 2,
}

COMMON_ENGLISH_WORDS: set[str] = {
    "the", "is", "are", "was", "were", "have", "has", "been", "will",
    "would", "could", "should", "this", "that", "these", "those",
    "with", "from", "they", "what", "when", "where", "who", "how",
    "which", "their", "there", "your", "our", "its", "about", "into",
    "than", "then", "also", "very", "just", "because",
}


@register_skill("signal_filter", "intent")
class SignalFilterSkill(BaseSkill):
    name = "signal_filter"
    description = "High-pass conversational filter that strips filler tokens before intent parsing"
    author = "Ara Mascarra"
    version = "1.2.0"
    category = "intent"
    tags = ["filter", "clean", "signal", "filler"]

    _FILLER_RE = re.compile(
        "|".join(
            r"\b" + p + r"\b"
            for p in [
                "you know what i mean",
                "at the end of the day",
                "when it comes down to it",
                "the thing is",
                "i feel like",
                "i think",
                "i dunno",
            ]
        ),
        re.IGNORECASE,
    )

    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Raw user input text"},
            "remove_fillers": {"type": "boolean", "default": True},
            "collapse_whitespace": {"type": "boolean", "default": True},
            "preserve_quotes": {"type": "boolean", "default": False},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "clean_text": {"type": "string"},
            "removed_tokens": {"type": "array", "items": {"type": "string"}},
            "token_count_before": {"type": "integer"},
            "token_count_after": {"type": "integer"},
        },
    }

    def _is_english(self, text: str) -> bool:
        words = text.lower().split()
        if not words:
            return True
        common = sum(1 for w in words if w.strip(".,!?;:\"'()[]{}") in COMMON_ENGLISH_WORDS)
        return common / len(words) > 0.05

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "")
        remove_fillers = kwargs.get("remove_fillers", True)
        collapse = kwargs.get("collapse_whitespace", True)
        preserve_quotes = kwargs.get("preserve_quotes", False)

        if not text:
            return {"error": "No text provided", "result": None}

        tokens_before = len(text.split())
        removed: list[str] = []

        if remove_fillers:
            if not self._is_english(text):
                pass
            else:
                if preserve_quotes:
                    quotes: list[str] = []
                    def _save_quote(m):
                        quotes.append(m.group(0))
                        return f"\x00QUOTE{len(quotes)-1}\x00"
                    text = re.sub(r'"[^"]*"|\'[^\']*\'', _save_quote, text)

                matches = self._FILLER_RE.findall(text)
                removed.extend(matches)
                text = self._FILLER_RE.sub("", text)

                words = text.split()
                cleaned: list[str] = []
                for w in words:
                    stripped = w.strip(".,!?;:\"'()[]{}")
                    lower = stripped.lower()
                    if lower in FILLER_TOKENS:
                        removed.append(stripped)
                        if lower in FILLER_CONTRACTIONS:
                            removed.append(stripped)
                    else:
                        cleaned.append(w)
                text = " ".join(cleaned)

                if preserve_quotes:
                    for i, q in enumerate(quotes):
                        text = text.replace(f"\x00QUOTE{i}\x00", q)

        if collapse:
            text = re.sub(r"\s+", " ", text).strip()

        tokens_after = len(text.split()) if text else 0

        result = {
            "clean_text": text,
            "removed_tokens": removed,
            "token_count_before": tokens_before,
            "token_count_after": tokens_after,
        }
        return {"error": None, "result": result}

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, str):
            payload = {"text": payload}
        result = self.execute(**payload) if isinstance(payload, dict) else self.execute(text=str(payload))
        if result.get("error"):
            return False, result["error"]
        return True, result["result"]


@register_skill("signal_filter_stats", "intent")
class SignalFilterStatsSkill(BaseSkill):
    name = "signal_filter_stats"
    description = "Report filler token statistics across multiple utterances"
    category = "intent"
    required_libs = []

    def execute(self, **kwargs) -> dict:
        utterances = kwargs.get("utterances", [])
        if not utterances:
            return {"error": "No utterances provided", "result": None}

        total_tokens = 0
        total_fillers = 0
        top_fillers: dict[str, int] = {}
        avg_signal_ratio = 0.0

        for utt in utterances:
            filter_skill = SignalFilterSkill()
            r = filter_skill.execute(text=utt)
            if r.get("error"):
                continue
            data = r["result"]
            total_tokens += data["token_count_before"]
            total_fillers += len(data["removed_tokens"])
            for t in data["removed_tokens"]:
                tl = t.lower()
                top_fillers[tl] = top_fillers.get(tl, 0) + 1

        if total_tokens > 0:
            avg_signal_ratio = round((total_tokens - total_fillers) / total_tokens, 4)

        sorted_fillers = sorted(top_fillers.items(), key=lambda x: -x[1])

        return {"error": None, "result": {
            "utterance_count": len(utterances),
            "total_tokens": total_tokens,
            "total_fillers_removed": total_fillers,
            "avg_signal_ratio": avg_signal_ratio,
            "top_fillers": [{"token": t, "count": c} for t, c in sorted_fillers[:10]],
        }}
