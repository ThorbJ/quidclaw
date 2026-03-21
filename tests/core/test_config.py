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
