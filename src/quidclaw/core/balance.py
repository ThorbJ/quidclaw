import datetime
from decimal import Decimal
from beancount.core import realization
from quidclaw.core.ledger import Ledger


class BalanceManager:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    def get_balance(self, account: str, date: datetime.date | None = None) -> dict[str, Decimal]:
        """Get balance for a single account. Returns {currency: amount}."""
        entries, _, options = self.ledger.load()
        real_root = realization.realize(entries)
        real_account = realization.get(real_root, account)
        if real_account is None:
            return {}
        result = {}
        for pos in real_account.balance:
            result[pos.units.currency] = pos.units.number
        return result

    def get_all_balances(self) -> dict[str, dict[str, Decimal]]:
        """Get balances for all accounts. Returns {account: {currency: amount}}."""
        entries, _, options = self.ledger.load()
        real_root = realization.realize(entries)
        result = {}
        for real_account in realization.iter_children(real_root):
            if not real_account.account or real_account.balance.is_empty():
                continue
            result[real_account.account] = {}
            for pos in real_account.balance:
                result[real_account.account][pos.units.currency] = pos.units.number
        return result

    def balance_check(
        self, account: str, expected: Decimal, currency: str, date: datetime.date | None = None
    ) -> tuple[bool, str]:
        """Check if account balance matches expected. Returns (ok, message)."""
        actual = self.get_balance(account, date)
        actual_amount = actual.get(currency, Decimal("0"))
        if actual_amount == expected:
            return True, f"{account}: {actual_amount} {currency}"
        diff = actual_amount - expected
        return False, f"{account}: expected {expected} {currency}, actual {actual_amount} {currency} (diff: {diff:+})"

    def add_balance_assertion(
        self, account: str, amount: Decimal, currency: str, date: datetime.date
    ) -> None:
        """Write a balance assertion directive."""
        line = f'{date} balance {account}  {amount} {currency}\n'
        month_file = self.ledger.config.month_bean(date.year, date.month)
        from quidclaw.core.transactions import TransactionManager
        txn_mgr = TransactionManager(self.ledger)
        txn_mgr._ensure_month_included(date.year, date.month)
        self.ledger.append(month_file, line)
