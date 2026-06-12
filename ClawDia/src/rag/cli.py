import argparse
import sys
from pathlib import Path

from src.rag.engine import RAGEngine
from src.rag.ingestion import discover_files, extract_text, extract_metadata
from src.rag.chunking import chunk_document


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rag", description="RAG document management CLI")
    sp = p.add_subparsers(dest="command", required=True)

    ingest = sp.add_parser("ingest", help="Ingest documents into vector store")
    ingest.add_argument("directory", help="Directory to scan")
    ingest.add_argument("--strategy", default="sentence", choices=["sentence", "token", "fixed"])
    ingest.add_argument("--recursive", action="store_true", default=True)
    ingest.add_argument("--index", default="rag_index.faiss")
    ingest.add_argument("--meta", default="rag_meta.jsonl")

    search_p = sp.add_parser("search", help="Search vector store")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--k", type=int, default=5)
    search_p.add_argument("--index", default="rag_index.faiss")
    search_p.add_argument("--meta", default="rag_meta.jsonl")

    status_p = sp.add_parser("status", help="Show vector store stats")
    status_p.add_argument("--index", default="rag_index.faiss")
    status_p.add_argument("--meta", default="rag_meta.jsonl")

    clear_p = sp.add_parser("clear", help="Clear vector store")
    clear_p.add_argument("--index", default="rag_index.faiss")
    clear_p.add_argument("--meta", default="rag_meta.jsonl")

    scan_p = sp.add_parser("scan", help="Scan directory and show file info")
    scan_p.add_argument("directory")
    scan_p.add_argument("--recursive", action="store_true", default=True)

    return p


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        files = discover_files(args.directory, args.recursive)
        if not files:
            print("No supported files found.")
            return
        for f in files:
            meta = extract_metadata(f)
            text = extract_text(f)
            print(f"  {f.name:30s} {meta['size_bytes']:>8}B  {len(text or ''):>6}chars  {meta['extension']}")
        print(f"\nTotal: {len(files)} files")
        return

    base_dir = Path(args.index).parent if Path(args.index).parent else Path.cwd()
    base_dir.mkdir(parents=True, exist_ok=True)

    engine = RAGEngine(
        index_path=args.index,
        metadata_path=args.meta,
    )

    if args.command == "ingest":
        count = engine.ingest(args.directory, args.recursive, args.strategy)
        print(f"Ingested {count} chunks from {args.directory}")

    elif args.command == "search":
        results = engine.retrieve(args.query, args.k)
        if not results:
            print("No results found.")
            return
        for i, r in enumerate(results):
            print(f"\n--- Result {i + 1} (score={r['score']:.4f}) ---")
            print(f"  Source: {r.get('source', '?')}")
            text = r.get("chunk_text", "")
            print(f"  Text: {text[:200]}{'...' if len(text) > 200 else ''}")

    elif args.command == "status":
        print(f"Vector store: {engine.store.count()} chunks indexed")

    elif args.command == "clear":
        engine.store.clear()
        print("Vector store cleared.")


if __name__ == "__main__":
    main()
