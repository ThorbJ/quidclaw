import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


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
    def config_dir(self) -> Path:
        return self.data_dir / ".quidclaw"

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.yaml"

    def load_settings(self) -> dict:
        """Load settings from .quidclaw/config.yaml. Returns empty dict if missing."""
        if self.config_file.exists():
            return yaml.safe_load(self.config_file.read_text()) or {}
        return {}

    def save_settings(self, settings: dict) -> None:
        """Save settings to .quidclaw/config.yaml."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(yaml.dump(settings, default_flow_style=False, allow_unicode=True))

    def get_setting(self, key: str, default=None):
        """Get a single setting value."""
        return self.load_settings().get(key, default)

    def set_setting(self, key: str, value) -> None:
        """Set a single setting value."""
        settings = self.load_settings()
        settings[key] = value
        self.save_settings(settings)

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
