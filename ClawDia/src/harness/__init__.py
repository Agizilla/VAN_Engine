import sys
from pathlib import Path
from typing import Optional

_skills_dir = Path(__file__).resolve().parent.parent / "skills"
if str(_skills_dir) not in sys.path:
    sys.path.insert(0, str(_skills_dir))

from skills.bullshit_detector import BullshitDetectorSkill
from skills.intent_enricher import IntentEnricherSkill
from skills.ascii_comic_skill import AsciiComicSkill
from skills.comic_compiler import ComicCompilerSkill
from skills.humor_skill import HumorMemeSkill, HumorAsciiGeneratorSkill
from skills.svg_animated_skill import SvgAnimatedSkill


class IntentPipeline:
    def __init__(self):
        self.bullshit = BullshitDetectorSkill()
        self.enricher = IntentEnricherSkill()
        self.ascii_comic = AsciiComicSkill()
        self.comic_compiler = ComicCompilerSkill()
        self.humor_meme = HumorMemeSkill()
        self.humor_ascii = HumorAsciiGeneratorSkill()
        self.svg_animated = SvgAnimatedSkill()

        self.skill_map = {
            "ascii_comic": self.ascii_comic,
            "comic_compiler": self.comic_compiler,
            "humor_meme": self.humor_meme,
            "humor_ascii": self.humor_ascii,
            "svg_animated": self.svg_animated,
        }

    def run(self, prompt: str, skill: Optional[str] = None,
            narrative: Optional[str] = None, action: Optional[str] = None,
            no_gate: bool = False) -> dict:
        gate_result = {}
        if not no_gate:
            gate = self.bullshit.execute(action="evaluate", prompt=prompt)
            gate_result = gate.get("result", {})
            gate_action = gate_result.get("action", "pass")
            if gate_action == "block":
                return {"status": "blocked", "gate": gate_result, "prompt": prompt}

        intent = self.enricher.execute(text=prompt)
        intent_result = intent.get("result", {})

        target = skill or self._route(intent_result, prompt)
        output = self._execute(target, narrative, action, intent_result, prompt)

        return {
            "status": "ok",
            "gate": gate_result,
            "intent": intent_result,
            "target": target,
            "output": output,
        }

    def _route(self, intent: dict, prompt: str) -> str:
        grid = intent.get("grid", {})
        x = grid.get("x", {}).get("category", "")
        y = grid.get("y", {}).get("category", "")
        z = grid.get("z", {}).get("category", "")
        pl = prompt.lower()

        if any(w in pl for w in ["comic", "narrative", "render", "ascii", "story", "panel"]):
            if any(w in pl for w in ["html", "pdf", "compile", "book", "chapter"]):
                return "comic_compiler"
            return "ascii_comic"
        if any(w in pl for w in ["meme", "funny", "lol", "humor", "joke", "slapback"]):
            return "humor_meme"
        if any(w in pl for w in ["banner", "ascii art", "title", "header", "big text"]):
            return "humor_ascii"
        if x in ("create", "generate") and y in ("image", "text", "code"):
            return "ascii_comic"
        if x in ("publish", "create") and z == "convert":
            return "comic_compiler"
        if x in ("query", "read") and any(w in pl for w in ["meme"]):
            return "humor_meme"
        if any(w in pl for w in ["animate", "svg", "animation", "pose", "keyframe"]):
            return "svg_animated"

        return "ascii_comic"

    def _execute(self, skill_name: str, narrative: Optional[str],
                 action: Optional[str], intent: dict, prompt: str) -> dict:
        skill = self.skill_map.get(skill_name)
        if not skill:
            return {"error": f"Unknown skill: {skill_name}"}

        if skill_name == "ascii_comic":
            return self._exec_comic(skill, narrative, action)
        if skill_name == "comic_compiler":
            return self._exec_compiler(skill, narrative, action)
        if skill_name == "humor_meme":
            return self._exec_meme(skill)
        if skill_name == "humor_ascii":
            return self._exec_ascii(skill, prompt)
        if skill_name == "svg_animated":
            return self._exec_svg(skill, narrative, action)
        return {"error": f"No executor for {skill_name}"}

    def _exec_comic(self, skill, narrative: Optional[str], action: Optional[str]) -> dict:
        narratives = skill.execute(action="list").get("result", {}).get("narratives", [])
        if not narrative and narratives:
            narrative = narratives[0]
        if narrative:
            act = action or "render"
            result = skill.execute(action=act, narrative=narrative)
            if result.get("error"):
                return {"error": result["error"], "narratives_available": narratives}
            return {"type": "ascii_comic", "narrative": narrative, "result": result["result"]}
        return {"type": "ascii_comic", "narratives_available": narratives, "hint": "specify --narrative"}

    def _exec_compiler(self, skill, narrative: Optional[str], action: Optional[str]) -> dict:
        narratives = skill.execute(action="list").get("result", {}).get("narratives", [])
        if not narrative and narratives:
            narrative = narratives[0]
        if narrative:
            act = action or "compile_html"
            result = skill.execute(action=act, narrative=narrative)
            if result.get("error"):
                return {"error": result["error"], "narratives_available": narratives}
            return {"type": "comic_compiler", "narrative": narrative, "result": result["result"]}
        return {"type": "comic_compiler", "narratives_available": narratives, "hint": "specify --narrative"}

    def _exec_meme(self, skill) -> dict:
        result = skill.execute(action="random")
        return {"type": "meme", "result": result.get("result", {})}

    def _exec_ascii(self, skill, prompt: str) -> dict:
        result = skill.execute(action="banner", text=prompt, style="double")
        return {"type": "ascii_banner", "result": result.get("result", {})}

    def _exec_svg(self, skill, pose_config: Optional[str], action: Optional[str]) -> dict:
        act = action or "animate"
        result = skill.execute(action=act, pose_config=pose_config)
        if result.get("error"):
            return {"error": result["error"]}
        return {"type": "svg_animated", "result": result.get("result", {})}
