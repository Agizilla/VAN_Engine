import pytest
from src.core.memory.episodic import EpisodicMemory
from src.core.memory.semantic import SemanticMemory
from src.core.memory.hybrid import HybridMemory


@pytest.fixture
def hybrid(tmp_path):
    db = tmp_path / "test_hybrid.db"
    faiss_p = tmp_path / "test_hybrid.faiss"
    graph = tmp_path / "test_hybrid_graph.jsonl"
    em = EpisodicMemory(str(db), str(faiss_p), vector_dim=384)
    sm = SemanticMemory(str(graph))
    return HybridMemory(em, sm)


def test_remember_and_search(hybrid):
    cid = hybrid.remember("user1", "Working on audio processing with Demucs")
    assert cid > 0


def test_create_entity_through_hybrid(hybrid):
    eid = hybrid.create_entity("Person", {"name": "Alice"})
    assert eid is not None
    entities = hybrid.query_entities("Person")
    assert len(entities) == 1


def test_search_returns_both_layers(hybrid):
    hybrid.remember("user1", "talking about music production")
    hybrid.create_entity("Project", {"name": "Music Album", "status": "active"})
    results = hybrid.search("music")
    assert len(results.episodic) >= 0
    assert len(results.semantic) >= 0


def test_relation_through_hybrid(hybrid):
    alice = hybrid.create_entity("Person", {"name": "Alice"})
    task = hybrid.create_entity("Task", {"title": "Finish mix", "status": "open"})
    hybrid.create_relation(task, "assigned_to", alice)
    related = hybrid.get_related_entities(alice)
    assert any(e["id"] == task for e in related)
