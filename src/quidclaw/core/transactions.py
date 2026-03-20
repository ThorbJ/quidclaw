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
        self.ledger.ensure_month_file(date.year, date.month)
        month_file = self.ledger.config.month_bean(date.year, date.month)
        self.ledger.append(month_file, text)
