import json
from pathlib import Path
from typing import Optional

import numpy as np
import faiss


class VectorStore:
    def __init__(self, index_path: str, metadata_path: str, dimension: int = 384):
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.dimension = dimension
        self._index: Optional[faiss.Index] = None
        self._metadata: list[dict] = []

    @property
    def index(self) -> faiss.Index:
        if self._index is None:
            if self.index_path.exists():
                self._index = faiss.read_index(str(self.index_path))
            else:
                self._index = faiss.IndexFlatL2(self.dimension)
        return self._index

    def _load_metadata(self):
        if self._metadata:
            return
        if self.metadata_path.exists():
            with open(self.metadata_path) as f:
                self._metadata = [json.loads(line) for line in f if line.strip()]

    def _save_metadata(self):
        with open(self.metadata_path, "w") as f:
            for entry in self._metadata:
                f.write(json.dumps(entry) + "\n")

    def add(self, embeddings: np.ndarray, metadatas: list[dict]) -> list[int]:
        ids = []
        start_id = self.index.ntotal
        for i, (emb, meta) in enumerate(zip(embeddings, metadatas)):
            vec = emb.reshape(1, -1).astype(np.float32)
            self.index.add(vec)
            entry = {"id": start_id + i, **meta}
            self._metadata.append(entry)
            ids.append(start_id + i)
        self._save()
        return ids

    def search(self, query_emb: np.ndarray, k: int = 10) -> list[dict]:
        if self.index.ntotal == 0:
            return []
        vec = query_emb.reshape(1, -1).astype(np.float32)
        distances, indices = self.index.search(vec, min(k, self.index.ntotal))
        self._load_metadata()
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            entry = dict(self._metadata[idx])
            entry["score"] = float(dist)
            results.append(entry)
        return results

    def delete(self, doc_id: int) -> bool:
        self._load_metadata()
        before = len(self._metadata)
        self._metadata = [m for m in self._metadata if m.get("id") != doc_id]
        if len(self._metadata) == before:
            return False
        self._rebuild_index()
        return True

    def clear(self):
        self._index = faiss.IndexFlatL2(self.dimension)
        self._metadata = []
        self._save()

    def count(self) -> int:
        return self.index.ntotal

    def _save(self):
        faiss.write_index(self._index, str(self.index_path))
        self._save_metadata()

    def _rebuild_index(self):
        self._index = faiss.IndexFlatL2(self.dimension)
        if self._metadata:
            all_vecs = np.zeros((len(self._metadata), self.dimension), dtype=np.float32)
            self._index.add(all_vecs)
        self._save()
