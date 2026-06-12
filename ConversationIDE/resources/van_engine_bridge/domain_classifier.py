#!/usr/bin/env python3
import sys, io, re, json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

@dataclass
class DomainKeyword:
    domain: str
    primary: List[str]
    secondary: List[str]

@dataclass
class ClassificationResult:
    domain: str
    path: str
    relevance: float
    primary_hits: int
    secondary_hits: int

class WisdomDomainClassifier:
    def __init__(self, base_directory: Path):
        self.wisdom_dir = base_directory / "MEMORY" / "WISDOM" / "FRAMES"
        self.domains = self._init_domains()

    def _init_domains(self) -> List[DomainKeyword]:
        return [
            DomainKeyword(domain="communication",
                primary=[r"response|format|output|verbose|concise|summary|explain",
                         r"tone|voice|style|wording|phrasing",
                         r"greeting|rating|feedback"],
                secondary=[r"short|long|brief|detail", r"say|tell|write|read"]),
            DomainKeyword(domain="development",
                primary=[r"code|function|class|module|import|export",
                         r"bug|fix|refactor|implement|build|create|add",
                         r"typescript|javascript|python|bun|git",
                         r"test|lint|type.?check|compile",
                         r"hook|skill|tool|agent|algorithm"],
                secondary=[r"file|path|directory|folder", r"error|crash|broken|issue"]),
            DomainKeyword(domain="deployment",
                primary=[r"deploy|push|ship|release|publish",
                         r"cloudflare|worker|pages|wrangler|vercel",
                         r"production|staging|live|remote",
                         r"git\s+push|git\s+remote"],
                secondary=[r"build|compile|bundle", r"url|domain|dns|ssl"]),
            DomainKeyword(domain="security",
                primary=[r"security|vulnerability|exploit|cve",
                         r"auth|authentication|authorization|oauth",
                         r"encryption|crypto|tls|ssl",
                         r"scan|audit|penetration"],
                secondary=[r"secret|key|token|credential", r"firewall|waf|ids|ips"]),
        ]

    def classify(self, text: str) -> List[ClassificationResult]:
        results = []
        text_lower = text.lower()
        for domain in self.domains:
            score = 0
            primary_hits = 0
            secondary_hits = 0
            for pattern in domain.primary:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                if matches:
                    primary_hits += matches
                    score += matches * 2
            for pattern in domain.secondary:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                if matches:
                    secondary_hits += matches
                    score += matches
            if primary_hits >= 1 or secondary_hits >= 2:
                frame_path = self.wisdom_dir / f"{domain.domain}.md"
                results.append(ClassificationResult(domain=domain.domain,
                    path=str(frame_path) if frame_path.exists() else "",
                    relevance=min(score / 10.0, 1.0),
                    primary_hits=primary_hits, secondary_hits=secondary_hits))
        return sorted(results, key=lambda x: x.relevance, reverse=True)

    def load_relevant_frames(self, text: str, max_frames: int = 3) -> List[Tuple[str, str]]:
        classified = self.classify(text)
        result = []
        for c in classified[:max_frames]:
            if c.path and Path(c.path).exists():
                content = Path(c.path).read_text(encoding='utf-8')
                result.append((c.domain, content))
        return result

    def list_frames(self) -> List[str]:
        if not self.wisdom_dir.exists():
            return []
        return [f.stem for f in self.wisdom_dir.glob("*.md")]

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", "-t", help="Text to classify")
    parser.add_argument("--list", "-l", action="store_true", help="List available frames")
    parser.add_argument("--base-dir", default=str(Path.home() / ".claude"))
    args = parser.parse_args()
    classifier = WisdomDomainClassifier(Path(args.base_dir))
    if args.list:
        frames = classifier.list_frames()
        print(json.dumps(frames, indent=2))
    elif args.text:
        results = classifier.classify(args.text)
        print(json.dumps([{"domain": r.domain, "relevance": r.relevance,
            "primary_hits": r.primary_hits, "secondary_hits": r.secondary_hits} for r in results], indent=2))
    else:
        print("Usage: domain_classifier.py --text 'your text' or --list")

if __name__ == "__main__":
    main()
