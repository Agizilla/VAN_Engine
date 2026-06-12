import tempfile
from pathlib import Path

import pytest

from src.plugin.base import BasePlugin, PluginManifest
from src.plugin.registry import PluginRegistry
from src.plugin.loader import PluginLoader
from src.plugin.lifecycle import PluginLifecycleManager, LifecycleError
from src.plugin.sandbox import SandboxExecutor, TimeoutError


class _TestPlugin(BasePlugin):
    manifest = PluginManifest(
        id="test_plugin",
        name="Test",
        version="1.0.0",
        description="Test plugin",
    )
    def on_install(self):
        self._installed = True
    def on_uninstall(self):
        self._installed = False
    def execute(self, **kwargs):
        return {"result": "ok", **kwargs}


class _SlowPlugin(BasePlugin):
    manifest = PluginManifest(id="slow", name="Slow", version="1.0.0")
    def on_install(self):
        pass
    def on_uninstall(self):
        pass
    def execute(self, **kwargs):
        import time
        time.sleep(5)
        return {}


class TestBasePlugin:
    def test_abstract_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BasePlugin()

    def test_concrete_plugin(self):
        p = _TestPlugin()
        assert p.manifest.id == "test_plugin"
        assert p.enabled is False
        p.on_activate()
        assert p.enabled is True
        p.on_deactivate()
        assert p.enabled is False

    def test_config(self):
        p = _TestPlugin()
        p.config = {"key": "val"}
        assert p.config == {"key": "val"}

    def test_execute(self):
        p = _TestPlugin()
        p.on_activate()
        result = p.execute(foo="bar")
        assert result["result"] == "ok"
        assert result["foo"] == "bar"


class TestPluginRegistry:
    @pytest.fixture
    def registry(self, tmp_path):
        return PluginRegistry(str(tmp_path / "manifest.yaml"))

    def test_empty(self, registry):
        assert registry.list_plugins() == {}

    def test_register_and_get(self, registry):
        m = PluginManifest(id="p1", name="Plugin 1", version="1.0")
        registry.register(m)
        entry = registry.get("p1")
        assert entry["name"] == "Plugin 1"

    def test_unregister(self, registry):
        m = PluginManifest(id="p1", name="P1", version="1.0")
        registry.register(m)
        assert registry.unregister("p1") is True
        assert registry.unregister("nonexistent") is False

    def test_enable_disable(self, registry):
        m = PluginManifest(id="p1", name="P1", version="1.0")
        registry.register(m)
        assert registry.is_enabled("p1") is True
        registry.set_enabled("p1", False)
        assert registry.is_enabled("p1") is False

    def test_dependencies(self, registry):
        a = PluginManifest(id="a", name="A", version="1.0", requires=["b"])
        b = PluginManifest(id="b", name="B", version="1.0")
        registry.register(a)
        registry.register(b)
        assert registry.check_dependencies("a") == []
        registry.set_enabled("b", False)
        missing = registry.check_dependencies("a")
        assert "b" in missing


class TestPluginLoader:
    @pytest.fixture
    def loader(self, tmp_path):
        registry = PluginRegistry(str(tmp_path / "manifest.yaml"))
        return PluginLoader(str(tmp_path / "plugins"), registry)

    def test_discover_empty(self, loader):
        assert loader.discover() == []

    def test_load_concrete_class(self, loader):
        plugin = _TestPlugin()
        assert plugin.manifest.id == "test_plugin"


class TestPluginLifecycle:
    @pytest.fixture
    def manager(self, tmp_path):
        registry = PluginRegistry(str(tmp_path / "manifest.yaml"))
        loader = PluginLoader(str(tmp_path / "plugins"), registry)
        return PluginLifecycleManager(loader, registry)

    def test_install_via_lifecycle(self, manager):
        plugin = _TestPlugin()
        manager.registry.register(plugin.manifest)
        manager.loader._loaded["test_plugin"] = plugin
        assert manager.registry.get("test_plugin") is not None
        manager.activate("test_plugin")
        assert plugin.enabled is True
        assert manager.registry.is_enabled("test_plugin")

    def test_uninstall_removes(self, manager):
        manager.registry.register(_TestPlugin.manifest)
        assert manager.uninstall("test_plugin") is True
        assert manager.registry.get("test_plugin") is None

    def test_activate_missing_deps(self, manager):
        manager.registry.register(PluginManifest(id="orphan", name="Orphan", version="1.0", requires=["missing"]))
        with pytest.raises(LifecycleError):
            manager.activate("orphan")

    def test_execute_via_lifecycle(self, manager):
        plugin = _TestPlugin()
        manager.loader._loaded["test_plugin"] = plugin
        manager.registry.register(plugin.manifest)
        plugin.on_activate()
        result = manager.execute("test_plugin", foo="bar")
        assert result["result"] == "ok"


class TestSandbox:
    def test_timeout(self):
        sb = SandboxExecutor(timeout=0.1)
        with pytest.raises(TimeoutError):
            sb.run(lambda: __import__("time").sleep(5))

    def test_normal_execution(self):
        sb = SandboxExecutor(timeout=5)
        result = sb.run(lambda x: x * 2, 21)
        assert result == 42

    def test_exception_propagation(self):
        sb = SandboxExecutor(timeout=5)
        with pytest.raises(IndexError):
            sb.run(lambda: [][1])
