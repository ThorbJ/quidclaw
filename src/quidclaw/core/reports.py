from decimal import Decimal

from beancount.core import data
from beanquery.query import run_query

from quidclaw.core.ledger import Ledger


class ReportManager:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    def query(self, bql: str) -> tuple[list[str], list[tuple]]:
        """Execute a BQL query. Returns (column_names, rows)."""
        entries, errors, options = self.ledger.load()
        columns, rows = run_query(entries, options, bql)
        col_names = [col.name for col in columns]
        result_rows = [tuple(row) for row in rows]
        return col_names, result_rows

    def income_statement(self, period: str | None = None) -> str:
        """Generate a text income statement."""
        if period:
            bql = f"SELECT account, sum(position) WHERE account ~ 'Income|Expenses' AND date >= {period} GROUP BY account ORDER BY account"
        else:
            bql = "SELECT account, sum(position) WHERE account ~ 'Income|Expenses' GROUP BY account ORDER BY account"
        columns, rows = self.query(bql)
        return self._format_table("Income Statement", columns, rows)

    def balance_sheet(self) -> str:
        """Generate a text balance sheet."""
        bql = "SELECT account, sum(position) WHERE account ~ 'Assets|Liabilities|Equity' GROUP BY account ORDER BY account"
        columns, rows = self.query(bql)
        return self._format_table("Balance Sheet", columns, rows)

    def monthly_summary(self, year: int, month: int) -> dict:
        """Income, expenses, and savings for a given month."""
        entries, _, _ = self.ledger.load()
        income = {}
        expenses = {}

        for entry in entries:
            if not isinstance(entry, data.Transaction):
                continue
            if entry.date.year != year or entry.date.month != month:
                continue
            for posting in entry.postings:
                if posting.units is None:
                    continue
                curr = posting.units.currency
                amt = posting.units.number
                if posting.account.startswith("Income:"):
                    income[curr] = income.get(curr, Decimal(0)) + abs(amt)
                elif posting.account.startswith("Expenses:"):
                    expenses[curr] = expenses.get(curr, Decimal(0)) + abs(amt)

        # Calculate savings per currency
        all_currencies = set(income.keys()) | set(expenses.keys())
        savings = {}
        for curr in all_currencies:
            savings[curr] = income.get(curr, Decimal(0)) - expenses.get(curr, Decimal(0))

        return {"income": income, "expenses": expenses, "savings": savings}

    def spending_by_category(self, year: int, month: int) -> list[dict]:
        """Spending breakdown by expense category for a month, sorted by amount desc."""
        entries, _, _ = self.ledger.load()
        categories = {}

        for entry in entries:
            if not isinstance(entry, data.Transaction):
                continue
            if entry.date.year != year or entry.date.month != month:
                continue
            for posting in entry.postings:
                if not posting.account.startswith("Expenses:") or posting.units is None:
                    continue
                # Use second-level category: Expenses:Food -> Food
                parts = posting.account.split(":")
                category = parts[1] if len(parts) > 1 else parts[0]
                curr = posting.units.currency
                key = (category, curr)
                categories[key] = categories.get(key, Decimal(0)) + abs(posting.units.number)

        result = [
            {"category": cat, "amount": amt, "currency": curr}
            for (cat, curr), amt in categories.items()
        ]
        result.sort(key=lambda x: x["amount"], reverse=True)
        return result

    def month_over_month(self, year: int, month: int) -> list[dict]:
        """Compare spending by category: current month vs previous month."""
        current = {(r["category"], r["currency"]): r["amount"]
                   for r in self.spending_by_category(year, month)}

        # Calculate previous month
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1

        previous = {(r["category"], r["currency"]): r["amount"]
                    for r in self.spending_by_category(prev_year, prev_month)}

        all_keys = set(current.keys()) | set(previous.keys())
        result = []
        for (category, currency) in sorted(all_keys):
            curr_amt = current.get((category, currency), Decimal(0))
            prev_amt = previous.get((category, currency), Decimal(0))
            if prev_amt > 0:
                change_pct = float((curr_amt - prev_amt) / prev_amt * 100)
            elif curr_amt > 0:
                change_pct = 100.0  # New category
            else:
                change_pct = 0.0
            result.append({
                "category": category,
                "currency": currency,
                "current": curr_amt,
                "previous": prev_amt,
                "change_pct": round(change_pct, 1),
            })
        return result

    def largest_transactions(self, year: int, month: int, limit: int = 5) -> list[dict]:
        """Top N largest expense transactions for a month."""
        entries, _, _ = self.ledger.load()
        txns = []

        for entry in entries:
            if not isinstance(entry, data.Transaction):
                continue
            if entry.date.year != year or entry.date.month != month:
                continue
            for posting in entry.postings:
                if not posting.account.startswith("Expenses:") or posting.units is None:
                    continue
                txns.append({
                    "date": entry.date.isoformat(),
                    "payee": entry.payee or "",
                    "narration": entry.narration or "",
                    "amount": abs(posting.units.number),
                    "currency": posting.units.currency,
                    "account": posting.account,
                })

        txns.sort(key=lambda x: x["amount"], reverse=True)
        return txns[:limit]

    def _format_table(self, title: str, columns: list[str], rows: list[tuple]) -> str:
        """Format query results as a readable text table."""
        lines = [title, "=" * len(title)]
        if not rows:
            lines.append("(no data)")
            return "\n".join(lines)
        header = " | ".join(str(c) for c in columns)
        lines.append(header)
        lines.append("-" * len(header))
        for row in rows:
            lines.append(" | ".join(str(v) for v in row))
        return "\n".join(lines)
