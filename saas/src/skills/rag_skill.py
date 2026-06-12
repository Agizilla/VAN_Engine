import time
from pathlib import Path
from typing import Any

from .base import BaseSkill, register_skill


_SUPPORTED_EXTENSIONS = {".txt", ".md", ".rst", ".json", ".csv", ".yaml", ".yml", ".xml", ".html", ".pdf"}


@register_skill("RAG", "general")
class RAGSkill(BaseSkill):
    def __init__(self, config: dict = None):
        super().__init__()
        self.name = "RAG"
        self.description = "Search and manage ingested documents. Can search for relevant information and ingest new documents."
        self.category = "general"
        self._engine = None
        self._config = config or {}
        self._embedding_model = self._config.get("embedding_model", None)

    def _get_engine(self):
        if self._engine is not None:
            return self._engine
        for attempt in range(3):
            try:
                from ..rag.engine import RAGEngine
                kwargs = {"index_path": "rag_index.faiss", "meta_path": "rag_meta.jsonl"}
                if self._embedding_model:
                    kwargs["embedding_model"] = self._embedding_model
                self._engine = RAGEngine(**kwargs)
                return self._engine
            except Exception:
                if attempt < 2:
                    time.sleep(1)
        return None

    def execute(self, **kwargs: Any) -> dict:
        action = kwargs.get("action", "search")
        engine = self._get_engine()
        if engine is None:
            return {"error": "RAG engine not available", "result": None}

        if action == "search":
            query = kwargs.get("query", "")
            if not query:
                return {"error": "No query provided", "result": []}
            k = kwargs.get("k", 5)
            try:
                results, context = engine.build_context(query, k)
                return {"error": None, "result": context, "chunks": results}
            except Exception as e:
                return {"error": str(e), "result": None}

        elif action == "ingest":
            directory = kwargs.get("directory", "")
            if not directory:
                return {"error": "No directory provided", "result": None}
            strategy = kwargs.get("strategy", "sentence")

            dir_path = Path(directory)
            if not dir_path.is_dir():
                return {"error": f"Directory not found: {directory}", "result": None}

            files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in _SUPPORTED_EXTENSIONS]
            if len(files) == 0:
                return {"error": "No supported files found (supported: .txt, .md, .rst, .json, .csv, .yaml, .yml, .xml, .html, .pdf)", "result": None}

            try:
                total = len(files)
                for i, f in enumerate(files):
                    self.publish({"type": "progress", "current": i + 1, "total": total})
                count = engine.ingest(directory, strategy=strategy)
                return {"error": None, "result": f"Ingested {count} chunks from {directory}"}
            except Exception as e:
                return {"error": str(e), "result": None}

        elif action == "status":
            try:
                count = engine.store.count()
                return {"error": None, "result": {"chunks": count}}
            except Exception as e:
                return {"error": str(e), "result": None}

        else:
            return {"error": f"Unknown action: {action}", "result": None}

    def search(self, query: str, k: int = 5) -> str:
        result = self.execute(action="search", query=query, k=k)
        if result["error"]:
            return f"[RAG error: {result['error']}]"
        return result["result"] or "No relevant documents found."
