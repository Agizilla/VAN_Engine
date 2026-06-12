import pytest
import yaml
from pathlib import Path
from src.core.memory.semantic import SemanticMemory, ValidationError


@pytest.fixture
def sm(tmp_path):
    graph = tmp_path / "test_graph.jsonl"
    return SemanticMemory(str(graph))


@pytest.fixture
def sm_with_schema(tmp_path):
    graph = tmp_path / "test_graph.jsonl"
    schema = tmp_path / "schema.yaml"
    schema.write_text(yaml.dump({
        "types": {
            "Task": {
                "required": ["title", "status"],
                "status_enum": ["open", "in_progress", "done"],
            }
        }
    }))
    return SemanticMemory(str(graph), str(schema))


def test_create_entity(sm):
    eid = sm.create_entity("Person", {"name": "Alice", "email": "alice@test.com"})
    assert eid.startswith("person_")
    entity = sm.get_entity(eid)
    assert entity is not None
    assert entity["properties"]["name"] == "Alice"


def test_get_nonexistent(sm):
    assert sm.get_entity("nonexistent") is None


def test_update_entity(sm):
    eid = sm.create_entity("Task", {"title": "Initial", "status": "open"})
    assert sm.update_entity(eid, {"status": "done"})
    entity = sm.get_entity(eid)
    assert entity["properties"]["status"] == "done"


def test_delete_entity(sm):
    eid = sm.create_entity("Note", {"content": "test note"})
    assert sm.get_entity(eid) is not None
    assert sm.delete_entity(eid)
    assert sm.get_entity(eid) is None


def test_query_by_type(sm):
    sm.create_entity("Person", {"name": "Alice"})
    sm.create_entity("Person", {"name": "Bob"})
    sm.create_entity("Project", {"name": "Test Project"})
    persons = sm.query_entities(entity_type="Person")
    assert len(persons) == 2
    projects = sm.query_entities(entity_type="Project")
    assert len(projects) == 1


def test_create_relation(sm):
    alice = sm.create_entity("Person", {"name": "Alice"})
    task = sm.create_entity("Task", {"title": "Review", "status": "open"})
    rel_id = sm.create_relation(task, "assigned_to", alice)
    assert rel_id.startswith("rel_")
    rels = sm.query_relations(entity_id=alice)
    assert len(rels) >= 1
    related = sm.get_related_entities(alice)
    assert any(e["id"] == task for e in related)


def test_schema_validation(sm_with_schema):
    eid = sm_with_schema.create_entity("Task", {"title": "Test", "status": "open"})
    assert eid is not None
    with pytest.raises(ValidationError, match="missing required field"):
        sm_with_schema.create_entity("Task", {"title": "Missing status"})
    with pytest.raises(ValidationError):
        sm_with_schema.create_entity("Task", {"title": "Bad status", "status": "invalid_status"})


def test_empty_entities(sm):
    assert sm.query_entities() == []
    assert sm.get_entity("x") is None
    assert sm.delete_entity("x") is False
