"""Tests for OpenClaw agent setup."""

from unittest.mock import patch

from quidclaw.config import QuidClawConfig
from quidclaw.core.openclaw import OpenClawSetup


class TestOpenClawDetection:
    def test_is_available_true(self):
        setup = OpenClawSetup.__new__(OpenClawSetup)
        with patch("quidclaw.core.openclaw.shutil.which", return_value="/usr/local/bin/openclaw"):
            assert setup.is_available() is True

    def test_is_available_false(self):
        setup = OpenClawSetup.__new__(OpenClawSetup)
        with patch("quidclaw.core.openclaw.shutil.which", return_value=None):
            assert setup.is_available() is False


class TestGenerateTemplates:
    def test_generates_soul_md(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        setup = OpenClawSetup(config)
        setup.generate_templates()
        assert (tmp_path / "SOUL.md").exists()
        assert "personal CFO" in (tmp_path / "SOUL.md").read_text()

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


class TestGenerateAgentsMd:
    def test_generates_agents_md(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        setup = OpenClawSetup(config)
        setup.generate_agents_md("# Entry\n")
        assert (tmp_path / "AGENTS.md").exists()
        content = (tmp_path / "AGENTS.md").read_text()
        assert content.startswith("# Entry")
        assert "Automation" in content
        assert "HEARTBEAT" in content

    def test_agents_md_contains_automation_section(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        setup = OpenClawSetup(config)
        setup.generate_agents_md("# Entry\n")
        content = (tmp_path / "AGENTS.md").read_text()
        assert "Pending Items" in content
        assert "/quidclaw-daily" in content
        assert "/quidclaw-review" in content

    def test_agents_md_without_entry_content(self, tmp_path):
        config = QuidClawConfig(data_dir=tmp_path)
        setup = OpenClawSetup(config)
        setup.generate_agents_md()
        content = (tmp_path / "AGENTS.md").read_text()
        assert "Automation" in content
