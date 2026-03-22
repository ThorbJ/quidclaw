import yaml
from quidclaw.config import QuidClawConfig


def test_sources_dir_property(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.sources_dir == tmp_path / "sources"


def test_logs_dir_property(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.logs_dir == tmp_path / "logs"


def test_source_dir(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.source_dir("my-email") == tmp_path / "sources" / "my-email"


def test_source_state_file(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.source_state_file("my-email") == tmp_path / "sources" / "my-email" / ".state.yaml"


def test_get_sources_empty(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.config_dir.mkdir(parents=True)
    assert config.get_sources() == {}


def test_add_and_get_source(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.config_dir.mkdir(parents=True)
    config.add_source("my-email", {"provider": "agentmail", "api_key": "test123"})
    source = config.get_source("my-email")
    assert source["provider"] == "agentmail"
    assert source["api_key"] == "test123"


def test_add_source_preserves_existing(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.config_dir.mkdir(parents=True)
    config.set_setting("operating_currency", "CNY")
    config.add_source("s1", {"provider": "agentmail"})
    config.add_source("s2", {"provider": "other"})
    assert config.get_setting("operating_currency") == "CNY"
    assert len(config.get_sources()) == 2


def test_remove_source(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.config_dir.mkdir(parents=True)
    config.add_source("my-email", {"provider": "agentmail"})
    config.remove_source("my-email")
    assert config.get_source("my-email") is None


def test_remove_source_not_found(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.config_dir.mkdir(parents=True)
    import pytest
    with pytest.raises(KeyError, match="Source not found"):
        config.remove_source("nonexistent")


class TestBackupConfig:
    def test_backup_defaults_not_set(self, tmp_path):
        from quidclaw.config import QuidClawConfig
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        assert config.get_backup_setting("enabled") is None

    def test_set_and_get_backup_setting(self, tmp_path):
        from quidclaw.config import QuidClawConfig
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        config.set_backup_setting("enabled", True)
        assert config.get_backup_setting("enabled") is True

    def test_backup_settings_nested_under_backup_key(self, tmp_path):
        from quidclaw.config import QuidClawConfig
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        config.set_backup_setting("enabled", True)
        config.set_backup_setting("auto_push", True)
        settings = config.load_settings()
        assert settings["backup"]["enabled"] is True
        assert settings["backup"]["auto_push"] is True

    def test_backup_setting_does_not_clobber_other_settings(self, tmp_path):
        from quidclaw.config import QuidClawConfig
        config = QuidClawConfig(data_dir=tmp_path)
        config.config_dir.mkdir(parents=True, exist_ok=True)
        config.set_setting("operating_currency", "CNY")
        config.set_backup_setting("enabled", True)
        assert config.get_setting("operating_currency") == "CNY"


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
