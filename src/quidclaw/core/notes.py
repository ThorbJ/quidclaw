from pathlib import Path
from quidclaw.config import QuidClawConfig


class NotesManager:
    def __init__(self, config: QuidClawConfig):
        self.config = config

    def list_notes(self) -> list[dict]:
        """List all notes with relative paths."""
        notes = []
        if not self.config.notes_dir.exists():
            return notes
        for f in sorted(self.config.notes_dir.rglob("*.md")):
            rel = f.relative_to(self.config.notes_dir)
            notes.append({
                "path": str(rel),
                "name": f.stem,
            })
        return notes

    def read_note(self, relative_path: str) -> str:
        """Read a note by its relative path under notes/."""
        full_path = self.config.notes_dir / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {relative_path}")
        return full_path.read_text()

    def write_note(self, relative_path: str, content: str) -> Path:
        """Write or overwrite a note. Creates subdirectories as needed."""
        full_path = self.config.notes_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return full_path

    def search_notes(self, query: str) -> list[dict]:
        """Full-text search across all notes. Case-insensitive.
        Returns [{path, name, matches: [lines containing query]}]."""
        if not self.config.notes_dir.exists():
            return []
        query_lower = query.lower()
        results = []
        for f in sorted(self.config.notes_dir.rglob("*.md")):
            content = f.read_text()
            lines = content.split("\n")
            matches = [line.strip() for line in lines if query_lower in line.lower()]
            if matches:
                rel = f.relative_to(self.config.notes_dir)
                results.append({
                    "path": str(rel),
                    "name": f.stem,
                    "matches": matches,
                })
        return results

    def append_note(self, relative_path: str, section: str, content: str) -> Path:
        """Append content under a section header. Preserves existing content.
        Creates the note/section if they don't exist."""
        full_path = self.config.notes_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        section_header = f"## {section}"

        if not full_path.exists():
            # Create new file with the section
            full_path.write_text(f"{section_header}\n{content}\n")
            return full_path

        existing = full_path.read_text()
        lines = existing.split("\n")

        # Find the section
        section_idx = None
        for i, line in enumerate(lines):
            if line.strip() == section_header:
                section_idx = i
                break

        if section_idx is not None:
            # Find the end of this section (next ## or end of file)
            insert_idx = len(lines)
            for i in range(section_idx + 1, len(lines)):
                if lines[i].startswith("## "):
                    insert_idx = i
                    break
            # Insert before the next section (or at end), skip trailing blanks
            while insert_idx > section_idx + 1 and lines[insert_idx - 1].strip() == "":
                insert_idx -= 1
            lines.insert(insert_idx, content)
        else:
            # Section doesn't exist — add at end
            # Ensure blank line before new section
            if lines and lines[-1].strip() != "":
                lines.append("")
            lines.append(section_header)
            lines.append(content)

        full_path.write_text("\n".join(lines))
        return full_path

    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from note content. Returns {} if none."""
        if not content.startswith("---"):
            return {}
        end = content.find("---", 3)
        if end == -1:
            return {}
        try:
            import yaml
            return yaml.safe_load(content[3:end]) or {}
        except Exception:
            return {}

    def find_by_tag(self, tag: str) -> list[dict]:
        """Find all notes with a specific tag in frontmatter."""
        if not self.config.notes_dir.exists():
            return []
        results = []
        for f in sorted(self.config.notes_dir.rglob("*.md")):
            content = f.read_text()
            meta = self._parse_frontmatter(content)
            tags = meta.get("tags", [])
            if isinstance(tags, list) and tag in tags:
                rel = f.relative_to(self.config.notes_dir)
                results.append({
                    "path": str(rel),
                    "name": f.stem,
                    "tags": tags,
                })
        return results

    def find_related(self, topic: str, ledger=None) -> dict:
        """Find everything related to a topic across notes, documents, and transactions."""
        topic_lower = topic.lower()
        result = {"notes": [], "documents": [], "transactions": []}

        # 1. Search notes
        for note in self.search_notes(topic):
            result["notes"].append({
                "path": note["path"],
                "excerpt": note["matches"][0] if note["matches"] else "",
            })

        # 2. Search documents by filename
        if self.config.documents_dir.exists():
            for f in self.config.documents_dir.rglob("*"):
                if f.is_file() and topic_lower in f.name.lower():
                    rel = f.relative_to(self.config.documents_dir)
                    result["documents"].append({
                        "path": str(rel),
                        "name": f.name,
                    })

        # 3. Search transactions if ledger provided
        if ledger is not None:
            from beancount.core import data as bdata
            entries, _, _ = ledger.load()
            for entry in entries:
                if not isinstance(entry, bdata.Transaction):
                    continue
                searchable = f"{entry.payee or ''} {entry.narration or ''}".lower()
                if topic_lower in searchable:
                    for posting in entry.postings:
                        if posting.units:
                            result["transactions"].append({
                                "date": entry.date.isoformat(),
                                "payee": entry.payee or "",
                                "narration": entry.narration or "",
                                "amount": abs(posting.units.number),
                                "currency": posting.units.currency,
                            })
                            break  # one posting per transaction is enough

        return result
