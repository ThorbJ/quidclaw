import datetime
from decimal import Decimal
from beancount.core import data
from quidclaw.core.ledger import Ledger


class AnomalyDetector:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger
        self._entries = None

    def _get_expense_transactions(self):
        """Load all expense transactions as flat list."""
        if self._entries is None:
            self._entries, _, _ = self.ledger.load()
        entries = self._entries
        txns = []
        for entry in entries:
            if not isinstance(entry, data.Transaction):
                continue
            for posting in entry.postings:
                if posting.account.startswith("Expenses:") and posting.units:
                    txns.append({
                        "date": entry.date,
                        "payee": entry.payee or "",
                        "narration": entry.narration or "",
                        "amount": abs(posting.units.number),
                        "currency": posting.units.currency,
                        "account": posting.account,
                    })
        return txns

    def find_duplicate_charges(self, days_window: int = 3) -> list[dict]:
        """Find potential duplicate charges: same amount + similar payee within N days."""
        txns = self._get_expense_transactions()
        duplicates = []
        seen = set()

        for i, a in enumerate(txns):
            for j, b in enumerate(txns):
                if j <= i:
                    continue
                pair_key = (i, j)
                if pair_key in seen:
                    continue
                if (a["amount"] == b["amount"]
                        and a["currency"] == b["currency"]
                        and a["payee"].lower() == b["payee"].lower()
                        and abs((a["date"] - b["date"]).days) <= days_window):
                    seen.add(pair_key)
                    duplicates.append({
                        "txn_a": {
                            "date": a["date"].isoformat(),
                            "payee": a["payee"],
                            "amount": a["amount"],
                            "currency": a["currency"],
                        },
                        "txn_b": {
                            "date": b["date"].isoformat(),
                            "payee": b["payee"],
                            "amount": b["amount"],
                            "currency": b["currency"],
                        },
                        "reason": f"Same amount ({a['amount']} {a['currency']}) + same payee within {abs((a['date'] - b['date']).days)} days",
                    })
        return duplicates

    def find_recurring_charges(self, min_occurrences: int = 3) -> list[dict]:
        """Find payees that appear across multiple months with similar amounts."""
        txns = self._get_expense_transactions()
        # Group by payee + currency
        by_payee = {}
        for t in txns:
            key = (t["payee"].lower(), t["currency"])
            if key not in by_payee:
                by_payee[key] = []
            by_payee[key].append(t)

        recurring = []
        for (payee_lower, currency), group in by_payee.items():
            # Count distinct months
            months = {(t["date"].year, t["date"].month) for t in group}
            if len(months) < min_occurrences:
                continue
            amounts = [t["amount"] for t in group]
            avg = sum(amounts) / len(amounts)
            recurring.append({
                "payee": group[0]["payee"],  # original case
                "currency": currency,
                "avg_amount": avg.quantize(Decimal("0.01")),
                "occurrences": len(months),
                "months": sorted(months),
            })
        recurring.sort(key=lambda x: x["avg_amount"], reverse=True)
        return recurring

    def find_price_changes(self) -> list[dict]:
        """For recurring payees, detect amount changes between months."""
        txns = self._get_expense_transactions()
        # Group by payee + currency, then by month
        by_payee = {}
        for t in txns:
            key = (t["payee"].lower(), t["currency"])
            if key not in by_payee:
                by_payee[key] = {}
            month_key = (t["date"].year, t["date"].month)
            by_payee[key][month_key] = t["amount"]

        changes = []
        for (payee_lower, currency), monthly in by_payee.items():
            if len(monthly) < 2:
                continue
            sorted_months = sorted(monthly.keys())
            for i in range(1, len(sorted_months)):
                prev_amt = monthly[sorted_months[i - 1]]
                curr_amt = monthly[sorted_months[i]]
                if prev_amt != curr_amt:
                    changes.append({
                        "payee": payee_lower,
                        "currency": currency,
                        "old_amount": prev_amt,
                        "new_amount": curr_amt,
                        "old_month": f"{sorted_months[i-1][0]}-{sorted_months[i-1][1]:02d}",
                        "new_month": f"{sorted_months[i][0]}-{sorted_months[i][1]:02d}",
                    })
        return changes

    def find_large_outliers(self, threshold: float = 3.0) -> list[dict]:
        """Find transactions significantly larger than their category average."""
        txns = self._get_expense_transactions()
        # Group by category (second-level account)
        by_category = {}
        for t in txns:
            parts = t["account"].split(":")
            category = parts[1] if len(parts) > 1 else parts[0]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(t)

        outliers = []
        for category, group in by_category.items():
            if len(group) < 2:
                continue
            amounts = [t["amount"] for t in group]
            avg = sum(amounts) / len(amounts)
            if avg == 0:
                continue
            for t in group:
                multiple = float(t["amount"] / avg)
                if multiple >= threshold:
                    outliers.append({
                        "date": t["date"].isoformat(),
                        "payee": t["payee"],
                        "amount": t["amount"],
                        "currency": t["currency"],
                        "category": category,
                        "category_avg": avg.quantize(Decimal("0.01")),
                        "multiple": round(multiple, 1),
                    })
        outliers.sort(key=lambda x: x["multiple"], reverse=True)
        return outliers

    def find_unknown_merchants(self, min_known: int = 2) -> list[dict]:
        """Find payees that appear only once (potential unknown charges)."""
        txns = self._get_expense_transactions()
        payee_counts = {}
        for t in txns:
            key = t["payee"].lower()
            if key not in payee_counts:
                payee_counts[key] = []
            payee_counts[key].append(t)

        unknown = []
        for payee_lower, group in payee_counts.items():
            if len(group) < min_known:
                t = group[0]
                unknown.append({
                    "payee": t["payee"],
                    "date": t["date"].isoformat(),
                    "amount": t["amount"],
                    "currency": t["currency"],
                })
        unknown.sort(key=lambda x: x["amount"], reverse=True)
        return unknown
