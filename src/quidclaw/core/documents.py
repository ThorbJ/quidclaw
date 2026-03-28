import datetime
from quidclaw.core.ledger import Ledger


class DocumentManager:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    def add_document(
        self,
        account: str,
        path: str,
        date: datetime.date | None = None,
    ) -> None:
        """Write a Beancount document directive to the monthly file.

        Links a file to an account at a specific date. The path can be
        absolute or relative to the ledger file.
        """
        date = date or datetime.date.today()
        line = f'{date} document {account} "{path}"\n'
        self.ledger.ensure_month_file(date.year, date.month)
        month_file = self.ledger.config.month_bean(date.year, date.month)
        self.ledger.append(month_file, line)
