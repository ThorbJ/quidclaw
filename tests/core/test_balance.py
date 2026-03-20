import datetime
from decimal import Decimal
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.accounts import AccountManager
from quidclaw.core.transactions import TransactionManager
from quidclaw.core.balance import BalanceManager


def make_ledger_with_txns(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    acct = AccountManager(ledger)
    acct.add_account("Assets:Bank:BOC", currencies=["CNY"], open_date=datetime.date(2026, 1, 1))
    acct.add_account("Expenses:Food", open_date=datetime.date(2026, 1, 1))
    acct.add_account("Income:Salary", open_date=datetime.date(2026, 1, 1))
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 1, 15),
        payee="Company",
        narration="Salary",
        postings=[
            {"account": "Assets:Bank:BOC", "amount": "10000.00", "currency": "CNY"},
            {"account": "Income:Salary", "amount": "-10000.00", "currency": "CNY"},
        ],
    )
    txn.add_transaction(
        date=datetime.date(2026, 1, 20),
        payee="Restaurant",
        narration="Dinner",
        postings=[
            {"account": "Expenses:Food", "amount": "200.00", "currency": "CNY"},
            {"account": "Assets:Bank:BOC", "amount": "-200.00", "currency": "CNY"},
        ],
    )
    return ledger


def test_get_balance_single_account(tmp_path):
    ledger = make_ledger_with_txns(tmp_path)
    bal = BalanceManager(ledger)
    result = bal.get_balance("Assets:Bank:BOC")
    assert "CNY" in result
    assert result["CNY"] == Decimal("9800.00")


def test_get_balance_all_accounts(tmp_path):
    ledger = make_ledger_with_txns(tmp_path)
    bal = BalanceManager(ledger)
    result = bal.get_all_balances()
    assert "Assets:Bank:BOC" in result
    assert "Expenses:Food" in result
    assert result["Expenses:Food"]["CNY"] == Decimal("200.00")


def test_balance_check_pass(tmp_path):
    ledger = make_ledger_with_txns(tmp_path)
    bal = BalanceManager(ledger)
    ok, msg = bal.balance_check("Assets:Bank:BOC", Decimal("9800.00"), "CNY")
    assert ok is True


def test_balance_check_fail(tmp_path):
    ledger = make_ledger_with_txns(tmp_path)
    bal = BalanceManager(ledger)
    ok, msg = bal.balance_check("Assets:Bank:BOC", Decimal("9999.00"), "CNY")
    assert ok is False
    assert "9800" in msg


def test_add_balance_assertion(tmp_path):
    ledger = make_ledger_with_txns(tmp_path)
    bal = BalanceManager(ledger)
    bal.add_balance_assertion("Assets:Bank:BOC", Decimal("9800.00"), "CNY", datetime.date(2026, 1, 21))
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    balance_entries = [e for e in entries if e.__class__.__name__ == "Balance"]
    assert len(balance_entries) == 1
