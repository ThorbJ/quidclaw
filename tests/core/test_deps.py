"""Tests for dependency detection and install helpers."""

from unittest.mock import patch

from quidclaw.core.deps import check_dependency, get_install_command


class TestCheckDependency:
    def test_finds_existing_binary(self):
        assert check_dependency("git") is True

    def test_missing_binary(self):
        with patch("quidclaw.core.deps.shutil.which", return_value=None):
            assert check_dependency("nonexistent-binary-xyz") is False


class TestGetInstallCommand:
    def test_macos_uses_brew(self):
        with patch("quidclaw.core.deps.platform.system", return_value="Darwin"):
            cmd = get_install_command("git", brew="git", apt="git")
            assert "brew install git" in cmd

    def test_linux_uses_apt(self):
        with patch("quidclaw.core.deps.platform.system", return_value="Linux"):
            cmd = get_install_command("git", brew="git", apt="git")
            assert "apt" in cmd and "git" in cmd

    def test_unknown_os_gives_url(self):
        with patch("quidclaw.core.deps.platform.system", return_value="Windows"):
            cmd = get_install_command("git", brew="git", apt="git")
            assert "http" in cmd or "manual" in cmd.lower()
