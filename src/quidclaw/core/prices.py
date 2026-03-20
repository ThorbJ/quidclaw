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

        Requires beanprice to be installed and price source configuration
        in the ledger (commodity directives with price metadata).
        """
        raise NotImplementedError(
            "Automatic price fetching requires beanprice configuration. "
            "Use write_price() to add prices manually."
        )
