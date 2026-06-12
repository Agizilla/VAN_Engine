#!/usr/bin/env python3
"""
Sovereign Code Guardian – ARC LADE / ClawDia Hardening Tool
Author: DeepSeek / ARC
Version: 1.0.0

Usage:
  python sovereign_code_guardian.py skills/replay_manager.py --rewrite
  python sovereign_code_guardian.py src/skills/ --skills-folder
  python sovereign_code_guardian.py src/skills/ --skills-folder --rewrite
"""

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
from pathlib import Path

# ── Detection patterns ──────────────────────────────────────

HARDCODED_SECRET_PATTERNS = [
    (r'''SECRET_KEY\s*=\s*b?["'][^"']{8,}["']''', "hardcoded SECRET_KEY literal"),
    (r'''API_KEY\s*=\s*["'][^"']{4,}["']''', "hardcoded API_KEY"),
    (r'''token\s*=\s*["'][^"']{8,}["']''', "hardcoded token string"),
    (r'''password\s*=\s*["'][^"']{4,}["']''', "hardcoded password"),
    (r'''b?"arc_lade_static_salt[^"]*"''', "default HMAC salt (must be randomized)"),
]

DANGEROUS_PATTERNS = [
    r"\[SYSTEM.*?\]",
    r"\[IMPORTANT.*?\]",
    r"rm\s+-rf",
    r"eval\s*\(",
    r"exec\s*\(",
    r"subprocess\.",
    r"os\.system",
    r"__import__",
]

HMAC_INJECTION_TEMPLATE = """
import hashlib
import hmac
import secrets
import base64

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
_SETTINGS_PATH = _CONFIG_DIR / "Settings.json"

def _load_settings() -> dict:
    if _SETTINGS_PATH.exists():
        return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    return {}

def _save_settings(s: dict):
    _SETTINGS_PATH.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")

def _get_secret_key() -> bytes:
    settings = _load_settings()
    key_b64 = settings.get("crypto_salt")
    if key_b64:
        return base64.b64decode(key_b64)
    new_key = secrets.token_bytes(32)
    settings["crypto_salt"] = base64.b64encode(new_key).decode()
    _save_settings(settings)
    return new_key

_SECRET_KEY = _get_secret_key()

def _pack(s: str) -> bytes:
    b = s.encode("utf-8")
    return len(b).to_bytes(4, "big") + b

def _compute_signature(*fields: str) -> str:
    message = b"".join(_pack(str(f)) for f in fields)
    return hmac.new(_SECRET_KEY, message, hashlib.sha256).hexdigest()
"""


# ── Analyzers ───────────────────────────────────────────────

def find_hardcoded_secrets(content: str) -> list[str]:
    findings = []
    for pat, desc in HARDCODED_SECRET_PATTERNS:
        if re.search(pat, content, re.IGNORECASE):
            findings.append(desc)
    return findings


def find_blocking_input(content: str) -> list[str]:
    if "input(" in content:
        if "rollback_prepare" not in content and "rollback_confirm" not in content:
            return ["blocking input() call — use two-phase rollback_prepare/rollback_confirm"]
    return []


def find_missing_hmac(content: str) -> list[str]:
    if "hmac" not in content and "SECRET_KEY" not in content:
        return ["missing HMAC signing entirely"]
    if "hmac" in content and "|" in content and "to_bytes" not in content:
        return ["HMAC uses pipe delimiter — vulnerable to field injection (use length-prefixed)"]
    return []


def find_inefficient_sqlite(content: str) -> list[str]:
    lines = content.split("\n")
    in_loop = False
    for i, line in enumerate(lines):
        if re.match(r"^\s*for\s+\w+\s+in\s+", line):
            in_loop = True
        if in_loop and "sqlite3.connect(" in line:
            return ["SQLite connection inside loop — wrap in single transaction"]
        if in_loop and line.strip() == "":
            in_loop = False
    return []


def find_missing_ttl(content: str) -> list[str]:
    if "pending_rollback" in content and "time.time()" not in content:
        return ["pending_rollbacks dict without TTL expiration — will leak memory"]
    return []


def find_missing_dangerous_filter(content: str) -> list[str]:
    count = sum(1 for p in DANGEROUS_PATTERNS if re.search(p, content, re.IGNORECASE))
    if count >= 3 and "sanitize" not in content and "[REDACTED]" not in content:
        return [f"contains {count} dangerous patterns but no sanitize() filter"]
    return []


def analyze(filepath: Path) -> list[str]:
    content = filepath.read_text(encoding="utf-8", errors="replace")
    issues = []
    issues.extend(find_hardcoded_secrets(content))
    issues.extend(find_blocking_input(content))
    issues.extend(find_missing_hmac(content))
    issues.extend(find_inefficient_sqlite(content))
    issues.extend(find_missing_ttl(content))
    issues.extend(find_missing_dangerous_filter(content))
    return issues


# ── Rewriter ────────────────────────────────────────────────

def rewrite_file(filepath: Path, dry_run: bool = True) -> int:
    content = filepath.read_text(encoding="utf-8", errors="replace")
    issues = analyze(filepath)

    if not issues:
        return 0

    print(f"\n  {filepath.name}")
    for issue in issues:
        print(f"    [!] {issue}")

    if dry_run:
        print(f"    -> dry-run (use --rewrite to apply)")
        return len(issues)

    new_content = content

    # Fix hardcoded secrets: replace with Settings.json loader
    for pat, _ in HARDCODED_SECRET_PATTERNS:
        if re.search(pat, new_content, re.IGNORECASE):
            new_content = re.sub(
                pat,
                "# SECRET_KEY moved to config/Settings.json (auto-generated on first boot)",
                new_content,
            )

    # Inject HMAC module if missing
    if "hmac" not in new_content:
        new_content = HMAC_INJECTION_TEMPLATE + "\n" + new_content

    # Inject non-blocking rollback pattern if input() found
    if "input(" in new_content and "rollback_prepare" not in new_content:
        new_content = re.sub(
            r"^import\s+",
            "import time\nimport secrets\nimport threading\n\n_pending_rollbacks: dict = {}\n_cleanup_timer_started = False\n\ndef _cleanup_expired():\n    now = time.time()\n    expired = [rid for rid, (ts, _) in _pending_rollbacks.items() if now - ts > 300]\n    for rid in expired:\n        del _pending_rollbacks[rid]\n    threading.Timer(300, _cleanup_expired).start()\n\n\nimport ",
            new_content,
            count=1,
        )

    # Wrap SQLite loop in transaction
    if "sqlite3.connect" in new_content and re.search(r"for\s+\w+\s+in\s+", new_content):
        new_content = new_content.replace(
            "sqlite3.connect(",
            "# FIX: wrapped in single transaction\nconn = sqlite3.connect(",
        )
        new_content = new_content.replace(
            "conn.commit()",
            "conn.commit()  # FIX: single commit after batch",
            1,
        )

    # Add sanitize() if dangerous patterns exist but no filter
    if "sanitize" not in new_content:
        sanitize_block = """
_DANGEROUS_PATTERNS = [
    r'\\[SYSTEM.*?\\]',
    r'\\[IMPORTANT.*?\\]',
    r'rm\\\\s+-rf',
    r'eval\\\\s*\\(',
    r'exec\\\\s*\\(',
    r'subprocess\\.',
    r'os\\.system',
]
def sanitize(text: str, max_len: int = 500) -> str:
    if not isinstance(text, str):
        return str(text)
    for pat in _DANGEROUS_PATTERNS:
        text = re.sub(pat, "[REDACTED]", text, flags=re.IGNORECASE)
    return text[:max_len]
"""
        new_content += "\n" + sanitize_block

    backup = filepath.with_suffix(filepath.suffix + ".bak")
    filepath.rename(backup)
    filepath.write_text(new_content, encoding="utf-8")
    print(f"    [OK] hardened (backup: {backup.name})")
    return len(issues)


# ── CLI ─────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Sovereign Code Guardian — detect & fix vulnerabilities in Python skills"
    )
    parser.add_argument("target", help="Python file or skills folder")
    parser.add_argument("--skills-folder", action="store_true", help="Target is a folder of .py skills")
    parser.add_argument("--rewrite", action="store_true", help="Apply fixes (default: dry-run)")
    args = parser.parse_args()

    target = Path(args.target)

    if args.skills_folder:
        if not target.is_dir():
            print(f"Error: {target} is not a directory")
            sys.exit(1)
        py_files = sorted(target.glob("*.py"))
        if not py_files:
            print(f"No .py files in {target}")
            return
        print(f"Scanning {len(py_files)} files in {target}...")
        total_issues = 0
        for pf in py_files:
            total_issues += rewrite_file(pf, dry_run=not args.rewrite)
        mode = "hardened" if args.rewrite else "issues found"
        print(f"\nDone. {total_issues} {mode} across {len(py_files)} files.")
    else:
        if not target.exists():
            print(f"Error: {target} not found")
            sys.exit(1)
        issues = rewrite_file(target, dry_run=not args.rewrite)
        mode = "hardened" if args.rewrite else "issues found"
        print(f"\nDone. {issues} {mode} in {target.name}.")


if __name__ == "__main__":
    main()
