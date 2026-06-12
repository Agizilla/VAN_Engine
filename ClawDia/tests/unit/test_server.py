import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src.server.app import create_app
    app = create_app()
    return TestClient(app)


class TestMemoryAPI:
    def test_list_conversations_empty(self, client):
        resp = client.get("/api/memory/conversations")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_store_and_retrieve(self, client):
        resp = client.post("/api/memory/conversations", json={"text": "hello world", "metadata": {"role": "user"}})
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data

        resp2 = client.get(f"/api/memory/conversations/{data['id']}")
        assert resp2.status_code == 200
        assert resp2.json()["text"] == "hello world"

    def test_list_entities_empty(self, client):
        resp = client.get("/api/memory/entities")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_entity(self, client):
        resp = client.post("/api/memory/entities", json={"entity_type": "Test", "properties": {"name": "test-entity"}})
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert "type" in data

    def test_search(self, client):
        client.post("/api/memory/conversations", json={"text": "test search query", "metadata": {"role": "user"}})
        resp = client.post("/api/memory/search", json={"query": "search", "limit": 5})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_relations(self, client):
        a = client.post("/api/memory/entities", json={"entity_type": "Node", "properties": {"name": "alpha"}}).json()
        b = client.post("/api/memory/entities", json={"entity_type": "Node", "properties": {"name": "beta"}}).json()
        resp = client.post("/api/memory/relations", json={"source": a["id"], "relation": "connects_to", "target": b["id"]})
        assert resp.status_code == 201
        resp2 = client.get("/api/memory/relations")
        assert len(resp2.json()) >= 1


class TestSkillsAPI:
    def test_list_skills(self, client):
        resp = client.get("/api/skills/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_registered(self, client):
        resp = client.get("/api/skills/registered")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestVoiceAPI:
    def test_status(self, client):
        resp = client.get("/api/voice/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "stt_available" in data
        assert "mic_available" in data
        assert "tts_available" in data


class TestWebSocket:
    def test_ws_ping_pong(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "ping"})
            resp = ws.receive_json()
            assert resp["type"] == "pong"

    def test_ws_get_skills(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "get_skills"})
            resp = ws.receive_json()
            assert resp["type"] == "skills"
            assert "skills" in resp

    def test_ws_get_conversations(self, client):
        with client.websocket_connect("/ws") as ws:
            ws.send_json({"type": "get_conversations"})
            resp = ws.receive_json()
            assert resp["type"] == "conversations"
