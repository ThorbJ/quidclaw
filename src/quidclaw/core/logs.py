import uuid
from datetime import datetime

import yaml

from quidclaw.config import QuidClawConfig


class AuditLogger:
    """Writes structured processing logs to logs/ directory."""

    def __init__(self, config: QuidClawConfig):
        self.config = config

    def log_event(self, action: str, source: dict, **fields) -> str:
        """Write a processing log entry. Returns the event ID."""
        now = datetime.now()
        suffix = uuid.uuid4().hex[:6]
        event_id = f"evt_{now.strftime('%Y%m%dT%H%M%S')}_{suffix}"

        log_entry = {
            "id": event_id,
            "timestamp": now.isoformat(),
            "action": action,
            "source": source,
            **fields,
        }

        self.config.logs_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{now.strftime('%Y-%m-%dT%H-%M-%S')}_{suffix}_{action}.yaml"
        log_path = self.config.logs_dir / filename
        log_path.write_text(
            yaml.dump(log_entry, default_flow_style=False, allow_unicode=True)
        )
        return event_id

    def list_logs(self, limit: int = 20) -> list[dict]:
        """List recent log entries, newest first."""
        if not self.config.logs_dir.exists():
            return []
        logs = []
        for f in sorted(self.config.logs_dir.glob("*.yaml"), reverse=True)[:limit]:
            logs.append(yaml.safe_load(f.read_text()))
        return logs
