import tempfile
from pathlib import Path

import pytest
import numpy as np

from src.rag.ingestion import discover_files, extract_text, clean_text, extract_metadata
from src.rag.chunking import sentence_chunker, token_chunker, fixed_length_chunker, chunk_document
from src.rag.embedding import EmbeddingPipeline
from src.rag.store import VectorStore
from src.rag.context import ContextWindow
from src.rag.engine import RAGEngine


class TestIngestion:
    def test_discover_files_empty_dir(self, tmp_path):
        assert discover_files(str(tmp_path)) == []

    def test_discover_files_finds_txt(self, tmp_path):
        (tmp_path / "test.txt").write_text("hello")
        files = discover_files(str(tmp_path))
        assert len(files) == 1
        assert files[0].name == "test.txt"

    def test_discover_files_skips_hidden(self, tmp_path):
        (tmp_path / ".hidden").write_text("")
        assert discover_files(str(tmp_path)) == []

    def test_extract_text_txt(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello world")
        assert extract_text(f) == "Hello world"

    def test_extract_text_unsupported(self, tmp_path):
        f = tmp_path / "test.bin"
        f.write_bytes(b"\x00\x01")
        assert extract_text(f) is None

    def test_clean_text(self):
        assert clean_text("hello   world\n\n\nfoo") == "hello world\n\nfoo"

    def test_extract_metadata(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("x")
        meta = extract_metadata(f)
        assert meta["filename"] == "test.txt"
        assert meta["extension"] == ".txt"
        assert meta["size_bytes"] == 1


class TestChunking:
    def test_sentence_chunker_empty(self):
        assert sentence_chunker("") == []

    def test_sentence_chunker_basic(self):
        text = "Hello world. This is a test. How are you?"
        chunks = sentence_chunker(text, max_sentences=2)
        assert len(chunks) >= 1
        assert all("text" in c for c in chunks)

    def test_token_chunker(self):
        text = "word " * 500
        chunks = token_chunker(text, max_tokens=100, overlap_tokens=10)
        assert len(chunks) >= 4

    def test_fixed_length_chunker(self):
        text = "a" * 1000
        chunks = fixed_length_chunker(text, chunk_size=200, overlap=20)
        assert 5 <= len(chunks) <= 6

    def test_chunk_document_default(self):
        chunks = chunk_document("Hello. World. Test.", "sentence")
        assert len(chunks) >= 1


class TestEmbedding:
    def test_embed_empty(self):
        ep = EmbeddingPipeline()
        result = ep.embed([])
        assert result.shape == (0, 384)

    def test_dimension(self):
        ep = EmbeddingPipeline()
        assert ep.dimension == 384

    def test_cache_key(self):
        ep = EmbeddingPipeline()
        k1 = ep.cache_key("hello")
        k2 = ep.cache_key("hello")
        assert k1 == k2
        assert len(k1) == 32


class TestVectorStore:
    @pytest.fixture
    def store(self, tmp_path):
        return VectorStore(
            str(tmp_path / "index.faiss"),
            str(tmp_path / "meta.jsonl"),
            dimension=384,
        )

    def test_empty_count(self, store):
        assert store.count() == 0

    def test_add_and_search(self, store):
        emb = np.random.randn(3, 384).astype(np.float32)
        metas = [{"text": f"doc {i}"} for i in range(3)]
        ids = store.add(emb, metas)
        assert len(ids) == 3
        assert store.count() == 3

        query = np.random.randn(384).astype(np.float32)
        results = store.search(query, k=2)
        assert len(results) == 2
        assert "score" in results[0]

    def test_delete(self, store):
        emb = np.random.randn(1, 384).astype(np.float32)
        ids = store.add(emb, [{"text": "doc"}])
        assert store.delete(ids[0]) is True
        assert store.count() == 0

    def test_clear(self, store):
        emb = np.random.randn(2, 384).astype(np.float32)
        store.add(emb, [{"text": "a"}, {"text": "b"}])
        store.clear()
        assert store.count() == 0


class TestContextWindow:
    def test_token_count(self):
        cw = ContextWindow()
        assert cw.token_count("hello world") > 0

    def test_available_tokens(self):
        cw = ContextWindow(max_tokens=1000, reserve_tokens=200)
        assert cw.available_tokens() == 800

    def test_fit_to_window(self):
        cw = ContextWindow(max_tokens=100, reserve_tokens=10)
        texts = ["short", "another short", "yet another"]
        fitted = cw.fit_to_window(texts)
        assert len(fitted) <= 3

    def test_truncate(self):
        cw = ContextWindow(max_tokens=10, reserve_tokens=0)
        long = "hello world this is a very long text " * 10
        truncated = cw.truncate(long)
        assert len(truncated) < len(long)


class TestRAGEngine:
    def test_ingest_and_retrieve(self, tmp_path):
        doc_dir = tmp_path / "docs"
        doc_dir.mkdir()
        (doc_dir / "test.txt").write_text("Artificial intelligence is transforming the world. Machine learning enables computers to learn from data. Deep learning uses neural networks with many layers.")

        engine = RAGEngine(
            index_path=str(tmp_path / "index.faiss"),
            metadata_path=str(tmp_path / "meta.jsonl"),
        )
        count = engine.ingest(str(doc_dir))
        assert count > 0

        results, context = engine.build_context("AI and machine learning", k=5)
        assert len(results) >= 1
        assert "intelligence" in context.lower() or "learning" in context.lower()

    def test_query_builds_prompt(self, tmp_path):
        doc_dir = tmp_path / "docs"
        doc_dir.mkdir()
        (doc_dir / "test.txt").write_text("Python is a programming language. It is used for web development and data science.")

        engine = RAGEngine(
            index_path=str(tmp_path / "index.faiss"),
            metadata_path=str(tmp_path / "meta.jsonl"),
        )
        engine.ingest(str(doc_dir))
        result = engine.query("What is Python?")
        assert "prompt" in result
        assert "context" in result
        assert "results" in result
        assert result["result_count"] > 0
