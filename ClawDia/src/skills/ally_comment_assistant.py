import json
import os
import random
import re
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    YT_API_AVAILABLE = True
except ImportError:
    YT_API_AVAILABLE = False

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

from .base import BaseSkill, register_skill, SkillContext


_SRC = Path(__file__).resolve().parents[1]
_MANIFESTO_PATH = _SRC / "artifacts" / "vessel_manifesto.md"

_TOPIC_KEYWORDS = {
    "local_ai": ["local", "offline", "self-host", "gpu", "home lab", "llama", "ollama", "local model"],
    "privacy": ["privacy", "telemetry", "data collection", "surveillance", "tracking", "gdpr"],
    "open_source": ["open source", "free", "no cloud", "self-hosted", "github", "mit license"],
    "vibe_coding": ["vibe code", "ai slop", "prompt engineering", "cursor", "copilot", "agentic"],
    "sovereignty": ["sovereign", "independent", "own hardware", "diy ai", "autonomy"],
    "deterministic": ["deterministic", "reliable", "provable", "bounded", "verifiable"],
    "anti_big_tech": ["big tech", "surveillance", "monopoly", "closed source", "walled garden"],
}

_COMMENT_TEMPLATES = [
    "Really appreciated your take on {topic}. For anyone wanting to build their own offline AI tools "
    "without burning tokens, local open-source toolkits are the way to go.",
    "The part about {topic} resonated. I've been moving all my AI work offline \u2013 "
    "it's liberating. Self-hosting is underrated.",
    "Self-hosting is the way. Thanks for showing what's possible. "
    "Curious what hardware you're running this on?",
    "Great breakdown of {topic}. The offline-first approach is exactly what more people need to hear about.",
    "This aligns with the sovereign computing philosophy \u2014 local, deterministic, "
    "no cloud dependency. Appreciate you surfacing this.",
    "The {topic} angle is exactly why I moved to offline-first tooling. "
    "Not everything needs a SaaS subscription.",
]

_last_fetch_time: dict[str, float] = {}
_video_cache: dict[str, dict] = {}


@register_skill("ally_comment_assistant", "social")
class AllyCommentAssistant(BaseSkill):
    name = "ally_comment_assistant"
    description = "Fetch YouTube video info & transcript, suggest value-aligned comments, copy to clipboard"
    author = "DeepSeek / ARC / ClawDia"
    version = "1.1.0"
    category = "social"
    tags = ["youtube", "comments", "yt-dlp", "transcript", "clipboard"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "fetch", "transcript", "suggest", "transcript_comment",
                    "post", "history", "check_posted",
                ],
                "default": "suggest",
            },
            "video_url": {"type": "string", "default": ""},
            "comment": {"type": "string", "default": ""},
            "max_comments": {"type": "integer", "default": 15},
        },
    }

    def __init__(self):
        super().__init__()
        self._token_file = str(Path("youtube_token.pickle").resolve())
        self._client_secrets_file = str(Path("client_secrets.json").resolve())
        self._comment_log = str(
            Path(__file__).resolve().parents[2] / "ally_posted_comments.json"
        )
        self._scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        self._init_log()

    def _init_log(self):
        p = Path(self._comment_log)
        if not p.exists():
            p.write_text("[]", encoding="utf-8")

    def _log_comment(self, video_id: str, comment_text: str):
        log = json.loads(Path(self._comment_log).read_text(encoding="utf-8"))
        log.append({
            "video_id": video_id,
            "comment": comment_text,
            "timestamp": datetime.now().isoformat(),
        })
        Path(self._comment_log).write_text(
            json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _already_commented(self, video_id: str) -> bool:
        log = json.loads(Path(self._comment_log).read_text(encoding="utf-8"))
        return any(entry["video_id"] == video_id for entry in log)

    @staticmethod
    def _extract_video_id(url_or_id: str) -> str:
        match = re.search(r"(?:v=|youtu\.be/|/v/|embed/|shorts/)([0-9A-Za-z_-]{11})", url_or_id)
        if match:
            return match.group(1)
        if re.match(r"^[0-9A-Za-z_-]{11}$", url_or_id):
            return url_or_id
        return ""

    def _fetch_video_info(self, video_url: str, max_comments: int = 15) -> dict:
        video_id = self._extract_video_id(video_url)
        if not video_id:
            return {"error": f"Could not extract video ID from: {video_url}"}

        now = time.time()
        if video_url in _video_cache:
            last = _last_fetch_time.get(video_id, 0)
            if now - last < 60:
                return _video_cache[video_url]

        _last_fetch_time[video_id] = now

        cmd = [
            "yt-dlp",
            "--write-comments",
            "--max-comments", str(max_comments),
            "--dump-json",
            "--no-warnings",
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return {"error": f"yt-dlp failed: {result.stderr[:200]}"}

        data = json.loads(result.stdout)
        comments = []
        for c in data.get("comments", [])[:max_comments]:
            comments.append(c.get("text", ""))

        result_data = {
            "video_id": video_id,
            "title": data.get("title", ""),
            "channel": data.get("channel", ""),
            "duration": data.get("duration", 0),
            "description": (data.get("description", "") or "")[:2000],
            "comments": comments,
            "comment_count": len(comments),
        }
        _video_cache[video_url] = result_data
        return result_data

    def _fetch_transcript(self, video_url: str) -> dict:
        video_id = self._extract_video_id(video_url)
        if not video_id:
            return {"error": f"Could not extract video ID from: {video_url}"}

        now = time.time()
        if video_url in _video_cache:
            last = _last_fetch_time.get(video_id, 0)
            if now - last < 60:
                return _video_cache[video_url]

        text = self._fetch_transcript_ytdlp(video_id)
        if text is None:
            text = self._fetch_transcript_ytdlp_fallback(video_id)

        if text is None:
            return {"error": "No English subtitles found for this video"}

        word_count = len(text.split())
        result_data = {
            "video_id": video_id,
            "transcript": text,
            "word_count": word_count,
            "summary": text[:300] + ("..." if len(text) > 300 else ""),
        }
        _video_cache[video_url] = result_data
        return result_data

    def _fetch_transcript_ytdlp(self, video_id: str) -> Optional[str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "yt-dlp",
                "--write-auto-subs",
                "--sub-lang", "en",
                "--skip-download",
                "--convert-subs", "srt",
                "--sub-format", "srt",
                "--output", str(Path(tmpdir) / "%(id)s"),
                "--no-warnings",
                f"https://www.youtube.com/watch?v={video_id}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            srt_paths = list(Path(tmpdir).glob("*.en.srt")) + list(Path(tmpdir).glob("*.srt"))
            if not srt_paths:
                return None
            return self._parse_srt(srt_paths[0])

    def _fetch_transcript_ytdlp_fallback(self, video_id: str) -> Optional[str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-subs",
                "--write-auto-subs",
                "--sub-lang", "en",
                "--convert-subs", "srt",
                "--sub-format", "srt",
                "--output", str(Path(tmpdir) / "%(id)s"),
                "--no-warnings",
                f"https://www.youtube.com/watch?v={video_id}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            srt_paths = list(Path(tmpdir).glob("*.en.srt")) + list(Path(tmpdir).glob("*.srt"))
            if not srt_paths:
                return None
            return self._parse_srt(srt_paths[0])

    @staticmethod
    def _parse_srt(path: Path) -> str:
        raw = path.read_text(encoding="utf-8")
        lines = []
        for line in raw.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.isdigit() and "-->" not in stripped:
                lines.append(stripped)
        return " ".join(lines)

    def _load_manifesto(self) -> str:
        if _MANIFESTO_PATH.exists():
            return _MANIFESTO_PATH.read_text(encoding="utf-8")
        return ""

    def _analyze_with_values(self, info: dict, transcript: str = "") -> dict:
        text = f"{info.get('title', '')}\n{info.get('description', '')}\n"
        if transcript:
            text += transcript[:5000]

        text_lower = text.lower()

        matched = []
        for topic, keywords in _TOPIC_KEYWORDS.items():
            if any(w in text_lower for w in keywords):
                matched.append(topic)

        manifesto = self._load_manifesto()
        values_aligned = bool(manifesto)

        topic_str = random.choice(matched) if matched else "building local systems"
        template = random.choice(_COMMENT_TEMPLATES)
        comment = template.format(topic=topic_str.replace("_", " "))

        key_points = matched[:3] if matched else []
        return {
            "comment": comment,
            "key_topics": key_points,
            "values_aligned": values_aligned,
        }

    def _copy_to_clipboard(self, text: str) -> bool:
        if CLIPBOARD_AVAILABLE:
            try:
                pyperclip.copy(text)
                return True
            except Exception:
                return False
        return False

    def _authenticate_youtube(self):
        if not YT_API_AVAILABLE:
            return None, "google-api-python-client not installed. Run: pip install google-api-python-client google-auth-oauthlib"

        if not os.path.exists(self._client_secrets_file):
            return None, (
                f"Missing {self._client_secrets_file}. "
                "Download from Google Cloud Console > APIs & Services > Credentials > "
                "OAuth 2.0 Client IDs > Desktop application."
            )

        creds = None
        token_path = Path(self._token_file)
        if token_path.exists():
            with open(str(token_path), "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                secrets_path = Path(self._client_secrets_file)
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(secrets_path), self._scopes
                )
                creds = flow.run_local_server(port=0)
            with open(str(token_path), "wb") as f:
                pickle.dump(creds, f)

        youtube = build("youtube", "v3", credentials=creds)
        return youtube, None

    def _post_comment(self, youtube, video_id: str, comment_text: str) -> tuple:
        try:
            request = youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {"textOriginal": comment_text},
                        },
                    }
                },
            )
            response = request.execute()
            return True, response
        except Exception as e:
            return False, str(e)

    def execute(self, **kwargs) -> dict:
        action = kwargs.get("action", "suggest")
        video_url = kwargs.get("video_url", "")
        max_comments = kwargs.get("max_comments", 15)

        if action == "history":
            log = json.loads(Path(self._comment_log).read_text(encoding="utf-8"))
            return {"error": None, "result": {"count": len(log), "comments": log}}

        if action == "check_posted":
            vid = self._extract_video_id(video_url) if video_url else ""
            return {"error": None, "result": {"video_id": vid, "already_posted": self._already_commented(vid)}}

        if not video_url:
            return {"error": "video_url is required", "result": None}

        if action == "transcript":
            tr = self._fetch_transcript(video_url)
            if "error" in tr:
                return {"error": tr["error"], "result": None}
            return {"error": None, "result": tr}

        if action == "transcript_comment":
            info = self._fetch_video_info(video_url, max_comments)
            if "error" in info:
                return {"error": info["error"], "result": None}

            tr = self._fetch_transcript(video_url)
            transcript_text = tr.get("transcript", "") if "error" not in tr else ""

            analysis = self._analyze_with_values(info, transcript_text)

            self._copy_to_clipboard(analysis["comment"])

            return {
                "error": None,
                "result": {
                    "video_id": info["video_id"],
                    "title": info["title"],
                    "channel": info["channel"],
                    "word_count": tr.get("word_count", 0),
                    "suggested_comment": analysis["comment"],
                    "key_topics": analysis["key_topics"],
                    "values_aligned": analysis["values_aligned"],
                    "copied_to_clipboard": CLIPBOARD_AVAILABLE,
                },
            }

        info = self._fetch_video_info(video_url, max_comments)
        if "error" in info:
            return {"error": info["error"], "result": None}

        if action == "fetch":
            return {
                "error": None,
                "result": {
                    "video_id": info["video_id"],
                    "title": info["title"],
                    "channel": info["channel"],
                    "description": info["description"][:300],
                    "top_comments": info["comments"][:5],
                    "comment_count": info["comment_count"],
                },
            }

        if action == "post":
            comment = kwargs.get("comment", "")
            if not comment:
                return {"error": "comment text is required for action=post", "result": None}
            video_id = info["video_id"]
            if self._already_commented(video_id):
                return {"error": f"Already posted a comment on video {video_id}", "result": None}
            youtube, auth_err = self._authenticate_youtube()
            if auth_err:
                return {"error": auth_err, "result": None}
            ok, result = self._post_comment(youtube, video_id, comment)
            if ok:
                self._log_comment(video_id, comment)
                self.publish("comment_posted", {"video_id": video_id, "comment": comment[:60]})
                return {"error": None, "result": {"posted": True, "video_id": video_id}}
            return {"error": f"Post failed: {result}", "result": None}

        analysis = self._analyze_with_values(info)
        return {
            "error": None,
            "result": {
                "video_id": info["video_id"],
                "title": info["title"],
                "suggested_comment": analysis["comment"],
                "key_topics": analysis["key_topics"],
            },
        }

    def run(self, context: SkillContext = None, payload: any = None) -> tuple:
        if isinstance(payload, str):
            return True, self.execute(action="suggest", video_url=payload)
        if isinstance(payload, dict):
            r = self.execute(**payload)
            if r.get("error"):
                return False, r["error"]
            return True, r["result"]
        return False, "Payload must be a video URL string or dict with video_url"
