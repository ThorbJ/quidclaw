"""Plugin framework for QuidClaw."""

import importlib.metadata
import warnings
from abc import ABC, abstractmethod
from pathlib import Path

PLUGIN_API_VERSION = 1
PLUGIN_GROUP = "quidclaw.plugins"


class QuidClawPlugin(ABC):
    """Base class for all QuidClaw plugins."""

    plugin_api_version: int = 1

    @staticmethod
    @abstractmethod
    def name() -> str: ...

    @staticmethod
    @abstractmethod
    def description() -> str: ...

    def register_commands(self, cli) -> None:
        pass

    def get_skills_dir(self) -> Path | None:
        return None


def discover_plugins() -> list[QuidClawPlugin]:
    """Find and instantiate all installed QuidClaw plugins."""
    plugins = []
    eps = importlib.metadata.entry_points()
    for ep in eps.select(group=PLUGIN_GROUP):
        try:
            plugin_cls = ep.load()
            api_ver = getattr(plugin_cls, "plugin_api_version", 1)
            if api_ver > PLUGIN_API_VERSION:
                warnings.warn(
                    f"Plugin '{ep.name}' requires API v{api_ver}, "
                    f"core is v{PLUGIN_API_VERSION}. Skipping.",
                    stacklevel=2,
                )
                continue
            plugins.append(plugin_cls())
        except Exception as e:
            warnings.warn(
                f"Plugin '{ep.name}' failed to load: {e}. Skipping.",
                stacklevel=2,
            )
    return plugins


def load_plugins(cli) -> list[QuidClawPlugin]:
    """Discover and activate all plugins at CLI startup."""
    plugins = discover_plugins()
    for plugin in plugins:
        plugin.register_commands(cli)
    return plugins
