from typing import Optional

from .episodic import EpisodicMemory
from .semantic import SemanticMemory


class HybridSearchResult:
    def __init__(self, episodic: list, semantic: list):
        self.episodic = episodic
        self.semantic = semantic


class HybridMemory:
    def __init__(self, episodic: EpisodicMemory, semantic: SemanticMemory):
        self.episodic = episodic
        self.semantic = semantic

    def remember(self, user_id: str, text: str, metadata: Optional[dict] = None) -> int:
        return self.episodic.store_conversation(user_id, text, metadata)

    def search(self, query: str, k: int = 5, user_id: Optional[str] = None) -> HybridSearchResult:
        episodic_results = self.episodic.search_similar(query, k=k, user_id=user_id)
        semantic_type = self._infer_entity_type(query)
        if semantic_type:
            semantic_results = self.semantic.query_entities(entity_type=semantic_type)
        else:
            semantic_results = self.semantic.query_entities(limit=k)
        return HybridSearchResult(episodic=episodic_results, semantic=semantic_results)

    def create_entity(self, entity_type: str, properties: Optional[dict] = None) -> str:
        return self.semantic.create_entity(entity_type, properties)

    def query_entities(self, entity_type: Optional[str] = None, limit: int = 100) -> list:
        return self.semantic.query_entities(entity_type, limit)

    def create_relation(self, from_id: str, relation: str, to_id: str) -> str:
        return self.semantic.create_relation(from_id, relation, to_id)

    def get_related_entities(self, entity_id: str, relation: Optional[str] = None) -> list:
        return self.semantic.get_related_entities(entity_id, relation)

    def _infer_entity_type(self, query: str) -> Optional[str]:
        query_lower = query.lower()
        type_map = {
            "person": "Person",
            "people": "Person",
            "who": "Person",
            "task": "Task",
            "todo": "Task",
            "project": "Project",
            "document": "Document",
            "file": "File",
            "note": "Note",
        }
        for keyword, etype in type_map.items():
            if keyword in query_lower:
                return etype
        return None
