# QuidClaw

Zero-barrier personal CFO.

**Local-first. Privacy by design. Your data never leaves your machine.**

QuidClaw turns any AI coding tool into a personal finance manager. It combines a CLI for Beancount accounting operations with Agent Skills (agentskills.io standard), so the AI knows exactly how to record transactions, import bank statements, detect anomalies, and generate reports. You talk to your AI in natural language — in any language — and it handles the bookkeeping. Works with Claude Code, Gemini CLI, OpenAI Codex, Cursor, or anything else that supports agent skills.

> "I had lunch for $15, paid with my debit card"
>
> The AI records a $15 lunch expense from your bank account. No forms, no menus, no learning curve.

## Why QuidClaw

- **Privacy first** — Everything runs locally. No cloud, no telemetry, no third-party access. Your financial data is plain text files on your machine.
- **You own your data** — Beancount plain text format. Version control with git. No vendor lock-in. Export, migrate, or audit anytime.
- **Zero barrier** — Talk to your AI the way you talk to a friend. Say "I paid rent today, $2400" or "spent €30 on groceries" and it just works.
- **Works with any AI** — Not locked to one tool. Claude Code today, Gemini CLI tomorrow. Skills are installed to each platform's native directory.
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

The AI reads the generated entry file (e.g. `CLAUDE.md`), discovers the installed skills, and uses the `quidclaw` CLI for accounting operations (transactions, balances, queries, reports). File operations — notes, document organization, inbox management — are handled directly by the AI using its native tools. Five Agent Skills teach the AI how to handle complex multi-step tasks like onboarding, bill import, daily routines, and financial review.

## Features

- **Natural language input** — Speak any language. The AI translates your words into structured transactions.
- **Multi-currency** — USD, EUR, GBP, JPY, or any currency. Mixed-currency accounts supported.
- **Bill import** — Drop bank statements or receipts into `inbox/`. The AI parses, deduplicates, and records them.
- **Duplicate detection** — Catches double-charges, repeated subscriptions, and already-imported transactions.
- **Document organization** — AI files documents from your inbox into a clean `documents/YYYY/MM/` archive.
- **Financial knowledge base** — Living notes for profiles, payment calendars, asset tracking, and decision logs.
- **Anomaly detection** — Flags duplicate charges, subscription price changes, spending outliers, and unknown merchants.
- **Monthly reports** — Income vs. expenses, category breakdowns, month-over-month comparisons, top expenses.
- **BQL queries** — Full Beancount Query Language access for custom analysis.
- **Reconciliation** — Balance assertions to verify your data matches your bank.
- **Email integration** — Forward bills to a dedicated email address. QuidClaw syncs and processes them automatically.
- **Audit trail** — Every transaction traces back to its source document. Processing logs record what was extracted and confirmed.
- **Extensible data sources** — Pull data from email (AgentMail), with architecture ready for future sources (bank APIs, broker integrations).
- **Git backup** — Automatic version control with multi-remote backup. Every change is committed and pushed to GitHub, Gitee, or any Git host. Supports Git LFS for binary files.

## Quick Start

### OpenClaw (recommended)

```bash
pip install quidclaw
quidclaw init --platform openclaw
```

This creates a dedicated financial agent. Connect it to Telegram, WhatsApp, or any supported chat app. The agent handles onboarding, daily routines, and monthly reports automatically.

### Claude Code

```bash
pip install quidclaw
mkdir ~/my-finances && cd ~/my-finances
quidclaw init --platform claude-code
claude
```

### Other AI Tools

```bash
pip install quidclaw
mkdir ~/my-finances && cd ~/my-finances
quidclaw init   # interactive platform selection
```

## Usage Example

```
You:   How much did I spend this month?
AI:    Let me check... [runs quidclaw monthly-summary 2026 03]

       Total expenses for March: $4,285.50

       Rent         $2,400.00  (56.0%)
       Dining       $540.00    (12.6%)
       Groceries    $380.00    (8.9%)
       Transport    $275.50    (6.4%)
       Other        $690.00    (16.1%)

       That's $320 more than last month (+8.1%), mainly from dining.

You:   Lunch was $15, paid with my debit card
AI:    Done. [runs quidclaw add-txn ...]
       Recorded: 2026-03-20 Lunch $15.00 (Assets:Bank:Checking → Expenses:Food:Dining)

You:   Put my bank statement in the inbox, help me import it
AI:    [loads the quidclaw-import skill]
       [scans inbox/, parses the CSV, deduplicates, records 47 transactions]
       Found 52 transactions in the statement. 5 were already recorded.
       Imported 47 new transactions totaling $3,892.10.
```

## Data Storage

```
my-finances/
├── CLAUDE.md                  # AI entry file (auto-generated, points to skills)
├── .claude/skills/            # Agent Skills (auto-installed)
│   ├── quidclaw.md            #   Core: project structure + CLI reference
│   ├── quidclaw-onboarding.md #   New user interview
│   ├── quidclaw-import.md     #   Parse and import documents
│   ├── quidclaw-daily.md      #   Daily financial check-in
│   └── quidclaw-review.md     #   Monthly review + reconciliation
├── .quidclaw/
│   └── workflows/             # Legacy workflow guides (deprecated)
├── ledger/                    # Beancount ledger (structured, verified)
│   ├── main.bean              #   includes all other files
│   ├── accounts.bean          #   Open/Close directives
│   ├── prices.bean            #   Price directives
│   └── YYYY/YYYY-MM.bean     #   Transactions by month
├── sources/                  # Synced data from external sources
│   └── my-email/             #   Email provider data
├── logs/                     # Processing audit trail
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

## CLI & Workflows

31 commands for accounting operations, data source management, and backup. 5 Agent Skills for multi-step tasks. All designed for AI agents — the AI loads the skills and calls the CLI.

See [docs/cli-reference.md](docs/cli-reference.md) for the complete command list.

## Development

```bash
git clone https://github.com/ThorbJ/quidclaw
cd quidclaw
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest                            # run all tests
pytest tests/core/                # core logic tests only
pytest tests/test_integration.py  # end-to-end workflow
```

### Tech Stack

- Python 3.10 – 3.13 (3.14+ is not yet supported)
- [Beancount V3](https://github.com/beancount/beancount) — accounting engine
- [beanquery](https://github.com/beancount/beanquery) — BQL query execution
- [Click](https://click.palletsprojects.com/) — CLI framework
- [PyYAML](https://pyyaml.org/) — YAML frontmatter parsing for notes
- [agentmail](https://agentmail.to/) — email integration (optional)

## Author

Yue Jiang

## License

GPL-2.0
