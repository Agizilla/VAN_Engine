import pytest
from datetime import datetime, timedelta
from src.core.memory.episodic import EpisodicMemory


@pytest.fixture
def mem(tmp_path):
    db = tmp_path / "test_episodic.db"
    faiss_p = tmp_path / "test.faiss"
    return EpisodicMemory(str(db), str(faiss_p), vector_dim=384)


def test_store_and_retrieve(mem):
    conv_id = mem.store_conversation("test_user", "Hello world", {"topic": "greeting"})
    assert conv_id > 0
    conv = mem.get_conversation(conv_id)
    assert conv is not None
    assert conv["text"] == "Hello world"
    assert conv["user_id"] == "test_user"
    assert conv["metadata"]["topic"] == "greeting"


def test_get_nonexistent(mem):
    conv = mem.get_conversation(99999)
    assert conv is None


def test_store_multiple(mem):
    ids = []
    for i in range(5):
        ids.append(mem.store_conversation("user", f"Conversation {i}"))
    assert len(set(ids)) == 5
    for cid in ids:
        conv = mem.get_conversation(cid)
        assert conv is not None


def test_date_range(mem):
    now = datetime.utcnow()
    cid = mem.store_conversation("user", "Recent chat")
    results = mem.query_by_date_range(now - timedelta(hours=1), now + timedelta(hours=1))
    assert len(results) >= 1
    assert any(r["id"] == cid for r in results)


def test_date_range_with_user(mem):
    mem.store_conversation("alice", "Alice message")
    mem.store_conversation("bob", "Bob message")
    now = datetime.utcnow()
    results = mem.query_by_date_range(now - timedelta(hours=1), now + timedelta(hours=1), user_id="alice")
    assert all(r["user_id"] == "alice" for r in results)
