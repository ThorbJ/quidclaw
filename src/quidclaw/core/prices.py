import datetime
from decimal import Decimal
from beancount.core import data
from quidclaw.core.ledger import Ledger


class PriceManager:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    def get_existing_commodities(self) -> set[str]:
        """Get currencies that already have commodity directives."""
        try:
            entries, _, _ = self.ledger.load()
            return {e.currency for e in entries if isinstance(e, data.Commodity)}
        except Exception:
            return set()

    def add_commodity(
        self,
        commodity: str,
        source: str,
        quote: str,
        date: datetime.date | None = None,
    ) -> None:
        """Register a commodity with its price source.

        Args:
            commodity: Commodity name (e.g., USD, BTC, AAPL).
            source: Beanprice source string (e.g., "yahoo/AAPL", "yahoo/BTC-CNY").
            quote: Quote currency (e.g., CNY, USD).
            date: Date for the commodity directive.

        Raises:
            ValueError: If commodity already exists.
        """
        existing = self.get_existing_commodities()
        if commodity in existing:
            raise ValueError(f"Commodity '{commodity}' already exists")

        date = date or datetime.date.today()
        lines = (
            f'\n{date} commodity {commodity}\n'
            f'  price: "{quote}:{source}"\n'
        )
        self.ledger.append(self.ledger.config.accounts_bean, lines)

    def write_price(
        self, commodity: str, price: Decimal, currency: str, date: datetime.date | None = None
    ) -> None:
        """Write a price directive to prices.bean."""
        date = date or datetime.date.today()
        line = f'{date} price {commodity}  {price} {currency}\n'
        self.ledger.append(self.ledger.config.prices_bean, line)

    def fetch_prices(self, commodities: list[str] | None = None) -> list[dict]:
        """Fetch latest prices using beanprice.

        Reads commodity directives with 'price' metadata from the ledger,
        fetches current prices via beanprice, and writes them to prices.bean.

        Args:
            commodities: Optional list of commodity names to fetch.
                If None, fetches all commodities with price metadata.

        Returns:
            List of dicts with keys: commodity, price, currency, date
            (or commodity, error on failure).
        """
        try:
            from beanprice.price import (
                DatedPrice,
                fetch_price,
                find_currencies_declared,
                setup_cache,
            )
        except ImportError:
            raise ImportError(
                "beanprice is required for automatic price fetching. "
                "Install it with: pip install beanprice"
            )

        setup_cache(None, False)

        entries, errors, options = self.ledger.load()
        declared = find_currencies_declared(entries)

        # Filter to requested commodities first, then check if any remain
        if commodities:
            commodity_set = set(commodities)
            declared = [(base, quote, sources) for base, quote, sources in declared
                        if base in commodity_set]
            if not declared:
                raise ValueError(
                    f"No price metadata found for: {', '.join(commodities)}"
                )
        elif not declared:
            raise ValueError(
                "No commodity directives with price metadata found in the ledger. "
                "Use 'quidclaw add-commodity' to register commodities first."
            )

        results = []
        for base, quote, sources in declared:
            dprice = DatedPrice(base=base, quote=quote, date=None, sources=sources)
            try:
                entry = fetch_price(dprice)
                if entry is None:
                    results.append({
                        "commodity": base,
                        "quote": quote,
                        "error": "No price returned from source",
                    })
                    continue

                self.write_price(
                    commodity=entry.currency,
                    price=entry.amount.number,
                    currency=entry.amount.currency,
                    date=entry.date,
                )
                results.append({
                    "commodity": entry.currency,
                    "price": str(entry.amount.number),
                    "currency": entry.amount.currency,
                    "date": entry.date.isoformat(),
                })
            except Exception as e:
                results.append({
                    "commodity": base,
                    "quote": quote,
                    "error": str(e),
                })

        return results
