"""Tests for Git backup manager."""

import subprocess
from unittest.mock import patch

from quidclaw.config import QuidClawConfig
from quidclaw.core.backup import BackupManager


class TestGitDetection:
    def test_is_git_available_true(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        assert mgr.is_git_available() is True

    def test_is_git_available_false(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        mgr = BackupManager(config)
        with patch("quidclaw.core.backup.shutil.which", return_value=None):
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
