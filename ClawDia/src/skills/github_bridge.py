"""GitHub Bridge — versioned, auditable agent-repo interaction layer.

Actions:
  commit        — Write content to a file in the repo and push
  create_pr     — Open a pull request
  list_issues   — Query open issues with optional label filter
  list_forks    — Enumerate forks of the repo
  repo_status   — Summary of repo state (branch, SHA, desc)
  create_repo   — Initialize repo on GitHub if it doesn't exist

Uses `gh` CLI (must be authenticated). Falls back to direct API calls with token.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

try:
    from .base import BaseSkill, register_skill
except ImportError:
    from skills.base import BaseSkill, register_skill


def _gh(args: list[str], input_data: str | None = None) -> dict | list:
    """Run `gh` CLI and return parsed JSON output.

    Raises RuntimeError on non-zero exit.
    """
    cmd = ["gh"] + args
    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"gh command timed out: {' '.join(args)}")

    if result.returncode != 0:
        err = result.stderr.strip() or "unknown error"
        raise RuntimeError(f"gh {' '.join(args)} failed: {err}")

    out = result.stdout.strip()
    if not out:
        return {}
    return json.loads(out)


@register_skill("github_bridge", "integration")
class GitHubBridgeSkill(BaseSkill):
    name = "github_bridge"
    description = "Versioned, auditable agent-repo interaction — commit, PR, issues, forks, releases"
    category = "integration"
    version = "1.0.0"
    author = "ClawDia / OpenCode"
    tags = ["github", "version-control", "agents", "integration", "ci-cd"]
    required_libs = []

    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["commit", "create_pr", "list_issues", "list_forks", "repo_status", "create_repo"],
                "description": "GitHub operation to perform",
            },
            "repo": {
                "type": "string",
                "description": "owner/repo (e.g. Agizilla/VAN_Engine). Defaults to GITHUB_REPO env var.",
                "default": "",
            },
            "branch": {
                "type": "string",
                "description": "Target branch (commit, create_pr). Default: main",
                "default": "main",
            },
            "path": {
                "type": "string",
                "description": "File path within repo (commit action)",
                "default": "",
            },
            "content": {
                "type": "string",
                "description": "File content to write (commit action)",
                "default": "",
            },
            "message": {
                "type": "string",
                "description": "Commit message (commit action) or PR title (create_pr action)",
                "default": "",
            },
            "body": {
                "type": "string",
                "description": "PR body (create_pr action)",
                "default": "",
            },
            "head": {
                "type": "string",
                "description": "Source branch for PR (create_pr). Default: auto-generated branch name",
                "default": "",
            },
            "base": {
                "type": "string",
                "description": "Target branch for PR (create_pr). Default: main",
                "default": "main",
            },
            "labels": {
                "type": "array",
                "description": "Label filter for issues (list_issues)",
                "items": {"type": "string"},
                "default": [],
            },
            "state": {
                "type": "string",
                "enum": ["open", "closed", "all"],
                "description": "Issue state filter (list_issues)",
                "default": "open",
            },
            "limit": {
                "type": "integer",
                "description": "Max results (list_issues, list_forks)",
                "default": 10,
                "minimum": 1,
                "maximum": 100,
            },
            "description": {
                "type": "string",
                "description": "Repo description (create_repo)",
                "default": "VAN_Engine — SAAS Hooks + ClawDia Skill Registry",
            },
            "visibility": {
                "type": "string",
                "enum": ["public", "private"],
                "description": "Repo visibility (create_repo)",
                "default": "public",
            },
        },
        "required": ["action"],
    }

    output_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "status": {"type": "string"},
            "data": {},
            "message": {"type": "string"},
        },
    }

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "").strip().lower()
        repo = kwargs.get("repo", "").strip() or os.environ.get("GITHUB_REPO", "")

        if not repo:
            return {
                "result": {
                    "action": action,
                    "status": "error",
                    "message": "repo is required (pass owner/repo or set GITHUB_REPO env var)",
                }
            }

        handlers = {
            "commit": self._commit,
            "create_pr": self._create_pr,
            "list_issues": self._list_issues,
            "list_forks": self._list_forks,
            "repo_status": self._repo_status,
            "create_repo": self._create_repo,
        }

        handler = handlers.get(action)
        if not handler:
            return {
                "result": {"action": action, "status": "error", "message": f"Unknown action: {action}"},
            }

        try:
            data = handler(repo, **kwargs)
            return {"result": {"action": action, "status": "ok", "data": data}}
        except RuntimeError as e:
            return {"result": {"action": action, "status": "error", "message": str(e)}}

    def _resolve_repo(self):
        """Return (owner, name) from GITHUB_REPO or git remote."""
        repo = os.environ.get("GITHUB_REPO", "")
        if "/" in repo:
            parts = repo.split("/")
            return parts[0], parts[1]
        try:
            out = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=5,
            )
            url = out.stdout.strip()
            if "github.com" in url:
                parts = url.rstrip(".git").split("github.com/")[-1].split("/")
                return parts[0], parts[1]
        except Exception:
            pass
        return None, None

    def _commit(self, repo: str, **kwargs) -> dict:
        path = kwargs.get("path", "").strip()
        content = kwargs.get("content", "")
        message = kwargs.get("message", "").strip() or f"agent commit: update {path}"
        branch = kwargs.get("branch", "main").strip()

        if not path:
            raise RuntimeError("path is required for commit action")
        if not content:
            raise RuntimeError("content is required for commit action")

        result = _gh([
            "api", f"/repos/{repo}/contents/{path}",
            "--method", "PUT",
            "--field", f"message={message}",
            "--field", f"content={content}",
            "--field", f"branch={branch}",
        ])

        sha = result.get("content", {}).get("sha", "") if isinstance(result, dict) else ""
        return {
            "path": path,
            "branch": branch,
            "commit_sha": sha,
            "message": message,
        }

    def _create_pr(self, repo: str, **kwargs) -> dict:
        title = kwargs.get("message", "").strip() or kwargs.get("title", "")
        body = kwargs.get("body", "").strip()
        head = kwargs.get("head", "").strip()
        base = kwargs.get("base", "main").strip()

        if not title:
            raise RuntimeError("message (PR title) is required for create_pr")
        if not head:
            raise RuntimeError("head branch is required for create_pr")

        args = [
            "api", f"/repos/{repo}/pulls",
            "--method", "POST",
            "--field", f"title={title}",
            "--field", f"head={head}",
            "--field", f"base={base}",
        ]
        if body:
            args.extend(["--field", f"body={body}"])

        result = _gh(args)
        return {
            "pr_number": result.get("number"),
            "pr_url": result.get("html_url", ""),
            "title": title,
            "state": result.get("state", "open"),
        }

    def _list_issues(self, repo: str, **kwargs) -> dict:
        labels = kwargs.get("labels", [])
        state = kwargs.get("state", "open").strip()
        limit = kwargs.get("limit", 10)

        args = [
            "api",
            f"/repos/{repo}/issues?state={state}&per_page={limit}&sort=updated&direction=desc",
        ]

        raw = _gh(args)
        issues = []
        for item in (raw if isinstance(raw, list) else []):
            if "pull_request" in item:
                continue
            issues.append({
                "number": item.get("number"),
                "title": item.get("title"),
                "state": item.get("state"),
                "labels": [l.get("name") for l in item.get("labels", [])],
                "updated_at": item.get("updated_at"),
                "url": item.get("html_url", ""),
            })

        if labels:
            label_set = set(labels)
            issues = [i for i in issues if label_set & set(i["labels"])]

        return {"count": len(issues), "issues": issues}

    def _list_forks(self, repo: str, **kwargs) -> dict:
        limit = kwargs.get("limit", 10)
        raw = _gh(["api", f"/repos/{repo}/forks?per_page={limit}&sort=newest"])
        forks = []
        for f in (raw if isinstance(raw, list) else []):
            forks.append({
                "owner": f.get("owner", {}).get("login"),
                "full_name": f.get("full_name"),
                "url": f.get("html_url", ""),
                "stars": f.get("stargazers_count", 0),
                "description": f.get("description", ""),
            })
        return {"count": len(forks), "forks": forks}

    def _repo_status(self, repo: str, **kwargs) -> dict:
        raw = _gh(["api", f"/repos/{repo}"])
        return {
            "full_name": raw.get("full_name"),
            "description": raw.get("description", ""),
            "default_branch": raw.get("default_branch", "main"),
            "visibility": raw.get("visibility", "public"),
            "open_issues": raw.get("open_issues_count", 0),
            "stars": raw.get("stargazers_count", 0),
            "forks": raw.get("forks_count", 0),
            "topics": raw.get("topics", []),
            "pushed_at": raw.get("pushed_at", ""),
            "url": raw.get("html_url", ""),
        }

    def _create_repo(self, repo: str, **kwargs) -> dict:
        desc = kwargs.get("description", "VAN_Engine — SAAS Hooks + ClawDia Skill Registry")
        visibility = kwargs.get("visibility", "public").strip()

        owner, name = repo.split("/")

        try:
            _gh(["repo", "view", repo, "--json", "name"])
            return {"message": f"Repo {repo} already exists", "created": False}
        except RuntimeError:
            pass

        result = _gh([
            "api", "/user/repos",
            "--method", "POST",
            "--field", f"name={name}",
            "--field", f"description={desc}",
            "--field", f"private={str(visibility == 'private').lower()}",
            "--field", "auto_init=false",
        ])

        return {
            "message": f"Created {repo}",
            "created": True,
            "url": result.get("html_url", ""),
        }
