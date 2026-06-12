from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from ...core.memory.episodic import EpisodicMemory
from ...core.memory.semantic import SemanticMemory


class ConversationStore(BaseModel):
    user_id: str = "default"
    text: str
    metadata: dict = {}


class EntityCreate(BaseModel):
    entity_type: str
    properties: dict = {}


class EntityUpdate(BaseModel):
    properties: dict


class RelationCreate(BaseModel):
    source: str
    relation: str
    target: str
    properties: dict = {}


class SearchQuery(BaseModel):
    query: str
    limit: int = 10


def get_episodic(request: Request) -> EpisodicMemory:
    return request.app.state.episodic


def get_semantic(request: Request) -> SemanticMemory:
    return request.app.state.semantic


router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/conversations")
def list_conversations(user_id: str = "default", limit: int = 50,
                        episodic: EpisodicMemory = Depends(get_episodic)):
    now = datetime.utcnow()
    results = episodic.query_by_date_range(
        datetime(2000, 1, 1), now, user_id=user_id
    )
    results.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    results = results[:limit]
    return [{
        "id": r["id"],
        "user_id": r["user_id"],
        "text": r["text"],
        "metadata": r.get("metadata", {}),
        "timestamp": r.get("created_at", ""),
    } for r in results]


@router.post("/conversations", status_code=201)
def store_conversation(data: ConversationStore,
                        episodic: EpisodicMemory = Depends(get_episodic)):
    conv_id = episodic.store_conversation(
        user_id=data.user_id,
        text=data.text,
        metadata=data.metadata,
    )
    return {"id": conv_id, "status": "ok"}


@router.get("/conversations/{conv_id}")
def get_conversation(conv_id: int,
                      episodic: EpisodicMemory = Depends(get_episodic)):
    conv = episodic.get_conversation(conv_id)
    if conv is None:
        raise HTTPException(404, "Conversation not found")
    return conv


@router.post("/search")
def search_memory(query: SearchQuery,
                   episodic: EpisodicMemory = Depends(get_episodic)):
    rows = episodic.search_similar(query.query, query.limit)
    return [{
        "id": r["id"],
        "user_id": r["user_id"],
        "text": r["text"],
        "metadata": r.get("metadata", {}),
        "timestamp": r.get("created_at", ""),
    } for r in rows]


@router.get("/entities")
def list_entities(semantic: SemanticMemory = Depends(get_semantic)):
    import json
    from pathlib import Path
    path = Path(semantic.graph_path)
    entities = {}
    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if entry.get("type") == "entity":
                    eid = entry.get("id", "")
                    entities[eid] = {
                        "id": eid,
                        "entity_type": entry.get("entity_type", ""),
                        "properties": entry.get("properties", {}),
                        "created_at": entry.get("created_at", ""),
                    }
    return list(entities.values())


@router.post("/entities", status_code=201)
def create_entity(data: EntityCreate,
                   semantic: SemanticMemory = Depends(get_semantic)):
    eid = semantic.create_entity(data.entity_type, data.properties)
    entity = semantic.get_entity(eid)
    if entity is None:
        raise HTTPException(500, "Failed to create entity")
    return {"id": eid, **entity}


@router.put("/entities/{entity_id}")
def update_entity(entity_id: str, data: EntityUpdate,
                   semantic: SemanticMemory = Depends(get_semantic)):
    ok = semantic.update_entity(entity_id, data.properties)
    if not ok:
        raise HTTPException(404, "Entity not found")
    entity = semantic.get_entity(entity_id)
    return {"id": entity_id, **entity}


@router.delete("/entities/{entity_id}", status_code=204)
def delete_entity(entity_id: str,
                   semantic: SemanticMemory = Depends(get_semantic)):
    if not semantic.delete_entity(entity_id):
        raise HTTPException(404, "Entity not found")


@router.post("/relations", status_code=201)
def create_relation(data: RelationCreate,
                     semantic: SemanticMemory = Depends(get_semantic)):
    rel_id = semantic.create_relation(data.source, data.relation, data.target)
    return {"id": rel_id, "status": "ok"}


@router.get("/relations")
def list_relations(source: Optional[str] = None, target: Optional[str] = None,
                    semantic: SemanticMemory = Depends(get_semantic)):
    if source:
        return semantic.query_relations(entity_id=source)
    if target:
        return semantic.query_relations(entity_id=target)
    return semantic.query_relations()
