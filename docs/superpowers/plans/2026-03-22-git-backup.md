# Git Backup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Git-based version control and multi-remote backup to QuidClaw data directories, with automatic commit after write operations and async push to all configured remotes.

**Architecture:** New `core/backup.py` module with `BackupManager` class that wraps `git` CLI via `subprocess`. CLI write commands call `try_backup()` after successful execution. Push is fire-and-forget via `Popen`, never blocking. Multiple remotes supported natively via standard Git.

**Tech Stack:** Python subprocess (git CLI), no new dependencies.

**Spec:** `docs/superpowers/specs/2026-03-22-git-backup-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/quidclaw/core/backup.py` | Create | BackupManager class — all Git operations |
| `tests/core/test_backup.py` | Create | Unit tests for BackupManager |
| `src/quidclaw/cli.py` | Modify | Add `backup` command group + `_try_backup()` wrapper in write commands |
| `tests/test_cli.py` | Modify | Add CLI tests for backup commands |
| `src/quidclaw/config.py` | Modify | Add backup config helpers (enabled, auto_commit, auto_push) |
| `tests/core/test_config.py` | Modify | Add tests for backup config |
| `src/quidclaw/workflows/onboarding.md` | Modify | Add Git Backup Setup phase |
| `docs/architecture.md` | Modify | Add backup module description |

---

### Task 1: BackupManager — Git Detection and Init

**Files:**
- Create: `src/quidclaw/core/backup.py`
- Create: `tests/core/test_backup.py`

- [ ] **Step 1: Write failing tests for git detection and init**

```python
# tests/core/test_backup.py
"""Tests for Git backup manager."""

import subprocess
from unittest.mock import patch

from quidclaw.config import QuidClawConfig
from quidclaw.core.backup import BackupManager


class TestGitDetection:
    def test_is_git_available_true(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        # git should be available in test environment
        assert mgr.is_git_available() is True

    def test_is_git_available_false(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        with patch("shutil.which", return_value=None):
            assert mgr.is_git_available() is False

    def test_is_initialized_false_when_no_repo(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        assert mgr.is_initialized() is False


class TestGitInit:
    def test_init_creates_git_repo(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        assert (tmp_path / ".git").is_dir()
        assert mgr.is_initialized() is True

    def test_init_creates_gitignore(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "inbox/" in content
        assert ".quidclaw/config.yaml" in content

    def test_init_creates_gitattributes(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        gitattributes = tmp_path / ".gitattributes"
        assert gitattributes.exists()
        content = gitattributes.read_text()
        assert "*.pdf" in content

    def test_init_creates_initial_commit(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert "Initialize QuidClaw" in result.stdout

    def test_init_idempotent(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        mgr.init()  # should not raise
        assert mgr.is_initialized() is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_backup.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'quidclaw.core.backup'`

- [ ] **Step 3: Implement BackupManager with detection and init**

```python
# src/quidclaw/core/backup.py
"""Git-based backup for QuidClaw data directories."""

import shutil
import subprocess
from pathlib import Path

from quidclaw.config import QuidClawConfig

GITIGNORE_CONTENT = """\
# QuidClaw — auto-generated
# Temporary files
inbox/

# Secrets (API keys in config)
.quidclaw/config.yaml

# OS files
.DS_Store
Thumbs.db

# Editor files
*.swp
*~
"""

GITATTRIBUTES_CONTENT = """\
# QuidClaw LFS — track binary files
documents/**/*.pdf filter=lfs diff=lfs merge=lfs -text
documents/**/*.png filter=lfs diff=lfs merge=lfs -text
documents/**/*.jpg filter=lfs diff=lfs merge=lfs -text
documents/**/*.jpeg filter=lfs diff=lfs merge=lfs -text
documents/**/*.gif filter=lfs diff=lfs merge=lfs -text
documents/**/*.xlsx filter=lfs diff=lfs merge=lfs -text
documents/**/*.xls filter=lfs diff=lfs merge=lfs -text
documents/**/*.docx filter=lfs diff=lfs merge=lfs -text
documents/**/*.doc filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.pdf filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.png filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.jpg filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.jpeg filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.gif filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.xlsx filter=lfs diff=lfs merge=lfs -text
sources/**/attachments/*.xls filter=lfs diff=lfs merge=lfs -text
"""


class BackupManager:
    """Git-based backup for QuidClaw data directories."""

    def __init__(self, config: QuidClawConfig):
        self.data_dir = Path(config.data_dir)

    def _run_git(self, *args, check=True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=self.data_dir,
            check=check,
            capture_output=True,
            text=True,
        )

    # --- Detection ---

    def is_git_available(self) -> bool:
        return shutil.which("git") is not None

    def is_initialized(self) -> bool:
        return (self.data_dir / ".git").is_dir()

    def is_lfs_available(self) -> bool:
        return shutil.which("git-lfs") is not None

    # --- Init ---

    def init(self) -> None:
        if self.is_initialized():
            return

        self._run_git("init")
        self._run_git("config", "user.email", "quidclaw@local")
        self._run_git("config", "user.name", "QuidClaw")

        (self.data_dir / ".gitignore").write_text(GITIGNORE_CONTENT)
        (self.data_dir / ".gitattributes").write_text(GITATTRIBUTES_CONTENT)

        if self.is_lfs_available():
            self._run_git("lfs", "install", "--local")

        self._run_git("add", "-A")
        self._run_git("commit", "-m", "Initialize QuidClaw data directory")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_backup.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/core/backup.py tests/core/test_backup.py
git commit -m "feat(backup): add BackupManager with git detection and init"
```

---

### Task 2: BackupManager — Remote Management

**Files:**
- Modify: `src/quidclaw/core/backup.py`
- Modify: `tests/core/test_backup.py`

- [ ] **Step 1: Write failing tests for remote management**

Append to `tests/core/test_backup.py`:

```python
class TestRemoteManagement:
    def _init_repo(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        return mgr

    def test_has_remotes_false_initially(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        assert mgr.has_remotes() is False

    def test_list_remotes_empty(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        assert mgr.list_remotes() == []

    def test_add_remote(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        mgr.add_remote("github", "https://github.com/user/repo.git")
        remotes = mgr.list_remotes()
        assert len(remotes) == 1
        assert remotes[0]["name"] == "github"
        assert remotes[0]["url"] == "https://github.com/user/repo.git"

    def test_add_multiple_remotes(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        mgr.add_remote("github", "https://github.com/user/repo.git")
        mgr.add_remote("gitee", "https://gitee.com/user/repo.git")
        remotes = mgr.list_remotes()
        assert len(remotes) == 2
        names = {r["name"] for r in remotes}
        assert names == {"github", "gitee"}

    def test_remove_remote(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        mgr.add_remote("github", "https://github.com/user/repo.git")
        mgr.remove_remote("github")
        assert mgr.has_remotes() is False

    def test_remove_remote_nonexistent_raises(self, tmp_path):
        import pytest
        mgr = self._init_repo(tmp_path)
        with pytest.raises(subprocess.CalledProcessError):
            mgr.remove_remote("nonexistent")

    def test_has_remotes_true(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        mgr.add_remote("origin", "https://example.com/repo.git")
        assert mgr.has_remotes() is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_backup.py::TestRemoteManagement -v`
Expected: FAIL — `AttributeError: 'BackupManager' object has no attribute 'has_remotes'`

- [ ] **Step 3: Implement remote management methods**

Add to `BackupManager` class in `src/quidclaw/core/backup.py`:

```python
    # --- Remote Management ---

    def list_remotes(self) -> list[dict]:
        if not self.is_initialized():
            return []
        result = self._run_git("remote", "-v", check=False)
        if result.returncode != 0 or not result.stdout.strip():
            return []
        remotes = {}
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] not in remotes:
                remotes[parts[0]] = {"name": parts[0], "url": parts[1]}
        return list(remotes.values())

    def has_remotes(self) -> bool:
        return len(self.list_remotes()) > 0

    def add_remote(self, name: str, url: str) -> None:
        self._run_git("remote", "add", name, url)

    def remove_remote(self, name: str) -> None:
        self._run_git("remote", "remove", name)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_backup.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/core/backup.py tests/core/test_backup.py
git commit -m "feat(backup): add remote management (multi-remote support)"
```

---

### Task 3: BackupManager — Auto Commit and Push

**Files:**
- Modify: `src/quidclaw/core/backup.py`
- Modify: `tests/core/test_backup.py`

- [ ] **Step 1: Write failing tests for auto_commit and commit_and_push**

Append to `tests/core/test_backup.py`:

```python
class TestAutoCommit:
    def _init_repo(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        return mgr

    def test_auto_commit_with_changes(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        (tmp_path / "ledger").mkdir(exist_ok=True)
        (tmp_path / "ledger" / "test.bean").write_text("test data")
        result = mgr.auto_commit("Add test data")
        assert result is True
        # Verify commit message
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert "Add test data" in log.stdout

    def test_auto_commit_no_changes(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        result = mgr.auto_commit("Nothing to commit")
        assert result is False

    def test_auto_commit_stages_new_and_modified(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        # Create new file
        (tmp_path / "notes").mkdir(exist_ok=True)
        (tmp_path / "notes" / "test.md").write_text("note")
        mgr.auto_commit("Add note")
        # Modify existing file
        (tmp_path / "notes" / "test.md").write_text("updated note")
        result = mgr.auto_commit("Update note")
        assert result is True

    def test_auto_commit_respects_gitignore(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        # inbox/ is in .gitignore
        (tmp_path / "inbox").mkdir(exist_ok=True)
        (tmp_path / "inbox" / "temp.csv").write_text("data")
        result = mgr.auto_commit("Should be empty")
        assert result is False


class TestAutoPush:
    def _init_repo(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        return mgr

    def test_auto_push_no_remote_does_nothing(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        # Should not raise
        mgr.auto_push()

    def test_auto_push_with_remote_fires_subprocess(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        mgr.add_remote("origin", "https://example.com/repo.git")
        with patch("subprocess.Popen") as mock_popen:
            mgr.auto_push()
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            assert args == ["git", "push", "origin"]

    def test_auto_push_multiple_remotes(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        mgr.add_remote("github", "https://github.com/u/r.git")
        mgr.add_remote("gitee", "https://gitee.com/u/r.git")
        with patch("subprocess.Popen") as mock_popen:
            mgr.auto_push()
            assert mock_popen.call_count == 2
            pushed = {call[0][0][2] for call in mock_popen.call_args_list}
            assert pushed == {"github", "gitee"}

    def test_commit_and_push(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        (tmp_path / "ledger").mkdir(exist_ok=True)
        (tmp_path / "ledger" / "test.bean").write_text("data")
        mgr.add_remote("origin", "https://example.com/repo.git")
        with patch("subprocess.Popen"):
            result = mgr.commit_and_push("Test commit")
            assert result is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_backup.py::TestAutoCommit tests/core/test_backup.py::TestAutoPush -v`
Expected: FAIL — `AttributeError: 'BackupManager' object has no attribute 'auto_commit'`

- [ ] **Step 3: Implement auto_commit, auto_push, commit_and_push**

Add to `BackupManager` class in `src/quidclaw/core/backup.py`:

```python
    # --- Daily Operations ---

    def auto_commit(self, message: str) -> bool:
        if not self.is_initialized():
            return False
        self._run_git("add", "-A")
        # Check if there are staged changes
        result = self._run_git("diff", "--cached", "--quiet", check=False)
        if result.returncode == 0:
            return False  # No changes
        self._run_git("commit", "-m", message)
        return True

    def auto_push(self) -> None:
        if not self.is_initialized():
            return
        remotes = self.list_remotes()
        for remote in remotes:
            try:
                subprocess.Popen(
                    ["git", "push", remote["name"]],
                    cwd=self.data_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except OSError:
                pass

    def commit_and_push(self, message: str) -> bool:
        if self.auto_commit(message):
            self.auto_push()
            return True
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_backup.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/core/backup.py tests/core/test_backup.py
git commit -m "feat(backup): add auto_commit, auto_push, commit_and_push"
```

---

### Task 4: BackupManager — Status and Install Instructions

**Files:**
- Modify: `src/quidclaw/core/backup.py`
- Modify: `tests/core/test_backup.py`

- [ ] **Step 1: Write failing tests for status and install instructions**

Append to `tests/core/test_backup.py`:

```python
import platform


class TestStatus:
    def test_status_not_initialized(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        status = mgr.status()
        assert status["initialized"] is False
        assert status["remotes"] == []

    def test_status_initialized_no_remote(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        status = mgr.status()
        assert status["initialized"] is True
        assert status["remotes"] == []
        assert status["last_commit"] is not None
        assert "Initialize QuidClaw" in status["last_commit"]

    def test_status_with_remotes(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        mgr.add_remote("github", "https://github.com/u/r.git")
        status = mgr.status()
        assert len(status["remotes"]) == 1
        assert status["remotes"][0]["name"] == "github"


class TestInstallInstructions:
    def test_returns_string(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        instructions = mgr.get_install_instructions()
        assert isinstance(instructions, str)
        assert "git" in instructions.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_backup.py::TestStatus tests/core/test_backup.py::TestInstallInstructions -v`
Expected: FAIL

- [ ] **Step 3: Implement status and get_install_instructions**

Add to `BackupManager` class in `src/quidclaw/core/backup.py`:

```python
    import platform  # add at top of file

    # --- Status ---

    def status(self) -> dict:
        result = {
            "initialized": self.is_initialized(),
            "git_available": self.is_git_available(),
            "lfs_available": self.is_lfs_available(),
            "remotes": [],
            "last_commit": None,
        }
        if not self.is_initialized():
            return result
        result["remotes"] = self.list_remotes()
        log = self._run_git("log", "--oneline", "-1", check=False)
        if log.returncode == 0:
            result["last_commit"] = log.stdout.strip()
        return result

    def get_install_instructions(self) -> str:
        system = platform.system()
        if system == "Darwin":
            return "Install Git: xcode-select --install  (or: brew install git)"
        elif system == "Linux":
            return "Install Git: sudo apt install git  (or: sudo yum install git)"
        else:
            return "Install Git: https://git-scm.com/downloads"
```

Note: move `import platform` to the top of the file alongside other imports.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_backup.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/core/backup.py tests/core/test_backup.py
git commit -m "feat(backup): add status reporting and install instructions"
```

---

### Task 5: try_backup Helper Function

**Files:**
- Modify: `src/quidclaw/core/backup.py`
- Modify: `tests/core/test_backup.py`

- [ ] **Step 1: Write failing test for try_backup**

Append to `tests/core/test_backup.py`:

```python
from quidclaw.core.backup import try_backup


class TestTryBackup:
    def test_try_backup_when_initialized(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        mgr.init()
        (tmp_path / "ledger").mkdir(exist_ok=True)
        (tmp_path / "ledger" / "test.bean").write_text("data")
        # Should not raise
        try_backup(config, "Test backup")
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert "Test backup" in log.stdout

    def test_try_backup_when_not_initialized(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        # Should not raise even though no git repo
        try_backup(config, "Should be fine")

    def test_try_backup_never_raises(self, tmp_path):
        config = QuidClawConfig(data_dir=None)
        # Even with broken config, should not raise
        try_backup(config, "Should not raise")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_backup.py::TestTryBackup -v`
Expected: FAIL — `ImportError: cannot import name 'try_backup'`

- [ ] **Step 3: Implement try_backup**

Add to the bottom of `src/quidclaw/core/backup.py` (module-level function, not a method):

```python
def try_backup(config: QuidClawConfig, message: str) -> None:
    """Attempt git backup if initialized. Never raises."""
    try:
        mgr = BackupManager(config)
        if mgr.is_initialized():
            mgr.commit_and_push(message)
    except Exception:
        pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_backup.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/core/backup.py tests/core/test_backup.py
git commit -m "feat(backup): add try_backup helper function"
```

---

### Task 6: Backup Config Settings

**Files:**
- Modify: `src/quidclaw/config.py`
- Modify: `tests/core/test_config.py`
- Modify: `src/quidclaw/core/backup.py`

- [ ] **Step 1: Write failing tests for backup config helpers**

Append to `tests/core/test_config.py`:

```python
class TestBackupConfig:
    def test_backup_defaults_not_set(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        assert config.get_backup_setting("enabled") is None

    def test_set_and_get_backup_setting(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        config.set_backup_setting("enabled", True)
        assert config.get_backup_setting("enabled") is True

    def test_backup_settings_nested_under_backup_key(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        config.set_backup_setting("enabled", True)
        config.set_backup_setting("auto_push", True)
        settings = config.load_settings()
        assert settings["backup"]["enabled"] is True
        assert settings["backup"]["auto_push"] is True

    def test_backup_setting_does_not_clobber_other_settings(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        config.set_setting("operating_currency", "CNY")
        config.set_backup_setting("enabled", True)
        assert config.get_setting("operating_currency") == "CNY"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_config.py::TestBackupConfig -v`
Expected: FAIL — `AttributeError: 'QuidClawConfig' object has no attribute 'get_backup_setting'`

- [ ] **Step 3: Implement backup config helpers in config.py**

Add to `QuidClawConfig` class in `src/quidclaw/config.py`:

```python
    def get_backup_setting(self, key: str, default=None):
        """Get a backup setting from backup.{key}."""
        return self.load_settings().get("backup", {}).get(key, default)

    def set_backup_setting(self, key: str, value) -> None:
        """Set a backup setting under backup.{key}."""
        settings = self.load_settings()
        settings.setdefault("backup", {})[key] = value
        self.save_settings(settings)
```

- [ ] **Step 4: Update BackupManager to check config before commit/push**

In `src/quidclaw/core/backup.py`, update `try_backup` to respect config:

```python
def try_backup(config: QuidClawConfig, message: str) -> None:
    """Attempt git backup if initialized and enabled. Never raises."""
    try:
        if config.get_backup_setting("enabled") is False:
            return
        mgr = BackupManager(config)
        if mgr.is_initialized():
            mgr.commit_and_push(message)
    except Exception:
        pass
```

Update `BackupManager.auto_push` to check `auto_push` setting:

```python
    def auto_push(self) -> None:
        if not self.is_initialized():
            return
        # Check if auto_push is explicitly disabled
        try:
            config = QuidClawConfig(data_dir=self.data_dir)
            if config.get_backup_setting("auto_push") is False:
                return
        except Exception:
            pass
        remotes = self.list_remotes()
        for remote in remotes:
            try:
                subprocess.Popen(
                    ["git", "push", remote["name"]],
                    cwd=self.data_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except OSError:
                pass
```

Update `BackupManager.init` to write default config:

```python
    def init(self) -> None:
        if self.is_initialized():
            return
        # ... existing init code ...
        # Write default backup config
        config = QuidClawConfig(data_dir=self.data_dir)
        config.set_backup_setting("enabled", True)
        config.set_backup_setting("auto_commit", True)
        config.set_backup_setting("auto_push", True)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/core/test_config.py tests/core/test_backup.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/quidclaw/config.py src/quidclaw/core/backup.py tests/core/test_config.py
git commit -m "feat(backup): add backup config settings (enabled, auto_commit, auto_push)"
```

---

### Task 7: CLI — Backup Command Group

**Files:**
- Modify: `src/quidclaw/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for backup CLI commands**

Append to `tests/test_cli.py`:

```python
# --- Backup ---


class TestBackup:
    def test_backup_init(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["backup", "init"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / ".git").is_dir()

    def test_backup_init_already_initialized(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        result = runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        assert result.exit_code == 0
        assert "already" in result.output.lower()

    def test_backup_status_not_initialized(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["backup", "status"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "not initialized" in result.output.lower() or "initialized: false" in result.output.lower()

    def test_backup_status_initialized(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        result = runner.invoke(
            main, ["backup", "status"], catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0

    def test_backup_status_json(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        result = runner.invoke(
            main, ["backup", "status", "--json"], catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["initialized"] is True

    def test_backup_add_remote(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        result = runner.invoke(
            main, ["backup", "add-remote", "github", "https://github.com/u/r.git"],
            catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0
        assert "github" in result.output

    def test_backup_add_multiple_remotes(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        runner.invoke(
            main, ["backup", "add-remote", "github", "https://github.com/u/r.git"],
            catch_exceptions=False, env=env,
        )
        runner.invoke(
            main, ["backup", "add-remote", "gitee", "https://gitee.com/u/r.git"],
            catch_exceptions=False, env=env,
        )
        result = runner.invoke(
            main, ["backup", "status", "--json"], catch_exceptions=False, env=env,
        )
        data = json.loads(result.output)
        assert len(data["remotes"]) == 2

    def test_backup_remove_remote(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        runner.invoke(
            main, ["backup", "add-remote", "github", "https://github.com/u/r.git"],
            catch_exceptions=False, env=env,
        )
        result = runner.invoke(
            main, ["backup", "remove-remote", "github"],
            catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0

    def test_backup_push_no_init(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["backup", "push"],
            env=_env(tmp_path),
        )
        assert result.exit_code != 0

    def test_backup_init_requires_git(self, tmp_path):
        runner = _init_project(tmp_path)
        from unittest.mock import patch
        with patch("quidclaw.core.backup.shutil.which", return_value=None):
            result = runner.invoke(
                main, ["backup", "init"],
                env=_env(tmp_path),
            )
        assert result.exit_code != 0
        assert "git" in result.output.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::TestBackup -v`
Expected: FAIL — `Error: No such command 'backup'.`

- [ ] **Step 3: Implement backup command group in cli.py**

Add to `src/quidclaw/cli.py` after the `# --- Helpers ---` section comment (before `_build_instruction_body`), insert a new section:

```python
# --- Backup ---


@main.group()
def backup():
    """Git backup management."""
    pass


@backup.command("init")
def backup_init():
    """Initialize Git backup for this data directory."""
    from quidclaw.core.backup import BackupManager
    config = get_config()
    mgr = BackupManager(config)
    if not mgr.is_git_available():
        click.echo(f"Error: Git is not installed. {mgr.get_install_instructions()}", err=True)
        sys.exit(1)
    if mgr.is_initialized():
        click.echo("Git backup already initialized.")
        return
    mgr.init()
    click.echo("Initialized Git backup.")
    if not mgr.is_lfs_available():
        click.echo("Note: git-lfs not installed. Binary files will be stored without LFS.")
        click.echo("  Install: brew install git-lfs  (or: apt install git-lfs)")


@backup.command("status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def backup_status(as_json):
    """Show backup status."""
    from quidclaw.core.backup import BackupManager
    config = get_config()
    mgr = BackupManager(config)
    status = mgr.status()
    if as_json:
        click.echo(json.dumps(status, indent=2))
    else:
        if not status["initialized"]:
            click.echo("Git backup: not initialized")
            click.echo("  Run 'quidclaw backup init' to enable.")
            return
        click.echo("Git backup: initialized")
        click.echo(f"  Last commit: {status['last_commit']}")
        click.echo(f"  LFS: {'available' if status['lfs_available'] else 'not installed'}")
        remotes = status["remotes"]
        if remotes:
            click.echo(f"  Remotes ({len(remotes)}):")
            for r in remotes:
                click.echo(f"    {r['name']}: {r['url']}")
        else:
            click.echo("  Remotes: none configured")


@backup.command("add-remote")
@click.argument("name")
@click.argument("url")
def backup_add_remote(name, url):
    """Add a remote repository for backup."""
    from quidclaw.core.backup import BackupManager
    config = get_config()
    mgr = BackupManager(config)
    if not mgr.is_initialized():
        click.echo("Error: Git backup not initialized. Run 'quidclaw backup init' first.", err=True)
        sys.exit(1)
    mgr.add_remote(name, url)
    click.echo(f"Added remote '{name}': {url}")
    click.echo(f"  Make sure the repository is Private (financial data!).")
    click.echo(f"  Test with: quidclaw backup push --remote {name}")


@backup.command("remove-remote")
@click.argument("name")
def backup_remove_remote(name):
    """Remove a remote repository."""
    from quidclaw.core.backup import BackupManager
    config = get_config()
    mgr = BackupManager(config)
    if not mgr.is_initialized():
        click.echo("Error: Git backup not initialized.", err=True)
        sys.exit(1)
    import subprocess as _sp
    try:
        mgr.remove_remote(name)
    except _sp.CalledProcessError:
        click.echo(f"Error: Remote '{name}' not found.", err=True)
        sys.exit(1)
    click.echo(f"Removed remote '{name}'.")


@backup.command("push")
@click.option("--remote", default=None, help="Push to specific remote (default: all)")
def backup_push(remote):
    """Push to remote repositories."""
    import subprocess as _sp
    from quidclaw.core.backup import BackupManager
    config = get_config()
    mgr = BackupManager(config)
    if not mgr.is_initialized():
        click.echo("Error: Git backup not initialized.", err=True)
        sys.exit(1)
    if remote:
        try:
            mgr._run_git("push", remote)
            click.echo(f"Pushed to '{remote}'.")
        except _sp.CalledProcessError as e:
            click.echo(f"Error pushing to '{remote}': {e.stderr.strip()}", err=True)
            sys.exit(1)
    else:
        remotes = mgr.list_remotes()
        if not remotes:
            click.echo("No remotes configured. Use 'quidclaw backup add-remote' first.", err=True)
            sys.exit(1)
        for r in remotes:
            try:
                mgr._run_git("push", r["name"])
                click.echo(f"Pushed to '{r['name']}'.")
            except _sp.CalledProcessError as e:
                click.echo(f"Error pushing to '{r['name']}': {e.stderr.strip()}", err=True)
```

Note: `subprocess` is imported locally in `backup_remove_remote` and `backup_push` (as `_sp`). No top-level import needed — this follows the lazy import pattern used throughout `cli.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py::TestBackup -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/cli.py tests/test_cli.py
git commit -m "feat(backup): add backup CLI command group (init, status, add-remote, remove-remote, push)"
```

---

### Task 8: CLI — Integrate try_backup into Write Commands

**Files:**
- Modify: `src/quidclaw/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test for auto-backup on write operations**

Append to `tests/test_cli.py` inside `TestBackup`:

```python
    def test_add_txn_triggers_backup(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        # Init backup
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        # Add transaction
        posting1 = json.dumps({"account": "Expenses:Food", "amount": "50", "currency": "CNY"})
        posting2 = json.dumps({"account": "Assets:Bank:Checking", "amount": "-50", "currency": "CNY"})
        runner.invoke(
            main, [
                "add-txn", "--date", "2026-03-15", "--payee", "TestStore",
                "--posting", posting1, "--posting", posting2,
            ],
            catch_exceptions=False, env=env,
        )
        # Verify git log has the backup commit
        import subprocess
        log = subprocess.run(
            ["git", "log", "--oneline"], cwd=tmp_path,
            capture_output=True, text=True,
        )
        assert "TestStore" in log.stdout

    def test_add_account_triggers_backup(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        runner.invoke(
            main, ["add-account", "Assets:Bank:Test:9999", "--currencies", "CNY"],
            catch_exceptions=False, env=env,
        )
        import subprocess
        log = subprocess.run(
            ["git", "log", "--oneline"], cwd=tmp_path,
            capture_output=True, text=True,
        )
        assert "Assets:Bank:Test:9999" in log.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::TestBackup::test_add_txn_triggers_backup tests/test_cli.py::TestBackup::test_add_account_triggers_backup -v`
Expected: FAIL — commit log won't contain the expected messages

- [ ] **Step 3: Add _try_backup wrapper and calls to all write commands in cli.py**

Add a thin wrapper function in `cli.py` (after `get_ledger()`, before `@click.group()`). This uses lazy import to follow the existing pattern in `cli.py` — no top-level import of `backup.py`:

```python
def _try_backup(config: QuidClawConfig, message: str) -> None:
    """Attempt git backup if initialized. Never raises."""
    try:
        from quidclaw.core.backup import try_backup
        try_backup(config, message)
    except Exception:
        pass
```

Then add `_try_backup(config, message)` at the end of each write command. Here are the exact insertions:

**`init` command** — after `click.echo(f"Initialized QuidClaw project in {config.data_dir}")`:
```python
    _try_backup(config, "Initialize QuidClaw data directory")
```

**`setup` command** — after `click.echo(f"Created {len(created)} default accounts ({operating})")`:
```python
    if created:
        _try_backup(ledger.config, f"Set up default accounts ({operating})")
```

**`set_config` command** — after `click.echo(f"Set {key} = {value}")`:
```python
    _try_backup(config, f"Update config: {key}")
```

**`add_account` command** — after `click.echo(f"Opened account {name}")`:
```python
    _try_backup(ledger.config, f"Add account: {name}")
```

**`close_account` command** — after `click.echo(f"Closed account {name}")`:
```python
    _try_backup(ledger.config, f"Close account: {name}")
```

**`add_txn` command** — after `click.echo(f"Recorded transaction: {date} {payee}")`:
```python
    _try_backup(ledger.config, f"Add transaction: {payee}")
```

**`balance_check` command** — after `click.echo(message)` and before `if not ok:`:
```python
    if ok:
        _try_backup(ledger.config, f"Balance assertion: {account}")
```

**`add_commodity` command** — after `click.echo(f"Registered commodity {name} ({quote}:{source})")`:
```python
    _try_backup(ledger.config, f"Add commodity: {name}")
```

**`fetch_prices` command** — after the final else block:
```python
    _try_backup(ledger.config, "Fetch prices")
```

**`add_source` command** — after `click.echo(f"  Inbox: {inbox}")` (at the end of the function):
```python
    _try_backup(config, f"Add data source: {name}")
```

**`remove_source` command** — at the end of the function:
```python
    _try_backup(config, f"Remove data source: {name}")
```

**`sync` command** — before the `has_errors` line (after all sync results):
```python
    total = sum(r.items_fetched for r in all_results)
    if total > 0:
        sources_str = ", ".join(r.source_name for r in all_results if r.items_fetched > 0)
        _try_backup(config, f"Sync: {total} new items from {sources_str}")
```

**`mark_processed` command** — after `click.echo(f"Marked {email_dir} as processed")`:
```python
    _try_backup(config, f"Mark processed: {source_name}/{email_dir}")
```

**`upgrade` command** — after `click.echo("Upgrade complete.")`:
```python
    _try_backup(config, "Upgrade QuidClaw workflows")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py -v`
Expected: All PASS (existing tests should still pass since try_backup is a no-op when git isn't initialized)

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/cli.py tests/test_cli.py
git commit -m "feat(backup): integrate auto-backup into all write CLI commands"
```

---

### Task 9: Update Onboarding Workflow

**Files:**
- Modify: `src/quidclaw/workflows/onboarding.md`

- [ ] **Step 1: Read current onboarding workflow**

Run: `cat src/quidclaw/workflows/onboarding.md` (to verify current content before editing)

- [ ] **Step 2: Add Git Backup Setup phase to onboarding.md**

Append the following section at the end of `src/quidclaw/workflows/onboarding.md` (before any closing remarks, after the email setup phase):

```markdown
## Phase: Git Backup Setup

After the main onboarding is complete, help the user set up automatic backup.

### Step 1: Check Git Availability

Run `quidclaw backup status --json` via Bash.

If git is not available:
- Inform user: "Git is not installed. Installing Git enables automatic backup of your financial data."
- Provide platform-specific install instructions
- If user declines, skip this phase entirely

### Step 2: Initialize Git Backup

If git is available but backup not initialized:
- Ask: "Would you like to enable automatic backup for your data? Every change will be versioned locally."
- If yes: Run `quidclaw backup init` via Bash

### Step 3: Remote Backup (Optional)

Ask if user wants remote backup:
- "You can back up to a private repository on any Git hosting service:"
  - **GitHub** (github.com) — most popular, free private repos
  - **Gitee** (gitee.com) — popular in China, free private repos
  - **GitLab** (gitlab.com) — free private repos
  - **Self-hosted** — Gitea, etc.
- "This keeps your data safe even if your computer is lost or damaged."
- "You can set up multiple remotes for redundant backup."

If user wants remote backup:
1. Ask for the remote name (e.g., "github", "gitee") and repository URL
2. Run `quidclaw backup add-remote NAME URL` via Bash
3. **IMPORTANT:** Remind user:
   - "Make sure the repository is set to **Private** — this is your financial data!"
   - Provide platform-specific instructions for creating a private repo and setting up authentication (SSH key or HTTPS token)
4. Ask: "Would you like to add another remote for redundant backup?" (repeat if yes)
5. Once all remotes are set, try `quidclaw backup push` to verify connectivity

### Step 4: LFS (if applicable)

If git-lfs is not installed but backup is enabled:
- Suggest: "Installing git-lfs would improve storage efficiency for PDF and image files."
- Provide install command: `brew install git-lfs` (macOS) or `apt install git-lfs` (Linux)
- This is optional — backup works without LFS, just less efficiently for binary files.
```

- [ ] **Step 3: Commit**

```bash
git add src/quidclaw/workflows/onboarding.md
git commit -m "feat(backup): add Git backup setup phase to onboarding workflow"
```

---

### Task 10: Update Instruction Files and Documentation

**Files:**
- Modify: `src/quidclaw/cli.py` (instruction body)
- Modify: `docs/cli-reference.md`
- Modify: `docs/architecture.md`

- [ ] **Step 1: Update `_build_instruction_body` in cli.py**

In the CLI commands section of the instruction body string (around line 660), add the backup commands:

```
# Backup
quidclaw backup init                    # Initialize Git backup
quidclaw backup status                  # Show backup status
quidclaw backup add-remote NAME URL     # Add remote for backup
quidclaw backup remove-remote NAME      # Remove a remote
quidclaw backup push [--remote NAME]    # Push to remotes
```

- [ ] **Step 2: Update docs/cli-reference.md**

Add a "Backup" section to `docs/cli-reference.md` documenting the 5 new commands.

- [ ] **Step 3: Update docs/architecture.md**

Add a backup module description to `docs/architecture.md` in the module listing section:

```markdown
### `core/backup.py` — Git Backup Manager

Manages Git-based versioning and multi-remote backup of the data directory. Wraps `git` CLI via subprocess. Supports:
- Auto-commit after write operations
- Async push to multiple remotes (fire-and-forget)
- Git LFS for binary files (PDFs, images)
- Status reporting

Backup never blocks normal operations — all failures are silently swallowed.
```

- [ ] **Step 4: Run all tests to verify nothing is broken**

Run: `pytest -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/cli.py docs/cli-reference.md docs/architecture.md
git commit -m "docs: add backup commands to instruction files, CLI reference, and architecture"
```

---

### Task 11: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 2: Manual smoke test**

```bash
cd /tmp && mkdir test-backup && cd test-backup
QUIDCLAW_DATA_DIR=/tmp/test-backup quidclaw init
QUIDCLAW_DATA_DIR=/tmp/test-backup quidclaw backup init
QUIDCLAW_DATA_DIR=/tmp/test-backup quidclaw backup status
QUIDCLAW_DATA_DIR=/tmp/test-backup quidclaw backup add-remote test https://example.com/repo.git
QUIDCLAW_DATA_DIR=/tmp/test-backup quidclaw backup status --json
QUIDCLAW_DATA_DIR=/tmp/test-backup quidclaw set-config operating_currency CNY
QUIDCLAW_DATA_DIR=/tmp/test-backup quidclaw setup
# Verify git log shows all operations
cd /tmp/test-backup && git log --oneline
# Clean up
rm -rf /tmp/test-backup
```

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix(backup): address issues found in smoke test"
```
