from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.rag.engine import RAGEngine

router = APIRouter(prefix="/api/rag", tags=["rag"])

_engine: RAGEngine | None = None


def get_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine(
            index_path="rag_index.faiss",
            metadata_path="rag_meta.jsonl",
        )
    return _engine


class IngestRequest(BaseModel):
    directory: str
    recursive: bool = True
    strategy: str = "sentence"


class SearchRequest(BaseModel):
    query: str
    k: int = 5


@router.post("/ingest")
async def api_ingest(req: IngestRequest):
    engine = get_engine()
    count = engine.ingest(req.directory, req.recursive, req.strategy)
    return {"chunks_ingested": count}


@router.post("/search")
async def api_search(req: SearchRequest):
    engine = get_engine()
    results = engine.retrieve(req.query, req.k)
    return {"results": results, "count": len(results)}


@router.get("/status")
async def api_status():
    engine = get_engine()
    return {"chunks": engine.store.count()}


@router.post("/clear")
async def api_clear():
    engine = get_engine()
    engine.store.clear()
    return {"status": "cleared"}
