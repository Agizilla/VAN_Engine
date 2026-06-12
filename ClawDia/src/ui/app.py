import re
from typing import Any, Optional

from .console import ConsoleUI
from .menu import Menu
from ..skills.base import BaseSkill
from ..skills.loader import SkillLoader


class WizardState:
    active: bool = False
    scan_path: str = ""
    scan_result: dict = {}
    welcome_data: dict = {}
    selected_ext: str = ""
    selected_action: str = ""
    action_data: dict = {}
    files: list[dict] = []

    def reset(self):
        self.active = False
        self.scan_path = ""
        self.scan_result = {}
        self.welcome_data = {}
        self.selected_ext = ""
        self.selected_action = ""
        self.action_data = {}
        self.files = []


class ClawDiaApp:
    def __init__(self, skills_dir: Optional[str] = None):
        self.ui = ConsoleUI()
        self.skill_loader = SkillLoader(skills_dir)
        self.skills: list[BaseSkill] = []
        self._voice = None
        self._agent = None

    def run(self):
        self.ui.welcome()
        self.skills = self.skill_loader.discover_skills()
        self.ui.success(f"Loaded {len(self.skills)} skills")
        self._init_agent()
        self.ui.divider()

        main_menu = Menu("ClawDia")
        main_menu.add("Run Skill", self._handle_run_skill)
        main_menu.add("Chat with Agent", self._handle_agent_chat)
        main_menu.add("List Skills", self._handle_list_skills)
        main_menu.add("Voice Mode", self._handle_voice_mode)
        main_menu.add("Quit", lambda _: None)

        while True:
            result = main_menu.show()
            if result is None:
                break
            self.ui.divider()

    def _init_agent(self):
        try:
            from ..agent.skill import AgentSkill
            self._agent = AgentSkill()
            self.ui.info("Agent core loaded (LM Studio required)")
        except Exception as e:
            self.ui.warning(f"Agent core not available: {e}")
            self._agent = None

    def _handle_agent_chat(self, item):
        if self._agent is None:
            self.ui.warning("Agent not available — check LM Studio")
            return
        if not self._agent.ensure_loop():
            self.ui.warning("LM Studio not running")
            return
        self.ui.info("Chat with ClawDia (type /reset to clear, /quit to exit)")
        while True:
            msg = self.ui.prompt_text("You")
            if msg is None or msg.lower() in ("/quit", "/exit"):
                break
            if msg.lower() == "/reset":
                self._agent.reset()
                self.ui.info("Memory cleared")
                continue
            if not msg.strip():
                continue
            with self.ui.spinner() as p:
                p.add_task(description="Thinking...", total=None)
                result = self._agent.execute(message=msg)
            if result.get("error"):
                self.ui.warning(result["error"])
            else:
                self.ui.echo(f"ClawDia: {result['response']}")

    def _handle_run_skill(self, item):
        if not self.skills:
            self.ui.warning("No skills available")
            return
        self.ui.table(
            ["#", "Skill", "Category", "Description"],
            [[i + 1, s.name, s.category, s.description] for i, s in enumerate(self.skills)],
            "Available Skills",
        )
        idx = self.ui.prompt_int("Enter skill number (0 to cancel)")
        if not idx or idx < 1 or idx > len(self.skills):
            return
        skill = self.skills[idx - 1]
        self.ui.info(f"Running: {skill.name}...")
        with self.ui.spinner() as p:
            p.add_task(description=f"Executing {skill.name}...", total=None)
            result = skill.execute()
        self.ui.echo(str(result))

    def _handle_list_skills(self, item):
        if not self.skills:
            self.ui.warning("No skills loaded")
            return
        self.ui.table(
            ["Name", "Category", "Description"],
            [[s.name, s.category, s.description] for s in self.skills],
            "Loaded Skills",
        )

    @property
    def voice(self):
        if self._voice is None:
            from ..voice.loop import VoiceLoop
            self._voice = VoiceLoop(self.ui)
        return self._voice

    def _handle_voice_mode(self, item):
        self.voice.warmup()
        agent_available = self._agent is not None and self._agent.ensure_loop() is not None
        if agent_available:
            self.ui.success("Agent connected — voice conversations active")

        wizard = WizardState()

        def on_command(text: str) -> Optional[str]:
            text_lower = text.lower().strip()

            if text_lower in ("quit", "exit", "goodbye"):
                wizard.reset()
                self.voice.stop()
                return "Logging off. The echo is quiet."

            if text_lower in ("cancel", "stop", "never mind"):
                wizard.reset()
                return "Cancelled. I'm here when you need me."

            if wizard.active:
                return _handle_wizard_turn(text, wizard)

            if "list" in text_lower and "skill" in text_lower:
                names = ", ".join(s.name for s in self.skills)
                return f"Loaded: {names}"

            if any(w in text_lower for w in ("wizard", "batch", "scan my", "point me")):
                return _start_wizard(text, wizard)

            if any(w in text_lower for w in ("look up", "search artist", "find artist", "who is", "lexicon")):
                return _handle_lexicon(text)

            if "chord" in text_lower or "chords" in text_lower:
                return _run_skill_text("chord_detection", text, {"action": "detect"})

            if "play" in text_lower and "midi" in text_lower:
                return _run_skill_text("midi_playback", text, {"action": "play"})

            if "transcribe" in text_lower:
                return _run_skill_text("audio_transcribe", text, {"action": "transcribe"})

            if any(w in text_lower for w in ("analyze", "tempo", "bpm", "audio analyze")):
                return _run_skill_text("audio_analyze", text)

            if "key" in text_lower and any(w in text_lower for w in ("detect", "what key", "musical key")):
                return _run_skill_text("chord_detection", text, {"action": "key"})

            # ── Meme Forge ──────────────────────────────────────
            if any(w in text_lower for w in ("tell me a joke", "tell me a meme", "make me laugh", "crack me up")):
                return _run_skill_text("meme_forge", text)

            if any(w in text_lower for w in ("meme about", "joke about")):
                return _run_meme_forge_topic(text)

            if any(w in text_lower for w in ("show meme", "show me the", "display meme", "meme id")):
                return _run_humor_meme_id(text)

            # ── Humor Collection ────────────────────────────────
            if any(w in text_lower for w in ("ascii art", "show me ascii", "random ascii", "slapback")):
                return _run_skill_text("humor_meme", text, {"action": "random"})

            if any(w in text_lower for w in ("list memes", "list ascii", "what memes")):
                r = _run_skill_text("humor_meme", text, {"action": "list"})
                return r

            # ── Dirty Talker ────────────────────────────────────
            if any(w in text_lower for w in ("dirty talk", "talk dirty", "say something dirty", "nsfw")):
                return _run_skill_text("dirty_talker", text)

            if any(w in text_lower for w in ("dirty about", "nsfw category")):
                return _run_dirty_talker_category(text)

            if any(w in text_lower for w in ("dirty batch", "nsfw batch", "multiple dirty")):
                return _run_skill_text("dirty_talker", text, {"action": "batch", "count": 5})

            if any(w in text_lower for w in ("dirty info", "dirty tokens", "nsfw tokens")):
                return _run_skill_text("dirty_talker", text, {"action": "info"})

            # ── Voice Trainer ────────────────────────────────────
            if any(w in text_lower for w in ("say this with piper", "speak through piper", "use my voice")):
                return _run_voice_trainer_speak(text)

            if any(w in text_lower for w in ("record audio", "record voice", "record my voice", "record")):
                return _run_skill_text("voice_trainer", text, {"action": "record"})

            if any(w in text_lower for w in ("train dataset", "prepare training", "build dataset", "voice train")):
                return _run_skill_text("voice_trainer", text, {"action": "train"})

            if any(w in text_lower for w in ("voice status", "trainer status", "voice trainer status")):
                return _run_skill_text("voice_trainer", text, {"action": "status"})

            # ── Comic Compiler ──────────────────────────────────────
            if any(w in text_lower for w in (
                "compile the latest narrative", "compile comic", "compile my comic",
                "compile and read", "build comic", "make a comic book",
            )):
                return _run_comic_compiler(text)

            if any(w in text_lower for w in ("list narratives", "list comics", "what comics", "available comics")):
                return _run_skill_text("comic_compiler", text, {"action": "list"})

            if any(w in text_lower for w in ("read me a comic", "read the comic", "tell me a story", "read chapter")):
                return _run_comic_read(text)

            # ── YouTube Comment Ally ─────────────────────────────
            if any(w in text_lower for w in (
                "read the full transcript", "analyze this video", "transcript from that video",
                "suggest a comment", "what should i comment",
            )):
                return _run_ally_transcript_comment(text)

            if any(w in text_lower for w in ("youtube info", "video info", "fetch video")):
                return _run_skill_text("ally_comment_assistant", text, {"action": "fetch"})

            if any(w in text_lower for w in ("post comment", "post to youtube", "youtube post")):
                return _run_ally_post(text)

            if agent_available:
                self.ui.info("Thinking...")
                result = self._agent.execute(message=text)
                if result.get("error"):
                    return f"Hit a snag: {result['error']}"
                return result.get("response", "No response.")

            return f"Not sure how to do that. Try 'list skills' or 'wizard'."

        def keyboard_input() -> Optional[str]:
            return self.ui.prompt_text("Enter command (or 'quit')")

        self.ui.info("Voice mode active — press Ctrl+C to return to menu")
        try:
            self.voice.run(on_command, keyboard_input)
        except KeyboardInterrupt:
            self.voice.stop()
        self.ui.info("Returned to menu")


def _start_wizard(text: str, w: WizardState) -> str:
    from ..skills.batch_wizard import build_welcome_script, scan_directory

    path = "."
    for prefix in ("scan my directory", "scan my folder", "scan", "point me at", "point me to", "process", "wizard on"):
        if prefix in text.lower():
            candidate = text.lower().split(prefix, 1)[-1].strip()
            if candidate:
                path = candidate
            break

    scan = scan_directory(path)
    if scan["error"]:
        return f"Can't read that path: {scan['error']}"
    if scan["total"] == 0:
        return f"Scanned {path} — no files found. Try a different path."

    welcome = build_welcome_script(path, scan)
    w.active = True
    w.scan_path = path
    w.scan_result = scan
    w.welcome_data = welcome
    w.files = scan["files"]
    return welcome["script"]


def _handle_wizard_turn(text: str, w: WizardState) -> str:
    from ..skills.batch_wizard import (CAPABILITY_MATRIX, build_action_prompt,
                                       build_complete, build_params_prompt,
                                       process_batch)

    text_lower = text.lower().strip()

    if not w.selected_ext:
        for ext in w.welcome_data.get("choices", []):
            if ext in text_lower:
                count = w.scan_result["grouped"].get(ext, 0)
                w.selected_ext = ext
                prompt = build_action_prompt(ext, count)
                if prompt["state"] == "no_action":
                    w.reset()
                    return prompt["script"]
                w.action_data = prompt
                return prompt["script"]
        if text_lower in ("all", "everything", "all of them"):
            w.reset()
            return "Processing all types at once isn't wired yet. Pick one type first."
        choices = w.welcome_data.get("choices", [])
        return f"Which file type? Options: {', '.join(choices)}"

    if not w.selected_action:
        caps = w.action_data.get("option_details", [])
        for cap_name, _ in caps:
            if cap_name in text_lower:
                w.selected_action = cap_name
                params = build_params_prompt(w.selected_ext, cap_name, caps)
                if params["state"] == "error":
                    w.reset()
                    return params["script"]
                return _run_wizard_batch(w, params)
        if text_lower in ("all", "everything"):
            params = build_params_prompt(w.selected_ext, "all", caps)
            return _run_wizard_batch(w, params)
        options = [c[0] for c in caps]
        return f"What action? Options: {', '.join(options)}"

    w.reset()
    return "Wizard state got confused. Try again with 'batch wizard'."


def _run_wizard_batch(w: WizardState, params: dict) -> str:
    from ..skills.batch_wizard import build_complete, process_batch

    ext = w.selected_ext
    action = w.selected_action or params.get("action", "all")
    result = process_batch(w.files, ext, action, params.get("params", {}))
    w.reset()

    if result["error"]:
        return f"Batch failed: {result['error']}"
    complete = build_complete(result["processed"], ext, action, result["errors"])
    return complete["script"]


def _handle_lexicon(text: str) -> str:
    from ..skills.lexicon_skill import LexiconSkill
    skill = LexiconSkill()

    name = text
    for prefix in ("look up ", "search for ", "find ", "who is ", "lexicon "):
        if prefix in text.lower():
            name = text.split(prefix, 1)[-1].strip()
            break

    if not name:
        return "Who should I search for?"

    result = skill.execute(action="artist", name=name)
    if not result.get("error"):
        r = result["result"]
        return f"{r['name']}: {r['collaborations']} collabs, {r['recommended']} recommended. Genres: {', '.join(r['genres'])}."

    result = skill.execute(action="search", query=name)
    if not result.get("error") and result["result"]["count"] > 0:
        names = [a["name"] for a in result["result"]["artists"]]
        return f"Found {result['result']['count']}: {', '.join(names)}."
    return f"Nothing on '{name}' in the lexicon."


def _run_voice_trainer_speak(text: str) -> str:
    from ..skills.voice_trainer_skill import VoiceTrainerSkill
    skill = VoiceTrainerSkill()
    for prefix in ("say this with piper ", "speak through piper "):
        if prefix in text.lower():
            phrase = text.lower().split(prefix, 1)[-1].strip()
            if not phrase:
                return "What should I say?"
            result = skill.execute(action="speak", text=phrase)
            if result.get("error"):
                return result["error"]
            return f"Piper said: {phrase[:60]}"
    return "Specify what to say, like 'say this with piper hello world'"


def _run_ally_transcript_comment(text: str) -> str:
    from ..skills.ally_comment_assistant import AllyCommentAssistant
    skill = AllyCommentAssistant()

    url = _extract_youtube_url(text)
    if not url:
        return "I need a YouTube URL. Try: 'read the full transcript from https://youtu.be/...'"

    result = skill.execute(action="transcript_comment", video_url=url)
    if result.get("error"):
        return f"Failed: {result['error']}"

    r = result["result"]
    lines = [
        f"Video: {r['title']}",
        f"Channel: {r['channel']}",
        f"Transcript: {r['word_count']} words",
        f"Topics: {', '.join(r['key_topics']) if r['key_topics'] else 'general'}",
        f"Values check: {'passed' if r['values_aligned'] else 'no manifesto loaded'}",
        "",
        f"Comment suggestion:",
        f"{r['suggested_comment']}",
    ]
    if r.get("copied_to_clipboard"):
        lines.append("")
        lines.append("Copied to clipboard — paste-ready.")
    else:
        lines.append("")
        lines.append("pip install pyperclip for auto-copy.")
    return "\n".join(lines)


def _run_ally_post(text: str) -> str:
    from ..skills.ally_comment_assistant import AllyCommentAssistant
    skill = AllyCommentAssistant()
    url = _extract_youtube_url(text)
    if not url:
        return "I need a YouTube URL."
    result = skill.execute(action="suggest", video_url=url)
    if result.get("error"):
        return f"Failed: {result['error']}"
    r = result["result"]
    return f"Suggested: {r['suggested_comment']}\n\nRun with action=post and comment=... to actually post."


def _extract_youtube_url(text: str) -> str:
    import re
    patterns = [
        r"https?://(?:www\.)?youtube\.com/watch\?v=([0-9A-Za-z_-]{11})",
        r"https?://youtu\.be/([0-9A-Za-z_-]{11})",
        r"https?://(?:www\.)?youtube\.com/embed/([0-9A-Za-z_-]{11})",
        r"https?://(?:www\.)?youtube\.com/shorts/([0-9A-Za-z_-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(0)
    for pat in patterns:
        m = re.search(pat.replace("(https?://", "(?:https?://)?"), text)
        if m:
            return m.group(0)
    return ""


def _run_dirty_talker_category(text: str) -> str:
    from ..skills.dirty_talker_skill import DirtyTalkerSkill
    skill = DirtyTalkerSkill()
    for prefix in ("dirty about ", "nsfw category "):
        if prefix in text.lower():
            cat = text.lower().split(prefix, 1)[-1].strip()
            result = skill.execute(action="generate", category=cat)
            if result.get("error"):
                return result["error"]
            return result["result"]["phrase"]
    result = skill.execute(action="generate")
    if result.get("result"):
        return result["result"]["phrase"]
    return "Dirty talker not available."


def _run_meme_forge_topic(text: str) -> str:
    from ..skills.meme_forge import MemeForgeSkill
    skill = MemeForgeSkill()
    topic = "random"
    for prefix in ("meme about ", "joke about "):
        if prefix in text.lower():
            topic = text.lower().split(prefix, 1)[-1].strip()
            break
    domains = skill.execute(action="list_topics")
    if domains.get("result"):
        valid = domains["result"]["topics"]
        if topic not in valid and topic != "random":
            return f"Don't have that domain. Try: {', '.join(valid)}"
    result = skill.execute(action="generate", topic=topic, tone="sarcastic")
    if result.get("error"):
        return f"Meme forge error: {result['error']}"
    body = result["result"]["body"]
    return body


def _run_humor_meme_id(text: str) -> str:
    from ..skills.humor_skill import HumorMemeSkill
    skill = HumorMemeSkill()
    r = skill.execute(action="list")
    if r.get("result"):
        for m in r["result"]["memes"]:
            if m["id"] in text.lower():
                r2 = skill.execute(action="by_id", meme_id=m["id"])
                if r2.get("result"):
                    return r2["result"]["ascii"]
    return "Say 'list memes' to see what's available."


def _run_comic_compiler(text: str) -> str:
    from ..skills.comic_compiler import ComicCompilerSkill
    skill = ComicCompilerSkill()
    list_r = skill.execute(action="list")
    if list_r.get("error"):
        return f"Comic compiler error: {list_r['error']}"
    nars = list_r["result"]["narratives"]
    if not nars:
        return "No narratives found in the studio."

    target = None
    for prefix in ("compile and read ", "compile the latest narrative ", "compile comic ", "build comic ", "make a comic book "):
        if prefix in text.lower():
            target = text.lower().split(prefix, 1)[-1].strip()
            break

    if target and target != " " and target != "":
        matches = [n for n in nars if target in n["filename"].lower() or target in n["title"].lower()]
        if matches:
            nar_name = matches[0]["filename"]
        else:
            nar_name = nars[0]["filename"]
    else:
        nar_name = nars[0]["filename"]

    result = skill.execute(action="compile_html", narrative=nar_name)
    if result.get("error"):
        return f"Compilation failed: {result['error']}"
    path = result["result"]["path"]
    return f"Compiled {nar_name} to HTML: {path}. Say 'read me the comic' to hear it."


def _run_comic_read(text: str) -> str:
    from ..skills.comic_compiler import ComicCompilerSkill
    skill = ComicCompilerSkill()
    nar_name = ""
    for prefix in ("read me the comic ", "read the comic ", "read me a comic ", "tell me the story of ", "read chapter "):
        if prefix in text.lower():
            nar_name = text.lower().split(prefix, 1)[-1].strip()
            break
    if not nar_name or nar_name in ("please", "for me", "now"):
        list_r = skill.execute(action="list")
        if list_r.get("error"):
            return f"Error: {list_r['error']}"
        nars = list_r["result"]["narratives"]
        if not nars:
            return "No comics available."
        nar_name = nars[0]["filename"]

    chapter_key = text if "read chapter" in text.lower() else ""

    if chapter_key:
        ch_match = re.search(r"(chapter_\d+)", chapter_key.lower().replace(" ", "_"))
        ch_key = ch_match.group(1) if ch_match else ""
    else:
        ch_key = ""

    if ch_key:
        result = skill.execute(action="read_chapter", narrative=nar_name, chapter=ch_key)
    else:
        result = skill.execute(action="read_all", narrative=nar_name)

    if result.get("error"):
        return f"Read failed: {result['error']}"

    if ch_key:
        return f"Narrating {nar_name} / {ch_key}: {result['result']['narration'][:500]}..."
    chapters = result["result"]["chapters"]
    if not chapters:
        return "No chapters found."
    summary = f"Narrating {nar_name} ({len(chapters)} chapters): "
    summary += " ".join(f"{c['title']} ({c['panel_count']} panels)." for c in chapters[:3])
    return summary


def _run_skill_text(skill_name: str, text: str, extra_kwargs: Optional[dict] = None) -> str:
    from ..skills.loader import SkillLoader

    loader = SkillLoader()
    skills = loader.discover_skills()
    for skill in skills:
        if skill.name == skill_name:
            kwargs = dict(extra_kwargs or {})
            m = re.search(r'["\']([^"\']+\.\w+)["\']', text)
            if m:
                kwargs["path"] = m.group(1)
            elif "path" not in kwargs:
                kwargs["path"] = ""
            result = skill.execute(**kwargs)
            if result.get("error"):
                return f"Error: {result['error']}"
            return str(result["result"])[:300]
    return f"Skill '{skill_name}' not available."
