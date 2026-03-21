# Data Sources & Audit Trail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add extensible data source architecture (email via AgentMail first), complete audit trail with processing logs and source metadata on transactions, and workflow integration for onboarding and daily routine.

**Architecture:** Three layers of change: (1) core library gains `sources/`, `logs.py`, and metadata support on transactions, (2) CLI gains source management and sync commands, (3) workflows guide AI through email setup, checking, and daily routines. All new directories (`sources/`, `logs/`) are created by `Ledger.init()`.

**Tech Stack:** Python, Click CLI, PyYAML, AgentMail SDK (optional dependency), Beancount V3

**Spec:** `docs/superpowers/specs/2026-03-21-data-sources-and-audit-trail-design.md`

---

### Task 1: Extend `QuidClawConfig` with source and log path properties

**Files:**
- Modify: `src/quidclaw/config.py`
- Test: `tests/core/test_config.py` (create)

- [ ] **Step 1: Write tests for new config properties and source management methods**

```python
# tests/core/test_config.py
import yaml
from quidclaw.config import QuidClawConfig


def test_sources_dir_property(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.sources_dir == tmp_path / "sources"


def test_logs_dir_property(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.logs_dir == tmp_path / "logs"


def test_source_dir(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.source_dir("my-email") == tmp_path / "sources" / "my-email"


def test_source_state_file(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    assert config.source_state_file("my-email") == tmp_path / "sources" / "my-email" / ".state.yaml"


def test_get_sources_empty(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.config_dir.mkdir(parents=True)
    assert config.get_sources() == {}


def test_add_and_get_source(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.config_dir.mkdir(parents=True)
    config.add_source("my-email", {"provider": "agentmail", "api_key": "test123"})
    source = config.get_source("my-email")
    assert source["provider"] == "agentmail"
    assert source["api_key"] == "test123"


def test_add_source_preserves_existing(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.config_dir.mkdir(parents=True)
    config.set_setting("operating_currency", "CNY")
    config.add_source("s1", {"provider": "agentmail"})
    config.add_source("s2", {"provider": "other"})
    assert config.get_setting("operating_currency") == "CNY"
    assert len(config.get_sources()) == 2


def test_remove_source(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.config_dir.mkdir(parents=True)
    config.add_source("my-email", {"provider": "agentmail"})
    config.remove_source("my-email")
    assert config.get_source("my-email") is None


def test_remove_source_not_found(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    config.config_dir.mkdir(parents=True)
    import pytest
    with pytest.raises(KeyError, match="Source not found"):
        config.remove_source("nonexistent")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_config.py -v`
Expected: FAIL — methods don't exist yet

- [ ] **Step 3: Implement config extensions**

Add to `src/quidclaw/config.py` — new properties and methods on `QuidClawConfig`:

```python
@property
def sources_dir(self) -> Path:
    return self.data_dir / "sources"

@property
def logs_dir(self) -> Path:
    return self.data_dir / "logs"

def source_dir(self, source_name: str) -> Path:
    return self.sources_dir / source_name

def source_state_file(self, source_name: str) -> Path:
    return self.source_dir(source_name) / ".state.yaml"

def get_sources(self) -> dict:
    return self.load_settings().get("data_sources", {})

def get_source(self, name: str) -> dict | None:
    return self.get_sources().get(name)

def add_source(self, name: str, source_config: dict) -> None:
    settings = self.load_settings()
    settings.setdefault("data_sources", {})[name] = source_config
    self.save_settings(settings)

def remove_source(self, name: str) -> None:
    settings = self.load_settings()
    sources = settings.get("data_sources", {})
    if name not in sources:
        raise KeyError(f"Source not found: {name}")
    del sources[name]
    self.save_settings(settings)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_config.py -v`
Expected: all PASS

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/quidclaw/config.py tests/core/test_config.py
git commit -m "feat: add data source config API and path properties"
```

---

### Task 2: Add `sources/` and `logs/` to `Ledger.init()` and add `ensure_dirs()`

**Files:**
- Modify: `src/quidclaw/core/ledger.py`
- Modify: `tests/core/test_ledger.py`

- [ ] **Step 1: Write tests for new directories and ensure_dirs**

Add to `tests/core/test_ledger.py`:

```python
def test_init_creates_sources_and_logs_directories(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    assert (tmp_path / "sources").is_dir()
    assert (tmp_path / "logs").is_dir()


def test_ensure_dirs_creates_missing_directories(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    # Simulate an old project that's missing sources/ and logs/
    import shutil
    shutil.rmtree(tmp_path / "sources")
    shutil.rmtree(tmp_path / "logs")
    assert not (tmp_path / "sources").exists()
    ledger.ensure_dirs()
    assert (tmp_path / "sources").is_dir()
    assert (tmp_path / "logs").is_dir()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_ledger.py::test_init_creates_sources_and_logs_directories tests/core/test_ledger.py::test_ensure_dirs_creates_missing_directories -v`
Expected: FAIL

- [ ] **Step 3: Implement changes in ledger.py**

In `Ledger.init()`, add after the existing `mkdir` calls:

```python
self.config.sources_dir.mkdir(exist_ok=True)
self.config.logs_dir.mkdir(exist_ok=True)
```

Add new method:

```python
def ensure_dirs(self) -> None:
    """Ensure all expected directories exist. Used by upgrade for older projects."""
    for d in [self.config.ledger_dir, self.config.inbox_dir,
              self.config.documents_dir, self.config.notes_dir,
              self.config.reports_dir, self.config.sources_dir,
              self.config.logs_dir]:
        d.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_ledger.py -v`
Expected: all PASS

- [ ] **Step 5: Update existing test that checks directory creation**

Update `test_init_creates_all_directories` in `tests/core/test_ledger.py` to also assert `sources` and `logs`. Similarly update `TestInit.test_creates_directories` in `tests/test_cli.py`.

- [ ] **Step 6: Run full test suite**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add src/quidclaw/core/ledger.py tests/core/test_ledger.py tests/test_cli.py
git commit -m "feat: add sources/ and logs/ directories to init, add ensure_dirs()"
```

---

### Task 3: Add `--meta` support to `TransactionManager` and `add-txn` CLI

**Files:**
- Modify: `src/quidclaw/core/transactions.py`
- Modify: `src/quidclaw/cli.py`
- Modify: `tests/core/test_transactions.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write core test for metadata on transactions**

Add to `tests/core/test_transactions.py`:

```python
def test_add_transaction_with_metadata(tmp_path):
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="McDonald's",
        narration="Lunch",
        postings=[
            {"account": "Expenses:Food", "amount": "45.00", "currency": "CNY"},
            {"account": "Assets:Bank:BOC", "amount": "-45.00", "currency": "CNY"},
        ],
        metadata={"source": "email:my-email/test", "import-id": "evt_123"},
    )
    month_file = ledger.config.month_bean(2026, 3)
    content = month_file.read_text()
    assert 'source: "email:my-email/test"' in content
    assert 'import-id: "evt_123"' in content
    # Verify beancount can still parse it
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    txns = [e for e in entries if e.__class__.__name__ == "Transaction"]
    assert len(txns) == 1


def test_add_transaction_without_metadata_unchanged(tmp_path):
    """Existing behavior is preserved when metadata is not provided."""
    ledger = make_ledger_with_accounts(tmp_path)
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 14),
        payee="Test",
        narration="No meta",
        postings=[
            {"account": "Expenses:Food", "amount": "10.00", "currency": "CNY"},
            {"account": "Assets:Bank:BOC"},
        ],
    )
    month_file = ledger.config.month_bean(2026, 3)
    content = month_file.read_text()
    assert "source:" not in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_transactions.py::test_add_transaction_with_metadata -v`
Expected: FAIL — `metadata` parameter not accepted

- [ ] **Step 3: Implement metadata support in TransactionManager**

Modify `src/quidclaw/core/transactions.py` `add_transaction`:

```python
def add_transaction(
    self,
    date: datetime.date,
    payee: str,
    narration: str,
    postings: list[dict],
    metadata: dict | None = None,
) -> None:
    lines = [f'{date} * "{payee}" "{narration}"\n']
    if metadata:
        for key, value in metadata.items():
            lines.append(f'  {key}: "{value}"\n')
    for p in postings:
        account = p["account"]
        amount = p.get("amount")
        currency = p.get("currency")
        if amount and currency:
            lines.append(f"  {account}  {amount} {currency}\n")
        elif amount:
            lines.append(f"  {account}  {amount}\n")
        else:
            lines.append(f"  {account}\n")
    lines.append("\n")
    text = "".join(lines)
    self.ledger.ensure_month_file(date.year, date.month)
    month_file = self.ledger.config.month_bean(date.year, date.month)
    self.ledger.append(month_file, text)
```

- [ ] **Step 4: Run core tests**

Run: `pytest tests/core/test_transactions.py -v`
Expected: all PASS

- [ ] **Step 5: Add CLI test for --meta flag**

Add to `tests/test_cli.py` `TestTransactions`:

```python
def test_add_transaction_with_meta(self, tmp_path):
    runner = _init_project(tmp_path)
    posting1 = json.dumps({"account": "Expenses:Food", "amount": "50", "currency": "CNY"})
    posting2 = json.dumps({"account": "Assets:Bank:Checking", "amount": "-50", "currency": "CNY"})
    meta = json.dumps({"source": "test-source", "import-id": "evt_test"})
    result = runner.invoke(
        main, [
            "add-txn",
            "--date", "2026-03-15",
            "--payee", "Restaurant",
            "--narration", "Lunch",
            "--posting", posting1,
            "--posting", posting2,
            "--meta", meta,
        ],
        catch_exceptions=False, env=_env(tmp_path),
    )
    assert result.exit_code == 0
    txn_file = tmp_path / "ledger" / "2026" / "2026-03.bean"
    content = txn_file.read_text()
    assert 'source: "test-source"' in content
    assert 'import-id: "evt_test"' in content
```

- [ ] **Step 6: Add --meta option to CLI add-txn command**

In `src/quidclaw/cli.py`, modify the `add_txn` command:

```python
@main.command("add-txn")
@click.option("--date", required=True, help="Transaction date (YYYY-MM-DD)")
@click.option("--payee", required=True, help="Payee name")
@click.option("--narration", default="", help="Description")
@click.option("--posting", multiple=True, required=True, help='Posting as JSON')
@click.option("--meta", default=None, help='Metadata as JSON: \'{"source":"..."}\'')
def add_txn(date, payee, narration, posting, meta):
    import datetime as dt
    from quidclaw.core.transactions import TransactionManager
    ledger = get_ledger()
    mgr = TransactionManager(ledger)
    postings = [json.loads(p) for p in posting]
    parsed_date = dt.date.fromisoformat(date)
    metadata = json.loads(meta) if meta else None
    mgr.add_transaction(parsed_date, payee, narration, postings, metadata)
    click.echo(f"Recorded transaction: {date} {payee}")
```

- [ ] **Step 7: Run all tests**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add src/quidclaw/core/transactions.py src/quidclaw/cli.py tests/core/test_transactions.py tests/test_cli.py
git commit -m "feat: add --meta support for source traceability on transactions"
```

---

### Task 4: Create `AuditLogger` (`core/logs.py`)

**Files:**
- Create: `src/quidclaw/core/logs.py`
- Create: `tests/core/test_logs.py`

- [ ] **Step 1: Write tests**

```python
# tests/core/test_logs.py
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
    # Don't create logs_dir — log_event should create it
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_logs.py -v`
Expected: FAIL — module doesn't exist

- [ ] **Step 3: Implement AuditLogger**

```python
# src/quidclaw/core/logs.py
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
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/core/test_logs.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/core/logs.py tests/core/test_logs.py
git commit -m "feat: add AuditLogger for processing event tracking"
```

---

### Task 5: Create DataSource ABC and provider registry

**Files:**
- Create: `src/quidclaw/core/sources/__init__.py`
- Create: `src/quidclaw/core/sources/base.py`
- Create: `src/quidclaw/core/sources/registry.py`
- Create: `tests/core/test_sources.py`

- [ ] **Step 1: Write tests for ABC, registry, and factory**

```python
# tests/core/test_sources.py
import pytest
from quidclaw.config import QuidClawConfig
from quidclaw.core.sources.base import DataSource, SyncResult
from quidclaw.core.sources.registry import (
    PROVIDERS,
    register_provider,
    get_provider,
    create_source,
)


class FakeSource(DataSource):
    @staticmethod
    def provider_name() -> str:
        return "fake"

    def sync(self) -> SyncResult:
        return SyncResult(
            source_name=self.source_name,
            provider="fake",
            items_fetched=0,
            items_stored=[],
            last_sync=None,
            errors=[],
        )

    def status(self) -> dict:
        return {"last_sync": None, "total_synced": 0}


def test_datasource_abc_enforces_methods():
    """Cannot instantiate DataSource without implementing abstract methods."""
    with pytest.raises(TypeError):
        DataSource(source_name="x", source_config={}, config=None)


def test_register_and_get_provider():
    register_provider(FakeSource)
    assert get_provider("fake") is FakeSource
    # Cleanup
    del PROVIDERS["fake"]


def test_get_provider_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("nonexistent")


def test_create_source_factory(tmp_path):
    register_provider(FakeSource)
    config = QuidClawConfig(data_dir=tmp_path)
    source = create_source("test", {"provider": "fake"}, config)
    assert isinstance(source, FakeSource)
    assert source.source_name == "test"
    assert source.config is config
    del PROVIDERS["fake"]


def test_provision_default_returns_config_unchanged(tmp_path):
    register_provider(FakeSource)
    config = QuidClawConfig(data_dir=tmp_path)
    source_config = {"provider": "fake", "key": "value"}
    source = FakeSource("test", source_config, config)
    result = source.provision()
    assert result is source_config
    del PROVIDERS["fake"]


def test_sync_result_dataclass():
    from datetime import datetime
    result = SyncResult(
        source_name="test",
        provider="fake",
        items_fetched=3,
        items_stored=["a", "b", "c"],
        last_sync=datetime(2026, 3, 21),
        errors=[],
    )
    assert result.items_fetched == 3
    assert len(result.items_stored) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_sources.py -v`
Expected: FAIL — modules don't exist

- [ ] **Step 3: Create source files**

`src/quidclaw/core/sources/__init__.py`:
```python
```

`src/quidclaw/core/sources/base.py`:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from quidclaw.config import QuidClawConfig


@dataclass
class SyncResult:
    """Result of a sync operation."""
    source_name: str
    provider: str
    items_fetched: int
    items_stored: list[str]
    last_sync: datetime | None
    errors: list[str]


class DataSource(ABC):
    """Base class for all data sources."""

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
```

`src/quidclaw/core/sources/registry.py`:
```python
import os

from quidclaw.config import QuidClawConfig
from quidclaw.core.sources.base import DataSource

PROVIDERS: dict[str, type[DataSource]] = {}


def register_provider(cls: type[DataSource]) -> type[DataSource]:
    PROVIDERS[cls.provider_name()] = cls
    return cls


def get_provider(provider_name: str) -> type[DataSource]:
    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider_name}. Available: {list(PROVIDERS.keys())}"
        )
    return PROVIDERS[provider_name]


def resolve_env_refs(source_config: dict) -> dict:
    """Resolve env:VAR_NAME references in config values."""
    resolved = {}
    for key, value in source_config.items():
        if isinstance(value, str) and value.startswith("env:"):
            env_var = value[4:]
            resolved[key] = os.environ.get(env_var, "")
        else:
            resolved[key] = value
    return resolved


def create_source(
    source_name: str, source_config: dict, config: QuidClawConfig
) -> DataSource:
    provider_name = source_config["provider"]
    cls = get_provider(provider_name)
    resolved = resolve_env_refs(source_config)
    return cls(source_name=source_name, source_config=resolved, config=config)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/core/test_sources.py -v`
Expected: all PASS

- [ ] **Step 5: Add test for env: resolution**

```python
# Add to tests/core/test_sources.py
def test_resolve_env_refs(monkeypatch):
    from quidclaw.core.sources.registry import resolve_env_refs
    monkeypatch.setenv("MY_KEY", "secret123")
    result = resolve_env_refs({"api_key": "env:MY_KEY", "provider": "test"})
    assert result["api_key"] == "secret123"
    assert result["provider"] == "test"


def test_resolve_env_refs_missing_var(monkeypatch):
    from quidclaw.core.sources.registry import resolve_env_refs
    monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
    result = resolve_env_refs({"api_key": "env:NONEXISTENT_VAR"})
    assert result["api_key"] == ""  # Returns empty string for missing vars
```

- [ ] **Step 6: Run all tests**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add src/quidclaw/core/sources/ tests/core/test_sources.py
git commit -m "feat: add DataSource ABC, provider registry, and env: resolution"
```

---

### Task 6: Implement AgentMail provider

**Files:**
- Create: `src/quidclaw/core/sources/agentmail.py`
- Create: `tests/core/test_agentmail.py`

- [ ] **Step 1: Write tests using mocked AgentMail SDK**

```python
# tests/core/test_agentmail.py
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

    # Mock list messages
    mock_list = MagicMock()
    mock_list.messages = [mock_msg]
    mock_client.inboxes.messages.list.return_value = mock_list

    # Mock get message (full content)
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
    # Check email directory was created
    email_dirs = [d for d in source.config.source_dir("test-email").iterdir()
                  if d.is_dir() and not d.name.startswith(".")]
    assert len(email_dirs) == 1
    # Check envelope.yaml
    envelope = yaml.safe_load((email_dirs[0] / "envelope.yaml").read_text())
    assert envelope["message_id"] == "msg_1"
    assert envelope["subject"] == "Statement"
    assert envelope["status"] == "unprocessed"
    # Check body.txt
    assert (email_dirs[0] / "body.txt").read_text() == "Hello world"
    # Check body.html
    assert (email_dirs[0] / "body.html").read_text() == "<p>Hello</p>"


@patch("quidclaw.core.sources.agentmail.AgentMail")
def test_sync_idempotent(MockAgentMail, tmp_path):
    """Second sync should not duplicate emails."""
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
    # Verify get was called only once (first sync), not twice
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_agentmail.py -v`
Expected: FAIL — module doesn't exist

- [ ] **Step 3: Implement AgentMailSource**

```python
# src/quidclaw/core/sources/agentmail.py
import re
from datetime import datetime

import yaml

from quidclaw.core.sources.base import DataSource, SyncResult
from quidclaw.core.sources.registry import register_provider


def sanitize_slug(text: str) -> str:
    """Sanitize text for use in directory names."""
    text = re.sub(r'[/:\\<>"|?*]', "-", text)
    return text[:50]


def _parse_from(from_str: str) -> tuple[str, str]:
    """Parse 'Name <email>' into (name, email). Returns (from_str, '') if no match."""
    match = re.match(r"(.+?)\s*<(.+?)>", from_str or "")
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return from_str or "", ""


@register_provider
class AgentMailSource(DataSource):
    @staticmethod
    def provider_name() -> str:
        return "agentmail"

    def _get_client(self):
        try:
            from agentmail import AgentMail
        except ImportError:
            raise ImportError(
                "AgentMail SDK not installed. Run: pip install agentmail"
            )
        return AgentMail(api_key=self.source_config["api_key"])

    def _load_state(self) -> dict:
        state_file = self.config.source_state_file(self.source_name)
        if state_file.exists():
            return yaml.safe_load(state_file.read_text()) or {}
        return {}

    def _save_state(self, state: dict) -> None:
        state_file = self.config.source_state_file(self.source_name)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(
            yaml.dump(state, default_flow_style=False, allow_unicode=True)
        )

    def _email_dir_exists(self, message_id: str) -> bool:
        """Check if we've already downloaded this email by scanning envelope files."""
        source_dir = self.config.source_dir(self.source_name)
        if not source_dir.exists():
            return False
        for d in source_dir.iterdir():
            if not d.is_dir() or d.name.startswith("."):
                continue
            envelope_file = d / "envelope.yaml"
            if envelope_file.exists():
                envelope = yaml.safe_load(envelope_file.read_text())
                if envelope and envelope.get("message_id") == message_id:
                    return True
        return False

    def sync(self) -> SyncResult:
        client = self._get_client()
        inbox_id = self.source_config["inbox_id"]
        source_dir = self.config.source_dir(self.source_name)
        source_dir.mkdir(parents=True, exist_ok=True)

        items_stored = []
        errors = []

        try:
            response = client.inboxes.messages.list(inbox_id=inbox_id)
            messages = response.messages or []
        except Exception as e:
            return SyncResult(
                source_name=self.source_name,
                provider="agentmail",
                items_fetched=0,
                items_stored=[],
                last_sync=datetime.now(),
                errors=[str(e)],
            )

        for msg in messages:
            try:
                if self._email_dir_exists(msg.message_id):
                    continue

                full_msg = client.inboxes.messages.get(
                    inbox_id=inbox_id, message_id=msg.message_id
                )

                from_name, from_addr = _parse_from(full_msg.from_)
                sender_slug = sanitize_slug(from_name or from_addr)
                ts = full_msg.timestamp
                if isinstance(ts, datetime):
                    ts_str = ts.strftime("%Y-%m-%dT%H-%M")
                else:
                    ts_str = str(ts).replace(":", "-")[:16]

                email_dir_name = f"{ts_str}_{sender_slug}"
                email_dir = source_dir / email_dir_name
                email_dir.mkdir(parents=True, exist_ok=True)

                # Save envelope
                attachments_meta = []
                for att in (full_msg.attachments or []):
                    attachments_meta.append({
                        "filename": att.filename,
                        "size": att.size,
                        "content_type": att.content_type,
                    })

                envelope = {
                    "message_id": full_msg.message_id,
                    "from": from_addr,
                    "from_name": from_name,
                    "to": full_msg.to if isinstance(full_msg.to, list) else [full_msg.to],
                    "subject": full_msg.subject,
                    "date": full_msg.timestamp.isoformat() if isinstance(full_msg.timestamp, datetime) else str(full_msg.timestamp),
                    "labels": full_msg.labels if full_msg.labels else [],
                    "attachments": attachments_meta,
                    "source_name": self.source_name,
                    "source_provider": "agentmail",
                    "synced_at": datetime.now().isoformat(),
                    "status": "unprocessed",
                }
                (email_dir / "envelope.yaml").write_text(
                    yaml.dump(envelope, default_flow_style=False, allow_unicode=True)
                )

                # Save body
                if hasattr(full_msg, "text") and full_msg.text:
                    (email_dir / "body.txt").write_text(full_msg.text)
                elif hasattr(full_msg, "preview") and full_msg.preview:
                    (email_dir / "body.txt").write_text(full_msg.preview)

                if hasattr(full_msg, "html") and full_msg.html:
                    (email_dir / "body.html").write_text(full_msg.html)

                # Save attachments
                if full_msg.attachments:
                    att_dir = email_dir / "attachments"
                    att_dir.mkdir(exist_ok=True)
                    for att in full_msg.attachments:
                        if hasattr(att, "content") and att.content:
                            (att_dir / att.filename).write_bytes(
                                att.content if isinstance(att.content, bytes)
                                else att.content.encode()
                            )

                rel_path = str(email_dir.relative_to(self.config.data_dir))
                items_stored.append(rel_path)

            except Exception as e:
                errors.append(f"Error processing {msg.message_id}: {e}")

        now = datetime.now()
        state = self._load_state()
        state["last_sync"] = now.isoformat()
        state["total_synced"] = state.get("total_synced", 0) + len(items_stored)
        self._save_state(state)

        return SyncResult(
            source_name=self.source_name,
            provider="agentmail",
            items_fetched=len(items_stored),
            items_stored=items_stored,
            last_sync=now,
            errors=errors,
        )

    def status(self) -> dict:
        state = self._load_state()
        source_dir = self.config.source_dir(self.source_name)
        unprocessed = 0
        if source_dir.exists():
            for d in source_dir.iterdir():
                if not d.is_dir() or d.name.startswith("."):
                    continue
                envelope_file = d / "envelope.yaml"
                if envelope_file.exists():
                    envelope = yaml.safe_load(envelope_file.read_text())
                    if envelope and envelope.get("status") == "unprocessed":
                        unprocessed += 1
        return {
            "last_sync": state.get("last_sync"),
            "total_synced": state.get("total_synced", 0),
            "unprocessed": unprocessed,
        }

    def provision(self) -> dict:
        client = self._get_client()
        inbox_id = self.source_config.get("inbox_id", "")
        if not inbox_id:
            from agentmail.inboxes.types import CreateInboxRequest
            username = self.source_config.get("username")
            display_name = self.source_config.get("display_name", "QuidClaw CFO")
            inbox = client.inboxes.create(
                request=CreateInboxRequest(
                    username=username,
                    display_name=display_name,
                )
            )
            updated = dict(self.source_config)
            updated["inbox_id"] = inbox.email
            return updated
        return self.source_config
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/core/test_agentmail.py -v`
Expected: all PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/quidclaw/core/sources/agentmail.py tests/core/test_agentmail.py
git commit -m "feat: implement AgentMail data source provider"
```

---

### Task 7: Add CLI commands for source management and sync

**Files:**
- Modify: `src/quidclaw/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write CLI tests**

Add to `tests/test_cli.py`:

```python
# --- Sources ---


class TestSources:
    def test_list_sources_empty(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["list-sources"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "No data sources configured" in result.output

    def test_list_sources_json_empty(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["list-sources", "--json"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == {}

    def test_remove_source_not_found(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["remove-source", "nonexistent", "--confirm"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code != 0

    def test_add_source_creates_config_entry(self, tmp_path):
        runner = _init_project(tmp_path)
        # Use a fake provider to avoid needing agentmail installed
        # We test at the config level only
        import yaml as _yaml
        result = runner.invoke(
            main, ["list-sources", "--json"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert json.loads(result.output) == {}

    def test_sync_no_sources(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["sync"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code != 0
        assert "No data sources" in result.output

    def test_sync_source_not_found(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["sync", "nonexistent"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code != 0

    def test_mark_processed(self, tmp_path):
        runner = _init_project(tmp_path)
        # Create a fake email directory with envelope
        import yaml as _yaml
        email_dir = tmp_path / "sources" / "test" / "2026-03-21_bank"
        email_dir.mkdir(parents=True)
        (email_dir / "envelope.yaml").write_text(
            _yaml.dump({"status": "unprocessed", "message_id": "msg1"})
        )
        result = runner.invoke(
            main, ["mark-processed", "test", "2026-03-21_bank"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        envelope = _yaml.safe_load((email_dir / "envelope.yaml").read_text())
        assert envelope["status"] == "processed"

    def test_mark_processed_not_found(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["mark-processed", "test", "nonexistent"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code != 0

    def test_remove_source_requires_confirm(self, tmp_path):
        runner = _init_project(tmp_path)
        # Add a source manually via config
        import yaml
        config_file = tmp_path / ".quidclaw" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump({"data_sources": {"test": {"provider": "fake"}}}))
        result = runner.invoke(
            main, ["remove-source", "test"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code != 0
        assert "confirm" in result.output.lower() or "Missing" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::TestSources -v`
Expected: FAIL — commands don't exist

- [ ] **Step 3: Implement CLI commands**

Add to `src/quidclaw/cli.py`:

```python
@main.command("add-source")
@click.argument("name")
@click.option("--provider", required=True, help="Provider type (e.g., agentmail)")
@click.option("--api-key", default=None, help="API key for the provider")
@click.option("--inbox-id", default=None, help="Inbox/mailbox ID (provider-specific)")
@click.option("--username", default=None, help="Preferred username for new inbox")
@click.option("--display-name", default=None, help="Display name for the inbox")
def add_source(name, provider, api_key, inbox_id, username, display_name):
    """Add a new data source."""
    from quidclaw.core.sources.registry import create_source
    config = get_config()
    source_config = {"provider": provider, "enabled": True}
    if api_key:
        source_config["api_key"] = api_key
    if inbox_id:
        source_config["inbox_id"] = inbox_id
    if username:
        source_config["username"] = username
    if display_name:
        source_config["display_name"] = display_name

    # Provision if needed (e.g., create mailbox)
    try:
        source = create_source(name, source_config, config)
        source_config = source.provision()
    except ImportError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    config.add_source(name, source_config)
    config.source_dir(name).mkdir(parents=True, exist_ok=True)

    inbox = source_config.get("inbox_id", "")
    click.echo(f"Added source '{name}' (provider: {provider})")
    if inbox:
        click.echo(f"  Inbox: {inbox}")


@main.command("list-sources")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_sources(as_json):
    """List configured data sources."""
    config = get_config()
    sources = config.get_sources()
    if as_json:
        click.echo(json.dumps(sources, indent=2, default=str))
    else:
        if not sources:
            click.echo("No data sources configured.")
            return
        for name, src in sources.items():
            enabled = src.get("enabled", True)
            status_str = "enabled" if enabled else "disabled"
            click.echo(f"  {name}: {src['provider']} ({status_str})")
            if src.get("inbox_id"):
                click.echo(f"    inbox: {src['inbox_id']}")


@main.command("remove-source")
@click.argument("name")
@click.option("--confirm", is_flag=True, help="Confirm removal")
def remove_source(name, confirm):
    """Remove a data source configuration."""
    if not confirm:
        click.echo("Error: Use --confirm to remove a source.", err=True)
        sys.exit(1)
    config = get_config()
    try:
        config.remove_source(name)
    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    data_dir = config.source_dir(name)
    click.echo(f"Removed source '{name}' from config.")
    if data_dir.exists():
        click.echo(f"  Synced data preserved at: {data_dir}")
        click.echo(f"  Delete manually if no longer needed.")


@main.command("sync")
@click.argument("source_name", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def sync(source_name, as_json):
    """Sync data from external sources."""
    from quidclaw.core.sources.registry import create_source
    config = get_config()
    sources = config.get_sources()

    if not sources:
        click.echo("No data sources configured. Use 'quidclaw add-source' first.")
        sys.exit(1)

    if source_name:
        src_config = config.get_source(source_name)
        if not src_config:
            click.echo(f"Error: Source '{source_name}' not found.", err=True)
            sys.exit(1)
        to_sync = {source_name: src_config}
    else:
        to_sync = {n: s for n, s in sources.items() if s.get("enabled", True)}

    all_results = []
    for name, src_config in to_sync.items():
        source = create_source(name, src_config, config)
        result = source.sync()
        all_results.append(result)
        if not as_json:
            if result.items_fetched > 0:
                click.echo(f"  {name}: {result.items_fetched} new item(s)")
            else:
                click.echo(f"  {name}: up to date")
            for err in result.errors:
                click.echo(f"    ERROR: {err}", err=True)

    if as_json:
        output = [
            {
                "source_name": r.source_name,
                "provider": r.provider,
                "items_fetched": r.items_fetched,
                "items_stored": r.items_stored,
                "last_sync": r.last_sync.isoformat() if r.last_sync else None,
                "errors": r.errors,
            }
            for r in all_results
        ]
        click.echo(json.dumps(output, indent=2))

    has_errors = any(r.errors for r in all_results)
    has_items = any(r.items_fetched > 0 for r in all_results)
    if has_errors and not has_items:
        sys.exit(1)


@main.command("mark-processed")
@click.argument("source_name")
@click.argument("email_dir")
def mark_processed(source_name, email_dir):
    """Mark an email as processed."""
    config = get_config()
    import yaml as _yaml
    email_path = config.source_dir(source_name) / email_dir
    envelope_file = email_path / "envelope.yaml"
    if not envelope_file.exists():
        click.echo(f"Error: envelope.yaml not found at {envelope_file}", err=True)
        sys.exit(1)
    envelope = _yaml.safe_load(envelope_file.read_text())
    envelope["status"] = "processed"
    envelope_file.write_text(
        _yaml.dump(envelope, default_flow_style=False, allow_unicode=True)
    )
    click.echo(f"Marked {email_dir} as processed")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_cli.py::TestSources -v`
Expected: all PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/quidclaw/cli.py tests/test_cli.py
git commit -m "feat: add CLI commands for source management and sync"
```

---

### Task 8: Add `agentmail` as optional dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add optional dependency**

Add to `pyproject.toml` under `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]
email = [
    "agentmail",
]
```

- [ ] **Step 2: Install with email extras**

Run: `pip install -e ".[email]"`

- [ ] **Step 3: Verify import works**

Run: `python -c "from quidclaw.core.sources.agentmail import AgentMailSource; print(AgentMailSource.provider_name())"`
Expected: `agentmail`

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add agentmail as optional dependency"
```

---

### Task 9: Write `check-email.md` workflow

**Files:**
- Create: `src/quidclaw/workflows/check-email.md`

- [ ] **Step 1: Write the workflow**

See spec Section 6 for the workflow structure. The workflow should:
1. Run `quidclaw sync SOURCE_NAME --json` to fetch new emails
2. List new emails for the user
3. For each unprocessed email:
   a. Read `envelope.yaml` for context
   b. Read `body.txt` for inline info
   c. Process attachments using import-bills logic
   d. Record transactions with `--meta` for traceability
   e. Create processing log via `logs/` (AI writes YAML using the documented format)
   f. Archive attachments to `documents/`
   g. Run `quidclaw mark-processed SOURCE_NAME EMAIL_DIR`

- [ ] **Step 2: Verify workflow is included in package build**

Run: `ls src/quidclaw/workflows/check-email.md`
Expected: file exists (already covered by `include = ["src/quidclaw/**/*.py", "src/quidclaw/workflows/*.md"]` in pyproject.toml)

- [ ] **Step 3: Commit**

```bash
git add src/quidclaw/workflows/check-email.md
git commit -m "feat: add check-email workflow for AI-guided email processing"
```

---

### Task 10: Write `daily-routine.md` workflow

**Files:**
- Create: `src/quidclaw/workflows/daily-routine.md`

- [ ] **Step 1: Write the workflow**

See spec Section 6 for the structure. Orchestrates:
1. Gather data: `quidclaw sync`, `quidclaw data-status`
2. Process: emails via check-email logic, inbox files via import-bills logic
3. Check & remind: calendar, anomalies
4. Report summary to user

- [ ] **Step 2: Commit**

```bash
git add src/quidclaw/workflows/daily-routine.md
git commit -m "feat: add daily-routine workflow for scheduled checks"
```

---

### Task 11: Update `onboarding.md` with Phase 9.5

**Files:**
- Modify: `src/quidclaw/workflows/onboarding.md`

- [ ] **Step 1: Add Phase 9.5 after Phase 9**

Insert the Phase 9.5 content from spec Section 5 between Phase 9 and Phase 10. The new phase goes after line 108 (after the "If not → encourage them" line) and before "### Phase 10: Save Profile & Summary".

- [ ] **Step 2: Commit**

```bash
git add src/quidclaw/workflows/onboarding.md
git commit -m "feat: add email setup phase to onboarding workflow"
```

---

### Task 12: Update `import-bills.md` with `--meta` usage

**Files:**
- Modify: `src/quidclaw/workflows/import-bills.md`

- [ ] **Step 1: Update the workflow**

In Step 5 (Record Transactions), add guidance to include `--meta` with source information:

```markdown
6. Include source metadata for traceability:
   `--meta '{"source":"inbox_file:FILENAME","source-file":"documents/YYYY/MM/ARCHIVED_NAME"}'`
```

After Step 6 (Archive), add a new Step 7a:

```markdown
### Step 7a: Write Processing Log

After archiving, create a processing log entry in `logs/`:
- Use Bash to write a YAML file to `logs/` following the format documented in `.quidclaw/workflows/check-email.md`
- Include: action, source info, extracted transaction counts, archived file paths
```

Renumber existing Step 7 to Step 8.

- [ ] **Step 2: Commit**

```bash
git add src/quidclaw/workflows/import-bills.md
git commit -m "feat: add source metadata and audit logging to import-bills workflow"
```

---

### Task 13: Update `CLAUDE.md` generation and `upgrade` command

**Files:**
- Modify: `src/quidclaw/cli.py` (both `_generate_claude_md` and `upgrade` command)

- [ ] **Step 1: Update `_generate_claude_md` to include new commands and workflows**

Add to the generated CLAUDE.md string:
- New CLI commands section for source management (`add-source`, `list-sources`, `remove-source`, `sync`, `mark-processed`)
- New workflow references (`check-email.md`, `daily-routine.md`)
- Updated directory structure (add `sources/` and `logs/`)
- Note about `--meta` for source tracking

- [ ] **Step 2: Update `upgrade` command to call `ensure_dirs()`**

Add to the `upgrade` command function body, guarded by ledger existence check:

```python
if config.main_bean.exists():
    ledger = Ledger(config)
    ledger.ensure_dirs()
```

- [ ] **Step 3: Run CLI tests**

Run: `pytest tests/test_cli.py -v`
Expected: all PASS (existing upgrade tests should still pass)

- [ ] **Step 4: Commit**

```bash
git add src/quidclaw/cli.py
git commit -m "feat: update CLAUDE.md generation and upgrade with new features"
```

---

### Task 14: Update `data-status` to include source information

**Files:**
- Modify: `src/quidclaw/core/inbox.py`
- Modify: `src/quidclaw/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write test**

Add to `tests/test_cli.py` `TestDataStatus`:

```python
def test_data_status_includes_sources(self, tmp_path):
    runner = _init_project(tmp_path)
    # Add a source config
    import yaml as _yaml
    config_file = tmp_path / ".quidclaw" / "config.yaml"
    settings = _yaml.safe_load(config_file.read_text()) if config_file.exists() else {}
    settings["data_sources"] = {"test": {"provider": "agentmail", "inbox_id": "test@agentmail.to", "enabled": True}}
    config_file.write_text(_yaml.dump(settings))

    result = runner.invoke(
        main, ["data-status", "--json"], catch_exceptions=False, env=_env(tmp_path),
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "sources" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::TestDataStatus::test_data_status_includes_sources -v`
Expected: FAIL

- [ ] **Step 3: Add `get_source_status` method to `InboxManager`**

Add to `src/quidclaw/core/inbox.py`:

```python
def get_source_status(self) -> dict:
    """Return status for all configured data sources."""
    import yaml as _yaml
    sources = self.config.get_sources()
    result = {}
    for name, src_config in sources.items():
        state_file = self.config.source_state_file(name)
        state = {}
        if state_file.exists():
            state = _yaml.safe_load(state_file.read_text()) or {}
        result[name] = {
            "provider": src_config.get("provider"),
            "last_sync": state.get("last_sync"),
            "total_synced": state.get("total_synced", 0),
        }
    return result
```

Then update `data_status` in `cli.py` to call this method (keeps CLI thin):

```python
@main.command("data-status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def data_status(as_json):
    from quidclaw.core.inbox import InboxManager
    config = get_config()
    mgr = InboxManager(config)
    status = mgr.get_data_status()
    status["sources"] = mgr.get_source_status()

    if as_json:
        click.echo(json.dumps(status, indent=2, default=str))
    else:
        click.echo(f"Inbox files: {status.get('inbox_count', 0)}")
        for f in status.get('inbox_files', []):
            click.echo(f"  - {f}")
        click.echo(f"Last modified: {status.get('last_modified', 'N/A')}")
        source_status = status.get("sources", {})
        if source_status:
            click.echo("\nData sources:")
            for name, info in source_status.items():
                last = info.get("last_sync") or "never"
                click.echo(f"  {name} ({info['provider']}): last sync {last}")
```

- [ ] **Step 4: Run all tests**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/cli.py tests/test_cli.py
git commit -m "feat: extend data-status with source sync information"
```

---

### Task 15: Update CLAUDE.md and run final verification

**Files:**
- Modify: `CLAUDE.md` (project root, manual update for command count)

- [ ] **Step 1: Update CLAUDE.md command count**

Update the command count line in the project CLAUDE.md to reflect the new commands (add-source, list-sources, remove-source, sync, mark-processed = 5 new commands).

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: all PASS

- [ ] **Step 3: Verify init creates all new directories**

Run: `python -c "
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
import tempfile, pathlib
d = pathlib.Path(tempfile.mkdtemp())
l = Ledger(QuidClawConfig(data_dir=d))
l.init()
print('sources:', (d / 'sources').is_dir())
print('logs:', (d / 'logs').is_dir())
"`
Expected: both `True`

- [ ] **Step 4: Verify new CLI commands are registered**

Run: `quidclaw --help`
Expected: shows `add-source`, `list-sources`, `remove-source`, `sync`, `mark-processed`

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with new command count"
```
