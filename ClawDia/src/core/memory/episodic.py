import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

Base = declarative_base()


class ConversationORM(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(128), nullable=False, index=True)
    text = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


class EpisodicMemory:
    def __init__(
        self,
        db_path: str = "memory/episodic/conversations.db",
        faiss_path: str = "memory/episodic/embeddings.faiss",
        vector_dim: int = 384,
        embed_model_name: str = "all-MiniLM-L6-v2",
        embed_cache_dir: Optional[str] = None,
    ):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.faiss_path = faiss_path
        self.vector_dim = vector_dim
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        self._embedder = None
        self._faiss_index = None
        self._faiss_loaded = False
        self._embed_model_name = embed_model_name
        self._embed_cache_dir = embed_cache_dir

    @property
    def embedder(self):
        if self._embedder is None and SentenceTransformer is not None:
            kwargs = {"cache_folder": self._embed_cache_dir} if self._embed_cache_dir else {}
            self._embedder = SentenceTransformer(self._embed_model_name, **kwargs)
        return self._embedder

    def _get_index(self):
        if self._faiss_index is not None:
            return self._faiss_index
        if faiss is None:
            return None
        p = Path(self.faiss_path)
        if p.exists() and self._faiss_loaded:
            self._faiss_index = faiss.read_index(str(p))
        else:
            self._faiss_index = faiss.IndexFlatL2(self.vector_dim)
        self._faiss_loaded = True
        return self._faiss_index

    def _save_index(self):
        if self._faiss_index is not None and faiss is not None:
            Path(self.faiss_path).parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self._faiss_index, str(self.faiss_path))

    def _embed(self, texts):
        if self.embedder is None:
            return np.zeros((len(texts), self.vector_dim), dtype=np.float32)
        return self.embedder.encode(texts, show_progress_bar=False).astype(np.float32)

    def store_conversation(
        self,
        user_id: str,
        text: str,
        metadata: Optional[dict] = None,
    ) -> int:
        session = self.Session()
        try:
            conv = ConversationORM(
                user_id=user_id,
                text=text,
                metadata_json=json.dumps(metadata or {}),
            )
            session.add(conv)
            session.commit()
            conv_id = conv.id

            emb = self._embed([text])
            index = self._get_index()
            if index is not None:
                index.add(emb)
                self._save_index()

            return conv_id
        finally:
            session.close()

    def get_conversation(self, conv_id: int):
        session = self.Session()
        try:
            conv = session.get(ConversationORM, conv_id)
            if conv is None:
                return None
            return {
                "id": conv.id,
                "user_id": conv.user_id,
                "text": conv.text,
                "metadata": json.loads(conv.metadata_json),
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
            }
        finally:
            session.close()

    def search_similar(
        self,
        query: str,
        k: int = 5,
        user_id: Optional[str] = None,
    ) -> list:
        index = self._get_index()
        if index is None or index.ntotal == 0:
            return []
        emb = self._embed([query])
        distances, indices = index.search(emb, min(k, index.ntotal))

        session = self.Session()
        try:
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0:
                    continue
                conv_id = idx + 1
                conv = session.get(ConversationORM, conv_id)
                if conv is None:
                    continue
                if user_id and conv.user_id != user_id:
                    continue
                results.append({
                    "id": conv.id,
                    "user_id": conv.user_id,
                    "text": conv.text,
                    "metadata": json.loads(conv.metadata_json),
                    "similarity": float(1.0 / (1.0 + dist)),
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                })
            return results
        finally:
            session.close()

    def query_by_date_range(self, start: datetime, end: datetime, user_id: Optional[str] = None) -> list:
        session = self.Session()
        try:
            q = session.query(ConversationORM).filter(
                ConversationORM.created_at >= start,
                ConversationORM.created_at <= end,
            )
            if user_id:
                q = q.filter(ConversationORM.user_id == user_id)
            q = q.order_by(ConversationORM.created_at.desc())
            return [
                {
                    "id": c.id,
                    "user_id": c.user_id,
                    "text": c.text,
                    "metadata": json.loads(c.metadata_json),
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in q.all()
            ]
        finally:
            session.close()
