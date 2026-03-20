import shutil
from pathlib import Path
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.inbox import InboxManager


def _setup(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    return config, ledger


def test_list_inbox_empty(tmp_path):
    config, ledger = _setup(tmp_path)
    mgr = InboxManager(config)
    assert mgr.list_files() == []


def test_list_inbox_with_files(tmp_path):
    config, ledger = _setup(tmp_path)
    (config.inbox_dir / "statement.pdf").write_bytes(b"fake pdf")
    (config.inbox_dir / "receipt.jpg").write_bytes(b"fake jpg")
    mgr = InboxManager(config)
    files = mgr.list_files()
    assert len(files) == 2
    names = {f["name"] for f in files}
    assert names == {"statement.pdf", "receipt.jpg"}


def test_list_inbox_file_metadata(tmp_path):
    config, ledger = _setup(tmp_path)
    (config.inbox_dir / "test.csv").write_text("a,b,c")
    mgr = InboxManager(config)
    files = mgr.list_files()
    assert len(files) == 1
    f = files[0]
    assert f["name"] == "test.csv"
    assert f["size"] > 0
    assert "modified" in f


def test_move_to_documents(tmp_path):
    config, ledger = _setup(tmp_path)
    (config.inbox_dir / "bank.pdf").write_bytes(b"pdf content")
    mgr = InboxManager(config)
    dest = mgr.move_to_documents("bank.pdf", "招商银行-信用卡账单-2026-03.pdf", 2026, 3)
    assert not (config.inbox_dir / "bank.pdf").exists()
    assert dest.exists()
    assert dest.parent == config.documents_dir / "2026" / "03"


def test_move_to_documents_nonexistent_file(tmp_path):
    config, ledger = _setup(tmp_path)
    mgr = InboxManager(config)
    import pytest
    with pytest.raises(FileNotFoundError):
        mgr.move_to_documents("nope.pdf", "nope.pdf", 2026, 3)


def test_get_data_status(tmp_path):
    config, ledger = _setup(tmp_path)
    mgr = InboxManager(config)
    status = mgr.get_data_status()
    assert status["inbox_count"] == 0
    assert "last_modified" in status


def test_get_data_status_with_inbox_files(tmp_path):
    config, ledger = _setup(tmp_path)
    (config.inbox_dir / "file.pdf").write_bytes(b"data")
    mgr = InboxManager(config)
    status = mgr.get_data_status()
    assert status["inbox_count"] == 1
