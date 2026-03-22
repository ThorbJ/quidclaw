"""E2E test configuration and fixtures."""

import shutil
from pathlib import Path

import pytest

from click.testing import CliRunner
from quidclaw.cli import main
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def data_dir(tmp_path):
    """Create a fresh QuidClaw data directory via CLI (includes CLAUDE.md + workflows)."""
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--platform", "claude-code"], env={"QUIDCLAW_DATA_DIR": str(tmp_path)})
    assert result.exit_code == 0
    return tmp_path


@pytest.fixture
def data_dir_with_accounts(data_dir):
    """Data directory with default accounts already created (via quidclaw init)."""
    # quidclaw init already creates default accounts, so data_dir is sufficient.
    # Verify accounts exist.
    from quidclaw.core.ledger import Ledger
    config = QuidClawConfig(data_dir=data_dir)
    ledger = Ledger(config)
    entries, errors, options = ledger.load()
    from beancount.core import data as bdata
    accounts = {e.account for e in entries if isinstance(e, bdata.Open)}
    assert len(accounts) > 0, "data_dir_with_accounts should have accounts"
    return data_dir


def copy_fixture_to_inbox(data_dir: Path, fixture_relative_path: str, rename: str = None):
    """Copy a fixture file into the data_dir's inbox."""
    src = FIXTURES_DIR / fixture_relative_path
    dest_name = rename or src.name
    dest = data_dir / "inbox" / dest_name
    shutil.copy2(str(src), str(dest))
    return dest
