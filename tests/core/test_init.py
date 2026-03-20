import datetime
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.init import LedgerInitializer


def test_init_default_template(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    initializer = LedgerInitializer(ledger)
    initializer.init_with_template()
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    account_names = [e.account for e in entries if hasattr(e, "account")]
    assert any("Assets" in a for a in account_names)
    assert any("Expenses" in a for a in account_names)
    assert any("Income" in a for a in account_names)
    assert any("Liabilities" in a for a in account_names)
    assert any("Equity" in a for a in account_names)


def test_init_custom_accounts(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    initializer = LedgerInitializer(ledger)
    custom = [
        {"name": "Assets:Bank:BOC", "currencies": ["CNY"]},
        {"name": "Assets:Bank:ENBD", "currencies": ["AED", "USD"]},
        {"name": "Expenses:Food"},
        {"name": "Income:Salary"},
    ]
    initializer.init_with_template(accounts=custom)
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    account_names = [e.account for e in entries if hasattr(e, "account")]
    assert "Assets:Bank:BOC" in account_names
    assert "Assets:Bank:ENBD" in account_names


def test_init_idempotent(tmp_path):
    """Calling init twice should not duplicate accounts."""
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    initializer = LedgerInitializer(ledger)
    initializer.init_with_template()
    initializer.init_with_template()
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
