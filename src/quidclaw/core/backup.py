"""Git-based backup for QuidClaw data directories."""

import platform
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

    # --- Daily Operations ---

    def auto_commit(self, message: str) -> bool:
        if not self.is_initialized():
            return False
        self._run_git("add", "-A")
        result = self._run_git("diff", "--cached", "--quiet", check=False)
        if result.returncode == 0:
            return False  # No changes
        self._run_git("commit", "-m", message)
        return True

    def _push_async(self, remote_name: str) -> None:
        """Fire-and-forget push to a single remote."""
        subprocess.Popen(
            ["git", "push", remote_name],
            cwd=self.data_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def auto_push(self) -> None:
        if not self.is_initialized():
            return
        remotes = self.list_remotes()
        for remote in remotes:
            try:
                self._push_async(remote["name"])
            except OSError:
                pass

    def commit_and_push(self, message: str) -> bool:
        if self.auto_commit(message):
            self.auto_push()
            return True
        return False


def try_backup(config: QuidClawConfig, message: str) -> None:
    """Attempt git backup if initialized. Never raises."""
    try:
        mgr = BackupManager(config)
        if mgr.is_initialized():
            mgr.commit_and_push(message)
    except Exception:
        pass
