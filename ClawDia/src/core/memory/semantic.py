import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


ENTITY_TYPES = {"Person", "Task", "Project", "Document", "Action", "Note", "File"}


class ValidationError(Exception):
    pass


def _generate_id(prefix: str = "ent") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class SemanticMemory:
    def __init__(self, graph_path: str = "memory/semantic/graph.jsonl", schema_path: Optional[str] = None):
        self.graph_path = graph_path
        Path(graph_path).parent.mkdir(parents=True, exist_ok=True)
        self._schema: dict = {}
        if schema_path and Path(schema_path).exists():
            self._load_schema(schema_path)

    def _load_schema(self, path: str):
        with open(path) as f:
            raw = yaml.safe_load(f)
        self._schema = raw.get("types", {}) if raw else {}

    def load_schema(self, path: str):
        self._load_schema(path)

    def _validate(self, entity_type: str, properties: dict):
        if entity_type not in ENTITY_TYPES and entity_type not in self._schema:
            return
        rules = self._schema.get(entity_type, {})
        required = rules.get("required", [])
        for field in required:
            if field not in properties:
                raise ValidationError(f"Entity '{entity_type}' missing required field: {field}")
        enum_fields = {k: v for k, v in rules.items() if k.endswith("_enum")}
        for field, allowed in enum_fields.items():
            field_name = field.replace("_enum", "")
            if field_name in properties and properties[field_name] not in allowed:
                raise ValidationError(
                    f"Field '{field_name}' must be one of {allowed}, got '{properties[field_name]}'"
                )

    def create_entity(
        self,
        entity_type: str,
        properties: Optional[dict] = None,
        entity_id: Optional[str] = None,
    ) -> str:
        self._validate(entity_type, properties or {})
        entity = {
            "id": entity_id or _generate_id(entity_type.lower()),
            "type": entity_type,
            "properties": properties or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        with open(self.graph_path, "a") as f:
            f.write(json.dumps(entity) + "\n")
        return entity["id"]

    def _load_all_entities(self) -> list:
        if not Path(self.graph_path).exists():
            return []
        entities = []
        with open(self.graph_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entities.append(json.loads(line))
        return entities

    def _save_all_entities(self, entities: list):
        with open(self.graph_path, "w") as f:
            for e in entities:
                f.write(json.dumps(e) + "\n")

    def get_entity(self, entity_id: str) -> Optional[dict]:
        for e in self._load_all_entities():
            if e["id"] == entity_id:
                return e
        return None

    def update_entity(self, entity_id: str, properties: dict) -> bool:
        entities = self._load_all_entities()
        found = False
        for e in entities:
            if e["id"] == entity_id:
                e["properties"].update(properties)
                e["updated_at"] = datetime.utcnow().isoformat()
                found = True
                break
        if found:
            self._save_all_entities(entities)
        return found

    def delete_entity(self, entity_id: str) -> bool:
        entities = self._load_all_entities()
        before = len(entities)
        entities = [e for e in entities if e["id"] != entity_id]
        if len(entities) < before:
            self._save_all_entities(entities)
            return True
        return False

    def query_entities(
        self,
        entity_type: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        entities = self._load_all_entities()
        if entity_type:
            entities = [e for e in entities if e["type"] == entity_type]
        return entities[:limit]

    def create_relation(self, from_id: str, relation: str, to_id: str) -> str:
        rel = {
            "id": f"rel_{uuid.uuid4().hex[:8]}",
            "from": from_id,
            "relation": relation,
            "to": to_id,
            "created_at": datetime.utcnow().isoformat(),
        }
        with open(self.graph_path, "a") as f:
            f.write(json.dumps(rel) + "\n")
        return rel["id"]

    def query_relations(self, entity_id: Optional[str] = None, relation: Optional[str] = None) -> list:
        entities = self._load_all_entities()
        rels = [e for e in entities if "from" in e and "relation" in e and "to" in e]
        if entity_id:
            rels = [r for r in rels if r["from"] == entity_id or r["to"] == entity_id]
        if relation:
            rels = [r for r in rels if r["relation"] == relation]
        return rels

    def get_related_entities(self, entity_id: str, relation: Optional[str] = None) -> list:
        rels = self.query_relations(entity_id=entity_id, relation=relation)
        related_ids = set()
        for r in rels:
            if r["from"] != entity_id:
                related_ids.add(r["from"])
            if r["to"] != entity_id:
                related_ids.add(r["to"])
        all_entities = {e["id"]: e for e in self._load_all_entities() if "type" in e}
        return [all_entities[eid] for eid in related_ids if eid in all_entities]
