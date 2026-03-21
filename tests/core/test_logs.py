import yaml
from quidclaw.config import QuidClawConfig
from quidclaw.core.logs import AuditLogger


def test_log_event_creates_file(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.logs_dir.mkdir(parents=True)
    logger = AuditLogger(config)
    event_id = logger.log_event(
        action="import",
        source={"type": "email", "path": "sources/my-email/test"},
    )
    assert event_id.startswith("evt_")
    log_files = list(config.logs_dir.glob("*.yaml"))
    assert len(log_files) == 1
    content = yaml.safe_load(log_files[0].read_text())
    assert content["action"] == "import"
    assert content["source"]["type"] == "email"
    assert content["id"] == event_id


def test_log_event_with_extra_fields(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.logs_dir.mkdir(parents=True)
    logger = AuditLogger(config)
    logger.log_event(
        action="import",
        source={"type": "inbox_file", "path": "inbox/test.csv"},
        extracted={"transactions_found": 10, "transactions_recorded": 8},
        archived_to=["documents/2026/03/test.csv"],
    )
    log_files = list(config.logs_dir.glob("*.yaml"))
    content = yaml.safe_load(log_files[0].read_text())
    assert content["extracted"]["transactions_found"] == 10
    assert content["archived_to"] == ["documents/2026/03/test.csv"]


def test_log_event_no_filename_collision(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.logs_dir.mkdir(parents=True)
    logger = AuditLogger(config)
    ids = set()
    for _ in range(10):
        event_id = logger.log_event(action="import", source={"type": "test"})
        ids.add(event_id)
    assert len(ids) == 10
    assert len(list(config.logs_dir.glob("*.yaml"))) == 10


def test_log_event_creates_logs_dir(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    logger = AuditLogger(config)
    logger.log_event(action="test", source={"type": "test"})
    assert config.logs_dir.is_dir()


def test_list_logs_empty(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    logger = AuditLogger(config)
    assert logger.list_logs() == []


def test_list_logs_returns_multiple(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.logs_dir.mkdir(parents=True)
    logger = AuditLogger(config)
    logger.log_event(action="first", source={"type": "test"})
    logger.log_event(action="second", source={"type": "test"})
    logs = logger.list_logs()
    assert len(logs) == 2
    actions = {log["action"] for log in logs}
    assert actions == {"first", "second"}


def test_list_logs_respects_limit(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.logs_dir.mkdir(parents=True)
    logger = AuditLogger(config)
    for i in range(5):
        logger.log_event(action=f"event_{i}", source={"type": "test"})
    logs = logger.list_logs(limit=3)
    assert len(logs) == 3
