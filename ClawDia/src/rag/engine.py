from typing import Optional

from .ingestion import discover_files, extract_text, clean_text, extract_metadata
from .chunking import chunk_document
from .embedding import EmbeddingPipeline
from .store import VectorStore
from .context import ContextWindow


DEFAULT_PROMPT_TEMPLATE = """You are a helpful AI assistant. Use the following context to answer the user's question. If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {question}

Answer:"""


class RAGEngine:
    def __init__(self, index_path: str, metadata_path: str, dimension: int = 384,
                 embed_model: str = "all-MiniLM-L6-v2", max_tokens: int = 4096):
        self.embedder = EmbeddingPipeline(embed_model)
        self.store = VectorStore(index_path, metadata_path, dimension)
        self.context_win = ContextWindow(max_tokens=max_tokens)

    def ingest(self, directory: str, recursive: bool = True, chunk_strategy: str = "sentence",
               chunk_kwargs: Optional[dict] = None) -> int:
        files = discover_files(directory, recursive)
        total_chunks = 0
        for path in files:
            text = extract_text(path)
            if not text:
                continue
            text = clean_text(text)
            meta = extract_metadata(path)
            chunks = chunk_document(text, chunk_strategy, **(chunk_kwargs or {}))
            if not chunks:
                continue

            texts = [c["text"] for c in chunks]
            embeddings = self.embedder.embed(texts)
            metadatas = []
            for c in chunks:
                m = dict(meta)
                m["chunk_index"] = c["index"]
                m["chunk_text"] = c["text"]
                metadatas.append(m)
            self.store.add(embeddings, metadatas)
            total_chunks += len(chunks)
        return total_chunks

    def retrieve(self, query: str, k: int = 10) -> list[dict]:
        emb = self.embedder.embed_single(query)
        return self.store.search(emb, k)

    def build_context(self, query: str, k: int = 5) -> tuple[list[dict], str]:
        results = self.retrieve(query, k)
        texts = [r["chunk_text"] for r in results]
        fitted = self.context_win.fit_to_window(texts)
        context = "\n\n---\n\n".join(fitted)
        return results, context

    def query(self, question: str, k: int = 5, prompt_template: Optional[str] = None) -> dict:
        results, context = self.build_context(question, k)
        template = prompt_template or DEFAULT_PROMPT_TEMPLATE
        prompt = template.format(context=context, question=question)
        return {
            "prompt": prompt,
            "context": context,
            "results": results,
            "result_count": len(results),
        }
