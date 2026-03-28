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
        metadata: dict | None = None,
        flag: str = "*",
        tags: list[str] | None = None,
        links: list[str] | None = None,
    ) -> None:
        """Add a transaction to the appropriate monthly file.

        Each posting dict has: account (required), amount (optional), currency (optional).
        If amount is omitted from one posting, beancount auto-balances.
        metadata is an optional dict of key/value pairs written as Beancount metadata lines.
        flag: transaction flag — '*' (cleared), '!' (pending), or any uppercase letter.
        tags: list of tag strings (without #), e.g. ["trip-beijing", "tax-2026"].
        links: list of link strings (without ^), e.g. ["invoice-jan"].
        """
        header = f'{date} {flag} "{payee}" "{narration}"'
        if tags:
            header += " " + " ".join(f"#{t}" for t in tags)
        if links:
            header += " " + " ".join(f"^{l}" for l in links)
        lines = [header + "\n"]
        if metadata:
            for key, value in metadata.items():
                lines.append(f'  {key}: "{value}"\n')
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
