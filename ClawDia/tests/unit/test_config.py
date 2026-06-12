import pytest
import yaml
from pathlib import Path
from src.core.config import load_config, resolve_path, RootConfig


def test_load_config_defaults():
    cfg = load_config()
    assert cfg.clawdia.name == "ClawDia"
    assert cfg.clawdia.version == "0.1.0"
    assert cfg.memory.episodic.vector_dim == 384


def test_load_config_custom(tmp_path):
    custom = tmp_path / "custom.yaml"
    custom.write_text(yaml.dump({
        "clawdia": {"name": "TestDia", "log_level": "DEBUG"},
        "memory": {"episodic": {"vector_dim": 768}},
        "models": {"embedding": {"name": "test-model"}},
        "data": {},
        "ui": {},
    }))
    cfg = load_config(custom)
    assert cfg.clawdia.name == "TestDia"
    assert cfg.clawdia.log_level == "DEBUG"
    assert cfg.memory.episodic.vector_dim == 768
    assert cfg.models.embedding.name == "test-model"


def test_resolve_path():
    cfg = load_config()
    resolved = resolve_path(cfg)
    assert "conversations.db" in resolved.memory.episodic.database_path
    assert resolved.memory.episodic.database_path.startswith(str(Path.cwd()))
