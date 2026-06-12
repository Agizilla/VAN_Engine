import hashlib
import json
from pathlib import Path
from typing import Optional

import numpy as np


DEFAULT_MODEL = "all-MiniLM-L6-v2"


class EmbeddingPipeline:
    def __init__(self, model_name: str = DEFAULT_MODEL, cache_dir: Optional[str] = None):
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            kwargs = {"cache_folder": str(self.cache_dir)} if self.cache_dir else {}
            self._model = SentenceTransformer(self.model_name, **kwargs)
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)
        model = self._load_model()
        return model.encode(texts, show_progress_bar=False).astype(np.float32)

    def embed_single(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    @property
    def dimension(self) -> int:
        model = self._load_model()
        return model.get_sentence_embedding_dimension()

    def cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()
