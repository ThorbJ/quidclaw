import os
from pathlib import Path
from quidclaw.config import QuidClawConfig


def test_default_data_dir_is_none():
    config = QuidClawConfig()
    assert config.data_dir is None
    assert config.is_configured is False


def test_custom_data_dir(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "mydata")
    assert config.data_dir == tmp_path / "mydata"
    assert config.is_configured is True


def test_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("QUIDCLAW_DATA_DIR", str(tmp_path / "envdata"))
    config = QuidClawConfig()
    assert config.data_dir == tmp_path / "envdata"


def test_ledger_dir(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.ledger_dir == tmp_path / "ledger"


def test_inbox_dir(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.inbox_dir == tmp_path / "inbox"


def test_documents_dir(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.documents_dir == tmp_path / "documents"


def test_notes_dir(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.notes_dir == tmp_path / "notes"


def test_reports_dir(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.reports_dir == tmp_path / "reports"


def test_main_bean_under_ledger(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.main_bean == tmp_path / "ledger" / "main.bean"


def test_accounts_bean_under_ledger(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.accounts_bean == tmp_path / "ledger" / "accounts.bean"


def test_prices_bean_under_ledger(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.prices_bean == tmp_path / "ledger" / "prices.bean"


def test_year_dir(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    path = config.year_dir(2026)
    assert path == tmp_path / "ledger" / "2026"


def test_month_bean(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    path = config.month_bean(2026, 3)
    assert path == tmp_path / "ledger" / "2026" / "2026-03.bean"
