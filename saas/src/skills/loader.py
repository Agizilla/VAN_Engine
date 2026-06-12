import importlib
import inspect
import pkgutil
import traceback
from pathlib import Path
from typing import Optional

from .base import BaseSkill, get_registered_skills, SKILL_REGISTRY
from .registry import detect_capabilities


class SkillLoader:
    _capability_cache: Optional[dict] = None
    _loading_modules: set = set()

    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = skills_dir
        self._cache = None

    def _log_import_error(self, pyfile: Path, exc: Exception):
        with open("loader_errors.log", "a", encoding="utf-8") as f:
            f.write(f"[{pyfile}] {exc}\n")
            traceback.print_exc(file=f)

    def discover_skills(self) -> list:
        if self._cache is not None:
            return self._cache

        cap = detect_capabilities()
        skills = []

        if self.skills_dir:
            self._load_from_directory(self.skills_dir, cap, skills)

        for name, info in get_registered_skills().items():
            cls = info["cls"]
            skill_instance = cls()
            if self._check_libs(skill_instance, cap):
                skills.append(skill_instance)

        skill_key = lambda s: len(getattr(s, "required_libs", []))
        skills.sort(key=skill_key)

        self._cache = skills
        return skills

    def _load_from_directory(self, directory: str, cap, skills: list):
        path = Path(directory)
        if not path.exists():
            return
        for pyfile in sorted(path.glob("*.py")):
            if pyfile.name.startswith("_"):
                continue
            mod_name = pyfile.stem
            if mod_name in self._loading_modules:
                import logging
                logging.warning(f"Circular import detected: {mod_name} already loading")
                continue
            self._loading_modules.add(mod_name)
            try:
                spec = importlib.util.spec_from_file_location(mod_name, pyfile)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                        instance = obj()
                        if self._check_libs(instance, cap):
                            skills.append(instance)
            except Exception as e:
                self._log_import_error(pyfile, e)
            finally:
                self._loading_modules.discard(mod_name)

    def _check_libs(self, skill, cap) -> bool:
        for lib in skill.required_libs:
            if not cap[lib]:
                return False
        return True
