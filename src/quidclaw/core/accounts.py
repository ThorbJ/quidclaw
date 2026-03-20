import re
import datetime
from beancount.core import data
from quidclaw.core.ledger import Ledger

VALID_PREFIXES = ("Assets", "Liabilities", "Income", "Expenses", "Equity")
ACCOUNT_RE = re.compile(r"^[A-Z][a-zA-Z0-9-]+(:[A-Za-z0-9][a-zA-Z0-9-]*)+$")


class AccountManager:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    @staticmethod
    def validate_account_name(name: str) -> None:
        """Validate that name follows Beancount account format."""
        if not ACCOUNT_RE.match(name):
            raise ValueError(
                f"Invalid account name '{name}'. Must be colon-separated, "
                f"each segment capitalized (e.g., Assets:Bank:Checking)"
            )
        if not name.startswith(VALID_PREFIXES):
            raise ValueError(
                f"Account '{name}' must start with one of: {', '.join(VALID_PREFIXES)}"
            )

    def add_account(
        self,
        name: str,
        currencies: list[str] | None = None,
        open_date: datetime.date | None = None,
    ) -> None:
        """Add an Open directive to accounts.bean."""
        self.validate_account_name(name)
        date = open_date or datetime.date.today()
        currency_str = ",".join(currencies) if currencies else ""
        line = f'{date} open {name}'
        if currency_str:
            line += f' {currency_str}'
        line += "\n"
        self.ledger.append(self.ledger.config.accounts_bean, line)

    def close_account(
        self,
        name: str,
        close_date: datetime.date | None = None,
    ) -> None:
        """Add a Close directive to accounts.bean."""
        self.validate_account_name(name)
        date = close_date or datetime.date.today()
        line = f"{date} close {name}\n"
        self.ledger.append(self.ledger.config.accounts_bean, line)

    def list_accounts(self, account_type: str | None = None) -> list[str]:
        """List all open accounts, optionally filtered by type prefix."""
        entries, _, _ = self.ledger.load()
        accounts = set()
        for entry in entries:
            if isinstance(entry, data.Open):
                accounts.add(entry.account)
            elif isinstance(entry, data.Close):
                accounts.discard(entry.account)
        if account_type:
            accounts = {a for a in accounts if a.startswith(account_type)}
        return sorted(accounts)
