from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import yaml


CLAWDIA_ROOT = Path(__file__).resolve().parent.parent.parent


class EpisodicMemoryConfig(BaseModel):
    database_path: str = "memory/episodic/conversations.db"
    vector_dim: int = 384
    faiss_index_path: str = "memory/episodic/embeddings.faiss"


class SemanticMemoryConfig(BaseModel):
    graph_path: str = "memory/semantic/graph.jsonl"
    schema_path: str = "memory/semantic/schema.yaml"


class MemoryConfig(BaseModel):
    episodic: EpisodicMemoryConfig = EpisodicMemoryConfig()
    semantic: SemanticMemoryConfig = SemanticMemoryConfig()


class EmbeddingModelConfig(BaseModel):
    name: str = "all-MiniLM-L6-v2"
    cache_dir: str = "models/embeddings/"


class WhisperModelConfig(BaseModel):
    model_size: str = "base"
    device: str = "cpu"


class PiperModelConfig(BaseModel):
    model_path: str = "models/piper/"
    voice: str = "female_base"


class ModelsConfig(BaseModel):
    embedding: EmbeddingModelConfig = EmbeddingModelConfig()
    whisper: WhisperModelConfig = WhisperModelConfig()
    piper: PiperModelConfig = PiperModelConfig()


class DataConfig(BaseModel):
    cache_dir: str = "data/cache/"
    voice_samples: str = "data/voice_samples/"
    knowledge: str = "data/knowledge/"


class UIConfig(BaseModel):
    theme: str = "dark"
    enable_voice: bool = False
    language: str = "en-US"


class ClawDiaAppConfig(BaseModel):
    name: str = "ClawDia"
    version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"


class RootConfig(BaseModel):
    clawdia: ClawDiaAppConfig = ClawDiaAppConfig()
    memory: MemoryConfig = MemoryConfig()
    models: ModelsConfig = ModelsConfig()
    data: DataConfig = DataConfig()
    ui: UIConfig = UIConfig()


def load_config(path: Optional[Path] = None) -> RootConfig:
    if path is None:
        path = CLAWDIA_ROOT / "config" / "default.yaml"
    with open(path) as f:
        raw = yaml.safe_load(f)
    return RootConfig(**raw)


def resolve_path(config: RootConfig) -> RootConfig:
    root = CLAWDIA_ROOT
    config.memory.episodic.database_path = str(root / config.memory.episodic.database_path)
    config.memory.episodic.faiss_index_path = str(root / config.memory.episodic.faiss_index_path)
    config.memory.semantic.graph_path = str(root / config.memory.semantic.graph_path)
    config.memory.semantic.schema_path = str(root / config.memory.semantic.schema_path)
    config.models.embedding.cache_dir = str(root / config.models.embedding.cache_dir)
    config.data.cache_dir = str(root / config.data.cache_dir)
    config.data.voice_samples = str(root / config.data.voice_samples)
    config.data.knowledge = str(root / config.data.knowledge)
    return config
