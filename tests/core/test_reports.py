import datetime
from decimal import Decimal

from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.accounts import AccountManager
from quidclaw.core.init import LedgerInitializer
from quidclaw.core.transactions import TransactionManager
from quidclaw.core.reports import ReportManager


def make_ledger_with_data(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    acct = AccountManager(ledger)
    acct.add_account("Assets:Bank:BOC", currencies=["CNY"], open_date=datetime.date(2026, 1, 1))
    acct.add_account("Expenses:Food", open_date=datetime.date(2026, 1, 1))
    acct.add_account("Income:Salary", open_date=datetime.date(2026, 1, 1))
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 1, 15), payee="Company", narration="Salary",
        postings=[
            {"account": "Assets:Bank:BOC", "amount": "10000.00", "currency": "CNY"},
            {"account": "Income:Salary", "amount": "-10000.00", "currency": "CNY"},
        ],
    )
    txn.add_transaction(
        date=datetime.date(2026, 1, 20), payee="Restaurant", narration="Dinner",
        postings=[
            {"account": "Expenses:Food", "amount": "200.00", "currency": "CNY"},
            {"account": "Assets:Bank:BOC", "amount": "-200.00", "currency": "CNY"},
        ],
    )
    return ledger


def test_query_bql(tmp_path):
    ledger = make_ledger_with_data(tmp_path)
    reports = ReportManager(ledger)
    columns, rows = reports.query("SELECT account, sum(position) WHERE account ~ 'Expenses' GROUP BY account")
    assert len(rows) >= 1


def test_income_statement(tmp_path):
    ledger = make_ledger_with_data(tmp_path)
    reports = ReportManager(ledger)
    result = reports.income_statement()
    assert "Income" in result or "Expenses" in result


def test_balance_sheet(tmp_path):
    ledger = make_ledger_with_data(tmp_path)
    reports = ReportManager(ledger)
    result = reports.balance_sheet()
    assert "Assets" in result


# --- Shared setup helpers for new report methods ---


def _setup_with_transactions(tmp_path):
    """Create ledger with sample transactions for March 2026."""
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    LedgerInitializer(ledger).init_with_template()
    txn = TransactionManager(ledger)

    # Income
    txn.add_transaction(
        date=datetime.date(2026, 3, 1), payee="Company", narration="Salary",
        postings=[
            {"account": "Assets:Bank:Checking", "amount": "15000", "currency": "CNY"},
            {"account": "Income:Salary"},
        ],
    )
    # Expenses
    txn.add_transaction(
        date=datetime.date(2026, 3, 15), payee="Starbucks", narration="Coffee",
        postings=[
            {"account": "Expenses:Food", "amount": "35.80", "currency": "CNY"},
            {"account": "Assets:Bank:Checking"},
        ],
    )
    txn.add_transaction(
        date=datetime.date(2026, 3, 17), payee="JD.com", narration="Electronics",
        postings=[
            {"account": "Expenses:Shopping", "amount": "299", "currency": "CNY"},
            {"account": "Assets:Bank:Checking"},
        ],
    )
    return ledger


def _setup_two_months(tmp_path):
    """Create ledger with Feb + Mar data for comparison."""
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    LedgerInitializer(ledger).init_with_template()
    txn = TransactionManager(ledger)

    # February: Food 200, Shopping 100
    txn.add_transaction(
        date=datetime.date(2026, 2, 10), payee="Restaurant", narration="Dinner",
        postings=[
            {"account": "Expenses:Food", "amount": "200", "currency": "CNY"},
            {"account": "Assets:Bank:Checking"},
        ],
    )
    txn.add_transaction(
        date=datetime.date(2026, 2, 20), payee="Mall", narration="Clothes",
        postings=[
            {"account": "Expenses:Shopping", "amount": "100", "currency": "CNY"},
            {"account": "Assets:Bank:Checking"},
        ],
    )
    # March: Food 300 (+50%), Shopping 50 (-50%)
    txn.add_transaction(
        date=datetime.date(2026, 3, 10), payee="Restaurant", narration="Dinner",
        postings=[
            {"account": "Expenses:Food", "amount": "300", "currency": "CNY"},
            {"account": "Assets:Bank:Checking"},
        ],
    )
    txn.add_transaction(
        date=datetime.date(2026, 3, 20), payee="Mall", narration="Clothes",
        postings=[
            {"account": "Expenses:Shopping", "amount": "50", "currency": "CNY"},
            {"account": "Assets:Bank:Checking"},
        ],
    )
    return ledger


# --- Task 1: monthly_summary ---


def test_monthly_summary(tmp_path):
    ledger = _setup_with_transactions(tmp_path)
    mgr = ReportManager(ledger)
    result = mgr.monthly_summary(2026, 3)

    assert "CNY" in result["income"]
    assert result["income"]["CNY"] == Decimal("15000")
    assert "CNY" in result["expenses"]
    assert result["expenses"]["CNY"] == Decimal("334.80")
    assert result["savings"]["CNY"] == Decimal("14665.20")


def test_monthly_summary_empty_month(tmp_path):
    ledger = _setup_with_transactions(tmp_path)
    mgr = ReportManager(ledger)
    result = mgr.monthly_summary(2026, 1)  # No data for January

    assert result["income"] == {}
    assert result["expenses"] == {}
    assert result["savings"] == {}


# --- Task 2: spending_by_category ---


def test_spending_by_category(tmp_path):
    ledger = _setup_with_transactions(tmp_path)
    mgr = ReportManager(ledger)
    result = mgr.spending_by_category(2026, 3)

    assert len(result) >= 2
    # Should be sorted by amount descending
    assert result[0]["amount"] >= result[1]["amount"]
    # Check categories exist
    categories = {r["category"] for r in result}
    assert "Food" in categories or "Expenses:Food" in categories
    assert "Shopping" in categories or "Expenses:Shopping" in categories


def test_spending_by_category_empty(tmp_path):
    ledger = _setup_with_transactions(tmp_path)
    mgr = ReportManager(ledger)
    result = mgr.spending_by_category(2026, 1)
    assert result == []


# --- Task 3: month_over_month ---


def test_month_over_month(tmp_path):
    ledger = _setup_two_months(tmp_path)
    mgr = ReportManager(ledger)
    result = mgr.month_over_month(2026, 3)

    food = next(r for r in result if r["category"] == "Food")
    assert food["current"] == Decimal("300")
    assert food["previous"] == Decimal("200")
    assert food["change_pct"] == 50.0

    shopping = next(r for r in result if r["category"] == "Shopping")
    assert shopping["current"] == Decimal("50")
    assert shopping["previous"] == Decimal("100")
    assert shopping["change_pct"] == -50.0


def test_month_over_month_no_previous(tmp_path):
    ledger = _setup_with_transactions(tmp_path)
    mgr = ReportManager(ledger)
    result = mgr.month_over_month(2026, 3)
    # No February data, so previous should be 0 for all
    for r in result:
        assert r["previous"] == Decimal(0)


# --- Task 4: largest_transactions ---


def test_largest_transactions(tmp_path):
    ledger = _setup_with_transactions(tmp_path)
    mgr = ReportManager(ledger)
    result = mgr.largest_transactions(2026, 3, limit=3)

    assert len(result) <= 3
    # Should be sorted by amount descending
    assert result[0]["amount"] >= result[1]["amount"]
    # Largest should be JD.com 299
    assert result[0]["payee"] == "JD.com"
    assert result[0]["amount"] == Decimal("299")


def test_largest_transactions_default_limit(tmp_path):
    ledger = _setup_with_transactions(tmp_path)
    mgr = ReportManager(ledger)
    result = mgr.largest_transactions(2026, 3)
    assert len(result) <= 5  # default limit
