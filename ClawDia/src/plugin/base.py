from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    author: str = ""
    description: str = ""
    requires: list[str] = field(default_factory=list)
    min_clawdia_version: str = "0.1.0"
    category: str = "general"


class BasePlugin(ABC):
    manifest: PluginManifest

    def __init__(self):
        self._enabled = False
        self._config: dict = {}

    @abstractmethod
    def on_install(self) -> None:
        ...

    @abstractmethod
    def on_uninstall(self) -> None:
        ...

    def on_activate(self) -> None:
        self._enabled = True

    def on_deactivate(self) -> None:
        self._enabled = False

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        ...

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def config(self) -> dict:
        return dict(self._config)

    @config.setter
    def config(self, value: dict):
        self._config = dict(value)
