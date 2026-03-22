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
        self.config.sources_dir.mkdir(exist_ok=True)
        self.config.logs_dir.mkdir(exist_ok=True)
        self.config.pending_dir.mkdir(exist_ok=True)

        if not self.config.accounts_bean.exists():
            self.config.accounts_bean.write_text("")

        if not self.config.prices_bean.exists():
            self.config.prices_bean.write_text("")

        if not self.config.main_bean.exists():
            operating = self.config.get_setting("operating_currency")
            lines = 'option "title" "QuidClaw Ledger"\n'
            if operating:
                lines += f'option "operating_currency" "{operating}"\n'
            lines += (
                '\n'
                'include "accounts.bean"\n'
                'include "prices.bean"\n'
            )
            self.config.main_bean.write_text(lines)

    def ensure_dirs(self) -> None:
        """Ensure all expected directories exist. Used by upgrade for older projects."""
        for d in [self.config.ledger_dir, self.config.inbox_dir,
                  self.config.documents_dir, self.config.notes_dir,
                  self.config.reports_dir, self.config.sources_dir,
                  self.config.logs_dir, self.config.pending_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def load(self):
        """Load and parse the entire ledger. Returns (entries, errors, options)."""
        return loader.load_file(str(self.config.main_bean))

    def ensure_month_file(self, year: int, month: int) -> None:
        """Ensure the year dir exists and the month file is included in main.bean."""
        year_dir = self.config.year_dir(year)
        year_dir.mkdir(parents=True, exist_ok=True)

        month_file = self.config.month_bean(year, month)
        if not month_file.exists():
            month_file.write_text("")

        main_content = self.config.main_bean.read_text()
        relative = f"{year}/{year}-{month:02d}.bean"
        include_line = f'include "{relative}"'
        if include_line not in main_content:
            self.append(self.config.main_bean, f'{include_line}\n')

    def append(self, filepath: Path, text: str) -> None:
        """Append text to a ledger file."""
        with open(filepath, "a") as f:
            f.write(text)
