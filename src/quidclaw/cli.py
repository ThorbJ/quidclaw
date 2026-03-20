"""QuidClaw CLI — AI-friendly interface to Beancount operations."""

import json
import os
import shutil
import sys
from importlib import resources
from pathlib import Path

import click

from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger


def get_config() -> QuidClawConfig:
    """Get config from current directory or QUIDCLAW_DATA_DIR."""
    data_dir = os.environ.get("QUIDCLAW_DATA_DIR", os.getcwd())
    return QuidClawConfig(data_dir)


def get_ledger() -> Ledger:
    """Get initialized ledger."""
    config = get_config()
    ledger = Ledger(config)
    if not config.main_bean.exists():
        click.echo("Error: No ledger found. Run 'quidclaw init' first.", err=True)
        sys.exit(1)
    return ledger


@click.group()
@click.version_option(version="0.3.0")
def main():
    """QuidClaw — Zero-barrier personal CFO powered by Beancount."""
    pass


# --- Setup ---


@main.command()
@click.option("--template", is_flag=True, default=True, help="Use default account template")
def init(template):
    """Initialize a new financial project in the current directory."""
    config = get_config()
    ledger = Ledger(config)
    ledger.init()

    if template:
        from quidclaw.core.init import LedgerInitializer
        initializer = LedgerInitializer(ledger)
        result = initializer.init_with_template()
        click.echo(result)

    # Copy workflow files
    workflows_dir = Path(__file__).parent / "workflows"
    target_dir = Path(config.data_dir) / ".quidclaw" / "workflows"
    if workflows_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in workflows_dir.glob("*.md"):
            shutil.copy2(f, target_dir / f.name)

    # Generate CLAUDE.md
    claude_md = Path(config.data_dir) / "CLAUDE.md"
    if not claude_md.exists():
        _generate_claude_md(config)
        click.echo("Created CLAUDE.md")

    click.echo(f"Initialized QuidClaw project in {config.data_dir}")


@main.command()
def upgrade():
    """Upgrade workflow files and instruction files to latest version."""
    config = get_config()

    workflows_dir = Path(__file__).parent / "workflows"
    target_dir = Path(config.data_dir) / ".quidclaw" / "workflows"
    if workflows_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in workflows_dir.glob("*.md"):
            shutil.copy2(f, target_dir / f.name)
        click.echo(f"Updated workflows in {target_dir}")

    _generate_claude_md(config)
    click.echo("Updated CLAUDE.md")
    click.echo("Upgrade complete.")


# --- Ledger Operations ---


@main.command("add-account")
@click.argument("name")
@click.option("--currencies", default="CNY", help="Comma-separated currencies")
@click.option("--date", "open_date", default=None, help="Open date (YYYY-MM-DD)")
def add_account(name, currencies, open_date):
    """Open a new account."""
    from quidclaw.core.accounts import AccountManager
    ledger = get_ledger()
    mgr = AccountManager(ledger)
    currency_list = [c.strip() for c in currencies.split(",")]
    result = mgr.add_account(name, currency_list, open_date)
    click.echo(result)


@main.command("close-account")
@click.argument("name")
@click.option("--date", "close_date", default=None, help="Close date (YYYY-MM-DD)")
def close_account(name, close_date):
    """Close an account."""
    from quidclaw.core.accounts import AccountManager
    ledger = get_ledger()
    mgr = AccountManager(ledger)
    result = mgr.close_account(name, close_date)
    click.echo(result)


@main.command("list-accounts")
@click.option("--type", "account_type", default=None, help="Filter by type (Assets, Liabilities, etc.)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_accounts(account_type, as_json):
    """List all accounts."""
    from quidclaw.core.accounts import AccountManager
    ledger = get_ledger()
    mgr = AccountManager(ledger)
    accounts = mgr.list_accounts(account_type)
    if as_json:
        click.echo(json.dumps(accounts, indent=2))
    else:
        for acc in accounts:
            click.echo(acc)


@main.command("add-txn")
@click.option("--date", required=True, help="Transaction date (YYYY-MM-DD)")
@click.option("--payee", required=True, help="Payee name")
@click.option("--narration", default="", help="Description")
@click.option("--posting", multiple=True, required=True, help='Posting as JSON: \'{"account":"...", "amount":"...", "currency":"..."}\'')
def add_txn(date, payee, narration, posting):
    """Record a transaction."""
    import datetime as dt
    from quidclaw.core.transactions import TransactionManager
    ledger = get_ledger()
    mgr = TransactionManager(ledger)
    postings = [json.loads(p) for p in posting]
    parsed_date = dt.date.fromisoformat(date)
    result = mgr.add_transaction(parsed_date, payee, narration, postings)
    click.echo(result)


@main.command()
@click.option("--account", default=None, help="Specific account (omit for all)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def balance(account, as_json):
    """Query account balances."""
    from quidclaw.core.balance import BalanceManager
    ledger = get_ledger()
    mgr = BalanceManager(ledger)
    if account:
        result = mgr.get_balance(account)
    else:
        result = mgr.get_all_balances()
    if as_json:
        # Convert Decimal to str for JSON
        serializable = {k: {ck: str(cv) for ck, cv in v.items()} if isinstance(v, dict) else str(v)
                       for k, v in result.items()}
        click.echo(json.dumps(serializable, indent=2))
    else:
        for k, v in result.items():
            click.echo(f"{k}: {v}")


@main.command("balance-check")
@click.argument("account")
@click.argument("expected")
@click.option("--currency", default="CNY")
@click.option("--date", default=None)
def balance_check(account, expected, currency, date):
    """Reconciliation: assert an account balance."""
    from quidclaw.core.balance import BalanceManager
    ledger = get_ledger()
    mgr = BalanceManager(ledger)
    ok, message = mgr.balance_check(account, expected, currency, date)
    click.echo(message)
    if not ok:
        sys.exit(1)


@main.command()
@click.argument("bql")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def query(bql, as_json):
    """Execute a BQL query."""
    from quidclaw.core.reports import ReportManager
    ledger = get_ledger()
    mgr = ReportManager(ledger)
    columns, rows = mgr.query(bql)
    if as_json:
        result = [dict(zip(columns, [str(v) for v in row])) for row in rows]
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo("\t".join(columns))
        for row in rows:
            click.echo("\t".join(str(v) for v in row))


@main.command()
@click.argument("report_type", type=click.Choice(["income", "balance_sheet"]))
@click.option("--period", default=None, help="Period filter")
def report(report_type, period):
    """Generate a financial report."""
    from quidclaw.core.reports import ReportManager
    ledger = get_ledger()
    mgr = ReportManager(ledger)
    if report_type == "income":
        result = mgr.income_statement(period)
    else:
        result = mgr.balance_sheet()
    click.echo(result)


@main.command("monthly-summary")
@click.argument("year", type=int)
@click.argument("month", type=int)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def monthly_summary(year, month, as_json):
    """Income, expenses, and savings for a month."""
    from quidclaw.core.reports import ReportManager
    ledger = get_ledger()
    mgr = ReportManager(ledger)
    result = mgr.monthly_summary(year, month)
    if as_json:
        serializable = {k: str(v) for k, v in result.items()}
        click.echo(json.dumps(serializable, indent=2))
    else:
        for k, v in result.items():
            click.echo(f"{k}: {v}")


@main.command("spending-by-category")
@click.argument("year", type=int)
@click.argument("month", type=int)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def spending_by_category(year, month, as_json):
    """Ranked category breakdown for a month."""
    from quidclaw.core.reports import ReportManager
    ledger = get_ledger()
    mgr = ReportManager(ledger)
    result = mgr.spending_by_category(year, month)
    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        click.echo(result)


@main.command("month-comparison")
@click.argument("year", type=int)
@click.argument("month", type=int)
def month_comparison(year, month):
    """Month-over-month comparison with percentages."""
    from quidclaw.core.reports import ReportManager
    ledger = get_ledger()
    mgr = ReportManager(ledger)
    result = mgr.month_over_month(year, month)
    click.echo(result)


@main.command("largest-txns")
@click.argument("year", type=int)
@click.argument("month", type=int)
@click.option("--limit", default=10, help="Number of transactions")
def largest_txns(year, month, limit):
    """Top N largest expense transactions."""
    from quidclaw.core.reports import ReportManager
    ledger = get_ledger()
    mgr = ReportManager(ledger)
    result = mgr.largest_transactions(year, month, limit)
    click.echo(result)


@main.command("detect-anomalies")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def detect_anomalies(as_json):
    """Run all anomaly checks."""
    from quidclaw.core.anomaly import AnomalyDetector
    ledger = get_ledger()
    detector = AnomalyDetector(ledger)
    results = {
        "duplicates": detector.find_duplicate_charges(),
        "recurring": detector.find_recurring_charges(),
        "price_changes": detector.find_price_changes(),
        "outliers": detector.find_large_outliers(),
        "unknown_merchants": detector.find_unknown_merchants(),
    }
    if as_json:
        click.echo(json.dumps(results, indent=2, default=str))
    else:
        for category, items in results.items():
            if items:
                click.echo(f"\n## {category}")
                for item in items:
                    click.echo(f"  - {item}")


@main.command("data-status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def data_status(as_json):
    """Data freshness: inbox count, last ledger update."""
    from quidclaw.core.inbox import InboxManager
    config = get_config()
    mgr = InboxManager(config)
    status = mgr.get_data_status()
    if as_json:
        click.echo(json.dumps(status, indent=2, default=str))
    else:
        click.echo(f"Inbox files: {status.get('inbox_count', 0)}")
        for f in status.get('inbox_files', []):
            click.echo(f"  - {f}")
        click.echo(f"Last modified: {status.get('last_modified', 'N/A')}")


@main.command("fetch-prices")
@click.argument("commodities", nargs=-1)
def fetch_prices(commodities):
    """Fetch and record asset prices."""
    from quidclaw.core.prices import PriceManager
    ledger = get_ledger()
    mgr = PriceManager(ledger)
    result = mgr.fetch_prices(list(commodities) if commodities else None)
    click.echo(result)


# --- Helpers ---


def _generate_claude_md(config: QuidClawConfig):
    """Generate CLAUDE.md for the financial project."""
    claude_md_path = Path(config.data_dir) / "CLAUDE.md"
    claude_md_path.write_text("""\
# QuidClaw — Personal CFO

You are a personal CFO managing finances in this directory.
Speak the user's language. Never mention beancount, double-entry, or accounting jargon.

## Directory Structure

- `ledger/` — Beancount ledger files (structured, verified data only)
- `inbox/` — Drop zone for unprocessed files (bank statements, receipts)
- `documents/` — Organized archive (by year/month)
- `notes/` — Financial knowledge base (living documents + append-only logs)
- `reports/` — Generated reports

## Available CLI Commands

Use these via Bash when you need Beancount engine operations:

```
quidclaw init                        # Initialize ledger
quidclaw add-account NAME            # Open account
quidclaw close-account NAME          # Close account
quidclaw list-accounts [--type X]    # List accounts
quidclaw add-txn --date D --payee P --posting '{...}'  # Record transaction
quidclaw balance [--account X]       # Query balances
quidclaw balance-check ACCT AMT      # Reconciliation assertion
quidclaw query "SELECT ..."          # Execute BQL query
quidclaw report income|balance_sheet # Financial reports
quidclaw monthly-summary YYYY MM     # Monthly income/expenses/savings
quidclaw spending-by-category YYYY MM # Category breakdown
quidclaw month-comparison YYYY MM    # Month-over-month changes
quidclaw largest-txns YYYY MM        # Top expenses
quidclaw detect-anomalies            # Find duplicates, outliers, etc.
quidclaw data-status                 # Inbox count, last ledger update
```

Most commands support `--json` for structured output.

## File Operations

For file operations, use your native tools directly:
- Read/write notes: Read and Write tools on `notes/*.md`
- List inbox: Glob `inbox/*`
- Search notes: Grep across `notes/`
- Move files: Bash `mv`
- List documents: Glob `documents/**/*`

## Workflows

Read `.quidclaw/workflows/<name>.md` for detailed workflow instructions:
- `onboarding.md` — New user setup
- `import-bills.md` — Parse and import financial documents
- `reconcile.md` — Data accuracy check (run before any report)
- `monthly-review.md` — Generate monthly financial review
- `detect-anomalies.md` — Scan for suspicious patterns
- `organize-documents.md` — Sort inbox files into documents/
- `financial-memory.md` — Capture non-transaction financial info

## Notes Structure

- **Living documents** (profile.md, calendar.md, assets/, accounts/, etc.) — always reflect current state
- **Append-only logs** (decisions/, journal/) — historical record, only grows

## Conventions

- Only verified data (bank statements, receipts) goes into the ledger
- Transactions go into monthly files: `ledger/YYYY/YYYY-MM.bean`
- Document naming: `{Source}-{Type}-{YYYY-MM}.{ext}`
- Account naming: use last 4 digits or identifiers (e.g., Assets:Bank:CMB:1234)
- Default currency: CNY (unless user specifies otherwise)
- Always reconcile before generating reports or answering financial questions
""")
