import os
import re
from pathlib import Path
from typing import Optional


SUPPORTED_EXTENSIONS = {".txt", ".md", ".py", ".yaml", ".yml", ".json", ".csv", ".html", ".xml"}


def discover_files(directory: str, recursive: bool = True) -> list[Path]:
    base = Path(directory)
    if not base.exists():
        return []
    if recursive:
        return [p for p in base.rglob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS and not p.name.startswith(".")]
    return [p for p in base.glob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS and not p.name.startswith(".")]


def extract_text(path: Path) -> Optional[str]:
    ext = path.suffix.lower()
    try:
        if ext in (".txt", ".md", ".py", ".yaml", ".yml", ".json", ".csv", ".html", ".xml"):
            return path.read_text(encoding="utf-8", errors="replace")
        elif ext == ".pdf":
            return _extract_pdf(path)
        else:
            return None
    except Exception:
        return None


def _extract_pdf(path: Path) -> Optional[str]:
    try:
        import pdfminer.high_level
        return pdfminer.high_level.extract_text(str(path))
    except ImportError:
        pass
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() for page in reader.pages)
    except ImportError:
        pass
    return None


def clean_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
    cleaned = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                cleaned.append("")
                prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False
    return "\n".join(cleaned).strip()


def extract_metadata(path: Path) -> dict:
    stat = path.stat()
    return {
        "source": str(path),
        "filename": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "modified": stat.st_mtime,
    }
