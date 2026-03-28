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


def test_add_transaction_with_metadata(tmp_path):
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
        metadata={"source": "email:my-email/test", "import-id": "evt_123"},
    )
    month_file = ledger.config.month_bean(2026, 3)
    content = month_file.read_text()
    assert 'source: "email:my-email/test"' in content
    assert 'import-id: "evt_123"' in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    txns = [e for e in entries if e.__class__.__name__ == "Transaction"]
    assert len(txns) == 1


def test_add_transaction_with_pending_flag(tmp_path):
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="Unknown Merchant",
        narration="Unconfirmed charge",
        postings=[
            {"account": "Expenses:Food", "amount": "45.00", "currency": "CNY"},
            {"account": "Assets:Bank:BOC"},
        ],
        flag="!",
    )
    month_file = ledger.config.month_bean(2026, 3)
    content = month_file.read_text()
    assert '2026-03-14 ! "Unknown Merchant"' in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0


def test_add_transaction_with_tags(tmp_path):
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="Air China",
        narration="Flight to Beijing",
        postings=[
            {"account": "Expenses:Food", "amount": "3200.00", "currency": "CNY"},
            {"account": "Assets:Bank:BOC"},
        ],
        tags=["trip-beijing", "tax-2026"],
    )
    month_file = ledger.config.month_bean(2026, 3)
    content = month_file.read_text()
    assert "#trip-beijing" in content
    assert "#tax-2026" in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0


def test_add_transaction_with_links(tmp_path):
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="Client A",
        narration="Invoice payment",
        postings=[
            {"account": "Assets:Bank:BOC", "amount": "5000.00", "currency": "CNY"},
            {"account": "Expenses:Food"},
        ],
        links=["invoice-jan-clientA"],
    )
    month_file = ledger.config.month_bean(2026, 3)
    content = month_file.read_text()
    assert "^invoice-jan-clientA" in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0


def test_add_transaction_with_tags_and_links(tmp_path):
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="Restaurant",
        narration="Team dinner",
        postings=[
            {"account": "Expenses:Food", "amount": "800.00", "currency": "CNY"},
            {"account": "Liabilities:CreditCard:CMB"},
        ],
        flag="!",
        tags=["team-event"],
        links=["project-alpha"],
    )
    month_file = ledger.config.month_bean(2026, 3)
    content = month_file.read_text()
    assert "! " in content
    assert "#team-event" in content
    assert "^project-alpha" in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0


def test_add_transaction_without_metadata_unchanged(tmp_path):
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="Test",
        narration="No meta",
        postings=[
            {"account": "Expenses:Food", "amount": "10.00", "currency": "CNY"},
            {"account": "Assets:Bank:BOC"},
        ],
    )
    month_file = ledger.config.month_bean(2026, 3)
    content = month_file.read_text()
    assert "source:" not in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
