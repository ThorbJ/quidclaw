import datetime
import pytest
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


# --- add_commodity ---


def test_add_commodity_fiat(tmp_path):
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    pm.add_commodity("USD", "yahoo/USDCNY=X", "CNY")
    content = ledger.config.accounts_bean.read_text()
    assert "commodity USD" in content
    assert 'price: "CNY:yahoo/USDCNY=X"' in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0


def test_add_commodity_crypto(tmp_path):
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    pm.add_commodity("BTC", "yahoo/BTC-CNY", "CNY")
    content = ledger.config.accounts_bean.read_text()
    assert "commodity BTC" in content
    assert 'price: "CNY:yahoo/BTC-CNY"' in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0


def test_add_commodity_stock(tmp_path):
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    pm.add_commodity("AAPL", "yahoo/AAPL", "USD")
    content = ledger.config.accounts_bean.read_text()
    assert "commodity AAPL" in content
    assert 'price: "USD:yahoo/AAPL"' in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0


def test_add_commodity_duplicate_raises(tmp_path):
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    pm.add_commodity("AAPL", "yahoo/AAPL", "USD")
    with pytest.raises(ValueError, match="already exists"):
        pm.add_commodity("AAPL", "yahoo/AAPL", "USD")


def test_add_commodity_with_date(tmp_path):
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    pm.add_commodity("ETH", "yahoo/ETH-CNY", "CNY", date=datetime.date(2024, 1, 1))
    content = ledger.config.accounts_bean.read_text()
    assert "2024-01-01 commodity ETH" in content


# --- fetch_prices ---


def test_fetch_prices_no_commodities(tmp_path):
    """fetch_prices raises ValueError when no commodity has price metadata."""
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    with pytest.raises(ValueError, match="No commodity directives"):
        pm.fetch_prices()


def test_fetch_prices_filter_unknown_commodity(tmp_path):
    """fetch_prices raises ValueError when filtering to a commodity without metadata."""
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    with pytest.raises(ValueError, match="No price metadata found for"):
        pm.fetch_prices(["NOSUCH"])


def test_fetch_prices_with_commodity(tmp_path):
    """fetch_prices fetches from beanprice when commodity is registered."""
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    pm.add_commodity("USD", "yahoo/USDCNY=X", "CNY")
    results = pm.fetch_prices()
    assert len(results) == 1
    r = results[0]
    assert r["commodity"] == "USD"
    assert r["currency"] == "CNY"
    assert "price" in r
    assert "date" in r
    # Verify it was written to prices.bean
    content = ledger.config.prices_bean.read_text()
    assert "price USD" in content
    assert "CNY" in content


def test_fetch_prices_filter_by_commodity(tmp_path):
    """fetch_prices can filter to specific commodities."""
    ledger = make_ledger(tmp_path)
    pm = PriceManager(ledger)
    pm.add_commodity("USD", "yahoo/USDCNY=X", "CNY")
    pm.add_commodity("EUR", "yahoo/EURCNY=X", "CNY")
    results = pm.fetch_prices(["USD"])
    assert len(results) == 1
    assert results[0]["commodity"] == "USD"
