# QuidClaw

Zero-barrier personal CFO.

**Local-first. Privacy by design. Your data never leaves your machine.**

QuidClaw turns any AI coding tool into a personal finance manager. It combines a CLI for Beancount accounting operations with AI workflow guides, so the AI knows exactly how to record transactions, import bank statements, detect anomalies, and generate reports. You talk to your AI in natural language — in any language — and it handles the bookkeeping. Works with Claude Code, Gemini CLI, OpenAI Codex, Cursor, or anything else that can read a markdown file and run shell commands.

> "午饭花了45，微信付的"
>
> The AI records a 45 CNY lunch expense from your WeChat account. No forms, no menus, no learning curve.

## Why QuidClaw

- **Privacy first** — Everything runs locally. No cloud, no telemetry, no third-party access. Your financial data is plain text files on your machine.
- **You own your data** — Beancount plain text format. Version control with git. No vendor lock-in. Export, migrate, or audit anytime.
- **Zero barrier** — Talk to your AI the way you talk to a friend. Say "昨天打车花了30" or "I paid rent today, $2400" and it just works.
- **Works with any AI** — Not locked to one tool. Claude Code today, Gemini CLI tomorrow. The workflows are portable markdown files.
- **Real accounting engine** — Powered by Beancount V3 with double-entry bookkeeping, multi-currency support, and a query language (BQL).

## How It Works

```
                    ┌─────────────────────────────────┐
                    │         Your Computer            │
                    │                                  │
 You ──► Any AI ──►│  reads CLAUDE.md                 │
         Tool      │    ├── understands your finances  │
                   │    ├── follows workflow guides    │
                   │    └── runs quidclaw CLI ──────► │ Beancount
                   │                                  │ Engine
                   │  manages files directly          │
                   │    ├── notes/    (knowledge)     │
                   │    ├── inbox/    (imports)       │
                   │    └── documents/(archive)       │
                   │                                  │
                   │  All data stays here ◄───────────│
                   └─────────────────────────────────┘
```

The AI reads the generated `CLAUDE.md`, understands the project structure, and uses the `quidclaw` CLI for accounting operations (transactions, balances, queries, reports). File operations — notes, document organization, inbox management — are handled directly by the AI using its native tools. Workflow guides (`.quidclaw/workflows/`) teach the AI how to handle complex multi-step tasks like onboarding, bill import, and reconciliation.

## Features

- **Natural language input** — Speak any language. The AI translates your words into structured transactions.
- **Multi-currency** — CNY, USD, EUR, JPY, or any currency. Mixed-currency accounts supported.
- **Bill import** — Drop bank statements or receipts into `inbox/`. The AI parses, deduplicates, and records them.
- **Duplicate detection** — Catches double-charges, repeated subscriptions, and already-imported transactions.
- **Document organization** — AI files documents from your inbox into a clean `documents/YYYY/MM/` archive.
- **Financial knowledge base** — Living notes for profiles, payment calendars, asset tracking, and decision logs.
- **Anomaly detection** — Flags duplicate charges, subscription price changes, spending outliers, and unknown merchants.
- **Monthly reports** — Income vs. expenses, category breakdowns, month-over-month comparisons, top expenses.
- **BQL queries** — Full Beancount Query Language access for custom analysis.
- **Reconciliation** — Balance assertions to verify your data matches your bank.

## Quick Start

```bash
pip install quidclaw
mkdir ~/my-finances && cd ~/my-finances
quidclaw init
claude    # or: gemini, codex, cursor — any AI coding tool
```

That's it. The AI reads the generated `CLAUDE.md`, understands your financial project, and starts managing your finances. Start by saying hello — it will walk you through onboarding.

## Supported AI Tools

| Tool | Instruction File | Status |
|------|-----------------|--------|
| Claude Code | `CLAUDE.md` | Supported |
| Gemini CLI | `GEMINI.md` | Planned |
| OpenAI Codex | `AGENTS.md` | Planned |
| Cursor | `CLAUDE.md` | Works |
| Any tool with Bash access | `CLAUDE.md` | Works |

QuidClaw generates `CLAUDE.md` on `init`. Support for other instruction file formats (`GEMINI.md`, `AGENTS.md`) is planned — the workflow content is the same, only the filename and format differ.

## Usage Example

```
You:   这个月花了多少钱？
AI:    Let me check... [runs quidclaw monthly-summary 2026 03]

       3月支出总计 ¥12,847.50

       餐饮      ¥3,240.00  (25.2%)
       房租      ¥4,500.00  (35.0%)
       交通      ¥1,080.00  (8.4%)
       日用品    ¥890.50    (6.9%)
       其他      ¥3,137.00  (24.4%)

       比上月多花了 ¥1,200 (+10.3%)，主要增长在餐饮。

You:   午饭花了45，微信付的
AI:    Done. [runs quidclaw add-txn ...]
       Recorded: 2026-03-20 午餐 ¥45.00 (WeChat → Expenses:Food:Dining)

You:   Put the CMB statement in my inbox, help me import it
AI:    [reads .quidclaw/workflows/import-bills.md]
       [scans inbox/, parses the CSV, deduplicates, records 47 transactions]
       Found 52 transactions in the statement. 5 were already recorded.
       Imported 47 new transactions totaling ¥8,932.10.
```

## Data Storage

```
my-finances/
├── CLAUDE.md                  # AI instructions (auto-generated)
├── .quidclaw/
│   └── workflows/             # AI workflow guides (auto-generated)
│       ├── onboarding.md
│       ├── import-bills.md
│       ├── reconcile.md
│       ├── monthly-review.md
│       ├── detect-anomalies.md
│       ├── organize-documents.md
│       └── financial-memory.md
├── ledger/                    # Beancount ledger (structured, verified)
│   ├── main.bean              #   includes all other files
│   ├── accounts.bean          #   Open/Close directives
│   ├── prices.bean            #   Price directives
│   └── YYYY/YYYY-MM.bean     #   Transactions by month
├── inbox/                     # Drop zone — put files here
├── documents/                 # Organized archive (AI-managed)
│   └── YYYY/MM/               #   Filed by year and month
├── notes/                     # Financial knowledge base (AI-managed)
│   ├── profile.md             #   User profile (living)
│   ├── calendar.md            #   Payment calendar (living)
│   ├── assets/                #   Property, vehicles, investments
│   ├── liabilities/           #   Loans, debts
│   ├── insurance/             #   Policy details
│   ├── accounts/              #   Bank/card details
│   ├── subscriptions/         #   Recurring charges
│   ├── income/                #   Income sources
│   ├── decisions/             #   Decision log (append-only)
│   └── journal/               #   Conversation captures (append-only)
└── reports/                   # Generated reports (AI-managed)
```

## CLI Reference

17 commands for Beancount operations. The AI calls these via Bash. Most commands support `--json` for structured output.

### Setup

| Command | Description |
|---------|-------------|
| `quidclaw init` | Initialize a new financial project in the current directory |
| `quidclaw upgrade` | Upgrade workflow files and CLAUDE.md to latest version |

### Ledger Operations

| Command | Description |
|---------|-------------|
| `quidclaw add-account NAME` | Open a new account (`--currencies`, `--date`) |
| `quidclaw close-account NAME` | Close an account (`--date`) |
| `quidclaw list-accounts` | List all accounts (`--type`, `--json`) |
| `quidclaw add-txn` | Record a transaction (`--date`, `--payee`, `--narration`, `--posting`) |
| `quidclaw balance` | Query account balances (`--account`, `--json`) |
| `quidclaw balance-check ACCOUNT EXPECTED` | Reconciliation: assert an account balance (`--currency`, `--date`) |
| `quidclaw query "SELECT ..."` | Execute a BQL query (`--json`) |
| `quidclaw report income\|balance_sheet` | Generate a financial report (`--period`) |

### Insights and Analysis

| Command | Description |
|---------|-------------|
| `quidclaw monthly-summary YYYY MM` | Income, expenses, and savings for a month (`--json`) |
| `quidclaw spending-by-category YYYY MM` | Ranked category breakdown for a month (`--json`) |
| `quidclaw month-comparison YYYY MM` | Month-over-month comparison with percentages |
| `quidclaw largest-txns YYYY MM` | Top N largest expense transactions (`--limit`) |
| `quidclaw detect-anomalies` | Run all anomaly checks (`--json`) |

### Data Management

| Command | Description |
|---------|-------------|
| `quidclaw data-status` | Inbox count, last ledger update (`--json`) |
| `quidclaw fetch-prices [COMMODITIES...]` | Fetch and record asset prices *(not yet implemented)* |

## Workflows

7 workflow guides that teach the AI how to handle complex multi-step tasks. Stored in `.quidclaw/workflows/` and auto-generated by `quidclaw init`.

| Workflow | Trigger | What It Does |
|----------|---------|-------------|
| `onboarding.md` | First conversation with a new user | Interview-style discovery of the user's financial life. Everything goes to notes, nothing to ledger. |
| `import-bills.md` | User drops files in inbox or uploads in chat | Parse bank statements/receipts, deduplicate, record transactions, archive source files. |
| `reconcile.md` | Before any report or financial question | Verify data completeness — check for gaps, run balance assertions, flag discrepancies. |
| `monthly-review.md` | User asks for a monthly summary or review | Generate plain-language financial report with trends, anomalies, and actionable insights. |
| `detect-anomalies.md` | User asks to check for issues, or proactively | Scan for duplicate charges, subscription price changes, spending outliers, unknown merchants. |
| `organize-documents.md` | Files accumulate in inbox | Sort and file documents from inbox into `documents/YYYY/MM/` with proper naming. |
| `financial-memory.md` | User shares non-transaction financial info | Capture insurance policies, loan terms, salary changes, financial decisions into notes. |

## Development

```bash
git clone https://github.com/thorb/quidclaw
cd quidclaw
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest                            # run all tests
pytest tests/core/                # core logic tests only
pytest tests/test_integration.py  # end-to-end workflow
```

### Tech Stack

- Python 3.10 - 3.13
- [Beancount V3](https://github.com/beancount/beancount) — accounting engine
- [beanquery](https://github.com/beancount/beanquery) — BQL query execution
- [Click](https://click.palletsprojects.com/) — CLI framework
- [PyYAML](https://pyyaml.org/) — YAML frontmatter parsing for notes

## Author

Yue Jiang

## License

GPL-2.0
