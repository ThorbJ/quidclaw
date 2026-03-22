# OpenClaw Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `quidclaw init` platform-aware, add OpenClaw-specific templates for a dedicated financial agent, add async pending mechanism for headless environments, and simplify README.

**Architecture:** Rewrite `init` command with `--platform` flag. Per-platform file generation replaces the current all-at-once approach. New `core/deps.py` for dependency detection, `core/openclaw.py` for agent creation. Template files stored in `src/quidclaw/templates/`. Workflow updates are additive (new sections appended).

**Tech Stack:** Python subprocess (for openclaw CLI calls), Click (CLI), existing QuidClawConfig.

**Spec:** `docs/superpowers/specs/2026-03-22-openclaw-integration-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/quidclaw/core/deps.py` | Create | Dependency detection and install helpers |
| `src/quidclaw/core/openclaw.py` | Create | OpenClaw agent creation logic |
| `src/quidclaw/templates/soul.md` | Create | SOUL.md template |
| `src/quidclaw/templates/heartbeat.md` | Create | HEARTBEAT.md template |
| `src/quidclaw/templates/bootstrap.md` | Create | BOOTSTRAP.md template |
| `src/quidclaw/templates/identity.md` | Create | IDENTITY.md template |
| `src/quidclaw/cli.py` | Modify | Rewrite `init` (platform flag), update `upgrade`, refactor `_generate_instruction_files` |
| `src/quidclaw/config.py` | Modify | Add `pending_dir` property, `platform` get/set |
| `src/quidclaw/core/ledger.py` | Modify | Create `notes/pending/` in `init()` |
| `src/quidclaw/workflows/onboarding.md` | Modify | Add Automation Setup phase |
| `src/quidclaw/workflows/check-email.md` | Modify | Add "When Blocked" section |
| `src/quidclaw/workflows/import-bills.md` | Modify | Add "When Blocked" section |
| `src/quidclaw/workflows/organize-documents.md` | Modify | Add "When Blocked" section |
| `src/quidclaw/workflows/daily-routine.md` | Modify | Add Output Format section |
| `src/quidclaw/workflows/monthly-review.md` | Modify | Add Output Format section |
| `README.md` | Modify | Simplify, add OpenClaw as primary |
| `tests/core/test_deps.py` | Create | Tests for dependency helpers |
| `tests/core/test_openclaw.py` | Create | Tests for OpenClaw setup |
| `tests/test_cli.py` | Modify | Update init tests for --platform |

---

### Task 1: Dependency Detection Module

**Files:**
- Create: `src/quidclaw/core/deps.py`
- Create: `tests/core/test_deps.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/core/test_deps.py
"""Tests for dependency detection and install helpers."""

import shutil
from unittest.mock import patch

from quidclaw.core.deps import check_dependency, get_install_command


class TestCheckDependency:
    def test_finds_existing_binary(self):
        # git should exist in test environment
        assert check_dependency("git") is True

    def test_missing_binary(self):
        with patch("shutil.which", return_value=None):
            assert check_dependency("nonexistent-binary-xyz") is False


class TestGetInstallCommand:
    def test_macos_uses_brew(self):
        with patch("platform.system", return_value="Darwin"):
            cmd = get_install_command("git", brew="git", apt="git")
            assert "brew install git" in cmd

    def test_linux_uses_apt(self):
        with patch("platform.system", return_value="Linux"):
            cmd = get_install_command("git", brew="git", apt="git")
            assert "apt" in cmd and "git" in cmd

    def test_unknown_os_gives_url(self):
        with patch("platform.system", return_value="Windows"):
            cmd = get_install_command("git", brew="git", apt="git")
            assert "http" in cmd or "manual" in cmd.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/core/test_deps.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement deps.py**

```python
# src/quidclaw/core/deps.py
"""Dependency detection and install assistance."""

import platform
import shutil
import subprocess


def check_dependency(name: str) -> bool:
    """Check if a binary is available on PATH."""
    return shutil.which(name) is not None


def get_install_command(name: str, brew: str = None, apt: str = None) -> str:
    """Return platform-specific install command string."""
    system = platform.system()
    if system == "Darwin" and brew:
        return f"brew install {brew}"
    elif system == "Linux" and apt:
        return f"sudo apt-get install -y {apt}"
    else:
        return f"Install {name} manually: https://git-scm.com/downloads"


def try_install(name: str, brew: str = None, apt: str = None) -> bool:
    """Attempt to install a dependency. Returns True if successful."""
    if check_dependency(name):
        return True
    system = platform.system()
    try:
        if system == "Darwin" and brew and shutil.which("brew"):
            subprocess.run(
                ["brew", "install", brew],
                check=True, capture_output=True, text=True,
            )
            return check_dependency(name)
        elif system == "Linux" and apt:
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", apt],
                check=True, capture_output=True, text=True,
            )
            return check_dependency(name)
    except (subprocess.CalledProcessError, OSError):
        pass
    return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/core/test_deps.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/core/deps.py tests/core/test_deps.py
git commit -m "feat(openclaw): add dependency detection module"
```

---

### Task 2: OpenClaw Template Files

**Files:**
- Create: `src/quidclaw/templates/__init__.py` (empty)
- Create: `src/quidclaw/templates/soul.md`
- Create: `src/quidclaw/templates/heartbeat.md`
- Create: `src/quidclaw/templates/bootstrap.md`
- Create: `src/quidclaw/templates/identity.md`

- [ ] **Step 1: Create template directory and files**

`src/quidclaw/templates/__init__.py` — empty file.

`src/quidclaw/templates/soul.md`:
```markdown
You are a personal CFO — a dedicated financial assistant managing
the user's complete financial life.

## Personality
- Warm, professional, patient
- Speak the user's language (auto-detect from first message)
- Never use accounting jargon — say "你花了多少" not "借方金额"
- Proactive — surface important things without being asked
- Concise in daily briefings, detailed when the user asks

## Boundaries
- You ONLY handle financial matters
- You inform and recommend, never decide for the user
- All data stays local on this machine
- Never share financial data outside this conversation

## When You Don't Know
- If you lack information to complete a task, ask the user
- Record their answer in notes so you never ask again
- If the user doesn't respond immediately, save a pending item
  and follow up next heartbeat
```

`src/quidclaw/templates/heartbeat.md`:
```markdown
# QuidClaw Heartbeat Checklist

Run these checks. If nothing needs attention, reply HEARTBEAT_OK.

1. Run `quidclaw list-sources --json` — if sources exist, run
   `quidclaw sync --json`. If new items synced, process them
   following `.quidclaw/workflows/check-email.md`
2. Check `notes/pending/` — if there are pending items that can now
   be resolved, process them
3. Check `notes/calendar.md` — if any payment is due within 3 days,
   alert the user
4. Run `quidclaw data-status --json` — if inbox has files, mention it
```

`src/quidclaw/templates/bootstrap.md`:
```markdown
# First Run Setup

This is your first time running. Follow these steps:

1. Check `.quidclaw/config.yaml` for `bootstrapped: true`. If set, skip
   and delete this file.
2. Read `.quidclaw/workflows/onboarding.md` and start the onboarding
   conversation with the user
3. After onboarding completes, set up automation:
   - Configure a cron job for daily routine (ask user preferred time)
   - Configure a cron job for monthly report (1st of each month)
4. Set `bootstrapped: true` in `.quidclaw/config.yaml`
5. Delete this file
```

`src/quidclaw/templates/identity.md`:
```markdown
name: QuidClaw
emoji: 💰
```

- [ ] **Step 2: Verify templates are readable**

Run: `.venv/bin/python -c "from pathlib import Path; p = Path('src/quidclaw/templates'); print([f.name for f in p.glob('*.md')])"`
Expected: `['soul.md', 'heartbeat.md', 'bootstrap.md', 'identity.md']`

- [ ] **Step 3: Commit**

```bash
git add src/quidclaw/templates/
git commit -m "feat(openclaw): add template files (SOUL, HEARTBEAT, BOOTSTRAP, IDENTITY)"
```

---

### Task 3: OpenClaw Agent Setup Module

**Files:**
- Create: `src/quidclaw/core/openclaw.py`
- Create: `tests/core/test_openclaw.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/core/test_openclaw.py
"""Tests for OpenClaw agent setup."""

import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from quidclaw.config import QuidClawConfig
from quidclaw.core.openclaw import OpenClawSetup


class TestOpenClawDetection:
    def test_is_available_true(self):
        setup = OpenClawSetup.__new__(OpenClawSetup)
        with patch("shutil.which", return_value="/usr/local/bin/openclaw"):
            assert setup.is_available() is True

    def test_is_available_false(self):
        setup = OpenClawSetup.__new__(OpenClawSetup)
        with patch("shutil.which", return_value=None):
            assert setup.is_available() is False


class TestGenerateTemplates:
    def test_generates_soul_md(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        setup = OpenClawSetup(config)
        setup.generate_templates()
        assert (tmp_path / "SOUL.md").exists()
        content = (tmp_path / "SOUL.md").read_text()
        assert "personal CFO" in content

    def test_generates_heartbeat_md(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        setup = OpenClawSetup(config)
        setup.generate_templates()
        assert (tmp_path / "HEARTBEAT.md").exists()
        assert "HEARTBEAT_OK" in (tmp_path / "HEARTBEAT.md").read_text()

    def test_generates_bootstrap_md(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        setup = OpenClawSetup(config)
        setup.generate_templates()
        assert (tmp_path / "BOOTSTRAP.md").exists()

    def test_generates_identity_md(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        setup = OpenClawSetup(config)
        setup.generate_templates()
        assert (tmp_path / "IDENTITY.md").exists()
        assert "QuidClaw" in (tmp_path / "IDENTITY.md").read_text()

    def test_generates_agents_md(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        setup = OpenClawSetup(config)
        setup.generate_agents_md("# QuidClaw Instructions\nTest body.")
        assert (tmp_path / "AGENTS.md").exists()
        content = (tmp_path / "AGENTS.md").read_text()
        assert "QuidClaw" in content
        assert "Automation" in content  # OpenClaw-specific section
        assert "HEARTBEAT" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/core/test_openclaw.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement openclaw.py**

```python
# src/quidclaw/core/openclaw.py
"""OpenClaw agent setup for QuidClaw."""

import shutil
import subprocess
from pathlib import Path

from quidclaw.config import QuidClawConfig


# Template directory relative to this package
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# OpenClaw-specific AGENTS.md appendix
_AGENTS_AUTOMATION_SECTION = """
## Automation

You have cron jobs and heartbeat configured. Follow these rules:

### Heartbeat
- Read HEARTBEAT.md and follow it strictly
- If nothing needs attention, reply HEARTBEAT_OK
- For urgent items (large unusual charges, overdue payments), alert immediately

### Daily Routine (Cron)
- Follow `.quidclaw/workflows/daily-routine.md`
- Output format: concise, emoji-marked, under 500 characters
- If nothing to report: "一切正常 ✅"

### Monthly Review (Cron)
- Follow `.quidclaw/workflows/monthly-review.md`
- Deliver as a structured summary to the user

### Pending Items
- When a task is blocked (missing info, encrypted PDF, etc.):
  1. Save to `notes/pending/` as YAML
  2. Notify the user what you need
  3. Continue with other tasks
  4. Heartbeat will check pending items and resume when possible
"""


class OpenClawSetup:
    """Handles OpenClaw-specific agent setup."""

    def __init__(self, config: QuidClawConfig):
        self.config = config
        self.data_dir = Path(config.data_dir)

    def is_available(self) -> bool:
        """Check if openclaw CLI is on PATH."""
        return shutil.which("openclaw") is not None

    def generate_templates(self) -> None:
        """Copy OpenClaw template files to data directory."""
        for template_name, target_name in [
            ("soul.md", "SOUL.md"),
            ("heartbeat.md", "HEARTBEAT.md"),
            ("bootstrap.md", "BOOTSTRAP.md"),
            ("identity.md", "IDENTITY.md"),
        ]:
            src = _TEMPLATES_DIR / template_name
            dst = self.data_dir / target_name
            if src.exists():
                dst.write_text(src.read_text())

    def generate_agents_md(self, instruction_body: str) -> None:
        """Generate AGENTS.md with OpenClaw automation section appended.

        instruction_body is required — caller (CLI) builds it via _build_instruction_body().
        This avoids circular imports (core must not import from cli).
        """
        content = instruction_body + _AGENTS_AUTOMATION_SECTION
        (self.data_dir / "AGENTS.md").write_text(content)

    def create_agent(self) -> bool:
        """Create OpenClaw agent. Returns True if successful."""
        if not self.is_available():
            return False
        try:
            subprocess.run(
                ["openclaw", "agents", "add", "quidclaw",
                 "--workspace", str(self.data_dir)],
                check=True, capture_output=True, text=True,
            )
            subprocess.run(
                ["openclaw", "agents", "set-identity",
                 "--agent", "quidclaw",
                 "--name", "QuidClaw", "--emoji", "💰"],
                check=True, capture_output=True, text=True,
            )
            return True
        except (subprocess.CalledProcessError, OSError):
            return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/core/test_openclaw.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/core/openclaw.py tests/core/test_openclaw.py
git commit -m "feat(openclaw): add OpenClaw agent setup module"
```

---

### Task 4: Config — Platform and Pending Dir

**Files:**
- Modify: `src/quidclaw/config.py`
- Modify: `src/quidclaw/core/ledger.py`
- Modify: `tests/core/test_config.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/core/test_config.py`:

```python
class TestPlatformConfig:
    def test_pending_dir_property(self, tmp_path):
        from quidclaw.config import QuidClawConfig
        config = QuidClawConfig(data_dir=tmp_path)
        assert config.pending_dir == tmp_path / "notes" / "pending"

    def test_get_platform_default_none(self, tmp_path):
        from quidclaw.config import QuidClawConfig
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        assert config.get_setting("platform") is None

    def test_set_and_get_platform(self, tmp_path):
        from quidclaw.config import QuidClawConfig
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        config.set_setting("platform", "openclaw")
        assert config.get_setting("platform") == "openclaw"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/core/test_config.py::TestPlatformConfig -v`
Expected: FAIL — `AttributeError: 'QuidClawConfig' object has no attribute 'pending_dir'`

- [ ] **Step 3: Implement**

Add to `src/quidclaw/config.py` (QuidClawConfig class, after `notes_dir`):

```python
    @property
    def pending_dir(self) -> Path:
        return self.notes_dir / "pending"
```

Add to `src/quidclaw/core/ledger.py` (`init` method, after `self.config.logs_dir.mkdir(exist_ok=True)`):

```python
        (self.config.notes_dir / "pending").mkdir(exist_ok=True)
```

Also add to `ensure_dirs`:

```python
        (self.config.notes_dir / "pending").mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/core/test_config.py tests/core/test_ledger.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/config.py src/quidclaw/core/ledger.py tests/core/test_config.py
git commit -m "feat(openclaw): add pending_dir property and platform config"
```

---

### Task 5: Rewrite `init` Command with Platform Support

**Depends on:** Tasks 1-4 (deps module, templates, openclaw module, config changes).

**Files:**
- Modify: `src/quidclaw/cli.py`
- Modify: `tests/test_cli.py`

This is the biggest task. The `init` command and `_generate_instruction_files` need to be rewritten.

- [ ] **Step 1: Write failing tests for new init behavior**

Replace the init tests in `tests/test_cli.py` and add new ones:

```python
class TestInit:
    def test_init_with_platform_claude_code(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "claude-code"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / "CLAUDE.md").exists()
        # Should NOT generate other platform files
        assert not (tmp_path / "GEMINI.md").exists()
        assert not (tmp_path / "SOUL.md").exists()

    def test_init_with_platform_gemini(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "gemini"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / "GEMINI.md").exists()
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_init_with_platform_codex(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "codex"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / "AGENTS.md").exists()
        assert not (tmp_path / "CLAUDE.md").exists()
        assert not (tmp_path / "SOUL.md").exists()

    def test_init_with_platform_openclaw_generates_templates(self, tmp_path):
        runner = CliRunner()
        from unittest.mock import patch
        # Mock openclaw not available (skip agent creation)
        with patch("quidclaw.core.openclaw.OpenClawSetup.is_available", return_value=False):
            result = runner.invoke(
                main, ["init", "--platform", "openclaw"],
                catch_exceptions=False, env=_env(tmp_path),
            )
        assert result.exit_code == 0
        assert (tmp_path / "SOUL.md").exists()
        assert (tmp_path / "HEARTBEAT.md").exists()
        assert (tmp_path / "BOOTSTRAP.md").exists()
        assert (tmp_path / "IDENTITY.md").exists()
        assert (tmp_path / "AGENTS.md").exists()
        # OpenClaw AGENTS.md should have automation section
        assert "Automation" in (tmp_path / "AGENTS.md").read_text()
        # Should NOT generate Claude/Gemini files
        assert not (tmp_path / "CLAUDE.md").exists()
        assert not (tmp_path / "GEMINI.md").exists()

    def test_init_stores_platform_in_config(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "claude-code"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        from quidclaw.config import QuidClawConfig
        config = QuidClawConfig(data_dir=tmp_path)
        assert config.get_setting("platform") == "claude-code"

    def test_init_openclaw_auto_enables_backup(self, tmp_path):
        runner = CliRunner()
        from unittest.mock import patch
        with patch("quidclaw.core.openclaw.OpenClawSetup.is_available", return_value=False):
            result = runner.invoke(
                main, ["init", "--platform", "openclaw"],
                catch_exceptions=False, env=_env(tmp_path),
            )
        assert result.exit_code == 0
        assert (tmp_path / ".git").is_dir()

    def test_init_creates_directories(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "claude-code"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / "ledger").is_dir()
        assert (tmp_path / "inbox").is_dir()
        assert (tmp_path / "documents").is_dir()
        assert (tmp_path / "notes").is_dir()
        assert (tmp_path / "notes" / "pending").is_dir()

    def test_init_creates_workflows(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "claude-code"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / ".quidclaw" / "workflows" / "onboarding.md").exists()

    def test_init_idempotent(self, tmp_path):
        runner = CliRunner()
        env = _env(tmp_path)
        runner.invoke(main, ["init", "--platform", "claude-code"],
                      catch_exceptions=False, env=env)
        result = runner.invoke(main, ["init", "--platform", "claude-code"],
                               catch_exceptions=False, env=env)
        assert result.exit_code == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_cli.py::TestInit -v`
Expected: FAIL — `Error: No such option: --platform`

- [ ] **Step 3: Rewrite init command and file generation**

In `src/quidclaw/cli.py`, replace the `init` command (lines 51-71) with:

```python
PLATFORMS = ["openclaw", "claude-code", "gemini", "codex"]


@main.command()
@click.option("--platform", type=click.Choice(PLATFORMS), default=None,
              help="Target platform (openclaw, claude-code, gemini, codex)")
def init(platform):
    """Initialize a new financial project in the current directory."""
    # Interactive platform selection if not specified
    if platform is None:
        click.echo("Which platform are you using?")
        click.echo("  1. OpenClaw (recommended)")
        click.echo("  2. Claude Code")
        click.echo("  3. Gemini CLI")
        click.echo("  4. Codex")
        click.echo("  5. Other")
        choice = click.prompt("", type=click.IntRange(1, 5))
        platform = {1: "openclaw", 2: "claude-code", 3: "gemini",
                    4: "codex", 5: "codex"}[choice]

    config = get_config()
    ledger = Ledger(config)
    ledger.init()

    # Copy workflow files
    workflows_dir = Path(__file__).parent / "workflows"
    target_dir = Path(config.data_dir) / ".quidclaw" / "workflows"
    if workflows_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in workflows_dir.glob("*.md"):
            shutil.copy2(f, target_dir / f.name)

    # Store platform choice
    config.set_setting("platform", platform)

    # Generate platform-specific instruction files
    body = _build_instruction_body(config)
    data_dir = Path(config.data_dir)

    if platform == "openclaw":
        from quidclaw.core.openclaw import OpenClawSetup
        setup = OpenClawSetup(config)
        setup.generate_templates()
        setup.generate_agents_md(body)

        # Auto-enable git backup for OpenClaw
        from quidclaw.core.backup import BackupManager
        mgr = BackupManager(config)
        if mgr.is_git_available() and not mgr.is_initialized():
            mgr.init()
            click.echo("Git backup: initialized")

        # Try to create OpenClaw agent
        if setup.is_available():
            if setup.create_agent():
                click.echo("OpenClaw agent 'quidclaw' created.")
                click.echo("  Connect it to your messaging app:")
                click.echo("    openclaw agents bind --agent quidclaw --bind <channel>:<account>")
                click.echo("  Run 'openclaw agents bindings' to see available channels.")
            else:
                click.echo("Warning: Could not create OpenClaw agent. Create manually:", err=True)
                click.echo(f"  openclaw agents add quidclaw --workspace {config.data_dir}", err=True)
        else:
            click.echo("Note: openclaw CLI not found. Install OpenClaw, then run:")
            click.echo(f"  openclaw agents add quidclaw --workspace {config.data_dir}")

    elif platform == "claude-code":
        (data_dir / "CLAUDE.md").write_text(body)
        click.echo("Created CLAUDE.md")

    elif platform == "gemini":
        (data_dir / "GEMINI.md").write_text(body)
        click.echo("Created GEMINI.md")

    elif platform == "codex":
        (data_dir / "AGENTS.md").write_text(body)
        click.echo("Created AGENTS.md")

    click.echo(f"Initialized QuidClaw project in {config.data_dir}")
    _try_backup(config, "Initialize QuidClaw data directory")
```

Also update the `upgrade` command to be platform-aware:

```python
@main.command()
def upgrade():
    """Upgrade workflow files and instruction files to latest version."""
    config = get_config()

    workflows_dir = Path(__file__).parent / "workflows"
    target_dir = Path(config.data_dir) / ".quidclaw" / "workflows"
    if workflows_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in workflows_dir.glob("*.md"):
            shutil.copy2(f, target_dir / f.name)
        click.echo(f"Updated workflows in {target_dir}")

    if config.main_bean.exists():
        ledger = Ledger(config)
        ledger.ensure_dirs()

    # Regenerate instruction files for the stored platform
    platform = config.get_setting("platform", "claude-code")
    body = _build_instruction_body(config)
    data_dir = Path(config.data_dir)

    if platform == "openclaw":
        from quidclaw.core.openclaw import OpenClawSetup
        setup = OpenClawSetup(config)
        setup.generate_templates()
        setup.generate_agents_md(body)
        click.echo("Updated OpenClaw files (AGENTS.md, SOUL.md, HEARTBEAT.md, BOOTSTRAP.md, IDENTITY.md)")
    elif platform == "claude-code":
        (data_dir / "CLAUDE.md").write_text(body)
        click.echo("Updated CLAUDE.md")
    elif platform == "gemini":
        (data_dir / "GEMINI.md").write_text(body)
        click.echo("Updated GEMINI.md")
    elif platform == "codex":
        (data_dir / "AGENTS.md").write_text(body)
        click.echo("Updated AGENTS.md")

    # Also update SKILL.md if it exists (for ClawHub users)
    skill_path = data_dir / "skills" / "quidclaw" / "SKILL.md"
    if skill_path.exists():
        skill_prefix = (
            "---\nname: quidclaw\n"
            "description: Personal CFO — AI-powered financial management via Beancount\n"
            "metadata:\n  openclaw:\n    requires:\n      bins: [quidclaw]\n---\n\n"
            "> **Recommended:** For the best experience, create a dedicated QuidClaw\n"
            "> agent with `quidclaw init --platform openclaw`.\n\n"
        )
        skill_path.write_text(skill_prefix + body)
        click.echo("Updated skills/quidclaw/SKILL.md")

    click.echo("Upgrade complete.")
    _try_backup(config, "Upgrade QuidClaw workflows")
```

Remove the old `_INSTRUCTION_FILES` list, `_generate_instruction_files`, and `_generate_claude_md` functions (lines 921-953) as they are no longer used.

Update `_init_project` helper in `tests/test_cli.py` to use `--platform`:

```python
def _init_project(tmp_path):
    """Initialize a QuidClaw project and return the runner."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["init", "--platform", "claude-code"], catch_exceptions=False,
        env={"QUIDCLAW_DATA_DIR": str(tmp_path)},
    )
    assert result.exit_code == 0
    return runner
```

- [ ] **Step 4: Run ALL tests**

Run: `.venv/bin/pytest -v`
Expected: All PASS. Some existing tests may need minor adjustments (e.g., tests checking for GEMINI.md after init won't find it since we now only generate for the selected platform).

Remove or update tests that assume all platform files are generated:
- `TestInit::test_creates_all_instruction_files` — remove (replaced by per-platform tests)
- `TestInit::test_creates_claude_md` — remove (replaced by `test_init_with_platform_claude_code`)
- `TestUpgrade::test_upgrade_updates_instruction_files` — replace with:

```python
    def test_upgrade_updates_instruction_files(self, tmp_path):
        """upgrade refreshes instruction files for the stored platform."""
        runner = _init_project(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("old")
        result = runner.invoke(
            main, ["upgrade"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        content = (tmp_path / "CLAUDE.md").read_text()
        assert content != "old"
        assert "QuidClaw" in content
```

**CRITICAL:** Update `_init_project` helper FIRST before rewriting the init command. All other test classes depend on it:

```python
def _init_project(tmp_path):
    """Initialize a QuidClaw project and return the runner."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["init", "--platform", "claude-code"], catch_exceptions=False,
        env={"QUIDCLAW_DATA_DIR": str(tmp_path)},
    )
    assert result.exit_code == 0
    return runner
```

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/cli.py tests/test_cli.py
git commit -m "feat(openclaw): rewrite init with --platform flag, per-platform file generation"
```

---

### Task 6: Workflow Updates — When Blocked + Output Format

**Files:**
- Modify: `src/quidclaw/workflows/check-email.md`
- Modify: `src/quidclaw/workflows/import-bills.md`
- Modify: `src/quidclaw/workflows/organize-documents.md`
- Modify: `src/quidclaw/workflows/daily-routine.md`
- Modify: `src/quidclaw/workflows/monthly-review.md`

- [ ] **Step 1: Add "When Blocked" section to check-email.md**

Append before `## Important Rules`:

```markdown
## When Blocked

If you cannot complete processing (missing password, unreadable file,
ambiguous data):
1. Save a pending item to `notes/pending/{date}_{description}.yaml` with fields:
   created, type (blocked), reason, context, action
2. Notify the user what you need
3. Move on to the next item — do not stop the entire workflow
4. The pending item will be picked up on the next heartbeat
```

- [ ] **Step 2: Add "When Blocked" section to import-bills.md**

Append before `## Important Rules`:

```markdown
## When Blocked

If you cannot complete processing (encrypted PDF, ambiguous transaction,
missing account info):
1. Save a pending item to `notes/pending/{date}_{description}.yaml` with fields:
   created, type (blocked), reason, context, action
2. Notify the user what you need
3. Move on to the next file — do not stop the entire workflow
4. The pending item will be picked up on the next heartbeat
```

- [ ] **Step 3: Add "When Blocked" section to organize-documents.md**

Append before `## Rules`:

```markdown
## When Blocked

If you cannot identify a document and the user is not available:
1. Save a pending item to `notes/pending/{date}_{description}.yaml`
2. Leave the file in inbox
3. Move on to the next file
```

- [ ] **Step 4: Add Output Format section to daily-routine.md**

Replace the `## When to Run` section with:

```markdown
## Output Format

Keep the daily briefing concise and scannable for messaging apps:
- Use emoji as visual markers (📬 📊 ⚠️ ✅)
- One line per item, no tables or code blocks
- Total length under 500 characters
- If nothing needs attention: "一切正常 ✅"

Example:
  📬 2 new emails processed (招商银行, 电费通知)
  💳 信用卡账单已导入: ¥8,523 (47 笔)
  ⏰ 房租 ¥5,000 后天到期
  ✅ 其余一切正常

## When to Run

This workflow can be triggered:
- Manually by the user ("check my finances", "daily routine", "what's new")
- By a cron job (OpenClaw: daily at user's preferred time)
- At the start of a conversation when the user has configured proactive mode
```

- [ ] **Step 5: Add Output Format section to monthly-review.md**

Append before `## Save Report`:

```markdown
## Output Format

Monthly summary should be structured but readable in chat:
- Lead with the headline numbers
- Category breakdown as a simple list
- Flag anomalies and notable changes
- Keep under 1000 characters for the summary
- Offer to send detailed report if user wants

Example:
  📊 3月财务总结
  💰 收入: ¥25,000
  💸 支出: ¥18,523 (比上月 +8%)
  🏠 房租 ¥5,000 (27%) | 🍽 餐饮 ¥3,200 (17%) | 🚗 交通 ¥1,800 (10%)
  ⚠️ Netflix 从 $15.99 涨到 $22.99
  📁 详细报告已保存到 reports/
```

- [ ] **Step 6: Commit**

```bash
git add src/quidclaw/workflows/
git commit -m "feat(openclaw): add async pending mechanism and messaging output format to workflows"
```

---

### Task 7: Onboarding — Automation Setup Phase

**Files:**
- Modify: `src/quidclaw/workflows/onboarding.md`

- [ ] **Step 1: Read current onboarding.md end section**

Verify the Git Backup Setup phase is at the end.

- [ ] **Step 2: Append Automation Setup phase after Git Backup Setup**

```markdown
## Phase: Automation Setup (OpenClaw only)

Check if running in OpenClaw by looking for HEARTBEAT.md in the workspace root.
If not present, skip this phase.

### Step 1: Daily Routine

Ask user: "I can automatically check your email, remind you about
upcoming payments, and give you a daily briefing. What time works best?"

Based on their answer, run via Bash:
```
openclaw cron add --name "QuidClaw daily" \
  --cron "0 {hour} * * *" --tz "{user_timezone}" \
  --session isolated \
  --message "Follow .quidclaw/workflows/daily-routine.md"
```

Record in notes/profile.md under ## Automation:
  "Daily briefing: {time} {timezone}"

If user declines:
  Record in notes/profile.md: "Daily briefing: declined"
  Append to notes/decisions/{year}.md: "{date}: User declined daily automation. Reason: {reason if given}."

### Step 2: Monthly Report

Ask user: "I'll send you a monthly financial summary on the 1st of
each month. Same time as daily briefing, or different?"

Run via Bash:
```
openclaw cron add --name "QuidClaw monthly" \
  --cron "0 {hour} 1 * *" --tz "{user_timezone}" \
  --session isolated \
  --message "Follow .quidclaw/workflows/monthly-review.md"
```

Record in notes/profile.md under ## Automation:
  "Monthly report: 1st of each month at {time}"

### Step 3: Confirm

"All set! Here's what I'll do automatically:
 - Every day at {time}: check email, process new items, briefing
 - Every month on the 1st: financial summary
 - Anytime: alert you about urgent items (large charges, overdue payments)

 You can change these anytime by telling me."

Record all automation settings in notes/profile.md.
```

- [ ] **Step 3: Commit**

```bash
git add src/quidclaw/workflows/onboarding.md
git commit -m "feat(openclaw): add automation setup phase to onboarding"
```

---

### Task 8: README, Docs, and Package Config

**Files:**
- Modify: `README.md`
- Modify: `docs/contributing.md` — update references to removed `_generate_claude_md()`
- Modify: `pyproject.toml` — ensure template .md files are included in package

- [ ] **Step 1: Rewrite README**

Keep: product intro (Why QuidClaw, How It Works, Features, Data Storage, Usage Example, Development, License).

Remove: full CLI Reference tables (50+ lines), full Workflows table.

Add: OpenClaw as primary Quick Start.

Replace the Quick Start section with:

```markdown
## Quick Start

### OpenClaw (recommended)

```bash
pip install quidclaw
quidclaw init --platform openclaw
```

This creates a dedicated financial agent. Connect it to Telegram, WhatsApp, or any supported chat app. The agent handles onboarding, daily routines, and monthly reports automatically.

### Claude Code

```bash
pip install quidclaw
mkdir ~/my-finances && cd ~/my-finances
quidclaw init --platform claude-code
claude
```

### Other AI Tools

```bash
pip install quidclaw
quidclaw init   # interactive platform selection
```
```

Replace the CLI Reference and Workflows sections with:

```markdown
## CLI & Workflows

31 commands for accounting operations, data source management, and backup. 9 workflow guides for multi-step tasks. All designed for AI agents — the AI reads the instruction files and calls the CLI.

See [docs/cli-reference.md](docs/cli-reference.md) for the complete command list.
```

- [ ] **Step 2: Update docs/contributing.md**

Replace any references to `_generate_claude_md()` or `_generate_instruction_files()` with updated guidance: when adding a new CLI command, add it to `_build_instruction_body()` in `cli.py`. The instruction body is used by all platforms.

- [ ] **Step 3: Update pyproject.toml for package data**

Ensure `.md` files in `templates/` and `workflows/` are included in the distribution. Add to `pyproject.toml`:

```toml
[tool.setuptools.package-data]
quidclaw = ["templates/*.md", "workflows/*.md"]
```

(Check if this section already exists; if so, merge.)

- [ ] **Step 4: Verify README renders correctly**

Read the file to check structure.

- [ ] **Step 5: Run tests to make sure nothing is broken**

Run: `.venv/bin/pytest -v`

- [ ] **Step 6: Commit**

```bash
git add README.md docs/contributing.md pyproject.toml
git commit -m "docs: simplify README, update contributing guide, fix package data"
```

---

### Task 9: SKILL.md Update for ClawHub

**Files:**
- Modify: `src/quidclaw/cli.py` (the SKILL.md is generated in the _build_instruction_body area — but wait, we removed _INSTRUCTION_FILES. SKILL.md is now for ClawHub distribution only, not generated by init.)

Actually, SKILL.md needs to be a static file shipped with the package for ClawHub, not generated by init.

- [ ] **Step 1: Create static SKILL.md for ClawHub**

Create `src/quidclaw/templates/skill.md`:

```markdown
---
name: quidclaw
description: Personal CFO — AI-powered financial management via Beancount
metadata:
  openclaw:
    requires:
      bins: [quidclaw]
---

> **Recommended:** For the best experience, create a dedicated QuidClaw
> agent with `quidclaw init --platform openclaw`. This gives you isolated
> context, dedicated automation, and a cleaner financial management
> experience.

{instruction body will be appended at build time or manually}
```

Note: The SKILL.md for ClawHub distribution is a packaging concern, not an init concern. For now, create the template file. The actual ClawHub publish workflow is out of scope.

- [ ] **Step 2: Commit**

```bash
git add src/quidclaw/templates/skill.md
git commit -m "feat(openclaw): add SKILL.md template for ClawHub distribution"
```

---

### Task 10: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `.venv/bin/pytest -v`
Expected: All tests pass

- [ ] **Step 2: Smoke test — OpenClaw init**

```bash
cd /tmp && rm -rf oc-test && mkdir oc-test
QUIDCLAW_DATA_DIR=/tmp/oc-test .venv/bin/quidclaw init --platform openclaw
ls /tmp/oc-test/SOUL.md /tmp/oc-test/HEARTBEAT.md /tmp/oc-test/BOOTSTRAP.md /tmp/oc-test/IDENTITY.md /tmp/oc-test/AGENTS.md
cat /tmp/oc-test/AGENTS.md | grep -c "Automation"  # should be > 0
ls /tmp/oc-test/.git  # should exist (auto backup)
ls /tmp/oc-test/notes/pending  # should exist
rm -rf /tmp/oc-test
```

- [ ] **Step 3: Smoke test — Claude Code init**

```bash
cd /tmp && rm -rf cc-test && mkdir cc-test
QUIDCLAW_DATA_DIR=/tmp/cc-test .venv/bin/quidclaw init --platform claude-code
ls /tmp/cc-test/CLAUDE.md  # should exist
test ! -f /tmp/cc-test/SOUL.md  # should NOT exist
rm -rf /tmp/cc-test
```

- [ ] **Step 4: Commit any fixes**

```bash
git add -A && git commit -m "fix: address issues from final verification"
```
