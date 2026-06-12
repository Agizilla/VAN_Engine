import json
from pathlib import Path
from typing import Optional

import yaml

from .base import PluginManifest


class PluginRegistry:
    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict = self._load()

    def _load(self) -> dict:
        if not self.manifest_path.exists():
            return {"plugins": {}}
        with open(self.manifest_path) as f:
            return yaml.safe_load(f) or {"plugins": {}}

    def _save(self):
        with open(self.manifest_path, "w") as f:
            yaml.dump(self._data, f, default_flow_style=False)

    def register(self, manifest: PluginManifest):
        entry = {
            "name": manifest.name,
            "version": manifest.version,
            "author": manifest.author,
            "description": manifest.description,
            "requires": manifest.requires,
            "min_clawdia_version": manifest.min_clawdia_version,
            "category": manifest.category,
            "enabled": True,
        }
        self._data["plugins"][manifest.id] = entry
        self._save()

    def unregister(self, plugin_id: str) -> bool:
        if plugin_id in self._data["plugins"]:
            del self._data["plugins"][plugin_id]
            self._save()
            return True
        return False

    def set_enabled(self, plugin_id: str, enabled: bool) -> bool:
        if plugin_id in self._data["plugins"]:
            self._data["plugins"][plugin_id]["enabled"] = enabled
            self._save()
            return True
        return False

    def is_enabled(self, plugin_id: str) -> bool:
        entry = self._data["plugins"].get(plugin_id)
        return entry is not None and entry.get("enabled", False)

    def get(self, plugin_id: str) -> Optional[dict]:
        return self._data["plugins"].get(plugin_id)

    def list_plugins(self) -> dict:
        return dict(self._data["plugins"])

    def check_dependencies(self, plugin_id: str) -> list[str]:
        entry = self._data["plugins"].get(plugin_id)
        if not entry:
            return ["not_found"]
        missing = []
        for dep in entry.get("requires", []):
            dep_entry = self._data["plugins"].get(dep)
            if dep_entry is None or not dep_entry.get("enabled", False):
                missing.append(dep)
        return missing
