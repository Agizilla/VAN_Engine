import traceback
from typing import Any, Optional

from .base import BasePlugin
from .registry import PluginRegistry
from .loader import PluginLoader


class LifecycleError(Exception):
    pass


class PluginLifecycleManager:
    def __init__(self, loader: PluginLoader, registry: PluginRegistry):
        self.loader = loader
        self.registry = registry

    def install(self, plugin_id: str) -> str:
        plugin = self.loader.load(plugin_id)
        if plugin is None:
            raise LifecycleError(f"Failed to load plugin: {plugin_id}")

        self.registry.register(plugin.manifest)
        try:
            plugin.on_install()
        except Exception as e:
            self.registry.unregister(plugin_id)
            raise LifecycleError(f"on_install failed: {e}")
        return plugin_id

    def uninstall(self, plugin_id: str) -> bool:
        plugin = self.loader.get_loaded().get(plugin_id)
        if plugin:
            try:
                plugin.on_uninstall()
            except Exception:
                pass
        self.loader.unload(plugin_id)
        return self.registry.unregister(plugin_id)

    def activate(self, plugin_id: str) -> bool:
        missing = self.registry.check_dependencies(plugin_id)
        if missing:
            raise LifecycleError(f"Missing dependencies: {missing}")

        plugin = self.loader.load(plugin_id)
        if plugin is None:
            raise LifecycleError(f"Cannot load plugin: {plugin_id}")

        try:
            plugin.on_activate()
        except Exception as e:
            raise LifecycleError(f"on_activate failed: {e}")

        return self.registry.set_enabled(plugin_id, True)

    def deactivate(self, plugin_id: str) -> bool:
        plugin = self.loader.get_loaded().get(plugin_id)
        if plugin:
            try:
                plugin.on_deactivate()
            except Exception:
                pass
        return self.registry.set_enabled(plugin_id, False)

    def execute(self, plugin_id: str, **kwargs) -> Any:
        plugin = self.loader.get_loaded().get(plugin_id)
        if plugin is None:
            raise LifecycleError(f"Plugin not loaded: {plugin_id}")
        if not plugin.enabled:
            raise LifecycleError(f"Plugin not activated: {plugin_id}")
        try:
            return plugin.execute(**kwargs)
        except Exception as e:
            raise LifecycleError(f"execute failed: {e}\n{traceback.format_exc()}")

    def list_active(self) -> list[str]:
        return [pid for pid, p in self.loader.get_loaded().items() if p.enabled]
