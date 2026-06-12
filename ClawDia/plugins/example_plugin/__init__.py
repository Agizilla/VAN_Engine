import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from plugin.base import BasePlugin, PluginManifest


class ExamplePlugin(BasePlugin):
    manifest = PluginManifest(
        id="example_plugin",
        name="Example Plugin",
        version="1.0.0",
        author="ClawDia",
        description="A minimal example plugin",
        category="example",
    )

    def on_install(self):
        pass

    def on_uninstall(self):
        pass

    def execute(self, **kwargs) -> dict:
        return {"status": "ok", "plugin": "example_plugin", "input": kwargs}
