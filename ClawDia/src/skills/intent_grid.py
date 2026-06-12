import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_INTENT_GRID_AXES_PATH = Path(__file__).resolve().parent / "intent_grid_axes.json"

GRID_AXES_HARDCODED = {
    "x": {
        "create": ["make", "build", "generate", "create", "write", "new", "spawn", "forge", "produce", "construct"],
        "read": ["read", "load", "open", "get", "fetch", "retrieve", "list", "show", "display", "view"],
        "update": ["update", "edit", "modify", "change", "patch", "set", "adjust", "rename", "rewrite"],
        "delete": ["delete", "remove", "clear", "erase", "destroy", "drop", "purge", "unlink"],
        "query": ["query", "search", "find", "lookup", "count", "check", "scan", "inspect", "examine"],
        "analyze": ["analyze", "detect", "measure", "examine", "study", "profile", "benchmark", "infer"],
        "transform": ["transform", "convert", "translate", "transcode", "reformat", "map", "parse"],
        "communicate": ["send", "speak", "say", "tell", "notify", "alert", "message", "broadcast", "announce"],
        "monitor": ["monitor", "watch", "track", "follow", "observe", "listen", "tail", "subscribe"],
        "orchestrate": ["orchestrate", "coordinate", "manage", "schedule", "chain", "pipeline", "sequence"],
    },
    "y": {
        "audio": ["audio", "sound", "music", "song", "voice", "speech", "mic", "microphone", "record"],
        "text": ["text", "string", "sentence", "word", "document", "paragraph", "line", "content"],
        "filesystem": ["file", "directory", "folder", "path", "fs", "drive", "disk", "storage", "archive"],
        "network": ["network", "url", "http", "web", "api", "endpoint", "socket", "request", "ip"],
        "system": ["system", "process", "service", "daemon", "task", "thread", "os", "kernel", "runtime"],
        "data": ["data", "json", "csv", "database", "db", "record", "row", "table", "dataset", "corpus"],
        "code": ["code", "function", "class", "module", "import", "script", "source", "repo", "syntax"],
        "image": ["image", "photo", "picture", "frame", "video", "visual", "diagram", "chart", "graphic"],
        "time": ["time", "date", "clock", "schedule", "timer", "deadline", "timestamp", "chrono", "delay"],
    },
    "z": {
        "count": ["count", "how many", "total", "number of", "numerous", "frequency", "tally"],
        "filter": ["filter", "match", "only", "except", "ignore", "exclude", "include", "select", "pick"],
        "search": ["search", "find", "locate", "lookup", "discover", "where", "which", "index"],
        "sort": ["sort", "order", "rank", "arrange", "sort by", "sorted", "ascending", "descending"],
        "generate": ["generate", "produce", "output", "render", "emit", "yield", "create"],
        "validate": ["validate", "verify", "check", "test", "assert", "confirm", "ensure", "lint"],
        "convert": ["convert", "as", "to", "export", "import", "reformat", "encode", "decode"],
        "summarize": ["summarize", "overview", "brief", "digest", "summary", "recap", "condense"],
        "compare": ["compare", "diff", "versus", "vs", "contrast", "match", "similar", "merge"],
        "notify": ["notify", "alert", "warn", "ping", "callback", "webhook", "trigger"],
    },
}


def _load_grid_axes() -> dict:
    if _INTENT_GRID_AXES_PATH.exists():
        try:
            data = json.loads(_INTENT_GRID_AXES_PATH.read_text(encoding="utf-8"))
            logger.info(f"Loaded GRID_AXES from {_INTENT_GRID_AXES_PATH}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load {_INTENT_GRID_AXES_PATH}: {e}, using hardcoded")
    return dict(GRID_AXES_HARDCODED)


GRID_AXES = _load_grid_axes()

ALL_SYNONYMS: dict[str, list[str]] = {}
for axis_name, categories in GRID_AXES.items():
    for cat_name, synonyms in categories.items():
        for syn in synonyms:
            key = syn.lower()
            if key not in ALL_SYNONYMS:
                ALL_SYNONYMS[key] = []
            ALL_SYNONYMS[key].append(f"{axis_name}:{cat_name}")

# ── Lemmatization ──────────────────────────────────────────────────

_has_nltk = False
_has_spacy = False
_nlp = None

try:
    from nltk.stem import WordNetLemmatizer
    _lemmatizer = WordNetLemmatizer()
    _has_nltk = True
except ImportError:
    _lemmatizer = None
    try:
        import spacy as _spacy_mod
        _nlp = _spacy_mod.load("en_core_web_sm", disable=["parser", "ner"])
        _has_spacy = True
    except Exception:
        pass


def _lemma(word: str) -> str:
    if _has_nltk and _lemmatizer:
        return _lemmatizer.lemmatize(word)
    if _has_spacy and _nlp:
        doc = _nlp(word)
        if doc:
            return doc[0].lemma_
    return _simple_stem(word)


# ── Negation detection ─────────────────────────────────────────────

_NEGATION_WORDS = {"not", "without", "no", "never", "n't", "cannot"}


def _has_negation(tokens: list[str], idx: int) -> bool:
    if idx > 0 and tokens[idx - 1] in _NEGATION_WORDS:
        return True
    if idx > 1 and tokens[idx - 2] in _NEGATION_WORDS:
        return True
    return False


# ── Stemming (fallback) ────────────────────────────────────────────

def _simple_stem(word: str) -> str:
    if len(word) <= 3:
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ves"):
        return word[:-3] + "f"
    if word.endswith("s") and not word.endswith("ss") and len(word) > 4:
        base = word[:-1]
        if len(base) >= 2:
            return base
    if word.endswith("ing") and len(word) > 5:
        return word[:-3]
    return word


def tokenize(text: str) -> list[str]:
    import re
    raw_tokens = re.findall(r"[a-zA-Z+#]+", text.lower())
    tokens = []
    for t in raw_tokens:
        tokens.append(t)
        stemmed = _lemma(t)
        if stemmed != t:
            tokens.append(stemmed)
    return tokens


def map_intent(text: str) -> dict:
    tokens = tokenize(text)
    scores = {"x": {}, "y": {}, "z": {}}
    max_possible = {"x": 0, "y": 0, "z": 0}

    for token in tokens:
        if token in ALL_SYNONYMS:
            for tag in ALL_SYNONYMS[token]:
                axis, cat = tag.split(":", 1)
                scores[axis][cat] = scores[axis].get(cat, 0) + 1
                max_possible[axis] += 1

    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]} {tokens[i + 1]}"
        if bigram in ALL_SYNONYMS:
            for tag in ALL_SYNONYMS[bigram]:
                axis, cat = tag.split(":", 1)
                scores[axis][cat] = scores[axis].get(cat, 0) + 2
                max_possible[axis] += 2

    # Negation detection: if NEGATION_WORD found adjacent to a keyword, flip that category score
    for axis_name in scores:
        for cat in list(scores[axis_name]):
            for i, token in enumerate(tokens):
                if token in GRID_AXES.get(axis_name, {}).get(cat, []):
                    if _has_negation(tokens, i):
                        scores[axis_name][cat] = -scores[axis_name][cat]

    result = {}
    for axis in ["x", "y", "z"]:
        if scores[axis]:
            best = max(scores[axis], key=scores[axis].get)
            raw_score = scores[axis][best]
            norm_score = raw_score / max_possible[axis] if max_possible[axis] > 0 else 0
            result[axis] = {"category": best, "score": norm_score}
        else:
            result[axis] = {"category": "unknown", "score": 0}

    result["raw_tokens"] = tokens
    result["score_summary"] = scores
    return result


def grid_to_label(grid: dict) -> str:
    x = grid.get("x", {}).get("category", "?")
    y = grid.get("y", {}).get("category", "?")
    z = grid.get("z", {}).get("category", "?")
    return f"{x}/{y}/{z}"
