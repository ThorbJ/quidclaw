# Data Sources & Audit Trail — Design Spec

## Problem

QuidClaw currently requires users to manually drop files into `inbox/`. This creates friction — a real personal CFO should proactively acquire data from where it already lives (email, APIs, etc.). Additionally, there's no audit trail: once a transaction is recorded, there's no way to trace it back to its source document or understand how the AI processed it.

## Goals

1. **Email integration**: Users can forward bills to a dedicated email address; QuidClaw automatically fetches and processes them.
2. **Extensible data source architecture**: Email is the first source, but the design must support future sources (Gmail MCP, broker APIs, bank APIs) without architectural changes.
3. **Complete audit trail**: Every transaction traces back to its source. Every processing event is logged. Errors can be investigated and corrected.

## Non-Goals (this iteration)

- Scheduled/cron-based sync (architecture supports it, but not implemented yet)
- Multiple email providers (only AgentMail for now)
- Webhook-based push notifications
- Bank API or MCP integrations (architecture supports it)

---

## 1. Directory Structure Changes

### Current structure

```
my-finances/
├── inbox/          # Manual file drop zone
├── documents/      # Archived source files
├── ledger/         # Beancount files
├── notes/          # Knowledge base
├── reports/        # Generated reports
└── .quidclaw/
    ├── config.yaml
    └── workflows/
```

### New structure

```
my-finances/
├── inbox/                          # Manual file drop zone (unchanged)
│
├── sources/                        # NEW: synced data from external sources
│   └── email/                      #   One subdirectory per source instance
│       ├── .state.yaml             #   Sync state (last_sync, cursor, etc.)
│       └── 2026-03-21T18-35_cmb/   #   One directory per email
│           ├── envelope.yaml       #     Metadata (from, to, subject, date, message_id)
│           ├── body.txt            #     Plain text body
│           ├── body.html           #     HTML body (if present)
│           └── attachments/        #     Original attachments
│               ├── 账单明细.pdf
│               └── 积分报告.pdf
│
├── logs/                           # NEW: processing audit trail
│   └── 2026-03-21T10-30-00_import-email.yaml
│
├── documents/                      # Archived source files (unchanged)
├── ledger/                         # Beancount files (unchanged, but with new metadata)
├── notes/                          # Knowledge base (unchanged)
├── reports/                        # Generated reports (unchanged)
└── .quidclaw/
    ├── config.yaml                 # Extended with data_sources section
    └── workflows/
        ├── ... (existing)
        ├── check-email.md          # NEW: email checking workflow
        └── daily-routine.md        # NEW: orchestrates all routine checks
```

### Key design decisions

**Why `sources/` instead of putting emails in `inbox/`?**
- `inbox/` is the user's manual drop zone — mixing automated content there creates confusion
- Each email is a complete information package (envelope + body + attachments) that must stay together
- `sources/` can hold data from any external source, each with its own subdirectory and sync state

**Why one directory per email?**
- Preserves the complete context: an AI processing the email reads `envelope.yaml` first, understands who sent it and why, then processes `body.txt` and `attachments/` together
- No information loss from splitting

**Why `logs/` at the top level?**
- Processing logs are cross-cutting — they reference sources, ledger entries, and documents
- They're the primary audit trail and should be easy to find

---

## 2. Data Source Architecture

### Config structure

```yaml
# .quidclaw/config.yaml
operating_currency: CNY

data_sources:
  my-email:                          # User-chosen name (unique identifier)
    provider: agentmail              # Provider type (determines which class to use)
    api_key: am_us_xxxxx             # Provider-specific credentials
    inbox_id: thorb-cfo@agentmail.to # Provider-specific config
    display_name: QuidClaw CFO       # Human-readable name for the inbox
    sync_interval: 10m               # How often to sync (for future scheduled sync)
    enabled: true                    # Can be disabled without removing

  # Future examples (not implemented this iteration):
  # work-gmail:
  #   provider: gmail_mcp
  #   sync_interval: 30m
  #   enabled: true
  # tiger-broker:
  #   provider: tiger_api
  #   endpoint: https://...
  #   sync_interval: 1h
  #   enabled: true
```

### Config API for nested data_sources

The existing `get_setting`/`set_setting` API works with flat keys. Data sources need nested structure, so `QuidClawConfig` gains dedicated methods:

```python
# New methods on QuidClawConfig
def get_sources(self) -> dict:
    """Return the data_sources subtree, default {}."""
    return self.load_settings().get("data_sources", {})

def get_source(self, name: str) -> dict | None:
    """Get a single source config by name."""
    return self.get_sources().get(name)

def add_source(self, name: str, source_config: dict) -> None:
    """Add or update a source entry under data_sources."""
    settings = self.load_settings()
    settings.setdefault("data_sources", {})[name] = source_config
    self.save_settings(settings)

def remove_source(self, name: str) -> None:
    """Remove a source entry. Raises KeyError if not found."""
    settings = self.load_settings()
    sources = settings.get("data_sources", {})
    if name not in sources:
        raise KeyError(f"Source not found: {name}")
    del sources[name]
    self.save_settings(settings)

@property
def sources_dir(self) -> Path:
    return self.data_dir / "sources"

@property
def logs_dir(self) -> Path:
    return self.data_dir / "logs"

def source_dir(self, source_name: str) -> Path:
    """Directory for a specific source's synced data."""
    return self.sources_dir / source_name

def source_state_file(self, source_name: str) -> Path:
    """Sync state file for a specific source."""
    return self.source_dir(source_name) / ".state.yaml"
```

### Core classes

```
core/sources/
├── __init__.py
├── base.py              # DataSource abstract base class
├── registry.py          # Source registration and discovery
└── agentmail.py         # AgentMail provider implementation
```

**`base.py` — DataSource ABC:**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from quidclaw.config import QuidClawConfig

@dataclass
class SyncResult:
    """Result of a sync operation."""
    source_name: str
    provider: str
    items_fetched: int          # Number of new items (emails, files, etc.)
    items_stored: list[str]     # Paths to stored items (relative to data_dir)
    last_sync: datetime         # Timestamp of this sync
    errors: list[str]           # Any errors encountered

class DataSource(ABC):
    """Base class for all data sources.

    All providers must accept these three constructor arguments.
    """

    def __init__(self, source_name: str, source_config: dict, config: QuidClawConfig):
        self.source_name = source_name
        self.source_config = source_config
        self.config = config

    @staticmethod
    @abstractmethod
    def provider_name() -> str:
        """Return the provider identifier (e.g., 'agentmail')."""
        ...

    @abstractmethod
    def sync(self) -> SyncResult:
        """Fetch new data from the source and store locally.

        Must be idempotent — calling sync twice should not duplicate data.
        Uses .state.yaml to track what has been fetched.
        """
        ...

    @abstractmethod
    def status(self) -> dict:
        """Return current status (last sync time, item count, etc.)."""
        ...

    def provision(self) -> dict:
        """Optional: provision remote resources (e.g., create a mailbox).

        Called by add-source when setting up a new source.
        Returns updated source_config with any new fields (e.g., inbox_id).
        Default: no-op, returns source_config unchanged.
        """
        return self.source_config
```

**`registry.py` — Provider registry:**

```python
from quidclaw.config import QuidClawConfig
from quidclaw.core.sources.base import DataSource

# Maps provider names to classes
# New providers register themselves here
PROVIDERS: dict[str, type[DataSource]] = {}

def register_provider(cls: type[DataSource]) -> type[DataSource]:
    """Decorator to register a data source provider."""
    PROVIDERS[cls.provider_name()] = cls
    return cls

def get_provider(provider_name: str) -> type[DataSource]:
    """Look up a provider class by name."""
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[provider_name]

def create_source(source_name: str, source_config: dict, config: QuidClawConfig) -> DataSource:
    """Factory: create a DataSource instance from config."""
    provider_name = source_config["provider"]
    cls = get_provider(provider_name)
    return cls(source_name=source_name, source_config=source_config, config=config)
```

**`agentmail.py` — AgentMail implementation:**

Key behaviors:
- `provision()`: calls AgentMail API to create a new inbox (with optional username), returns updated config with `inbox_id`
- `sync()`: calls AgentMail API to list messages since last sync, downloads each email (envelope + body + attachments) into `sources/{source_name}/{timestamp}_{sender}/`
- Sender slug in directory names is sanitized: replace `/`, `:`, `\`, `<`, `>` with `-`, truncate to 50 chars
- Uses `sources/{source_name}/.state.yaml` to track `last_sync` timestamp only (no unbounded ID list — deduplication is by checking if local directory already exists for a given `message_id`)
- `sync()` exit behavior: returns `SyncResult` with `errors` list populated for partial failures. CLI exits 0 if any items were fetched, exits 1 only if zero items fetched AND errors occurred

### Email storage format

Each email is stored as a directory:

```
sources/my-email/2026-03-21T18-35_招商银行/
├── envelope.yaml
├── body.txt
├── body.html          # Only if HTML body exists
└── attachments/
    ├── 账单明细.pdf
    └── 积分报告.pdf
```

**`envelope.yaml`:**
```yaml
message_id: "msg_abc123"
from: "creditcard@cmbchina.com"
from_name: "招商银行信用卡中心"
to: "thorb-cfo@agentmail.to"
subject: "您的2026年3月信用卡电子账单"
date: "2026-03-21T18:35:00+08:00"
labels: ["received", "unread"]
attachments:
  - filename: "账单明细.pdf"
    size: 245000
    content_type: "application/pdf"
  - filename: "积分报告.pdf"
    size: 18000
    content_type: "application/pdf"
source_name: "my-email"
source_provider: "agentmail"
synced_at: "2026-03-21T19:00:00+08:00"
status: "unprocessed"             # unprocessed → processed → archived
```

**Sync state file (`sources/my-email/.state.yaml`):**
```yaml
last_sync: "2026-03-21T19:00:00+08:00"
total_synced: 15
```

Note: no `processed_ids` list — deduplication uses `last_sync` timestamp plus checking if a local directory already exists for a given `message_id` (stored in each `envelope.yaml`). This avoids unbounded list growth.

---

## 3. Audit Trail

### 3.1 Processing logs

Every processing event creates a log file in `logs/`:

```yaml
# logs/2026-03-21T10-30-00_import-email.yaml
id: "evt_20260321T103000"
timestamp: "2026-03-21T10:30:00+08:00"
action: "import"
trigger: "manual"                    # manual | scheduled | conversation

source:
  type: "email"                      # email | inbox_file | conversation | api
  path: "sources/my-email/2026-03-21T18-35_招商银行"
  provider: "agentmail"
  original_subject: "您的2026年3月信用卡电子账单"
  original_from: "creditcard@cmbchina.com"

input_files:
  - "sources/my-email/2026-03-21T18-35_招商银行/attachments/账单明细.pdf"

extracted:
  transactions_found: 45
  transactions_recorded: 43
  transactions_rejected: 2
  accounts_created:
    - "Expenses:Transport:Taxi"

recorded_transactions:
  - date: "2026-03-15"
    payee: "滴滴出行"
    amount: "-45.00"
    currency: "CNY"
    ledger_file: "ledger/2026/2026-03.bean"
  # ... (all 43 transactions)

rejected:
  - date: "2026-03-10"
    payee: "美团外卖"
    amount: "-32.50"
    reason: "user marked as duplicate"

archived_to:
  - "documents/2026/03/招商银行-信用卡账单-2026-03.pdf"

user_confirmations:
  - "User approved 43 of 45 transactions"
  - "User rejected 2 as duplicates"
```

### 3.1.1 AuditLogger class design

```python
# core/logs.py
import uuid
from datetime import datetime
from pathlib import Path
from quidclaw.config import QuidClawConfig
import yaml

class AuditLogger:
    """Writes structured processing logs to logs/ directory."""

    def __init__(self, config: QuidClawConfig):
        self.config = config

    def log_event(self, action: str, source: dict, **fields) -> str:
        """Write a processing log entry. Returns the event ID.

        Args:
            action: "import", "record", "fetch-prices", etc.
            source: dict with type, path, provider, etc.
            **fields: additional fields (extracted, recorded_transactions,
                      rejected, archived_to, user_confirmations, etc.)
        """
        event_id = f"evt_{datetime.now().strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:6]}"
        timestamp = datetime.now().isoformat()

        log_entry = {
            "id": event_id,
            "timestamp": timestamp,
            "action": action,
            "source": source,
            **fields,
        }

        self.config.logs_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}_{uuid.uuid4().hex[:6]}_{action}.yaml"
        log_path = self.config.logs_dir / filename
        log_path.write_text(yaml.dump(log_entry, default_flow_style=False, allow_unicode=True))

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

The filename includes a 6-char random suffix to prevent collisions when processing multiple items in rapid succession.

### 3.2 Source metadata on transactions

When recording transactions, `add-txn` gains an optional `--meta` parameter:

```bash
quidclaw add-txn \
  --date 2026-03-15 \
  --payee "滴滴出行" \
  --narration "打车" \
  --posting '{"account":"Expenses:Transport:Taxi","amount":"45.00","currency":"CNY"}' \
  --posting '{"account":"Liabilities:CreditCard:CMB:1234"}' \
  --meta '{"source":"email:my-email/2026-03-21T18-35_招商银行","source-file":"documents/2026/03/招商银行-信用卡账单-2026-03.pdf","import-id":"evt_20260321T103000"}'
```

This produces in the `.bean` file:

```beancount
2026-03-15 * "滴滴出行" "打车"
  source: "email:my-email/2026-03-21T18-35_招商银行"
  source-file: "documents/2026/03/招商银行-信用卡账单-2026-03.pdf"
  import-id: "evt_20260321T103000"
  Expenses:Transport:Taxi     45.00 CNY
  Liabilities:CreditCard:CMB:1234
```

**`TransactionManager.add_transaction` signature change:**

```python
def add_transaction(
    self,
    date: datetime.date,
    payee: str,
    narration: str,
    postings: list[dict],
    metadata: dict | None = None,    # NEW parameter
) -> None:
    lines = [f'{date} * "{payee}" "{narration}"\n']
    # Metadata lines go BEFORE postings (Beancount V3 format)
    if metadata:
        for key, value in metadata.items():
            lines.append(f'  {key}: "{value}"\n')
    for p in postings:
        # ... existing posting logic unchanged
```

Note: Beancount V3 metadata keys support hyphens (`source-file`, `import-id`). Verified in Beancount V3 spec.

### 3.3 Log types

Different data sources produce different log entries, but they share a common envelope:

| Source type | action | source.type | Typical input |
|-------------|--------|-------------|---------------|
| Email bill | `import` | `email` | Email envelope + attachments |
| Manual file | `import` | `inbox_file` | File from inbox/ |
| Conversation | `record` | `conversation` | User said "午饭花了45" |
| API sync | `import` | `api` | Broker transaction data |
| Price fetch | `fetch-prices` | `api` | Yahoo Finance |

### 3.4 Audit queries

The AI can use existing file tools to investigate:
- **"This transaction looks wrong"** → read `source` metadata → find the log → find the original email/file
- **"Show me all imports from last week"** → Glob `logs/2026-03-1*`
- **"Did we process the CMB bill?"** → Grep `logs/` for "招商银行"

No special CLI command needed — the AI's native file tools are sufficient.

---

## 4. CLI Commands

### New commands

```bash
# Data source management
quidclaw add-source NAME --provider PROVIDER [--api-key KEY] [--inbox-id ID]
quidclaw list-sources [--json]
quidclaw remove-source NAME --confirm

# Sync
quidclaw sync [SOURCE_NAME] [--json]    # Sync one source, or all enabled sources

# Processing
quidclaw mark-processed SOURCE_NAME EMAIL_DIR   # Update envelope.yaml status
```

### Modified commands

```bash
# add-txn gains --meta
quidclaw add-txn --date D --payee P --posting '...' [--meta '{"source":"..."}']
```

### Command details

**`add-source`**: Creates config entry under `data_sources`. For AgentMail, also calls the API to create the inbox if `--inbox-id` is not provided (user can specify a preferred username or get a random one).

**`sync`**: Instantiates the appropriate DataSource via the registry, calls `sync()`, prints summary. Returns JSON with `SyncResult` fields when `--json` is used.

**`list-sources`**: Shows all configured sources with last sync time and status. Also includes count of unprocessed items per source.

**`remove-source`**: Removes the config entry from `data_sources`. Does NOT delete the local `sources/{name}/` directory (synced data is preserved for audit trail). Prints a message telling the user where the data is if they want to delete it manually. Requires `--confirm` flag to prevent accidental removal.

**`data-status`** (existing, extended): Now also reports source status — for each enabled source, shows unprocessed item count and last sync time. The `--json` output gains a `sources` key.

---

## 5. Onboarding Integration

### Where in the flow

After Phase 9 (Inbox Introduction), add a new **Phase 9.5: Email Setup (Optional)**:

```markdown
### Phase 9.5: Email Setup (Optional)

After showing them the inbox folder, offer email integration:

"By the way — would you like me to set up a dedicated email address for you?
You can forward your bank statements and bills there, and I'll automatically
pick them up and process them. It's completely optional."

If they say yes:

1. Explain: "I'll use a service called AgentMail to create a mailbox for you.
   It's a third-party email service — I want to be upfront about that.
   Your emails go directly to their servers, and I fetch them from there.
   I don't store any credentials beyond the API key, and I can only see
   the emails sent to this specific address."

2. Ask: "Do you have an AgentMail account? If not, you can create one for
   free at console.agentmail.to — it takes about a minute. The free plan
   gives you 3 mailboxes and 3,000 emails per month, which is plenty."

3. Once they provide the API key:
   "Great! What name would you like for your email address?
   For example, 'thorb-cfo' would give you thorb-cfo@agentmail.to.
   Or I can generate a random one for you."

4. Run the setup:
   $ quidclaw add-source my-email \
       --provider agentmail \
       --api-key <their_key> \
       --inbox-id <chosen_name>@agentmail.to

5. Confirm: "Done! Your email is {address}. You can now go to your banks
   and set up bill forwarding to this address. Whenever a new bill arrives,
   I'll pick it up automatically."

6. Save to notes/profile.md under a new "## Data Sources" section.

If they say no:
  "No problem! You can always set this up later. Just tell me
  'set up email' whenever you're ready."
```

### Privacy disclosure requirements

The workflow MUST:
- Explicitly name AgentMail as a third-party service
- Clarify that the AI cannot see the user's other emails — only those sent to this specific address
- Explain that the API key is stored locally in `.quidclaw/config.yaml`
- Never pressure the user — this is entirely optional

---

## 6. Workflows

### New: `check-email.md`

Guides the AI through checking email sources:

1. Run `quidclaw sync my-email --json` to fetch new emails
2. If new emails arrived, list them for the user
3. For each unprocessed email in `sources/my-email/`:
   a. Read `envelope.yaml` — understand context (who sent it, subject)
   b. Read `body.txt` — extract any inline information (totals, due dates, notifications)
   c. Check `attachments/` — process PDFs/CSVs using import-bills logic
   d. Record transactions with source metadata (`--meta`)
   e. Create processing log in `logs/`
   f. Archive attachments to `documents/`
   g. Mark as processed: `quidclaw mark-processed SOURCE_NAME EMAIL_DIR`

### New: `daily-routine.md`

Orchestrates all routine checks. This is what a scheduled task would invoke:

1. **Gather data**:
   - `quidclaw sync` (all enabled sources)
   - Check `inbox/` for manually dropped files (`quidclaw data-status`)
2. **Process new data**:
   - For each new email → follow `check-email.md` logic
   - For each new inbox file → follow `import-bills.md` logic
3. **Check & remind**:
   - Read `notes/calendar.md` — any upcoming payments?
   - `quidclaw detect-anomalies` — anything suspicious?
4. **Report to user**:
   - Brief summary of what was done

### Modified: `import-bills.md`

Add source metadata to the recording step:
- When recording transactions from a file, include `--meta` with source information
- After archiving, create a processing log entry in `logs/`

---

## 7. `init` and `upgrade` Changes

### `quidclaw init`

`Ledger.init()` gains `sources/` and `logs/` in its directory creation list (alongside `inbox/`, `documents/`, `notes/`, `reports/`). Directory creation responsibility stays in `Ledger.init()`, not duplicated elsewhere.

### `quidclaw upgrade`

- Copy new workflow files (`check-email.md`, `daily-routine.md`)
- Update `CLAUDE.md` with new commands and workflow references
- Call `Ledger.ensure_dirs()` (new method) to create any missing directories — this covers `sources/` and `logs/` for existing projects that were initialized before this feature

### Updated `CLAUDE.md` generation

Add to the generated CLAUDE.md:
- New CLI commands (`add-source`, `sync`, `list-sources`, `remove-source`)
- New workflows (`check-email.md`, `daily-routine.md`)
- Updated directory structure documentation
- Guidance on using `--meta` for source tracking

---

## 8. Implementation Sequence

### Phase 1: Foundation (no external dependencies)
1. Add `sources/` and `logs/` directories to `init`
2. Create `core/sources/base.py` with `DataSource` ABC and `SyncResult`
3. Create `core/sources/registry.py` with provider registration
4. Extend `config.py` with `sources_dir`, `logs_dir` properties
5. Add `--meta` support to `add-txn` command and `TransactionManager`
6. Create `core/logs.py` — `AuditLogger` for writing processing logs

### Phase 2: AgentMail Integration
7. Create `core/sources/agentmail.py` — the first provider implementation
8. Add CLI commands: `add-source`, `list-sources`, `remove-source`, `sync`
9. Write tests for all of the above

### Phase 3: Workflows & Onboarding
10. Write `check-email.md` workflow
11. Write `daily-routine.md` workflow
12. Update `onboarding.md` with Phase 9.5
13. Update `import-bills.md` with `--meta` usage
14. Update `CLAUDE.md` generation
15. Update `init` and `upgrade` commands

### Phase 4: Testing
16. Unit tests for `DataSource`, `AgentMailSource`, `AuditLogger`
17. CLI tests for new commands
18. Integration test: full sync → process → log → archive flow

---

## 9. Dependencies

### New Python dependency

```
agentmail    # AgentMail Python SDK
```

Add to `pyproject.toml` as an optional dependency:
```toml
[project.optional-dependencies]
email = ["agentmail"]
```

This keeps the core QuidClaw installable without email support. The `agentmail` provider checks for the import and gives a clear error if not installed.

---

## 10. Security Considerations

- **API keys in config**: Stored in plaintext in `.quidclaw/config.yaml` by default. Supports `env:VAR_NAME` syntax (e.g., `api_key: env:AGENTMAIL_API_KEY`) so power users can keep secrets out of config files. The `create_source` factory resolves `env:` references before passing config to the provider. Users should `.gitignore` config.yaml if version-controlling their finances.
- **Email content on disk**: Emails are stored locally in `sources/`. This is intentional — the user owns their data. But the directory should be mentioned in `.gitignore` suggestions.
- **No credentials in logs**: Processing logs never contain API keys or auth tokens.
- **Provider isolation**: Each provider only has access to its own config values. The base class enforces this.
