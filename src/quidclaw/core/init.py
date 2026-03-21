import datetime
from beancount.core import data
from quidclaw.core.ledger import Ledger
from quidclaw.core.accounts import AccountManager

# Default account template. Currency is filled in from config at runtime.
DEFAULT_ACCOUNTS = [
    # Assets
    {"name": "Assets:Bank:Checking", "use_operating_currency": True},
    {"name": "Assets:Bank:Savings", "use_operating_currency": True},
    {"name": "Assets:Cash", "use_operating_currency": True},
    # Liabilities
    {"name": "Liabilities:CreditCard", "use_operating_currency": True},
    # Income
    {"name": "Income:Salary"},
    {"name": "Income:Bonus"},
    {"name": "Income:Interest"},
    {"name": "Income:Other"},
    # Expenses
    {"name": "Expenses:Food"},
    {"name": "Expenses:Transport"},
    {"name": "Expenses:Housing"},
    {"name": "Expenses:Shopping"},
    {"name": "Expenses:Entertainment"},
    {"name": "Expenses:Health"},
    {"name": "Expenses:Education"},
    {"name": "Expenses:Utilities"},
    {"name": "Expenses:Other"},
    # Equity
    {"name": "Equity:Opening-Balances"},
]


class LedgerInitializer:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    def init_with_template(self, accounts: list[dict] | None = None) -> list[str]:
        """Initialize ledger with account template. Returns list of created account names.

        If accounts is None, uses DEFAULT_ACCOUNTS.
        Each account dict: {"name": str, "currencies": list[str] (optional)}
        """
        self.ledger.init()

        # Check existing accounts to avoid duplicates
        existing = set()
        try:
            entries, _, _ = self.ledger.load()
            existing = {e.account for e in entries if isinstance(e, data.Open)}
        except Exception:
            pass

        # Resolve operating currency from config
        operating = self.ledger.config.get_setting("operating_currency")

        template = accounts or DEFAULT_ACCOUNTS
        mgr = AccountManager(self.ledger)
        created = []
        today = datetime.date.today()

        for acct in template:
            name = acct["name"]
            if name in existing:
                continue
            currencies = acct.get("currencies")
            if currencies is None and acct.get("use_operating_currency") and operating:
                currencies = [operating]
            mgr.add_account(name, currencies=currencies, open_date=today)
            created.append(name)

        return created
