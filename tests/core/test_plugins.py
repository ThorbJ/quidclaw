"""Tests for the plugin framework."""

import warnings
from unittest.mock import MagicMock, patch
from pathlib import Path

from quidclaw.core.plugins import (
    QuidClawPlugin, discover_plugins, load_plugins,
    PLUGIN_API_VERSION, PLUGIN_GROUP,
)


class FakePlugin(QuidClawPlugin):
    @staticmethod
    def name():
        return "fake"

    @staticmethod
    def description():
        return "A fake plugin for testing"


class TestDiscoverPlugins:
    def test_empty_when_no_plugins(self):
        plugins = discover_plugins()
        assert plugins == []

    def test_finds_installed_plugin(self):
        ep = MagicMock()
        ep.name = "fake"
        ep.load.return_value = FakePlugin
        with patch("quidclaw.core.plugins.importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [ep]
            plugins = discover_plugins()
        assert len(plugins) == 1
        assert plugins[0].name() == "fake"

    def test_skips_incompatible_api_version(self):
        class FuturePlugin(FakePlugin):
            plugin_api_version = 999
        ep = MagicMock()
        ep.name = "future"
        ep.load.return_value = FuturePlugin
        with patch("quidclaw.core.plugins.importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [ep]
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                plugins = discover_plugins()
        assert plugins == []
        assert any("future" in str(warning.message) for warning in w)

    def test_skips_broken_plugin(self):
        ep = MagicMock()
        ep.name = "broken"
        ep.load.side_effect = ImportError("no such module")
        with patch("quidclaw.core.plugins.importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [ep]
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                plugins = discover_plugins()
        assert plugins == []
        assert any("broken" in str(warning.message) for warning in w)


class TestLoadPlugins:
    def test_registers_commands(self):
        plugin = FakePlugin()
        plugin.register_commands = MagicMock()
        with patch("quidclaw.core.plugins.discover_plugins", return_value=[plugin]):
            cli = MagicMock()
            load_plugins(cli)
        plugin.register_commands.assert_called_once_with(cli)
