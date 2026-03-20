# QuidClaw

Zero-barrier personal CFO.

## What It Is

QuidClaw is an AI-powered personal finance manager that runs entirely on your machine. It uses Beancount V3 as its accounting engine and stores everything as plain text files. QuidClaw works with any AI coding tool — Claude Code, Gemini CLI, OpenAI Codex, Cursor, or anything else that can run shell commands. All data stays local. There is zero cost to the developer: users bring their own AI subscription.

## Quick Start

```bash
pip install quidclaw
mkdir ~/my-finances && cd ~/my-finances
quidclaw init
claude    # or gemini, codex, cursor — any AI tool
```

That's it. The AI reads the generated `CLAUDE.md`, understands the project structure, and starts managing your finances.

## How It Works

When you run `quidclaw init`, it creates a financial project directory with a `CLAUDE.md` instruction file and workflow guides. Any AI coding tool that reads project instructions will immediately know how to manage your finances — recording transactions, importing bank statements, generating reports, detecting anomalies, and more. The AI uses the `quidclaw` CLI for accounting operations and handles file management (notes, documents, inbox) directly.

## Supported AI Tools

| Tool | Reads | Status |
|------|-------|--------|
| Claude Code / Coworker | `CLAUDE.md` | Supported |
| Gemini CLI | `GEMINI.md` | Planned |
| OpenAI Codex | `AGENTS.md` | Planned |
| Any tool with Bash | `CLAUDE.md` | Works |

## CLI Reference

| Command | Description |
|---------|-------------|
| `quidclaw init` | Initialize a new financial project in the current directory |
| `quidclaw upgrade` | Upgrade workflow files and instruction files to latest version |
| `quidclaw add-account NAME` | Open a new account |
| `quidclaw close-account NAME` | Close an account |
| `quidclaw list-accounts` | List all accounts (--type, --json) |
| `quidclaw add-txn` | Record a transaction (--date, --payee, --posting) |
| `quidclaw balance` | Query account balances (--account, --json) |
| `quidclaw balance-check ACCOUNT EXPECTED` | Reconciliation: assert an account balance |
| `quidclaw query "SELECT ..."` | Execute a BQL query (--json) |
| `quidclaw report income\|balance_sheet` | Generate a financial report (--period) |
| `quidclaw monthly-summary YYYY MM` | Income, expenses, and savings for a month (--json) |
| `quidclaw spending-by-category YYYY MM` | Ranked category breakdown for a month (--json) |
| `quidclaw month-comparison YYYY MM` | Month-over-month comparison with percentages |
| `quidclaw largest-txns YYYY MM` | Top N largest expense transactions (--limit) |
| `quidclaw detect-anomalies` | Run all anomaly checks (--json) |
| `quidclaw data-status` | Data freshness: inbox count, last ledger update (--json) |
| `quidclaw fetch-prices [COMMODITIES...]` | Fetch and record asset prices |

## Directory Structure

```
my-finances/
├── CLAUDE.md              # AI instructions (auto-generated)
├── .quidclaw/workflows/   # AI workflow guides
├── ledger/                # Beancount files
├── inbox/                 # Drop zone for documents
├── documents/             # Organized archive
├── notes/                 # Financial knowledge base
└── reports/               # Generated reports
```

## Privacy

Everything runs locally. No cloud services, no telemetry, no data leaves your machine. Your financial data is stored as plain text files that you own and can version control with git.

## License

GPL-2.0
