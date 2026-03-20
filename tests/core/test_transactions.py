import datetime
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.accounts import AccountManager
from quidclaw.core.transactions import TransactionManager


def make_ledger_with_accounts(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    mgr = AccountManager(ledger)
    mgr.add_account("Assets:Bank:BOC", currencies=["CNY"], open_date=datetime.date(2026, 1, 1))
    mgr.add_account("Expenses:Food", open_date=datetime.date(2026, 1, 1))
    mgr.add_account("Liabilities:CreditCard:CMB", currencies=["CNY"], open_date=datetime.date(2026, 1, 1))
    return ledger


def test_add_transaction(tmp_path):
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="McDonald's",
        narration="Lunch",
        postings=[
            {"account": "Expenses:Food", "amount": "45.00", "currency": "CNY"},
            {"account": "Assets:Bank:BOC", "amount": "-45.00", "currency": "CNY"},
        ],
    )
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    txns = [e for e in entries if e.__class__.__name__ == "Transaction"]
    assert len(txns) == 1


def test_add_transaction_auto_balance(tmp_path):
    """When one posting omits amount, beancount auto-balances."""
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="McDonald's",
        narration="Lunch",
        postings=[
            {"account": "Expenses:Food", "amount": "45.00", "currency": "CNY"},
            {"account": "Assets:Bank:BOC"},
        ],
    )
    entries, errors, _ = ledger.load()
    assert len(errors) == 0


def test_add_transaction_creates_month_file(tmp_path):
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="Test",
        narration="Test",
        postings=[
            {"account": "Expenses:Food", "amount": "10.00", "currency": "CNY"},
            {"account": "Assets:Bank:BOC"},
        ],
    )
    month_file = ledger.config.month_bean(2026, 3)
    assert month_file.exists()
    assert "Expenses:Food" in month_file.read_text()


def test_add_transaction_with_credit_card(tmp_path):
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="Starbucks",
        narration="Coffee",
        postings=[
            {"account": "Expenses:Food", "amount": "38.00", "currency": "CNY"},
            {"account": "Liabilities:CreditCard:CMB", "amount": "-38.00", "currency": "CNY"},
        ],
    )
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
