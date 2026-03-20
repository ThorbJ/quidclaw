from pathlib import Path
from beancount import loader
from quidclaw.config import QuidClawConfig


class Ledger:
    def __init__(self, config: QuidClawConfig):
        self.config = config

    def init(self) -> None:
        """Initialize the data directory structure."""
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        self.config.ledger_dir.mkdir(exist_ok=True)
        self.config.inbox_dir.mkdir(exist_ok=True)
        self.config.documents_dir.mkdir(exist_ok=True)
        self.config.notes_dir.mkdir(exist_ok=True)
        self.config.reports_dir.mkdir(exist_ok=True)

        if not self.config.accounts_bean.exists():
            self.config.accounts_bean.write_text("")

        if not self.config.prices_bean.exists():
            self.config.prices_bean.write_text("")

        if not self.config.main_bean.exists():
            self.config.main_bean.write_text(
                'option "title" "QuidClaw Ledger"\n'
                'option "operating_currency" "CNY"\n'
                '\n'
                'include "accounts.bean"\n'
                'include "prices.bean"\n'
            )

    def load(self):
        """Load and parse the entire ledger. Returns (entries, errors, options)."""
        return loader.load_file(str(self.config.main_bean))

    def append(self, filepath: Path, text: str) -> None:
        """Append text to a ledger file."""
        with open(filepath, "a") as f:
            f.write(text)
