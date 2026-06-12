#!/usr/bin/env python3
import sys, io, json, re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
from dataclasses import dataclass, field

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

@dataclass
class FileChange:
    path: str
    action: str
    relative_path: str

@dataclass
class ActivityCategories:
    skills: List[FileChange] = field(default_factory=list)
    workflows: List[FileChange] = field(default_factory=list)
    tools: List[FileChange] = field(default_factory=list)
    hooks: List[FileChange] = field(default_factory=list)
    architecture: List[FileChange] = field(default_factory=list)
    other: List[FileChange] = field(default_factory=list)

@dataclass
class ParsedActivity:
    date: str
    categories: ActivityCategories
    summary: str
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    skills_affected: Set[str] = field(default_factory=set)
    session_id: str = ""
    error: str = ""

class ActivityParser:
    SKIP_PATTERNS = [
        r"MEMORY/UPDATES/", r"MEMORY/",
        r"WORK/.*/scratch/", r"\.quote-cache$",
        r"history\.jsonl$", r"cache/", r"plans/"
    ]
    CATEGORY_PATTERNS = {
        "skills": r"skills/[^/]+/",
        "workflows": r"Workflows/",
        "tools": r"skills/[^/]+/Tools/",
        "hooks": r"hooks/",
        "architecture": r"(ARCHITECTURE|PAISYSTEMARCHITECTURE|SKILLSYSTEM)\.md$"
    }

    def __init__(self, base_directory: Path):
        self.session_dir = base_directory / "sessions"
        self.updates_dir = base_directory / "MEMORY" / "UPDATES"
        self.updates_dir.mkdir(parents=True, exist_ok=True)

    def parse_today(self, session_filter: str = None) -> ParsedActivity:
        since = datetime.now() - timedelta(days=1)
        session_files = self._get_session_files(since, session_filter)
        return self._parse_activity(session_files)

    def parse_session(self, session_id: str) -> ParsedActivity:
        session_file = self.session_dir / f"{session_id}.jsonl"
        if not session_file.exists():
            return ParsedActivity(date="", categories=ActivityCategories(),
                summary="", error=f"Session not found: {session_id}")
        return self._parse_activity([session_file])

    def _get_session_files(self, since: datetime, session_filter: str = None) -> List[Path]:
        if not self.session_dir.exists():
            return []
        files = [f for f in self.session_dir.glob("*.jsonl") if f.stat().st_mtime >= since.timestamp()]
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        if session_filter:
            files = [f for f in files if session_filter in str(f)]
        return files

    def _parse_activity(self, session_files: List[Path]) -> ParsedActivity:
        activity = ParsedActivity(date=datetime.now().strftime("%Y-%m-%d"),
            categories=ActivityCategories(), summary="")
        files_modified = set()
        files_created = set()
        for session_file in session_files:
            try:
                content = session_file.read_text(encoding='utf-8')
                for line in content.split('\n'):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get('type') != 'assistant':
                            continue
                        content_blocks = entry.get('message', {}).get('content', [])
                        for block in content_blocks:
                            if block.get('type') != 'tool_use':
                                continue
                            tool_name = block.get('name')
                            tool_input = block.get('input', {})
                            if tool_name == 'Write' and 'file_path' in tool_input:
                                file_path = tool_input['file_path']
                                if '/.claude/' in file_path:
                                    files_created.add(file_path)
                            elif tool_name == 'Edit' and 'file_path' in tool_input:
                                file_path = tool_input['file_path']
                                if '/.claude/' in file_path:
                                    files_modified.add(file_path)
                    except json.JSONDecodeError:
                        continue
            except:
                continue
        files_modified -= files_created
        activity.files_created = list(files_created)
        activity.files_modified = list(files_modified)
        for f in files_created:
            self._categorize_file(f, "created", activity)
        for f in files_modified:
            self._categorize_file(f, "modified", activity)
        summary_parts = []
        if activity.skills_affected:
            summary_parts.append(f"{len(activity.skills_affected)} skill(s) affected")
        if activity.categories.tools:
            summary_parts.append(f"{len(activity.categories.tools)} tool(s)")
        if activity.categories.hooks:
            summary_parts.append(f"{len(activity.categories.hooks)} hook(s)")
        if activity.categories.workflows:
            summary_parts.append(f"{len(activity.categories.workflows)} workflow(s)")
        activity.summary = ", ".join(summary_parts) if summary_parts else "documentation updates"
        return activity

    def _categorize_file(self, file_path: str, action: str, activity: ParsedActivity):
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return
        skill_match = re.search(r'skills[/\\]([^/\\]+)[/\\]', file_path)
        if skill_match:
            activity.skills_affected.add(skill_match.group(1))
        category = "other"
        for cat, pattern in self.CATEGORY_PATTERNS.items():
            if re.search(pattern, file_path, re.IGNORECASE):
                category = cat
                break
        change = FileChange(path=file_path, action=action, relative_path=self._get_relative_path(file_path))
        getattr(activity.categories, category).append(change)

    def _get_relative_path(self, full_path: str) -> str:
        idx = full_path.find("/.claude/")
        if idx == -1:
            idx = full_path.find("\\.claude\\")
        return full_path[idx + 9:] if idx != -1 else full_path

    def generate_update_file(self, activity: ParsedActivity) -> Path:
        timestamp = datetime.now().isoformat()
        slug = re.sub(r'[^a-z0-9]+', '-', activity.summary.lower()).strip('-')
        year_month = datetime.now().strftime("%Y/%m")
        update_dir = self.updates_dir / year_month
        update_dir.mkdir(parents=True, exist_ok=True)
        update_path = update_dir / f"{activity.date}_{slug}.md"
        content = f"""---
id: "{activity.date}-{slug}"
timestamp: "{timestamp}"
title: "System Update: {activity.summary}"
significance: "moderate"
change_type: "multi_area"
files_affected:
{chr(10).join(f'  - "{self._get_relative_path(f)}"' for f in activity.files_created[:10])}
{chr(10).join(f'  - "{self._get_relative_path(f)}"' for f in activity.files_modified[:10])}
---

# System Update: {activity.summary}

**Timestamp:** {timestamp}
**Significance:** Moderate
**Change Type:** Multi-Area

## Summary
{activity.summary}

## Changes Made
### Skills
{chr(10).join(f'- `{{c.relative_path}}` - {{c.action}}' for c in activity.categories.skills)}
### Tools
{chr(10).join(f'- `{{c.relative_path}}` - {{c.action}}' for c in activity.categories.tools)}
### Hooks
{chr(10).join(f'- `{{c.relative_path}}` - {{c.action}}' for c in activity.categories.hooks)}

## Integrity Check
- **References Found:** 0
- **References Updated:** 0

## Verification
*Auto-generated from session activity.*

---
**Status:** Auto-generated
"""
        update_path.write_text(content, encoding='utf-8')
        return update_path

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--today", action="store_true", help="Parse today's activity")
    parser.add_argument("--session", help="Parse specific session")
    parser.add_argument("--generate", action="store_true", help="Generate update file")
    parser.add_argument("--base-dir", default=str(Path.home() / ".claude"))
    args = parser.parse_args()
    parser_obj = ActivityParser(Path(args.base_dir))
    if args.session:
        activity = parser_obj.parse_session(args.session)
    else:
        activity = parser_obj.parse_today()
    if args.generate:
        path = parser_obj.generate_update_file(activity)
        print(json.dumps({"filepath": str(path), "activity": activity.__dict__}, indent=2, default=str))
    else:
        print(json.dumps({"date": activity.date, "summary": activity.summary,
            "files_created": len(activity.files_created), "files_modified": len(activity.files_modified),
            "skills_affected": list(activity.skills_affected)}, indent=2))

if __name__ == "__main__":
    main()
