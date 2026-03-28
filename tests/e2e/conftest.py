"""E2E test configuration and fixtures.

E2E tests call the real claude CLI and make API calls. They are slow and
expensive, so they are gated behind the 'e2e' marker.

Run with: pytest -m e2e
"""

import shutil
from pathlib import Path

import pytest

from click.testing import CliRunner
from quidclaw.cli import main
from quidclaw.config import QuidClawConfig


# Give e2e tests generous timeout — each test may invoke claude multiple times,
# and each call can take up to 5 minutes. This overrides any global
# --timeout flag passed to pytest, preventing pytest-timeout from killing
# e2e tests prematurely while subprocess.run is still waiting for claude.
pytestmark = pytest.mark.timeout(900)  # 15 minutes per test

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Minimal set of accounts needed for E2E tests (import, query, reconcile, etc.)
DEFAULT_TEST_ACCOUNTS = [
    ("Assets:Bank:CMB:1234", "CNY"),
    ("Assets:Cash", "CNY"),
    ("Liabilities:CreditCard:CMB", "CNY"),
    ("Income:Salary", None),
    ("Expenses:Food", None),
    ("Expenses:Transport", None),
    ("Expenses:Shopping", None),
    ("Expenses:Entertainment", None),
    ("Expenses:Utilities", None),
    ("Expenses:Other", None),
    ("Equity:Opening-Balances", None),
]


@pytest.fixture
def data_dir(tmp_path):
    """Create a fresh QuidClaw data directory via CLI (includes skills + entry file)."""
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--platform", "claude-code"], env={"QUIDCLAW_DATA_DIR": str(tmp_path)})
    assert result.exit_code == 0
    return tmp_path


@pytest.fixture
def data_dir_with_accounts(data_dir):
    """Data directory with test accounts created via add-account CLI command."""
    runner = CliRunner()
    env = {"QUIDCLAW_DATA_DIR": str(data_dir)}
    for name, currencies in DEFAULT_TEST_ACCOUNTS:
        args = ["add-account", name]
        if currencies:
            args += ["--currencies", currencies]
        result = runner.invoke(main, args, env=env)
        assert result.exit_code == 0, f"Failed to create account {name}: {result.output}"
    return data_dir


def copy_fixture_to_inbox(data_dir: Path, fixture_relative_path: str, rename: str = None):
    """Copy a fixture file into the data_dir's inbox."""
    src = FIXTURES_DIR / fixture_relative_path
    dest_name = rename or src.name
    dest = data_dir / "inbox" / dest_name
    shutil.copy2(str(src), str(dest))
    return dest
