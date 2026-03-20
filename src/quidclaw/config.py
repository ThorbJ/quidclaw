import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class QuidClawConfig:
    data_dir: Path = field(default=None)

    def __post_init__(self):
        if self.data_dir is None:
            env = os.environ.get("QUIDCLAW_DATA_DIR")
            self.data_dir = Path(env) if env else None
        else:
            self.data_dir = Path(self.data_dir)

    @property
    def is_configured(self) -> bool:
        """Whether a data directory has been set."""
        return self.data_dir is not None

    @property
    def ledger_dir(self) -> Path:
        return self.data_dir / "ledger"

    @property
    def inbox_dir(self) -> Path:
        return self.data_dir / "inbox"

    @property
    def documents_dir(self) -> Path:
        return self.data_dir / "documents"

    @property
    def notes_dir(self) -> Path:
        return self.data_dir / "notes"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"

    @property
    def main_bean(self) -> Path:
        return self.ledger_dir / "main.bean"

    @property
    def accounts_bean(self) -> Path:
        return self.ledger_dir / "accounts.bean"

    @property
    def prices_bean(self) -> Path:
        return self.ledger_dir / "prices.bean"

    def year_dir(self, year: int) -> Path:
        return self.ledger_dir / str(year)

    def month_bean(self, year: int, month: int) -> Path:
        return self.year_dir(year) / f"{year}-{month:02d}.bean"
