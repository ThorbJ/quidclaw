from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from quidclaw.config import QuidClawConfig


@dataclass
class SyncResult:
    source_name: str
    provider: str
    items_fetched: int
    items_stored: list[str]
    last_sync: datetime | None
    errors: list[str]


class DataSource(ABC):
    def __init__(self, source_name: str, source_config: dict, config: QuidClawConfig):
        self.source_name = source_name
        self.source_config = source_config
        self.config = config

    @staticmethod
    @abstractmethod
    def provider_name() -> str:
        ...

    @abstractmethod
    def sync(self) -> SyncResult:
        ...

    @abstractmethod
    def status(self) -> dict:
        ...

    def provision(self) -> dict:
        return self.source_config
