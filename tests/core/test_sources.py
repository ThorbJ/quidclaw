import pytest
from quidclaw.config import QuidClawConfig
from quidclaw.core.sources.base import DataSource, SyncResult
from quidclaw.core.sources.registry import (
    PROVIDERS,
    register_provider,
    get_provider,
    create_source,
)


class FakeSource(DataSource):
    @staticmethod
    def provider_name() -> str:
        return "fake"

    def sync(self) -> SyncResult:
        return SyncResult(
            source_name=self.source_name,
            provider="fake",
            items_fetched=0,
            items_stored=[],
            last_sync=None,
            errors=[],
        )

    def status(self) -> dict:
        return {"last_sync": None, "total_synced": 0}


def test_datasource_abc_enforces_methods():
    with pytest.raises(TypeError):
        DataSource(source_name="x", source_config={}, config=None)


def test_register_and_get_provider():
    register_provider(FakeSource)
    assert get_provider("fake") is FakeSource
    del PROVIDERS["fake"]


def test_get_provider_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("nonexistent")


def test_create_source_factory(tmp_path):
    register_provider(FakeSource)
    config = QuidClawConfig(data_dir=tmp_path)
    source = create_source("test", {"provider": "fake"}, config)
    assert isinstance(source, FakeSource)
    assert source.source_name == "test"
    assert source.config is config
    del PROVIDERS["fake"]


def test_provision_default_returns_config_unchanged(tmp_path):
    register_provider(FakeSource)
    config = QuidClawConfig(data_dir=tmp_path)
    source_config = {"provider": "fake", "key": "value"}
    source = FakeSource("test", source_config, config)
    result = source.provision()
    assert result is source_config
    del PROVIDERS["fake"]


def test_sync_result_dataclass():
    from datetime import datetime
    result = SyncResult(
        source_name="test",
        provider="fake",
        items_fetched=3,
        items_stored=["a", "b", "c"],
        last_sync=datetime(2026, 3, 21),
        errors=[],
    )
    assert result.items_fetched == 3
    assert len(result.items_stored) == 3


def test_resolve_env_refs(monkeypatch):
    from quidclaw.core.sources.registry import resolve_env_refs
    monkeypatch.setenv("MY_KEY", "secret123")
    result = resolve_env_refs({"api_key": "env:MY_KEY", "provider": "test"})
    assert result["api_key"] == "secret123"
    assert result["provider"] == "test"


def test_resolve_env_refs_missing_var(monkeypatch):
    from quidclaw.core.sources.registry import resolve_env_refs
    monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
    result = resolve_env_refs({"api_key": "env:NONEXISTENT_VAR"})
    assert result["api_key"] == ""
