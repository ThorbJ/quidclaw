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
        (tmp_path / "notes").mkdir(exist_ok=True)
        (tmp_path / "notes" / "test.md").write_text("note")
        mgr.auto_commit("Add note")
        (tmp_path / "notes" / "test.md").write_text("updated note")
        result = mgr.auto_commit("Update note")
        assert result is True

    def test_auto_commit_respects_gitignore(self, tmp_path):
        mgr = self._init_repo(tmp_path)
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
        mgr.auto_push()  # Should not raise

    def test_auto_push_with_remote_fires_subprocess(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        mgr.add_remote("origin", "https://example.com/repo.git")
        with patch.object(mgr, "_push_async") as mock_push:
            mgr.auto_push()
            mock_push.assert_called_once_with("origin")

    def test_auto_push_multiple_remotes(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        mgr.add_remote("github", "https://github.com/u/r.git")
        mgr.add_remote("gitee", "https://gitee.com/u/r.git")
        with patch.object(mgr, "_push_async") as mock_push:
            mgr.auto_push()
            assert mock_push.call_count == 2
            pushed = {call[0][0] for call in mock_push.call_args_list}
            assert pushed == {"github", "gitee"}

    def test_commit_and_push(self, tmp_path):
        mgr = self._init_repo(tmp_path)
        (tmp_path / "ledger").mkdir(exist_ok=True)
        (tmp_path / "ledger" / "test.bean").write_text("data")
        mgr.add_remote("origin", "https://example.com/repo.git")
        with patch.object(mgr, "_push_async"):
            result = mgr.commit_and_push("Test commit")
            assert result is True
