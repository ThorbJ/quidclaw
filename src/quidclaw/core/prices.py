import datetime
from decimal import Decimal
from quidclaw.core.ledger import Ledger


class PriceManager:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger

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
                "Add a directive like:\n"
                '  2024-01-01 commodity USD\n'
                '    price: "CNY:yahoo/USDCNY=X"'
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
