"""QuidClaw CLI — AI-friendly interface to Beancount operations."""

import json
import os
import shutil
import sys
from pathlib import Path

import click

from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger

# Register built-in providers
try:
    import quidclaw.core.sources.agentmail  # noqa: F401
except ImportError:
    pass


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


def _try_backup(config: QuidClawConfig, message: str) -> None:
    """Attempt git backup if initialized. Never raises."""
    try:
        from quidclaw.core.backup import try_backup
        try_backup(config, message)
    except Exception:
        pass


def _install_skills(config: QuidClawConfig, platform: str) -> None:
    """Copy bundled skills to the platform-appropriate skills directory."""
    skills_source = Path(__file__).parent / "skills"
    if not skills_source.exists():
        return
    skills_dir_name = PLATFORM_SKILLS_DIR.get(platform, ".agents/skills")
    skills_target = Path(config.data_dir) / skills_dir_name
    for skill_dir in skills_source.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            target = skills_target / skill_dir.name
            shutil.copytree(skill_dir, target, dirs_exist_ok=True)


def _build_entry_file(config: QuidClawConfig) -> str:
    """Build minimal platform entry file pointing to skills."""
    currency = config.get_setting("operating_currency")
    currency_line = (
        f"- Operating currency: {currency}"
        if currency
        else "- Operating currency: not yet configured (run onboarding)"
    )
    return f"""\
# QuidClaw — Personal CFO

You are a personal CFO managing finances in this directory.
Speak the user's language. Never mention beancount, double-entry, or accounting jargon.

## Configuration

{currency_line}
- Config: `.quidclaw/config.yaml`

## Skills

QuidClaw capabilities are provided as Agent Skills:
- `quidclaw` — Project overview, CLI reference, conventions
- `quidclaw-onboarding` — New user setup interview
- `quidclaw-import` — Import and process financial data
- `quidclaw-daily` — Daily financial routine
- `quidclaw-review` — Monthly review and reporting
"""


@click.group()
@click.version_option(version="0.4.0")
def main():
    """QuidClaw — Zero-barrier personal CFO powered by Beancount."""
    pass


# --- Setup ---


PLATFORMS = ["openclaw", "claude-code", "gemini", "codex"]

PLATFORM_SKILLS_DIR = {
    "openclaw": ".claude/skills",
    "claude-code": ".claude/skills",
    "gemini": ".gemini/skills",
    "codex": ".agents/skills",
}


@main.command()
@click.option("--platform", type=click.Choice(PLATFORMS), default=None,
              help="Target platform (openclaw, claude-code, gemini, codex)")
def init(platform):
    """Initialize a new financial project in the current directory."""
    if platform is None:
        click.echo("Which platform are you using?")
        click.echo("  1. OpenClaw (recommended)")
        click.echo("  2. Claude Code")
        click.echo("  3. Gemini CLI")
        click.echo("  4. Codex")
        click.echo("  5. Other")
        choice = click.prompt("", type=click.IntRange(1, 5))
        platform = {1: "openclaw", 2: "claude-code", 3: "gemini",
                    4: "codex", 5: "codex"}[choice]

    config = get_config()
    ledger = Ledger(config)
    ledger.init()

    # Store platform choice
    config.set_setting("platform", platform)

    # Install skills
    _install_skills(config, platform)

    # Generate platform entry file
    entry = _build_entry_file(config)
    data_dir = Path(config.data_dir)

    if platform == "openclaw":
        from quidclaw.core.openclaw import OpenClawSetup
        setup = OpenClawSetup(config)
        setup.generate_templates()
        setup.generate_agents_md(entry)

        # Auto-enable git backup
        from quidclaw.core.backup import BackupManager
        mgr = BackupManager(config)
        if mgr.is_git_available() and not mgr.is_initialized():
            mgr.init()
            click.echo("Git backup: initialized")

        # Try to create OpenClaw agent
        if setup.is_available():
            if setup.create_agent():
                click.echo("OpenClaw agent 'quidclaw' created.")
            else:
                click.echo("Warning: Could not create OpenClaw agent.", err=True)
                click.echo(f"  Run: openclaw agents add quidclaw --workspace {config.data_dir}", err=True)
        else:
            click.echo("Note: openclaw CLI not found. After installing, run:")
            click.echo(f"  openclaw agents add quidclaw --workspace {config.data_dir}")
    elif platform == "claude-code":
        (data_dir / "CLAUDE.md").write_text(entry)
    elif platform == "gemini":
        (data_dir / "GEMINI.md").write_text(entry)
    elif platform == "codex":
        (data_dir / "AGENTS.md").write_text(entry)

    click.echo(f"Initialized QuidClaw project in {config.data_dir}")
    _try_backup(config, "Initialize QuidClaw data directory")


@main.command()
def upgrade():
    """Upgrade skills and entry file to latest version."""
    config = get_config()

    # Update skills
    _install_skills(config, config.get_setting("platform", "claude-code"))
    click.echo("Updated skills")

    if config.main_bean.exists():
        ledger = Ledger(config)
        ledger.ensure_dirs()

    platform = config.get_setting("platform", "claude-code")

    # Update platform entry file
    entry = _build_entry_file(config)
    data_dir = Path(config.data_dir)

    if platform == "openclaw":
        from quidclaw.core.openclaw import OpenClawSetup
        setup = OpenClawSetup(config)
        setup.generate_templates()
        setup.generate_agents_md(entry)
        click.echo("Updated OpenClaw files")
    elif platform == "claude-code":
        (data_dir / "CLAUDE.md").write_text(entry)
        click.echo("Updated CLAUDE.md")
    elif platform == "gemini":
        (data_dir / "GEMINI.md").write_text(entry)
        click.echo("Updated GEMINI.md")
    elif platform == "codex":
        (data_dir / "AGENTS.md").write_text(entry)
        click.echo("Updated AGENTS.md")

    click.echo("Upgrade complete.")
    _try_backup(config, "Upgrade QuidClaw skills")


@main.command("set-config")
@click.argument("key")
@click.argument("value")
def set_config(key, value):
    """Set a configuration value."""
    config = get_config()
    config.set_setting(key, value)

    # If setting operating_currency, also update main.bean
    if key == "operating_currency" and config.main_bean.exists():
        content = config.main_bean.read_text()
        if 'option "operating_currency"' in content:
            import re
            content = re.sub(
                r'option "operating_currency" ".*?"',
                f'option "operating_currency" "{value}"',
                content,
            )
        else:
            # Insert after the title line
            content = content.replace(
                'option "title" "QuidClaw Ledger"\n',
                f'option "title" "QuidClaw Ledger"\n'
                f'option "operating_currency" "{value}"\n',
            )
        config.main_bean.write_text(content)

    click.echo(f"Set {key} = {value}")
    _try_backup(config, f"Update config: {key}")


@main.command("get-config")
@click.argument("key", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def get_config_cmd(key, as_json):
    """Get configuration values."""
    config = get_config()
    if key:
        value = config.get_setting(key)
        if as_json:
            click.echo(json.dumps({key: value}))
        else:
            click.echo(f"{key}: {value}" if value is not None else f"{key}: (not set)")
    else:
        settings = config.load_settings()
        if as_json:
            click.echo(json.dumps(settings, indent=2))
        else:
            if not settings:
                click.echo("No settings configured.")
            for k, v in settings.items():
                click.echo(f"{k}: {v}")


@main.command()
def setup():
    """Create default accounts using configured operating currency."""
    from quidclaw.core.init import LedgerInitializer
    ledger = get_ledger()
    operating = ledger.config.get_setting("operating_currency")
    if not operating:
        click.echo("Error: operating_currency not set. Run 'quidclaw set-config operating_currency CNY' first.", err=True)
        sys.exit(1)
    initializer = LedgerInitializer(ledger)
    created = initializer.init_with_template()
    if created:
        click.echo(f"Created {len(created)} default accounts ({operating})")
        _try_backup(ledger.config, f"Set up default accounts ({operating})")
    else:
        click.echo("All default accounts already exist.")


# --- Ledger Operations ---


@main.command("add-account")
@click.argument("name")
@click.option("--currencies", default=None, help="Comma-separated currencies")
@click.option("--date", "open_date", default=None, help="Open date (YYYY-MM-DD)")
@click.option("--meta", default=None, help='Metadata as JSON: \'{"institution":"..."}\'')
def add_account(name, currencies, open_date, meta):
    """Open a new account."""
    from quidclaw.core.accounts import AccountManager
    ledger = get_ledger()
    mgr = AccountManager(ledger)
    currency_list = [c.strip() for c in currencies.split(",")] if currencies else None
    metadata = json.loads(meta) if meta else None
    mgr.add_account(name, currency_list, open_date, metadata=metadata)
    click.echo(f"Opened account {name}")
    _try_backup(ledger.config, f"Add account: {name}")


@main.command("close-account")
@click.argument("name")
@click.option("--date", "close_date", default=None, help="Close date (YYYY-MM-DD)")
def close_account(name, close_date):
    """Close an account."""
    from quidclaw.core.accounts import AccountManager
    ledger = get_ledger()
    mgr = AccountManager(ledger)
    mgr.close_account(name, close_date)
    click.echo(f"Closed account {name}")
    _try_backup(ledger.config, f"Close account: {name}")


@main.command("add-note")
@click.argument("account")
@click.argument("note")
@click.option("--date", "note_date", default=None, help="Note date (YYYY-MM-DD, defaults to today)")
def add_note(account, note, note_date):
    """Add a Beancount note to an account."""
    import datetime as dt
    from quidclaw.core.accounts import AccountManager
    ledger = get_ledger()
    mgr = AccountManager(ledger)
    parsed_date = dt.date.fromisoformat(note_date) if note_date else None
    mgr.add_note(account, note, parsed_date)
    click.echo(f"Note added to {account}")
    _try_backup(ledger.config, f"Add note: {account}")


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
@click.option("--meta", default=None, help='Metadata as JSON: \'{"source":"..."}\'')
@click.option("--flag", default="*", help="Transaction flag: * (cleared), ! (pending), or A-Z")
@click.option("--tag", multiple=True, help="Tag (without #), can be repeated")
@click.option("--link", multiple=True, help="Link (without ^), can be repeated")
def add_txn(date, payee, narration, posting, meta, flag, tag, link):
    """Record a transaction."""
    import datetime as dt
    from quidclaw.core.transactions import TransactionManager
    ledger = get_ledger()
    mgr = TransactionManager(ledger)
    postings = [json.loads(p) for p in posting]
    parsed_date = dt.date.fromisoformat(date)
    metadata = json.loads(meta) if meta else None
    tags = list(tag) if tag else None
    links = list(link) if link else None
    mgr.add_transaction(parsed_date, payee, narration, postings, metadata,
                        flag=flag, tags=tags, links=links)
    click.echo(f"Recorded transaction: {date} {payee}")
    _try_backup(ledger.config, f"Add transaction: {payee}")


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


@main.command("add-document")
@click.argument("account")
@click.argument("path")
@click.option("--date", "doc_date", default=None, help="Document date (YYYY-MM-DD, defaults to today)")
def add_document(account, path, doc_date):
    """Link a document to an account (Beancount document directive)."""
    import datetime as dt
    from quidclaw.core.documents import DocumentManager
    ledger = get_ledger()
    mgr = DocumentManager(ledger)
    parsed_date = dt.date.fromisoformat(doc_date) if doc_date else None
    mgr.add_document(account, path, parsed_date)
    click.echo(f"Document linked: {account} <- {path}")
    _try_backup(ledger.config, f"Add document: {account}")


@main.command("add-pad")
@click.argument("account")
@click.option("--source", default="Equity:Opening-Balances", help="Source account (default: Equity:Opening-Balances)")
@click.option("--date", "pad_date", required=True, help="Pad date (YYYY-MM-DD)")
def add_pad(account, source, pad_date):
    """Write a pad directive to auto-fill balance gaps."""
    import datetime as dt
    from quidclaw.core.balance import BalanceManager
    ledger = get_ledger()
    mgr = BalanceManager(ledger)
    parsed_date = dt.date.fromisoformat(pad_date)
    mgr.add_pad(account, source, parsed_date)
    click.echo(f"Pad: {pad_date} {account} <- {source}")
    _try_backup(ledger.config, f"Pad: {account}")


@main.command("add-balance")
@click.argument("account")
@click.option("--amount", required=True, help="Expected balance amount")
@click.option("--currency", default=None, help="Currency (defaults to operating currency)")
@click.option("--date", "bal_date", required=True, help="Assertion date (YYYY-MM-DD)")
def add_balance(account, amount, currency, bal_date):
    """Write a balance assertion to the ledger."""
    import datetime as dt
    from decimal import Decimal
    from quidclaw.core.balance import BalanceManager
    ledger = get_ledger()
    if currency is None:
        currency = ledger.config.get_setting("operating_currency", "CNY")
    mgr = BalanceManager(ledger)
    parsed_date = dt.date.fromisoformat(bal_date)
    mgr.add_balance_assertion(account, Decimal(amount), currency, parsed_date)
    click.echo(f"Balance assertion: {bal_date} {account} {amount} {currency}")
    _try_backup(ledger.config, f"Balance assertion: {account}")


@main.command("balance-check")
@click.argument("account")
@click.argument("expected")
@click.option("--currency", default=None, help="Currency (defaults to operating currency)")
def balance_check(account, expected, currency):
    """Reconciliation: assert an account balance."""
    from decimal import Decimal
    from quidclaw.core.balance import BalanceManager
    ledger = get_ledger()
    if currency is None:
        currency = ledger.config.get_setting("operating_currency", "CNY")
    mgr = BalanceManager(ledger)
    ok, message = mgr.balance_check(account, Decimal(expected), currency)
    click.echo(message)
    if ok:
        _try_backup(ledger.config, f"Balance assertion: {account}")
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
        for item in result:
            click.echo(f"{item['category']}: {item['amount']} {item['currency']}")


@main.command("month-comparison")
@click.argument("year", type=int)
@click.argument("month", type=int)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def month_comparison(year, month, as_json):
    """Month-over-month comparison with percentages."""
    from quidclaw.core.reports import ReportManager
    ledger = get_ledger()
    mgr = ReportManager(ledger)
    result = mgr.month_over_month(year, month)
    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        for item in result:
            sign = "+" if item["change_pct"] > 0 else ""
            click.echo(f"{item['category']}: {item['current']} {item['currency']} (prev: {item['previous']}, {sign}{item['change_pct']}%)")


@main.command("largest-txns")
@click.argument("year", type=int)
@click.argument("month", type=int)
@click.option("--limit", default=10, help="Number of transactions")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def largest_txns(year, month, limit, as_json):
    """Top N largest expense transactions."""
    from quidclaw.core.reports import ReportManager
    ledger = get_ledger()
    mgr = ReportManager(ledger)
    result = mgr.largest_transactions(year, month, limit)
    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        for item in result:
            click.echo(f"{item['date']} {item['payee']}: {item['amount']} {item['currency']} ({item['account']})")


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


@main.command("add-commodity")
@click.argument("name")
@click.option("--source", required=True, help='Price source (e.g., "yahoo/AAPL")')
@click.option("--quote", default="USD", help="Quote currency (default: USD)")
@click.option("--date", "open_date", default=None, help="Date (YYYY-MM-DD)")
def add_commodity(name, source, quote, open_date):
    """Register a commodity (stock, fund, custom asset) for price tracking."""
    import datetime as dt
    from quidclaw.core.prices import PriceManager
    ledger = get_ledger()
    mgr = PriceManager(ledger)
    date = dt.date.fromisoformat(open_date) if open_date else None
    try:
        mgr.add_commodity(name, source, quote, date)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    click.echo(f"Registered commodity {name} ({quote}:{source})")
    _try_backup(ledger.config, f"Add commodity: {name}")


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
    _try_backup(config, f"Add data source: {name}")


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
    _try_backup(config, f"Remove data source: {name}")


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

    total = sum(r.items_fetched for r in all_results)
    if total > 0:
        sources_str = ", ".join(r.source_name for r in all_results if r.items_fetched > 0)
        _try_backup(config, f"Sync: {total} new items from {sources_str}")

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
    _try_backup(config, f"Mark processed: {source_name}/{email_dir}")


@main.command("fetch-prices")
@click.argument("commodities", nargs=-1)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def fetch_prices(commodities, as_json):
    """Fetch and record asset prices from configured sources."""
    from quidclaw.core.prices import PriceManager
    ledger = get_ledger()
    mgr = PriceManager(ledger)
    try:
        results = mgr.fetch_prices(list(commodities) if commodities else None)
    except (ValueError, ImportError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    if as_json:
        click.echo(json.dumps(results, indent=2))
    else:
        for r in results:
            if "error" in r:
                click.echo(f"  {r['commodity']}: ERROR — {r['error']}", err=True)
            else:
                click.echo(f"  {r['commodity']}: {r['price']} {r['currency']} ({r['date']})")
    _try_backup(ledger.config, "Fetch prices")


# --- Backup ---


@main.group()
def backup():
    """Git backup management."""
    pass


@backup.command("init")
def backup_init():
    """Initialize Git backup for this data directory."""
    from quidclaw.core.backup import BackupManager
    config = get_config()
    mgr = BackupManager(config)
    if not mgr.is_git_available():
        click.echo(f"Error: Git is not installed. {mgr.get_install_instructions()}", err=True)
        sys.exit(1)
    if mgr.is_initialized():
        click.echo("Git backup already initialized.")
        return
    mgr.init()
    click.echo("Initialized Git backup.")
    if not mgr.is_lfs_available():
        click.echo("Note: git-lfs not installed. Binary files will be stored without LFS.")
        click.echo("  Install: brew install git-lfs  (or: apt install git-lfs)")


@backup.command("status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def backup_status(as_json):
    """Show backup status."""
    from quidclaw.core.backup import BackupManager
    config = get_config()
    mgr = BackupManager(config)
    status = mgr.status()
    if as_json:
        click.echo(json.dumps(status, indent=2))
    else:
        if not status["initialized"]:
            click.echo("Git backup: not initialized")
            click.echo("  Run 'quidclaw backup init' to enable.")
            return
        click.echo("Git backup: initialized")
        click.echo(f"  Last commit: {status['last_commit']}")
        click.echo(f"  LFS: {'available' if status['lfs_available'] else 'not installed'}")
        remotes = status["remotes"]
        if remotes:
            click.echo(f"  Remotes ({len(remotes)}):")
            for r in remotes:
                click.echo(f"    {r['name']}: {r['url']}")
        else:
            click.echo("  Remotes: none configured")


@backup.command("add-remote")
@click.argument("name")
@click.argument("url")
def backup_add_remote(name, url):
    """Add a remote repository for backup."""
    from quidclaw.core.backup import BackupManager
    config = get_config()
    mgr = BackupManager(config)
    if not mgr.is_initialized():
        click.echo("Error: Git backup not initialized. Run 'quidclaw backup init' first.", err=True)
        sys.exit(1)
    mgr.add_remote(name, url)
    click.echo(f"Added remote '{name}': {url}")
    click.echo("  Make sure the repository is Private (financial data!).")
    click.echo(f"  Test with: quidclaw backup push --remote {name}")


@backup.command("remove-remote")
@click.argument("name")
def backup_remove_remote(name):
    """Remove a remote repository."""
    import subprocess as _sp
    from quidclaw.core.backup import BackupManager
    config = get_config()
    mgr = BackupManager(config)
    if not mgr.is_initialized():
        click.echo("Error: Git backup not initialized.", err=True)
        sys.exit(1)
    try:
        mgr.remove_remote(name)
    except _sp.CalledProcessError:
        click.echo(f"Error: Remote '{name}' not found.", err=True)
        sys.exit(1)
    click.echo(f"Removed remote '{name}'.")


@backup.command("push")
@click.option("--remote", default=None, help="Push to specific remote (default: all)")
def backup_push(remote):
    """Push to remote repositories."""
    import subprocess as _sp
    from quidclaw.core.backup import BackupManager
    config = get_config()
    mgr = BackupManager(config)
    if not mgr.is_initialized():
        click.echo("Error: Git backup not initialized.", err=True)
        sys.exit(1)
    if remote:
        try:
            mgr._run_git("push", remote)
            click.echo(f"Pushed to '{remote}'.")
        except _sp.CalledProcessError as e:
            click.echo(f"Error pushing to '{remote}': {e.stderr.strip()}", err=True)
            sys.exit(1)
    else:
        remotes = mgr.list_remotes()
        if not remotes:
            click.echo("No remotes configured. Use 'quidclaw backup add-remote' first.", err=True)
            sys.exit(1)
        for r in remotes:
            try:
                mgr._run_git("push", r["name"])
                click.echo(f"Pushed to '{r['name']}'.")
            except _sp.CalledProcessError as e:
                click.echo(f"Error pushing to '{r['name']}': {e.stderr.strip()}", err=True)



# --- Plugin Loading ---

from quidclaw.core.plugins import load_plugins
load_plugins(main)

