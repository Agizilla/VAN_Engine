import importlib
import inspect
import sys
from pathlib import Path
from typing import Optional

from .base import BasePlugin, PluginManifest
from .registry import PluginRegistry


class PluginLoader:
    def __init__(self, plugins_dir: str, registry: PluginRegistry):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.registry = registry
        self._loaded: dict[str, BasePlugin] = {}

    def discover(self) -> list[str]:
        found = []
        for entry in self.plugins_dir.iterdir():
            if entry.is_dir():
                manifest_file = entry / "plugin.yaml"
                if manifest_file.exists():
                    found.append(entry.name)
                continue
            if entry.suffix == ".py" and not entry.name.startswith("_"):
                found.append(entry.stem)
        return found

    def load(self, plugin_id: str) -> Optional[BasePlugin]:
        if plugin_id in self._loaded:
            return self._loaded[plugin_id]

        module = self._import_module(plugin_id)
        if module is None:
            return None

        plugin_class = self._find_plugin_class(module)
        if plugin_class is None:
            return None

        try:
            instance = plugin_class()
        except Exception:
            return None
        self._loaded[plugin_id] = instance
        return instance

    def unload(self, plugin_id: str):
        self._loaded.pop(plugin_id, None)

    def reload(self, plugin_id: str) -> Optional[BasePlugin]:
        self.unload(plugin_id)
        return self.load(plugin_id)

    def get_loaded(self) -> dict[str, BasePlugin]:
        return dict(self._loaded)

    def _import_module(self, plugin_id: str):
        py_file = self.plugins_dir / f"{plugin_id}.py"
        pkg_dir = self.plugins_dir / plugin_id

        if py_file.exists():
            return self._import_from_file(py_file, plugin_id)
        elif pkg_dir.exists():
            init_file = pkg_dir / "__init__.py"
            if init_file.exists():
                return self._import_from_file(init_file, f"plugins.{plugin_id}")
        return None

    def _import_from_file(self, path: Path, module_name: str):
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            return module
        except Exception:
            return None

    def _find_plugin_class(self, module) -> Optional[type[BasePlugin]]:
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                return obj
        return None
