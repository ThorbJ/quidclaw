# Phase 2: Plugin Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a plugin framework to QuidClaw so external packages can register data source providers, CLI commands, and skills.

**Architecture:** Plugins are Python packages that declare a `quidclaw.plugins` entry point pointing to a `QuidClawPlugin` subclass. At CLI startup, `load_plugins()` discovers and activates all installed plugins. `init` and `upgrade` copy plugin skills alongside core skills.

**Tech Stack:** Python 3.10+, Click, pytest, importlib.metadata entry points

**Spec:** `docs/superpowers/specs/2026-03-28-plugin-system-and-crypto-design.md` (Phase 2 section)

---

## File Structure

### New files

```
src/quidclaw/core/plugins.py              # QuidClawPlugin ABC, discover_plugins(), load_plugins()
tests/core/test_plugins.py                 # Plugin framework tests
```

### Modified files

```
src/quidclaw/cli.py                        # load_plugins() call, agentmail consolidation, plugins command,
                                           #   _install_skills + _build_entry_file plugin support
tests/test_cli.py                          # plugins command test, plugin skills installation tests
```

---

## Task 1: Plugin ABC + Discovery

**Files:**
- Create: `src/quidclaw/core/plugins.py`
- Create: `tests/core/test_plugins.py`

- [ ] **Step 1: Write failing tests**

Create `tests/core/test_plugins.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/core/test_plugins.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'quidclaw.core.plugins'`

- [ ] **Step 3: Implement plugins.py**

Create `src/quidclaw/core/plugins.py`:

```python
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
```

- [ ] **Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/core/test_plugins.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/core/plugins.py tests/core/test_plugins.py
git commit -m "feat: add plugin framework — QuidClawPlugin ABC + entry point discovery"
```

---

## Task 2: CLI Integration — load_plugins + agentmail consolidation

**Files:**
- Modify: `src/quidclaw/cli.py`

- [ ] **Step 1: Consolidate agentmail imports**

In `src/quidclaw/cli.py`, add a module-level import after the existing imports (after line 12):

```python
# Register built-in providers
try:
    import quidclaw.core.sources.agentmail  # noqa: F401
except ImportError:
    pass
```

Delete the two lazy import blocks:
- In `add_source()` (~line 646-649): remove the `try: import quidclaw.core.sources.agentmail` block
- In `sync()` (~line 726-729): remove the same block

- [ ] **Step 2: Add load_plugins call**

At the END of `cli.py` (after all `@main.command()` definitions, before nothing), add:

```python
# --- Plugin Loading ---

from quidclaw.core.plugins import load_plugins
load_plugins(main)
```

- [ ] **Step 3: Run tests**

Run: `source .venv/bin/activate && pytest tests/ -v --ignore=tests/e2e`
Expected: ALL PASS (existing tests unaffected — no plugins are installed)

- [ ] **Step 4: Commit**

```bash
git add src/quidclaw/cli.py
git commit -m "feat: load plugins at CLI startup, consolidate agentmail import"
```

---

## Task 3: `quidclaw plugins` Command

**Files:**
- Modify: `src/quidclaw/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_cli.py`:

```python
class TestPlugins:
    def test_plugins_no_plugins(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["plugins"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "No plugins installed" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_cli.py::TestPlugins -v`
Expected: FAIL with `No such command 'plugins'`

- [ ] **Step 3: Implement plugins command**

Add to `src/quidclaw/cli.py` before the plugin loading section:

```python
@main.command("plugins")
def list_plugins():
    """List installed plugins."""
    from quidclaw.core.plugins import discover_plugins
    plugins = discover_plugins()
    if not plugins:
        click.echo("No plugins installed. Install with: pip install quidclaw-<name>")
        return
    for plugin in plugins:
        click.echo(f"  {plugin.name()} — {plugin.description()}")
```

- [ ] **Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_cli.py::TestPlugins tests/test_cli.py::TestInit tests/test_cli.py::TestUpgrade -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/cli.py tests/test_cli.py
git commit -m "feat: add 'quidclaw plugins' command"
```

---

## Task 4: Plugin Skills Installation in init/upgrade

**Files:**
- Modify: `src/quidclaw/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_cli.py` inside `class TestUpgrade`:

```python
def test_upgrade_installs_plugin_skills(self, tmp_path):
    """Plugin skills should be copied to the skills directory on upgrade."""
    from unittest.mock import patch, MagicMock
    from quidclaw.core.plugins import QuidClawPlugin
    import tempfile

    # Create a fake plugin with a skill directory
    with tempfile.TemporaryDirectory() as skill_src:
        skill_dir = Path(skill_src) / "quidclaw-fake"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: quidclaw-fake\ndescription: Fake\n---\nBody")

        class FakePlugin(QuidClawPlugin):
            @staticmethod
            def name(): return "fake"
            @staticmethod
            def description(): return "Fake plugin"
            def get_skills_dir(self):
                return Path(skill_src)

        runner = _init_project(tmp_path)
        with patch("quidclaw.cli.discover_plugins", return_value=[FakePlugin()]):
            result = runner.invoke(
                main, ["upgrade"], catch_exceptions=False,
                env=_env(tmp_path),
            )
        assert result.exit_code == 0
        assert (tmp_path / ".claude" / "skills" / "quidclaw-fake" / "SKILL.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_cli.py::TestUpgrade::test_upgrade_installs_plugin_skills -v`
Expected: FAIL — plugin skills not installed yet

- [ ] **Step 3: Add `_install_plugin_skills` helper**

Add to `src/quidclaw/cli.py` after `_install_skills`:

```python
def _install_plugin_skills(config: QuidClawConfig, platform: str) -> None:
    """Copy skills from installed plugins to the platform skills directory."""
    from quidclaw.core.plugins import discover_plugins
    skills_dir_name = PLATFORM_SKILLS_DIR.get(platform, ".agents/skills")
    skills_target = Path(config.data_dir) / skills_dir_name
    for plugin in discover_plugins():
        plugin_skills = plugin.get_skills_dir()
        if plugin_skills and plugin_skills.exists():
            for skill_dir in plugin_skills.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    target = skills_target / skill_dir.name
                    shutil.copytree(skill_dir, target, dirs_exist_ok=True)
```

- [ ] **Step 4: Call from init and upgrade**

In `init`, after `_install_skills(config, platform)` (line 127), add:
```python
    _install_plugin_skills(config, platform)
```

In `upgrade`, after `_install_skills(...)` (line 173), add:
```python
    _install_plugin_skills(config, platform)
```

(The `platform` variable is already available in both functions.)

- [ ] **Step 5: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_cli.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/quidclaw/cli.py tests/test_cli.py
git commit -m "feat: install plugin skills in init and upgrade"
```

---

## Task 5: Dynamic Entry File with Plugin Skills

**Files:**
- Modify: `src/quidclaw/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_cli.py`:

```python
class TestEntryFile:
    def test_entry_file_includes_plugin_skills(self, tmp_path):
        """Entry file should list plugin skills."""
        from unittest.mock import patch, MagicMock
        from quidclaw.core.plugins import QuidClawPlugin
        import tempfile

        with tempfile.TemporaryDirectory() as skill_src:
            skill_dir = Path(skill_src) / "quidclaw-fake"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("---\nname: quidclaw-fake\ndescription: Fake\n---\n")

            class FakePlugin(QuidClawPlugin):
                @staticmethod
                def name(): return "fake"
                @staticmethod
                def description(): return "Fake plugin"
                def get_skills_dir(self):
                    return Path(skill_src)

            runner = CliRunner()
            with patch("quidclaw.cli.discover_plugins", return_value=[FakePlugin()]):
                result = runner.invoke(
                    main, ["init", "--platform", "claude-code"],
                    catch_exceptions=False, env=_env(tmp_path),
                )
            assert result.exit_code == 0
            content = (tmp_path / "CLAUDE.md").read_text()
            assert "quidclaw-fake" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_cli.py::TestEntryFile -v`
Expected: FAIL — `quidclaw-fake` not in CLAUDE.md

- [ ] **Step 3: Update `_build_entry_file` to include plugin skills**

Replace `_build_entry_file` in `src/quidclaw/cli.py`:

```python
def _build_entry_file(config: QuidClawConfig) -> str:
    """Build minimal platform entry file pointing to skills."""
    from quidclaw.core.plugins import discover_plugins

    currency = config.get_setting("operating_currency")
    currency_line = (
        f"- Operating currency: {currency}"
        if currency
        else "- Operating currency: not yet configured (run onboarding)"
    )

    # Core skills (always present)
    skills_lines = [
        "- `quidclaw` — Project overview, CLI reference, conventions",
        "- `quidclaw-onboarding` — New user setup interview",
        "- `quidclaw-import` — Import and process financial data",
        "- `quidclaw-daily` — Daily financial routine",
        "- `quidclaw-review` — Monthly review and reporting",
    ]

    # Plugin skills
    for plugin in discover_plugins():
        plugin_skills = plugin.get_skills_dir()
        if plugin_skills and plugin_skills.exists():
            for skill_dir in plugin_skills.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    skills_lines.append(
                        f"- `{skill_dir.name}` — {plugin.description()}"
                    )

    skills_block = "\n".join(skills_lines)

    return f"""\
# QuidClaw — Personal CFO

You are a personal CFO managing finances in this directory.
Speak the user's language. Never mention beancount, double-entry, or accounting jargon.

## Configuration

{currency_line}
- Config: `.quidclaw/config.yaml`

## Skills

QuidClaw capabilities are provided as Agent Skills:
{skills_block}
"""
```

- [ ] **Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_cli.py -v`
Expected: ALL PASS

- [ ] **Step 5: Run full test suite**

Run: `source .venv/bin/activate && pytest tests/ -v --ignore=tests/e2e`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/quidclaw/cli.py tests/test_cli.py
git commit -m "feat: entry file dynamically includes plugin skills"
```
