import datetime
from decimal import Decimal
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.prices import PriceManager


def make_ledger(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    return ledger


def test_write_price_directive(tmp_path):
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    pm.write_price("USD", Decimal("7.24"), "CNY", datetime.date(2026, 3, 14))
    content = ledger.config.prices_bean.read_text()
    assert "USD" in content
    assert "7.24" in content
    assert "CNY" in content


def test_write_price_loads_without_error(tmp_path):
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    pm.write_price("USD", Decimal("7.24"), "CNY", datetime.date(2026, 3, 14))
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    price_entries = [e for e in entries if e.__class__.__name__ == "Price"]
    assert len(price_entries) == 1
