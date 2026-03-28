# QuidClaw Architecture

QuidClaw is a CLI tool that provides AI-friendly access to Beancount V3 operations. Any AI coding tool that can run shell commands becomes a personal CFO.

## Two-Layer Architecture

QuidClaw follows a strict two-layer separation:

```
┌──────────────────────────────────────────────────────────┐
│                      AI Tool Layer                       │
│         (Claude Code, Gemini CLI, Codex, etc.)           │
│                                                          │
│  Reads CLAUDE.md ──► Discovers installed skills           │
│  Loads skills ──► Follows step-by-step guides             │
│  Calls quidclaw CLI ──► Accounting operations            │
│  Uses native tools ──► File I/O (notes, inbox, docs)     │
└────────────────────────┬─────────────────────────────────┘
                         │ shell commands
                         ▼
┌──────────────────────────────────────────────────────────┐
│                     CLI Adapter                          │
│                  src/quidclaw/cli.py                     │
│                                                          │
│  Click command group (35 commands)                       │
│  Parses arguments ──► Calls core ──► Formats output      │
│  Supports --json for structured output                   │
│  No business logic here                                  │
└────────────────────────┬─────────────────────────────────┘
                         │ function calls
                         ▼
┌──────────────────────────────────────────────────────────┐
│                    Core Library                          │
│                 src/quidclaw/core/                       │
│                                                          │
│  AccountManager    TransactionManager    BalanceManager  │
│  ReportManager     AnomalyDetector       InboxManager    │
│  NotesManager      PriceManager          DocumentManager │
│  LedgerInitializer Ledger                AuditLogger     │
│  sources/: DataSource, AgentMailSource, registry        │
│                                                          │
│  Pure business logic. Depends on Beancount, NOT on CLI.  │
└────────────────────────┬─────────────────────────────────┘
                         │ beancount API
                         ▼
┌──────────────────────────────────────────────────────────┐
│                   Beancount V3                           │
│                                                          │
│  loader.load_file()     data.Transaction                 │
│  realization.realize()  beanquery.run_query()            │
│                                                          │
│  Plain text .bean files on disk                          │
└──────────────────────────────────────────────────────────┘
```

### Layer 1: Core (`src/quidclaw/core/`)

Pure Python business logic. Each module has a single responsibility:

| Module | Class | Responsibility |
|--------|-------|----------------|
| `ledger.py` | `Ledger` | Init, load, append, ensure monthly files exist |
| `accounts.py` | `AccountManager` | Open/close/list accounts, notes on accounts |
| `transactions.py` | `TransactionManager` | Add transactions with flags, tags, links |
| `balance.py` | `BalanceManager` | Balance queries, assertions, pad directives |
| `documents.py` | `DocumentManager` | Beancount document directives (link files to accounts) |
| `reports.py` | `ReportManager` | BQL queries, monthly summaries, category breakdowns, comparisons |
| `anomaly.py` | `AnomalyDetector` | Duplicates, subscriptions, outliers, unknown merchants |
| `inbox.py` | `InboxManager` | List inbox files, data freshness status |
| `notes.py` | `NotesManager` | Knowledge base CRUD, search, tags |
| `prices.py` | `PriceManager` | Price directives |
| `init.py` | `LedgerInitializer` | Default account templates |
| `sources/base.py` | `DataSource` | Abstract base class for all data sources |
| `sources/registry.py` | — | Provider registration, factory, env: resolution |
| `sources/agentmail.py` | `AgentMailSource` | AgentMail email sync provider |
| `logs.py` | `AuditLogger` | Processing event audit trail |
| `backup.py` | `BackupManager` | Git-based versioning and multi-remote backup |

**Dependency convention:**
- Classes that operate on **ledger data** take a `Ledger` instance in their constructor
- Classes that operate on **files** (inbox, notes) take a `QuidClawConfig` instance

### `core/backup.py` — Git Backup Manager

Manages Git-based versioning and multi-remote backup of the data directory. Wraps `git` CLI via subprocess. Supports:
- Auto-commit after write operations
- Async push to multiple remotes (fire-and-forget)
- Git LFS for binary files (PDFs, images)
- Status reporting

Backup never blocks normal operations — all failures are silently swallowed.

### Layer 2: CLI Adapter (`src/quidclaw/cli.py`)

A thin Click command group that translates shell arguments into core function calls. The adapter:

1. Resolves the data directory (current directory or `QUIDCLAW_DATA_DIR`)
2. Parses CLI arguments
3. Instantiates the appropriate core manager
4. Calls the core method
5. Formats the output (plain text or JSON)

No business logic lives here. If a feature can be implemented without changing `cli.py`, it should be.

### Supporting Files

| File | Purpose |
|------|---------|
| `config.py` | `QuidClawConfig` dataclass — all path derivations from data directory |
| `skills/` | Agent Skills (agentskills.io standard), installed to platform directories at init/upgrade |

## Component Collaboration Flow

A typical user interaction follows this path:

```
1. User drops bank-statement.csv into inbox/

2. User opens AI tool in the project directory
       │
       ▼
3. AI reads CLAUDE.md
   ├── Understands directory structure
   ├── Knows available CLI commands
   └── Discovers installed skills
       │
       ▼
4. AI loads the quidclaw-import skill
   └── Gets step-by-step instructions for bill import
       │
       ▼
5. AI executes the workflow:
   ├── Reads inbox/bank-statement.csv (native file read)
   ├── Parses transactions from the CSV
   ├── quidclaw add-txn --date ... --payee ... --posting '...'  (×N)
   ├── mv inbox/bank-statement.csv documents/2026/03/  (native bash)
   └── quidclaw data-status --json  (verify)
       │
       ▼
6. Beancount ledger updated with verified transactions
```

## Data Flow Example

Recording a transaction from natural language:

```
User: "午饭花了45，微信付的"
         │
         ▼
AI interprets:
  date = 2026-03-20
  payee = "午餐"
  from = Expenses:Food:Lunch
  to = Assets:WeChat:1234
  amount = 45.00 CNY
         │
         ▼
AI executes:
  $ quidclaw add-txn \
      --date 2026-03-20 \
      --payee "午餐" \
      --posting '{"account":"Expenses:Food:Lunch","amount":"45.00","currency":"CNY"}' \
      --posting '{"account":"Assets:WeChat:1234","amount":"-45.00","currency":"CNY"}'
         │
         ▼
CLI layer (cli.py):
  Parses args → TransactionManager(ledger).add_transaction(...)
         │
         ▼
Core layer (transactions.py):
  Formats Beancount directive → Appends to ledger/2026/2026-03.bean
  Creates year directory and include directive if needed
         │
         ▼
Result on disk (ledger/2026/2026-03.bean):
  2026-03-20 * "午餐" ""
    Expenses:Food:Lunch     45.00 CNY
    Assets:WeChat:1234     -45.00 CNY
```

## Data Directory Structure

QuidClaw uses a directory-as-project model (like git). The data directory is the current working directory by default, overridable via `QUIDCLAW_DATA_DIR`.

```
my-finances/                       # Data directory root
├── CLAUDE.md                      # AI entry file (generated, points to skills)
├── .claude/skills/                # Agent Skills (agentskills.io, 5 skills)
│   ├── quidclaw.md               #   Core skill: project structure + CLI reference
│   ├── quidclaw-onboarding.md    #   New user interview
│   ├── quidclaw-import.md        #   Parse and import documents
│   ├── quidclaw-daily.md         #   Daily financial check-in
│   └── quidclaw-review.md        #   Monthly financial analysis + reconciliation
├── .quidclaw/
│   └── config.yaml                # QuidClaw settings
│
├── ledger/                        # Beancount ledger (structured data)
│   ├── main.bean                  #   Root file, includes everything
│   ├── accounts.bean              #   Open/Close directives
│   ├── prices.bean                #   Price directives
│   └── YYYY/
│       └── YYYY-MM.bean           #   Monthly transaction files
│
├── inbox/                         # Drop zone (user puts files here)
├── documents/                     # Organized archive (AI-managed)
│   └── YYYY/MM/                   #   Filed by year and month
├── notes/                         # Financial knowledge base (AI-managed)
│   ├── profile.md                 #   Living: user profile
│   ├── calendar.md                #   Living: payment calendar
│   ├── assets/                    #   Living: property, investments
│   ├── liabilities/               #   Living: loans, debts
│   ├── accounts/                  #   Living: bank/card details
│   ├── subscriptions/             #   Living: recurring charges
│   ├── decisions/                 #   Append-only: decision log
│   └── journal/                   #   Append-only: conversation captures
├── sources/                       # Synced external data (AI-managed)
│   └── my-email/                  #   Per-source directory
│       └── {timestamp}_{sender}/  #   Per-message bundle
│           ├── envelope.yaml      #     Metadata + processing status
│           ├── body.txt           #     Email body
│           └── attachments/       #     Attached files
├── logs/                          # Audit trail (append-only)
│   └── YYYY-MM-DD.jsonl           #   Processing events per day
└── reports/                       # Generated reports (AI-managed)
```

**Key distinction:** The `ledger/` directory contains only verified, evidence-based data (from bank statements, receipts). The `notes/` directory contains AI-managed knowledge that may be approximate or conversational.

## Email Sync Collaboration Flow

The email sync path uses the data sources subsystem and audit logger:

```
1. User configures email source during onboarding

2. quidclaw sync → AgentMailSource.sync()
   └── Fetches new emails from AgentMail API

3. Emails stored in sources/my-email/{timestamp}_{sender}/
   ├── envelope.yaml   (metadata, status: unprocessed)
   ├── body.txt
   └── attachments/

4. AI loads the quidclaw-import skill
   └── Gets step-by-step instructions for email processing

5. AI processes each email:
   └── Reads envelope.yaml + body.txt + attachments/

6. quidclaw add-txn --flag '*' --meta '{"source":"email:..."}' (×N)
   ├── Transactions recorded with source provenance
   └── Uncertain items use --flag '!' for user review

7. quidclaw mark-processed → envelope.yaml status updated
   └── Prevents duplicate processing on next sync

8. Audit log written to logs/
   └── AuditLogger appends event to YYYY-MM-DD.jsonl
```

## Testing Architecture

Three layers of tests, from fast and isolated to slow and realistic:

```
┌─────────────────────────────────────────────────────┐
│  Layer 3: E2E Tests (tests/e2e/)                    │
│  • Runs claude -p with QuidClaw installed            │
│  • Verifies data state, not AI text output           │
│  • Slow: each test calls the AI API                  │
│  • pytest tests/e2e/ -v -m e2e --timeout=180        │
│                                                      │
│  8 test groups: import, dedup, reconcile, query,     │
│     onboarding, organize, insights, knowledge_base    │
├─────────────────────────────────────────────────────┤
│  Layer 2: CLI + Integration Tests                    │
│  • tests/test_cli.py — Click test runner             │
│  • tests/test_integration.py — multi-step workflows  │
│  • Tests CLI argument parsing and output formatting  │
│  • Fast: no AI API calls                             │
├─────────────────────────────────────────────────────┤
│  Layer 1: Core Unit Tests (tests/core/)              │
│  • One test file per core module                     │
│  • Uses tmp_path fixture for isolated data dirs      │
│  • Tests pure business logic                         │
│  • Fast: no CLI, no I/O beyond tmp_path              │
└─────────────────────────────────────────────────────┘
```

### Test conventions

- All tests use `tmp_path` for isolated, disposable data directories
- E2E tests follow the principle: **Don't check what AI says. Check what AI does.** They verify `.bean` file entries, directory structure, and balances — never AI text output.
- E2E fixtures live in `tests/e2e/fixtures/` (simulated bank statements, receipts)

## Design Decisions

### Why CLI instead of MCP?

The original QuidClaw used MCP (Model Context Protocol) as its interface. The CLI architecture replaced it for several reasons:

1. **Universality** — Any AI tool that can run shell commands works. MCP requires explicit protocol support.
2. **Simplicity** — A Click CLI is debuggable, scriptable, and testable without an AI.
3. **File operations handled by AI** — Notes, inbox, and documents are just files. AI tools already have file I/O. No need to wrap every file operation in a tool.
4. **Skills as the interface** — Agent Skills (agentskills.io standard) teach any AI how to use the CLI. A minimal entry file (CLAUDE.md, GEMINI.md, etc.) points the AI to the installed skills. No protocol negotiation needed.

### Why directory-as-project?

Like git, QuidClaw treats the current directory as the project root. This means:
- No global config file to manage
- Multiple financial projects can coexist (personal, business, etc.)
- The entire project is portable and version-controllable

### Layer boundary: what belongs where?

The two-layer architecture has a clear division of responsibility:

**CLI/Core layer** (deterministic, testable without AI):
- Accounting operations: add transactions, query balances, generate reports
- Data movement: sync emails, fetch prices, manage files
- Configuration: manage settings, data sources, directory structure

**AI layer** (intelligent, requires understanding):
- Parsing and interpreting documents (PDFs, CSVs, images, emails)
- Deciding how to categorize transactions
- Interacting with the user (onboarding, confirmations, explanations)
- Orchestrating multi-step tasks via skills

**Rule of thumb**: if it requires understanding what data *means*, it belongs in the AI layer. If it's moving data or doing math, it belongs in CLI/Core.

Never duplicate AI capabilities in the CLI layer. For example, don't add PDF parsing to the CLI — the AI reads PDFs natively. Don't add transaction categorization logic — the AI decides categories based on context.

### Local-first: no server components

QuidClaw runs entirely on the user's machine. There is no backend service, no cloud component, no public endpoint. This is a deliberate architectural choice:

- **Data sovereignty**: Financial data stays on the user's device
- **Zero infrastructure**: Users don't need to deploy or maintain anything
- **Offline capable**: Core operations work without internet

Consequence: all external data acquisition is **pull-based** (the CLI polls/syncs from external services). Push-based patterns (webhooks, callbacks, server-sent events) require a publicly accessible endpoint and are therefore incompatible with QuidClaw's architecture.
