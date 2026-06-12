"""
Skill CLI — Interactive terminal test harness for ClawDia skills.

Features:
  - Lists all registered skills with descriptions
  - Select a skill → view available actions → enter kwargs
  - Runs the skill and displays the result
  - Optional TTS readback via ClawDia voice bridge
  - Keyword shortcuts for meme forge, humor, lexicon, audio

Usage:
  python -m src.scripts.skill_cli
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _try_speak(text: str):
    try:
        from voice.loop import VoiceLoop
        from ui.console import ConsoleUI
        vl = VoiceLoop(ConsoleUI())
        vl.synthesize(text[:500])
    except Exception:
        pass


def _clear():
    import os
    os.system("cls" if os.name == "nt" else "clear")


def _header(title: str):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _menu(options: list[tuple], prompt: str = "Choice") -> int:
    for i, (label, _) in enumerate(options, 1):
        print(f"  {i:>2}. {label}")
    print(f"  0. Back / Quit")
    try:
        n = int(input(f"\n  [{prompt}] > ").strip())
        return n
    except (ValueError, EOFError):
        return 0


def skill_explorer():
    from skills.base import SKILL_REGISTRY

    while True:
        _clear()
        _header("SKILL EXPLORER — All Registered Skills")
        skills = sorted(SKILL_REGISTRY.items(), key=lambda x: x[1]["category"])
        options = [(f"[{cat}] {name}", name) for name, info in skills for cat in [info["category"]]]
        choice = _menu(options, "Skill #")

        if choice == 0:
            break
        if choice < 1 or choice > len(options):
            continue

        name = options[choice - 1][1]
        skill_interact(name)


def skill_interact(name: str):
    from skills.base import SKILL_REGISTRY

    info = SKILL_REGISTRY.get(name)
    if not info:
        print(f"  Skill '{name}' not found.")
        return

    cls = info["cls"]
    skill = cls()
    meta = skill.get_metadata()

    while True:
        _clear()
        _header(f"SKILL: {name}")
        print(f"  Description: {meta.get('description', '')}")
        print(f"  Author:      {meta.get('author', 'ClawDia')}")
        print(f"  Version:     {meta.get('version', '1.0.0')}")
        print(f"  Category:    {meta.get('category', 'general')}")
        print(f"  Tags:        {', '.join(meta.get('tags', []))}")
        print()

        # Check if skill has specific actions
        schema = getattr(skill, "input_schema", {})
        props = schema.get("properties", {})
        has_actions = "action" in props
        if has_actions:
            action_enum = props["action"].get("enum", [])
        else:
            action_enum = []

        if action_enum:
            _header("ACTIONS")
            actions = [(a, "") for a in action_enum]
            actions.append(("custom_kwargs", "Enter raw kwargs"))
            act_choice = _menu(actions, "Action #")
            if act_choice == 0:
                break
            if act_choice < 1 or act_choice > len(actions) - 1:
                kwargs_str = input("  kwargs (key=val space-separated) > ").strip()
            else:
                action = action_enum[act_choice - 1]
                kwargs_str = f"action={action}"
        else:
            print("  No predefined actions — enter kwargs or press Enter for defaults.")
            print("  Format: key=val pairs separated by spaces (e.g., text=hello count=3)")
            kwargs_str = input("  kwargs > ").strip()

        # Parse kwargs
        kwargs = {}
        if kwargs_str:
            parts = kwargs_str.split()
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    kwargs[k.strip()] = v.strip()

        print(f"\n  Executing {name}(**{kwargs})...")

        try:
            result = skill.execute(**kwargs)
            print()
            _header("RESULT")
            if result.get("error"):
                print(f"  ERROR: {result['error']}")
            else:
                r = result.get("result", {})
                if isinstance(r, dict):
                    for k, v in r.items():
                        val = str(v)
                        if len(val) > 200:
                            val = val[:197] + "..."
                        print(f"  {k}: {val}")
                else:
                    print(f"  {r}")
        except Exception as e:
            print(f"  EXCEPTION: {e}")

        print()
        tts = input("  Speak result? (y/N) > ").strip().lower()
        if tts == "y":
            _try_speak(str(result))

        input("  Press Enter to continue...")
        if input("  Run again? (Y/n) > ").strip().lower() == "n":
            break


def main():
    while True:
        _clear()
        _header("CLAWDIA SKILL CLI")
        print("  1. Skill Explorer — browse and run any skill")
        print("  2. Meme Forge — quick meme generation")
        print("  3. Humor Collection — browse ASCII memes")
        print("  4. Lexicon — search music artist lexicon")
        print("  5. Run All Skills Demo")
        print("  0. Quit")
        print()

        try:
            choice = input("  [Main] > ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "1":
            skill_explorer()
        elif choice == "2":
            _quick_meme_forge()
        elif choice == "3":
            _quick_humor()
        elif choice == "4":
            _quick_lexicon()
        elif choice == "5":
            _run_all_demo()
        elif choice == "0":
            break


def _quick_meme_forge():
    from skills.meme_forge import MemeForgeSkill
    skill = MemeForgeSkill()

    _clear()
    _header("QUICK MEME FORGE")
    topic = input("  Topic (Enter=random, or: ai_slop, offline_first, etc) > ").strip()
    tone = input("  Tone (sarcastic/self_deprecating/hopeful, Enter=random) > ").strip()
    frame = input("  Frame (single/double/rounded/none, Enter=none) > ").strip()
    count_s = input("  Count (Enter=1) > ").strip()

    kwargs = {}
    if topic:
        kwargs["topic"] = topic
    if tone:
        kwargs["tone"] = tone
    if frame:
        kwargs["frame"] = frame
    count = int(count_s) if count_s.isdigit() else 1

    print()
    if count == 1:
        result = skill.execute(action="generate", **kwargs)
        if result.get("result"):
            print(result["result"]["ascii"])
    else:
        result = skill.execute(action="batch", count=count, **kwargs)
        if result.get("result"):
            for i, m in enumerate(result["result"]["memes"], 1):
                print(f"\n--- Meme {i} ---")
                print(m["body"])

    tts = input("\n  Speak result? (y/N) > ").strip().lower()
    if tts == "y":
        _try_speak(str(result))

    input("\n  Press Enter to return...")


def _quick_humor():
    from skills.humor_skill import HumorMemeSkill
    skill = HumorMemeSkill()

    _clear()
    _header("HUMOR COLLECTION")
    r = skill.execute(action="list")
    if r.get("result"):
        for m in r["result"]["memes"]:
            print(f"  {m['id']:30s} [{', '.join(m['tags'][:3])}]")
    print()
    meme_id = input("  Enter meme id (or Enter for random) > ").strip()
    if meme_id:
        r = skill.execute(action="by_id", meme_id=meme_id)
    else:
        r = skill.execute(action="random")
    if r.get("result"):
        print()
        print(r["result"]["ascii"])

    tts = input("\n  Speak result? (y/N) > ").strip().lower()
    if tts == "y":
        _try_speak(str(r["result"].get("ascii", "")))

    input("\n  Press Enter to return...")


def _quick_lexicon():
    from skills.lexicon_skill import LexiconSkill
    skill = LexiconSkill()

    _clear()
    _header("LEXICON SEARCH")
    name = input("  Artist name > ").strip()
    if not name:
        return
    r = skill.execute(action="artist", name=name)
    if r.get("result"):
        data = r["result"]
        print(f"\n  {data['name']}")
        print(f"  Genres: {', '.join(data['genres'])}")
        print(f"  Collaborations: {data['collaborations']}")
        print(f"  Recommended: {data['recommended']}")
        if data.get("top_songs"):
            print(f"  Top songs: {', '.join(data['top_songs'][:5])}")
    else:
        r = skill.execute(action="search", query=name)
        if r.get("result") and r["result"]["count"] > 0:
            print(f"\n  Found {r['result']['count']} artists:")
            for a in r["result"]["artists"]:
                print(f"    - {a['name']}")
        else:
            print(f"\n  No results for '{name}'")

    tts = input("\n  Speak result? (y/N) > ").strip().lower()
    if tts == "y":
        _try_speak(str(r))

    input("\n  Press Enter to return...")


def _run_all_demo():
    from skills.base import SKILL_REGISTRY
    from skills.meme_forge import MemeForgeSkill
    from skills.humor_skill import HumorMemeSkill
    from skills.intent_enricher import IntentEnricherSkill
    from skills.signal_filter import SignalFilterSkill
    from skills.replay_manager import ReplayManagerSkill

    _clear()
    _header("ALL SKILLS DEMO")

    demos = [
        ("signal_filter", SignalFilterSkill(), {"text": "So anyway I dunno, like, build an offline-first system maybe?"}),
        ("intent_enricher", IntentEnricherSkill(), {"text": "count audio files"}),
        ("meme_forge", MemeForgeSkill(), {"action": "generate", "topic": "offline_first", "tone": "hopeful"}),
        ("humor_meme", HumorMemeSkill(), {"action": "random"}),
    ]

    for name, skill, kwargs in demos:
        print(f"\n── {name} ──")
        try:
            result = skill.execute(**kwargs)
            if result.get("error"):
                print(f"  ERROR: {result['error']}")
            else:
                r = result.get("result", {})
                if isinstance(r, dict):
                    for k, v in r.items():
                        val = str(v)
                        if len(val) > 120:
                            val = val[:117] + "..."
                        print(f"  {k}: {val}")
                else:
                    print(f"  {r}")
        except Exception as e:
            print(f"  EXCEPTION: {e}")

    input("\n  Press Enter to return...")


if __name__ == "__main__":
    main()
