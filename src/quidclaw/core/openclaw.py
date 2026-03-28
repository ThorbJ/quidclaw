"""OpenClaw agent setup for QuidClaw."""

import shutil
import subprocess
from pathlib import Path

from quidclaw.config import QuidClawConfig

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_AGENTS_AUTOMATION_SECTION = """
## Automation

You have cron jobs and heartbeat configured. Follow these rules:

### Heartbeat
- Read HEARTBEAT.md and follow it strictly
- If nothing needs attention, reply HEARTBEAT_OK
- For urgent items (large unusual charges, overdue payments), alert immediately

### Daily Routine (Cron)
- Run /quidclaw-daily
- Output format: concise, emoji-marked, under 500 characters
- If nothing to report: "一切正常 ✅"

### Monthly Review (Cron)
- Run /quidclaw-review
- Deliver as a structured summary to the user

### Pending Items
- When a task is blocked (missing info, encrypted PDF, etc.):
  1. Save to `notes/pending/` as YAML
  2. Notify the user what you need
  3. Continue with other tasks
  4. Heartbeat will check pending items and resume when possible
"""


class OpenClawSetup:
    """Handles OpenClaw-specific agent setup."""

    def __init__(self, config: QuidClawConfig):
        self.config = config
        self.data_dir = Path(config.data_dir)

    def is_available(self) -> bool:
        """Check if openclaw CLI is on PATH."""
        return shutil.which("openclaw") is not None

    def generate_templates(self) -> None:
        """Copy OpenClaw template files to data directory."""
        for template_name, target_name in [
            ("soul.md", "SOUL.md"),
            ("heartbeat.md", "HEARTBEAT.md"),
            ("bootstrap.md", "BOOTSTRAP.md"),
            ("identity.md", "IDENTITY.md"),
        ]:
            src = _TEMPLATES_DIR / template_name
            dst = self.data_dir / target_name
            if src.exists():
                dst.write_text(src.read_text())

    def generate_agents_md(self, entry_content: str = "") -> None:
        """Generate AGENTS.md with entry content + automation section."""
        content = entry_content + _AGENTS_AUTOMATION_SECTION
        (self.data_dir / "AGENTS.md").write_text(content)

    def create_agent(self) -> bool:
        """Create OpenClaw agent. Returns True if successful."""
        if not self.is_available():
            return False
        try:
            subprocess.run(
                ["openclaw", "agents", "add", "quidclaw",
                 "--workspace", str(self.data_dir)],
                check=True, capture_output=True, text=True,
            )
            subprocess.run(
                ["openclaw", "agents", "set-identity",
                 "--agent", "quidclaw",
                 "--name", "QuidClaw", "--emoji", "💰"],
                check=True, capture_output=True, text=True,
            )
            return True
        except (subprocess.CalledProcessError, OSError):
            return False
