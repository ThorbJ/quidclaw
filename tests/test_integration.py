"""End-to-end test: init -> add accounts -> add transactions -> query -> report."""
import datetime
from decimal import Decimal
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.init import LedgerInitializer
from quidclaw.core.accounts import AccountManager
from quidclaw.core.transactions import TransactionManager
from quidclaw.core.balance import BalanceManager
from quidclaw.core.reports import ReportManager


def test_full_workflow(tmp_path):
    # 1. Initialize ledger and add accounts with explicit early open dates
    config = QuidClawConfig(data_dir=tmp_path / "ledger")
    ledger = Ledger(config)
    ledger.init()
    acct = AccountManager(ledger)
    open_date = datetime.date(2020, 1, 1)
    acct.add_account("Assets:Bank:Chase", currencies=["USD"], open_date=open_date)
    acct.add_account("Assets:ApplePay", currencies=["USD"], open_date=open_date)
    acct.add_account("Income:Salary", open_date=open_date)
    acct.add_account("Expenses:Food", open_date=open_date)
    acct.add_account("Equity:Opening-Balances", open_date=open_date)

    # 2. Record transactions
    txn = TransactionManager(ledger)

    # Salary
    txn.add_transaction(
        date=datetime.date(2026, 1, 15),
        payee="Acme Corp",
        narration="January salary",
        postings=[
            {"account": "Assets:Bank:Chase", "amount": "5000.00", "currency": "USD"},
            {"account": "Income:Salary", "amount": "-5000.00", "currency": "USD"},
        ],
    )

    # Lunch via Apple Pay
    txn.add_transaction(
        date=datetime.date(2026, 1, 16),
        payee="Chipotle",
        narration="Lunch",
        postings=[
            {"account": "Expenses:Food", "amount": "12.50", "currency": "USD"},
            {"account": "Assets:ApplePay"},
        ],
    )

    # 3. Check balances
    bal = BalanceManager(ledger)
    chase_balance = bal.get_balance("Assets:Bank:Chase")
    assert chase_balance["USD"] == Decimal("5000.00")

    applepay_balance = bal.get_balance("Assets:ApplePay")
    assert applepay_balance["USD"] == Decimal("-12.50")

    food_balance = bal.get_balance("Expenses:Food")
    assert food_balance["USD"] == Decimal("12.50")

    # 4. Reconciliation check
    ok, msg = bal.balance_check("Assets:Bank:Chase", Decimal("5000.00"), "USD")
    assert ok is True

    # 5. Reports
    reports = ReportManager(ledger)
    bs = reports.balance_sheet()
    assert "Assets:Bank:Chase" in bs

    income = reports.income_statement()
    assert "Expenses:Food" in income

    # 6. BQL query
    cols, rows = reports.query("SELECT DISTINCT payee, narration, date WHERE payee = 'Chipotle'")
    assert len(rows) == 1

    # 7. No errors in ledger
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
