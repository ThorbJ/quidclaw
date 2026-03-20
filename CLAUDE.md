# QuidClaw

Zero-barrier personal CFO. AI-powered, local-first, powered by Beancount V3.

## Architecture

### Two Layers

- `src/quidclaw/core/` — Pure business logic. Depends only on Beancount, NOT on Click or any CLI framework. Every financial operation lives here.
- `src/quidclaw/cli.py` — Thin Click CLI adapter. Translates CLI commands into core function calls. No business logic here.

This separation exists so core logic can be reused by other adapters without importing Click.

### User-Facing Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Workflows** | `.quidclaw/workflows/` | AI workflow instructions (markdown), copied to user's project on `quidclaw init` |
| **Generated CLAUDE.md** | User's project root | Created by `quidclaw init`, tells AI how to use CLI and workflows |

Workflows are bundled inside the package (`src/quidclaw/workflows/`) and copied to the user's `.quidclaw/workflows/` directory during init. The generated CLAUDE.md is produced by `_generate_claude_md()` in `cli.py`.

## Key Files

| File | Purpose |
|------|---------|
| `src/quidclaw/config.py` | `QuidClawConfig` dataclass — data directory paths |
| `src/quidclaw/cli.py` | Click CLI — all commands + `_generate_claude_md()` |
| `src/quidclaw/core/ledger.py` | `Ledger` — init, load, append to .bean files |
| `src/quidclaw/core/accounts.py` | `AccountManager` — open/close/list accounts |
| `src/quidclaw/core/transactions.py` | `TransactionManager` — add transactions to monthly files |
| `src/quidclaw/core/balance.py` | `BalanceManager` — balance queries and assertions |
| `src/quidclaw/core/reports.py` | `ReportManager` — BQL queries, monthly summaries, category breakdowns |
| `src/quidclaw/core/anomaly.py` | `AnomalyDetector` — duplicates, subscriptions, outliers, unknown merchants |
| `src/quidclaw/core/prices.py` | `PriceManager` — write price directives |
| `src/quidclaw/core/init.py` | `LedgerInitializer` — default account templates |
| `src/quidclaw/core/inbox.py` | `InboxManager` — inbox files, data status |

## Development

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest                          # all tests
pytest tests/core/              # core logic tests
pytest tests/test_cli.py        # CLI tests
```

## CLI Commands

### Setup (2)

| Command | Purpose |
|---------|---------|
| `quidclaw init` | Initialize a new financial project in the current directory |
| `quidclaw upgrade` | Upgrade workflow files and CLAUDE.md to latest version |

### Ledger Operations (7)

| Command | Purpose |
|---------|---------|
| `quidclaw add-account NAME` | Open a new account |
| `quidclaw close-account NAME` | Close an account |
| `quidclaw list-accounts` | List all accounts (filter with `--type`) |
| `quidclaw add-txn` | Record a transaction (requires `--date`, `--payee`, `--posting`) |
| `quidclaw balance` | Query account balances (filter with `--account`) |
| `quidclaw balance-check ACCT AMT` | Reconciliation: assert an account balance |
| `quidclaw fetch-prices [COMMODITIES...]` | Fetch and record asset prices *(not yet implemented)* |

### Reports & Queries (6)

| Command | Purpose |
|---------|---------|
| `quidclaw query "SELECT ..."` | Execute a BQL query |
| `quidclaw report income\|balance_sheet` | Generate a financial report |
| `quidclaw monthly-summary YYYY MM` | Income, expenses, and savings for a month |
| `quidclaw spending-by-category YYYY MM` | Ranked category breakdown for a month |
| `quidclaw month-comparison YYYY MM` | Month-over-month comparison with percentages |
| `quidclaw largest-txns YYYY MM` | Top N largest expense transactions |

### Data & Anomalies (2)

| Command | Purpose |
|---------|---------|
| `quidclaw detect-anomalies` | Run all anomaly checks (duplicates, outliers, subscriptions, unknown merchants) |
| `quidclaw data-status` | Data freshness: inbox count, last ledger update |

## How to Add a New CLI Command

1. Add core logic in `src/quidclaw/core/<module>.py` with tests in `tests/core/`
2. Add a Click command in `src/quidclaw/cli.py` under the appropriate section
3. Add CLI test in `tests/test_cli.py`
4. Update the command list in `_generate_claude_md()` so user-facing CLAUDE.md stays current

Pattern:
```python
@main.command("my-command")
@click.argument("arg")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def my_command(arg, as_json):
    """One-line description."""
    from quidclaw.core.module import Manager
    ledger = get_ledger()  # or get_config() for non-ledger operations
    mgr = Manager(ledger)
    result = mgr.some_method(arg)
    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        click.echo(result)
```

## How to Add a New Workflow

1. Create `.quidclaw/workflows/<name>.md` (and the bundled copy in `src/quidclaw/workflows/`)
2. Workflow instructions should use CLI commands (via Bash) for Beancount operations
3. Use native AI tools (Read, Write, Glob, Grep) for file operations — never reference MCP tools
4. Reference the new workflow in `_generate_claude_md()` so users know it exists

## Conventions

- Core classes that operate on ledger data take a `Ledger` instance in their constructor
- Core classes that operate on files (inbox, notes) take a `QuidClawConfig` instance
- All CLI commands support `--json` where applicable for structured AI-friendly output
- Workflows never reference MCP tools — they use CLI commands and native AI tools
- Tests use `tmp_path` fixture for isolated data directories
- Data directory: current working directory by default, override with `QUIDCLAW_DATA_DIR` env var
- Transactions go into monthly files: `ledger/YYYY/YYYY-MM.bean`
- Document naming convention: `{Source}-{Type}-{YYYY-MM}.{ext}`
- Account naming: use last 4 digits or identifiers (e.g., `Assets:Bank:CMB:1234`)
