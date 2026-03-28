import datetime
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.accounts import AccountManager


def make_ledger(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    return ledger


def test_add_account(tmp_path):
    ledger = make_ledger(tmp_path)
    mgr = AccountManager(ledger)
    mgr.add_account("Assets:Bank:BOC", currencies=["CNY"], open_date=datetime.date(2026, 1, 1))
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    account_names = [e.account for e in entries if hasattr(e, "account")]
    assert "Assets:Bank:BOC" in account_names


def test_add_account_default_date(tmp_path):
    ledger = make_ledger(tmp_path)
    mgr = AccountManager(ledger)
    mgr.add_account("Expenses:Food")
    entries, errors, _ = ledger.load()
    assert len(errors) == 0


def test_list_accounts(tmp_path):
    ledger = make_ledger(tmp_path)
    mgr = AccountManager(ledger)
    mgr.add_account("Assets:Bank:BOC", currencies=["CNY"])
    mgr.add_account("Expenses:Food")
    mgr.add_account("Liabilities:CreditCard:CMB", currencies=["CNY"])
    accounts = mgr.list_accounts()
    assert "Assets:Bank:BOC" in accounts
    assert "Expenses:Food" in accounts
    assert "Liabilities:CreditCard:CMB" in accounts


def test_list_accounts_by_type(tmp_path):
    ledger = make_ledger(tmp_path)
    mgr = AccountManager(ledger)
    mgr.add_account("Assets:Bank:BOC")
    mgr.add_account("Expenses:Food")
    assets = mgr.list_accounts(account_type="Assets")
    assert "Assets:Bank:BOC" in assets
    assert "Expenses:Food" not in assets


def test_add_account_with_metadata(tmp_path):
    ledger = make_ledger(tmp_path)
    mgr = AccountManager(ledger)
    mgr.add_account(
        "Assets:Bank:CMB:1234",
        currencies=["CNY"],
        open_date=datetime.date(2026, 1, 1),
        metadata={"institution": "China Merchants Bank", "account-number": "6225-xxxx-xxxx-1234"},
    )
    content = ledger.config.accounts_bean.read_text()
    assert 'institution: "China Merchants Bank"' in content
    assert 'account-number: "6225-xxxx-xxxx-1234"' in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0


def test_add_note(tmp_path):
    ledger = make_ledger(tmp_path)
    mgr = AccountManager(ledger)
    mgr.add_account("Assets:Bank:BOC", open_date=datetime.date(2026, 1, 1))
    mgr.add_note("Assets:Bank:BOC", "Called to confirm wire transfer", datetime.date(2026, 3, 15))
    month_file = ledger.config.month_bean(2026, 3)
    content = month_file.read_text()
    assert '2026-03-15 note Assets:Bank:BOC "Called to confirm wire transfer"' in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    note_entries = [e for e in entries if e.__class__.__name__ == "Note"]
    assert len(note_entries) == 1


def test_close_account(tmp_path):
    ledger = make_ledger(tmp_path)
    mgr = AccountManager(ledger)
    mgr.add_account("Assets:Bank:Old", open_date=datetime.date(2020, 1, 1))
    mgr.close_account("Assets:Bank:Old", close_date=datetime.date(2026, 3, 1))
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    close_entries = [e for e in entries if hasattr(e, "account") and e.__class__.__name__ == "Close"]
    assert len(close_entries) == 1
