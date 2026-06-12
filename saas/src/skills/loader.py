import importlib
import importlib.util
import inspect
import sys
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
        seen: set[str] = set()
        skills: list = []

        if self.skills_dir:
            self._load_from_directory(self.skills_dir, cap, skills, seen)

        for name, info in get_registered_skills().items():
            if name in seen:
                continue
            cls = info["cls"]
            try:
                skill_instance = cls()
                if self._check_libs(skill_instance, cap):
                    skills.append(skill_instance)
                    seen.add(name)
            except Exception:
                pass

        skill_key = lambda s: len(getattr(s, "required_libs", []))
        skills.sort(key=skill_key)

        self._cache = skills
        return skills

    def _load_from_directory(self, directory: str, cap, skills: list, seen: set):
        path = Path(directory)
        if not path.exists():
            return
        package_name = path.name
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
                full_name = f"{package_name}.{mod_name}"
                if full_name in sys.modules:
                    mod = sys.modules[full_name]
                else:
                    try:
                        mod = importlib.import_module(full_name)
                    except ImportError:
                        spec = importlib.util.spec_from_file_location(mod_name, pyfile)
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                for _, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                        try:
                            instance = obj()
                            sname = getattr(instance, "name", None) or getattr(obj, "name", None)
                            if sname and sname in seen:
                                continue
                            if self._check_libs(instance, cap):
                                skills.append(instance)
                                if sname:
                                    seen.add(sname)
                        except Exception:
                            pass
            except Exception as e:
                self._log_import_error(pyfile, e)
            finally:
                self._loading_modules.discard(mod_name)

    def _check_libs(self, skill, cap) -> bool:
        for lib in skill.required_libs:
            if not cap[lib]:
                return False
        return True
