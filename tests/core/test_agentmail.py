import yaml
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from quidclaw.config import QuidClawConfig
from quidclaw.core.sources.agentmail import AgentMailSource, sanitize_slug


def test_sanitize_slug():
    assert sanitize_slug("招商银行信用卡中心") == "招商银行信用卡中心"
    assert sanitize_slug("user/name:test") == "user-name-test"
    assert sanitize_slug("a" * 100) == "a" * 50
    assert "/" not in sanitize_slug("path/with/slashes")


def test_provider_name():
    assert AgentMailSource.provider_name() == "agentmail"


def _make_source(tmp_path, **overrides):
    config = QuidClawConfig(data_dir=tmp_path)
    config.sources_dir.mkdir(parents=True)
    source_config = {
        "provider": "agentmail",
        "api_key": "test_key",
        "inbox_id": "test@agentmail.to",
        **overrides,
    }
    return AgentMailSource("test-email", source_config, config)


def _make_mock_message(message_id="msg_1", from_addr="bank@test.com",
                        from_name="Test Bank", subject="Statement",
                        preview="Hello", attachments=None):
    msg = MagicMock()
    msg.message_id = message_id
    msg.from_ = f"{from_name} <{from_addr}>"
    msg.to = ["test@agentmail.to"]
    msg.subject = subject
    msg.preview = preview
    msg.timestamp = datetime(2026, 3, 21, 18, 35)
    msg.labels = ["received", "unread"]
    msg.attachments = attachments or []
    msg.cc = None
    msg.bcc = None
    msg.in_reply_to = None
    return msg


@patch("quidclaw.core.sources.agentmail.AgentMail")
def test_sync_downloads_email(MockAgentMail, tmp_path):
    source = _make_source(tmp_path)
    mock_client = MockAgentMail.return_value
    mock_msg = _make_mock_message()

    mock_list = MagicMock()
    mock_list.messages = [mock_msg]
    mock_client.inboxes.messages.list.return_value = mock_list

    mock_full = MagicMock()
    mock_full.text = "Hello world"
    mock_full.html = "<p>Hello</p>"
    mock_full.attachments = []
    mock_full.message_id = "msg_1"
    mock_full.from_ = "Test Bank <bank@test.com>"
    mock_full.to = ["test@agentmail.to"]
    mock_full.subject = "Statement"
    mock_full.timestamp = datetime(2026, 3, 21, 18, 35)
    mock_full.labels = ["received", "unread"]
    mock_full.cc = None
    mock_full.bcc = None
    mock_client.inboxes.messages.get.return_value = mock_full

    result = source.sync()

    assert result.items_fetched == 1
    assert result.errors == []
    email_dirs = [d for d in source.config.source_dir("test-email").iterdir()
                  if d.is_dir() and not d.name.startswith(".")]
    assert len(email_dirs) == 1
    envelope = yaml.safe_load((email_dirs[0] / "envelope.yaml").read_text())
    assert envelope["message_id"] == "msg_1"
    assert envelope["subject"] == "Statement"
    assert envelope["status"] == "unprocessed"
    assert (email_dirs[0] / "body.txt").read_text() == "Hello world"
    assert (email_dirs[0] / "body.html").read_text() == "<p>Hello</p>"


@patch("quidclaw.core.sources.agentmail.AgentMail")
def test_sync_idempotent(MockAgentMail, tmp_path):
    source = _make_source(tmp_path)
    mock_client = MockAgentMail.return_value
    mock_msg = _make_mock_message()

    mock_list = MagicMock()
    mock_list.messages = [mock_msg]
    mock_client.inboxes.messages.list.return_value = mock_list

    mock_full = MagicMock()
    mock_full.text = "Hello"
    mock_full.html = None
    mock_full.attachments = []
    mock_full.message_id = "msg_1"
    mock_full.from_ = "Test Bank <bank@test.com>"
    mock_full.to = ["test@agentmail.to"]
    mock_full.subject = "Statement"
    mock_full.timestamp = datetime(2026, 3, 21, 18, 35)
    mock_full.labels = ["received"]
    mock_full.cc = None
    mock_full.bcc = None
    mock_client.inboxes.messages.get.return_value = mock_full

    source.sync()
    result = source.sync()

    assert result.items_fetched == 0
    email_dirs = [d for d in source.config.source_dir("test-email").iterdir()
                  if d.is_dir() and not d.name.startswith(".")]
    assert len(email_dirs) == 1
    mock_client.inboxes.messages.get.assert_called_once()


@patch("quidclaw.core.sources.agentmail.AgentMail")
def test_sync_updates_state(MockAgentMail, tmp_path):
    source = _make_source(tmp_path)
    mock_client = MockAgentMail.return_value
    mock_list = MagicMock()
    mock_list.messages = []
    mock_client.inboxes.messages.list.return_value = mock_list

    source.sync()

    state_file = source.config.source_state_file("test-email")
    assert state_file.exists()
    state = yaml.safe_load(state_file.read_text())
    assert "last_sync" in state


def test_status_no_state(tmp_path):
    source = _make_source(tmp_path)
    status = source.status()
    assert status["last_sync"] is None
    assert status["total_synced"] == 0


@patch("quidclaw.core.sources.agentmail.AgentMail")
def test_provision_creates_inbox(MockAgentMail, tmp_path):
    source = _make_source(tmp_path, inbox_id="")
    mock_client = MockAgentMail.return_value
    mock_inbox = MagicMock()
    mock_inbox.email = "random123@agentmail.to"
    mock_client.inboxes.create.return_value = mock_inbox

    result = source.provision()
    assert result["inbox_id"] == "random123@agentmail.to"
