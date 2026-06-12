import re
from typing import Callable, Optional


Chunk = dict  # {"text": str, "index": int, "start_char": int, "end_char": int}


def sentence_chunker(text: str, max_sentences: int = 5, overlap_sentences: int = 1) -> list[Chunk]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return []

    chunks = []
    step = max_sentences - overlap_sentences
    if step < 1:
        step = 1

    char_pos = 0
    sentence_starts = []
    for s in sentences:
        idx = text.find(s, char_pos)
        if idx == -1:
            idx = char_pos
        sentence_starts.append(idx)
        char_pos = idx + len(s)

    for i in range(0, len(sentences), step):
        group = sentences[i:i + max_sentences]
        start_idx = sentence_starts[i]
        end_idx = (sentence_starts[i + len(group)] + len(group[-1]) if i + len(group) < len(sentence_starts) else len(text))
        chunks.append({
            "text": " ".join(group),
            "index": len(chunks),
            "start_char": start_idx,
            "end_char": end_idx,
        })

    return chunks


def token_chunker(text: str, max_tokens: int = 256, overlap_tokens: int = 32) -> list[Chunk]:
    words = text.split()
    if not words:
        return []

    chunks = []
    step = max_tokens - overlap_tokens
    if step < 1:
        step = 1

    for i in range(0, len(words), step):
        group = words[i:i + max_tokens]
        chunk_text = " ".join(group)
        start_char = text.find(chunk_text[:20])
        if start_char == -1:
            start_char = 0
        chunks.append({
            "text": chunk_text,
            "index": len(chunks),
            "start_char": start_char,
            "end_char": start_char + len(chunk_text),
        })

    return chunks


def fixed_length_chunker(text: str, chunk_size: int = 500, overlap: int = 50) -> list[Chunk]:
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append({
            "text": text[start:end].strip(),
            "index": len(chunks),
            "start_char": start,
            "end_char": end,
        })
        start += chunk_size - overlap
    return [c for c in chunks if c["text"]]


CHUNK_STRATEGIES: dict[str, Callable] = {
    "sentence": sentence_chunker,
    "token": token_chunker,
    "fixed": fixed_length_chunker,
}


def chunk_document(text: str, strategy: str = "sentence", **kwargs) -> list[Chunk]:
    fn = CHUNK_STRATEGIES.get(strategy)
    if fn is None:
        fn = sentence_chunker
    return fn(text, **kwargs)
