import datetime
from pathlib import Path
from quidclaw.core.ledger import Ledger


class TransactionManager:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    def add_transaction(
        self,
        date: datetime.date,
        payee: str,
        narration: str,
        postings: list[dict],
    ) -> None:
        """Add a transaction to the appropriate monthly file.

        Each posting dict has: account (required), amount (optional), currency (optional).
        If amount is omitted from one posting, beancount auto-balances.
        """
        lines = [f'{date} * "{payee}" "{narration}"\n']
        for p in postings:
            account = p["account"]
            amount = p.get("amount")
            currency = p.get("currency")
            if amount and currency:
                lines.append(f"  {account}  {amount} {currency}\n")
            elif amount:
                lines.append(f"  {account}  {amount}\n")
            else:
                lines.append(f"  {account}\n")
        lines.append("\n")
        text = "".join(lines)

        # Write to monthly file
        self._ensure_month_included(date.year, date.month)
        month_file = self.ledger.config.month_bean(date.year, date.month)
        self.ledger.append(month_file, text)

    def _ensure_month_included(self, year: int, month: int) -> None:
        """Ensure the year dir exists and the month file is included in main.bean."""
        year_dir = self.ledger.config.year_dir(year)
        year_dir.mkdir(parents=True, exist_ok=True)

        month_file = self.ledger.config.month_bean(year, month)
        if not month_file.exists():
            month_file.write_text("")

        # Check if include already exists in main.bean
        main_content = self.ledger.config.main_bean.read_text()
        relative = f"{year}/{year}-{month:02d}.bean"
        include_line = f'include "{relative}"'
        if include_line not in main_content:
            self.ledger.append(self.ledger.config.main_bean, f'{include_line}\n')
