from pathlib import Path
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger


def test_init_creates_directory_structure(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    assert config.main_bean.exists()
    assert config.accounts_bean.exists()
    assert config.prices_bean.exists()


def test_init_main_bean_includes_other_files(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    content = config.main_bean.read_text()
    assert 'include "accounts.bean"' in content
    assert 'include "prices.bean"' in content


def test_load_empty_ledger(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    entries, errors, options = ledger.load()
    assert isinstance(entries, list)
    assert isinstance(errors, list)


def test_append_text_to_file(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    ledger.append(config.accounts_bean, '2026-01-01 open Assets:Bank:Checking CNY\n')
    content = config.accounts_bean.read_text()
    assert "Assets:Bank:Checking" in content


def test_init_creates_all_directories(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    assert (tmp_path / "ledger").is_dir()
    assert (tmp_path / "inbox").is_dir()
    assert (tmp_path / "documents").is_dir()
    assert (tmp_path / "notes").is_dir()
    assert (tmp_path / "reports").is_dir()
    assert (tmp_path / "sources").is_dir()
    assert (tmp_path / "logs").is_dir()


def test_init_creates_sources_and_logs_directories(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    assert (tmp_path / "sources").is_dir()
    assert (tmp_path / "logs").is_dir()


def test_ensure_dirs_creates_missing_directories(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    import shutil
    shutil.rmtree(tmp_path / "sources")
    shutil.rmtree(tmp_path / "logs")
    assert not (tmp_path / "sources").exists()
    ledger.ensure_dirs()
    assert (tmp_path / "sources").is_dir()
    assert (tmp_path / "logs").is_dir()


def test_load_after_append(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    ledger.append(config.accounts_bean, '2026-01-01 open Assets:Bank:Checking CNY\n')
    entries, errors, options = ledger.load()
    assert len(errors) == 0
    assert len(entries) >= 1
