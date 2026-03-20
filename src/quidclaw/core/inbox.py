import shutil
from datetime import datetime
from pathlib import Path
from quidclaw.config import QuidClawConfig


class InboxManager:
    def __init__(self, config: QuidClawConfig):
        self.config = config

    def list_files(self) -> list[dict]:
        """List all files in inbox/ with metadata."""
        files = []
        for f in sorted(self.config.inbox_dir.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        return files

    def move_to_documents(
        self, inbox_filename: str, new_name: str, year: int, month: int
    ) -> Path:
        """Move a file from inbox/ to documents/YYYY/MM/ with a new name."""
        src = self.config.inbox_dir / inbox_filename
        if not src.exists():
            raise FileNotFoundError(f"File not found in inbox: {inbox_filename}")
        dest_dir = self.config.documents_dir / str(year) / f"{month:02d}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / new_name
        shutil.move(str(src), str(dest))
        return dest

    def get_data_status(self) -> dict:
        """Return data status: inbox count, last ledger modification time."""
        inbox_files = self.list_files()
        last_modified = None
        if self.config.ledger_dir.exists():
            for bean in self.config.ledger_dir.rglob("*.bean"):
                mtime = bean.stat().st_mtime
                if last_modified is None or mtime > last_modified:
                    last_modified = mtime
        return {
            "inbox_count": len(inbox_files),
            "inbox_files": [f["name"] for f in inbox_files],
            "last_modified": datetime.fromtimestamp(last_modified).isoformat() if last_modified else None,
        }
