import datetime
from decimal import Decimal
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.init import LedgerInitializer
from quidclaw.core.transactions import TransactionManager
from quidclaw.core.anomaly import AnomalyDetector


def _setup_ledger(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    LedgerInitializer(ledger).init_with_template()
    return ledger


def _add_txn(ledger, date, payee, amount, currency="CNY", account="Expenses:Food"):
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=date, payee=payee, narration=payee,
        postings=[
            {"account": account, "amount": str(amount), "currency": currency},
            {"account": "Assets:Bank:Checking"},
        ],
    )


def test_find_duplicate_charges(tmp_path):
    ledger = _setup_ledger(tmp_path)
    # Two identical charges 1 day apart
    _add_txn(ledger, datetime.date(2026, 3, 15), "Starbucks", "35.80")
    _add_txn(ledger, datetime.date(2026, 3, 16), "Starbucks", "35.80")
    # A different charge (should not be flagged)
    _add_txn(ledger, datetime.date(2026, 3, 20), "McDonald's", "25.00")

    detector = AnomalyDetector(ledger)
    dupes = detector.find_duplicate_charges(days_window=3)

    assert len(dupes) >= 1
    assert any("Starbucks" in str(d) for d in dupes)


def test_no_duplicates(tmp_path):
    ledger = _setup_ledger(tmp_path)
    _add_txn(ledger, datetime.date(2026, 3, 15), "Starbucks", "35.80")
    _add_txn(ledger, datetime.date(2026, 3, 25), "Starbucks", "35.80")  # 10 days apart

    detector = AnomalyDetector(ledger)
    dupes = detector.find_duplicate_charges(days_window=3)
    assert len(dupes) == 0


def test_find_recurring_charges(tmp_path):
    ledger = _setup_ledger(tmp_path)
    # Netflix 3 months in a row
    _add_txn(ledger, datetime.date(2026, 1, 15), "Netflix", "88", account="Expenses:Entertainment")
    _add_txn(ledger, datetime.date(2026, 2, 15), "Netflix", "88", account="Expenses:Entertainment")
    _add_txn(ledger, datetime.date(2026, 3, 15), "Netflix", "88", account="Expenses:Entertainment")
    # One-time purchase (should not be recurring)
    _add_txn(ledger, datetime.date(2026, 3, 20), "Apple Store", "999", account="Expenses:Shopping")

    detector = AnomalyDetector(ledger)
    recurring = detector.find_recurring_charges(min_occurrences=3)

    assert len(recurring) >= 1
    netflix = next(r for r in recurring if "Netflix" in r["payee"])
    assert netflix["avg_amount"] == Decimal("88")
    assert netflix["occurrences"] >= 3


def test_find_price_changes(tmp_path):
    ledger = _setup_ledger(tmp_path)
    # Netflix price increase: 88 -> 98
    _add_txn(ledger, datetime.date(2026, 1, 15), "Netflix", "88", account="Expenses:Entertainment")
    _add_txn(ledger, datetime.date(2026, 2, 15), "Netflix", "88", account="Expenses:Entertainment")
    _add_txn(ledger, datetime.date(2026, 3, 15), "Netflix", "98", account="Expenses:Entertainment")

    detector = AnomalyDetector(ledger)
    changes = detector.find_price_changes()

    assert len(changes) >= 1
    netflix = next(c for c in changes if "netflix" in c["payee"])
    assert netflix["old_amount"] == Decimal("88")
    assert netflix["new_amount"] == Decimal("98")


def test_find_large_outliers(tmp_path):
    ledger = _setup_ledger(tmp_path)
    # Normal food: ~30-50
    _add_txn(ledger, datetime.date(2026, 3, 1), "Restaurant A", "35")
    _add_txn(ledger, datetime.date(2026, 3, 5), "Restaurant B", "42")
    _add_txn(ledger, datetime.date(2026, 3, 10), "Restaurant C", "38")
    # Outlier: 500 (>3x average of ~38)
    _add_txn(ledger, datetime.date(2026, 3, 15), "Fancy Restaurant", "500")

    detector = AnomalyDetector(ledger)
    outliers = detector.find_large_outliers(threshold=3.0)

    assert len(outliers) >= 1
    assert any("Fancy" in o["payee"] for o in outliers)


def test_no_outliers_when_all_similar(tmp_path):
    ledger = _setup_ledger(tmp_path)
    _add_txn(ledger, datetime.date(2026, 3, 1), "Restaurant", "35")
    _add_txn(ledger, datetime.date(2026, 3, 5), "Restaurant", "38")
    _add_txn(ledger, datetime.date(2026, 3, 10), "Restaurant", "40")

    detector = AnomalyDetector(ledger)
    outliers = detector.find_large_outliers(threshold=3.0)
    assert len(outliers) == 0


def test_find_unknown_merchants(tmp_path):
    ledger = _setup_ledger(tmp_path)
    # Known merchant (appears twice)
    _add_txn(ledger, datetime.date(2026, 3, 1), "Starbucks", "35")
    _add_txn(ledger, datetime.date(2026, 3, 15), "Starbucks", "35")
    # Unknown merchant (appears once)
    _add_txn(ledger, datetime.date(2026, 3, 10), "XYZ Tech Ltd", "199")

    detector = AnomalyDetector(ledger)
    unknown = detector.find_unknown_merchants(min_known=2)

    assert len(unknown) >= 1
    assert any("XYZ" in u["payee"] for u in unknown)
