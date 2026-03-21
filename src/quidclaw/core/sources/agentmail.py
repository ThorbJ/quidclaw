"""AgentMail data source provider for QuidClaw.

Forwards bills/statements to a dedicated AgentMail inbox and syncs them locally.
Emails are stored as packages in sources/{source_name}/{timestamp}_{sender}/
with envelope.yaml, body.txt, body.html, and an attachments/ directory.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from quidclaw.config import QuidClawConfig
from quidclaw.core.sources.base import DataSource, SyncResult
from quidclaw.core.sources.registry import register_provider

# Lazy import — agentmail is an optional dependency
AgentMail = None


def _ensure_agentmail():
    """Lazily import agentmail.AgentMail, raising a helpful error if missing."""
    global AgentMail
    if AgentMail is None:
        try:
            from agentmail import AgentMail as _AgentMail
            AgentMail = _AgentMail
        except ImportError as exc:
            raise ImportError(
                "The 'agentmail' package is required for the agentmail provider. "
                "Install it with: pip install agentmail"
            ) from exc
    return AgentMail


_UNSAFE_CHARS = re.compile(r'[/:\\<>"|?*]')
_MAX_SLUG_LEN = 50


def sanitize_slug(text: str) -> str:
    """Replace filesystem-unsafe characters with '-' and truncate to 50 chars."""
    slug = _UNSAFE_CHARS.sub("-", text)
    return slug[:_MAX_SLUG_LEN]


def _parse_from(from_str: str) -> tuple[str, str]:
    """Parse 'Display Name <email@example.com>' into (name, email).

    Falls back to (from_str, from_str) if the pattern does not match.
    """
    if from_str is None:
        return ("", "")
    m = re.match(r"^(.*?)\s*<([^>]+)>$", from_str.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return from_str.strip(), from_str.strip()


@register_provider
class AgentMailSource(DataSource):
    """DataSource implementation backed by an AgentMail inbox."""

    @staticmethod
    def provider_name() -> str:
        return "agentmail"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        """Return an authenticated AgentMail client."""
        AgentMailCls = _ensure_agentmail()
        return AgentMailCls(api_key=self.source_config["api_key"])

    def _load_state(self) -> dict:
        state_file = self.config.source_state_file(self.source_name)
        if state_file.exists():
            return yaml.safe_load(state_file.read_text()) or {}
        return {}

    def _save_state(self, state: dict) -> None:
        state_file = self.config.source_state_file(self.source_name)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(yaml.dump(state, default_flow_style=False, allow_unicode=True))

    def _known_message_ids(self) -> set[str]:
        """Return the set of message_ids already stored on disk."""
        source_dir = self.config.source_dir(self.source_name)
        if not source_dir.exists():
            return set()
        ids: set[str] = set()
        for envelope in source_dir.glob("*/envelope.yaml"):
            try:
                data = yaml.safe_load(envelope.read_text()) or {}
                mid = data.get("message_id")
                if mid:
                    ids.add(mid)
            except Exception:
                pass
        return ids

    def _email_dir_exists(self, message_id: str) -> bool:
        return message_id in self._known_message_ids()

    def _make_email_dir(self, msg) -> Path:
        """Create and return a unique directory for one email message."""
        ts = msg.timestamp
        if isinstance(ts, datetime):
            ts_str = ts.strftime("%Y%m%d_%H%M%S")
        else:
            ts_str = str(ts).replace(":", "").replace("-", "").replace(" ", "_")[:15]

        sender_name, sender_email = _parse_from(msg.from_)
        sender_slug = sanitize_slug(sender_name or sender_email or "unknown")

        dir_name = f"{ts_str}_{sender_slug}"
        email_dir = self.config.source_dir(self.source_name) / dir_name
        # If a collision occurs, append the message_id suffix
        if email_dir.exists():
            short_id = sanitize_slug(msg.message_id)[:12]
            email_dir = self.config.source_dir(self.source_name) / f"{dir_name}_{short_id}"
        email_dir.mkdir(parents=True, exist_ok=True)
        return email_dir

    def _store_message(self, msg, client=None) -> str:
        """Persist a full message to disk and return the directory path as string."""
        email_dir = self._make_email_dir(msg)

        # Build envelope metadata
        sender_name, sender_email = _parse_from(msg.from_)
        to_list = msg.to if isinstance(msg.to, list) else ([msg.to] if msg.to else [])
        envelope = {
            "message_id": msg.message_id,
            "from_name": sender_name,
            "from_email": sender_email,
            "to": to_list,
            "cc": msg.cc,
            "bcc": msg.bcc,
            "subject": msg.subject or "",
            "timestamp": msg.timestamp.isoformat() if isinstance(msg.timestamp, datetime) else str(msg.timestamp),
            "labels": list(msg.labels) if msg.labels else [],
            "status": "unprocessed",
        }
        (email_dir / "envelope.yaml").write_text(
            yaml.dump(envelope, default_flow_style=False, allow_unicode=True)
        )

        # Body
        if msg.text:
            (email_dir / "body.txt").write_text(msg.text, encoding="utf-8")
        if msg.html:
            (email_dir / "body.html").write_text(msg.html, encoding="utf-8")

        # Attachments — download via get_attachment() → download_url
        attachments = msg.attachments or []
        if attachments and client:
            att_dir = email_dir / "attachments"
            att_dir.mkdir(exist_ok=True)
            inbox_id = self.source_config.get("inbox_id", "")
            for att in attachments:
                filename = sanitize_slug(att.filename or "attachment")
                att_path = att_dir / filename
                try:
                    att_resp = client.inboxes.messages.get_attachment(
                        inbox_id=inbox_id,
                        message_id=msg.message_id,
                        attachment_id=att.attachment_id,
                    )
                    if att_resp.download_url:
                        import urllib.request
                        data = urllib.request.urlopen(att_resp.download_url).read()
                        att_path.write_bytes(data)
                except Exception:
                    pass  # Attachment download failure is non-fatal

        return str(email_dir)

    # ------------------------------------------------------------------
    # DataSource interface
    # ------------------------------------------------------------------

    def sync(self) -> SyncResult:
        client = self._get_client()
        inbox_id = self.source_config.get("inbox_id", "")
        errors: list[str] = []
        items_stored: list[str] = []

        # Fetch message listing
        try:
            listing = client.inboxes.messages.list(inbox_id=inbox_id)
            messages = listing.messages or []
        except Exception as exc:
            errors.append(f"Failed to list messages: {exc}")
            messages = []

        known_ids = self._known_message_ids()
        new_messages = [m for m in messages if m.message_id not in known_ids]

        for msg in new_messages:
            try:
                full_msg = client.inboxes.messages.get(
                    inbox_id=inbox_id, message_id=msg.message_id
                )
                path = self._store_message(full_msg, client=client)
                items_stored.append(path)
            except Exception as exc:
                errors.append(f"Failed to fetch/store message {msg.message_id}: {exc}")

        # Persist state
        state = self._load_state()
        state["last_sync"] = datetime.now(timezone.utc).isoformat()
        state["total_synced"] = state.get("total_synced", 0) + len(items_stored)
        self._save_state(state)

        return SyncResult(
            source_name=self.source_name,
            provider=self.provider_name(),
            items_fetched=len(new_messages),
            items_stored=items_stored,
            last_sync=datetime.now(timezone.utc),
            errors=errors,
        )

    def status(self) -> dict:
        state = self._load_state()
        source_dir = self.config.source_dir(self.source_name)

        # Count unprocessed emails by checking envelope status
        unprocessed = 0
        if source_dir.exists():
            for envelope in source_dir.glob("*/envelope.yaml"):
                try:
                    data = yaml.safe_load(envelope.read_text()) or {}
                    if data.get("status") == "unprocessed":
                        unprocessed += 1
                except Exception:
                    pass

        return {
            "source_name": self.source_name,
            "provider": self.provider_name(),
            "inbox_id": self.source_config.get("inbox_id", ""),
            "last_sync": state.get("last_sync"),
            "total_synced": state.get("total_synced", 0),
            "unprocessed": unprocessed,
        }

    def provision(self) -> dict:
        """If inbox_id is empty, create a new AgentMail inbox and return updated config."""
        inbox_id = self.source_config.get("inbox_id", "")
        if inbox_id:
            return self.source_config

        client = self._get_client()
        username = self.source_config.get("username") or None
        display_name = self.source_config.get("display_name") or None

        try:
            from agentmail.inboxes.types import CreateInboxRequest
        except ImportError:
            # Fallback: try calling without the typed request
            inbox = client.inboxes.create()
            updated = dict(self.source_config)
            updated["inbox_id"] = inbox.email
            return updated

        inbox = client.inboxes.create(
            request=CreateInboxRequest(username=username, display_name=display_name)
        )
        updated = dict(self.source_config)
        updated["inbox_id"] = inbox.email
        return updated
