# QuidClaw CLI Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the migration from MCP Plugin to CLI + workflow architecture so QuidClaw works with any AI coding tool (Claude Code, Gemini CLI, Codex).

**Architecture:** QuidClaw is a `pip install`-able CLI that wraps Beancount operations + a set of workflow markdown files that guide any AI assistant. Core business logic (already migrated) is untouched. This plan covers: missing CLI command, workflow file updates, CLI tests, and project documentation.

**Tech Stack:** Python 3.10+, Click, Beancount V3, pytest

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/quidclaw/cli.py` | Modify | Add `data-status` command |
| `.quidclaw/workflows/onboarding.md` | Modify | Replace MCP references with CLI + native tools |
| `.quidclaw/workflows/import-bills.md` | Modify | Replace MCP references with CLI + native tools |
| `.quidclaw/workflows/reconcile.md` | Modify | Replace MCP references with CLI + native tools |
| `.quidclaw/workflows/monthly-review.md` | Modify | Replace MCP references with CLI + native tools |
| `.quidclaw/workflows/detect-anomalies.md` | Modify | Replace MCP references with CLI + native tools |
| `.quidclaw/workflows/organize-documents.md` | Modify | Replace MCP references with CLI + native tools |
| `.quidclaw/workflows/financial-memory.md` | Modify | Replace MCP references with CLI + native tools |
| `tests/test_cli.py` | Create | CLI command tests |
| `CLAUDE.md` | Create | Developer instructions for this repo |
| `README.md` | Modify | User-facing documentation |

---

### Task 1: Add `data-status` CLI Command

The `get_data_status` MCP tool is referenced in workflows but has no CLI equivalent.

**Files:**
- Modify: `src/quidclaw/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli.py`:

```python
"""Tests for QuidClaw CLI commands."""

import json
from pathlib import Path

from click.testing import CliRunner

from quidclaw.cli import main


def _init_project(tmp_path):
    """Helper: initialize a QuidClaw project in tmp_path."""
    runner = CliRunner()
    result = runner.invoke(main, ["init"], catch_exceptions=False, env={"QUIDCLAW_DATA_DIR": str(tmp_path)})
    assert result.exit_code == 0
    return runner


class TestDataStatus:
    def test_data_status_empty_inbox(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(main, ["data-status", "--json"], env={"QUIDCLAW_DATA_DIR": str(tmp_path)})
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["inbox_count"] == 0
        assert "last_modified" in data

    def test_data_status_with_inbox_files(self, tmp_path):
        runner = _init_project(tmp_path)
        (tmp_path / "inbox" / "statement.csv").write_text("test")
        result = runner.invoke(main, ["data-status", "--json"], env={"QUIDCLAW_DATA_DIR": str(tmp_path)})
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["inbox_count"] == 1
        assert "statement.csv" in str(data["inbox_files"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && pytest tests/test_cli.py::TestDataStatus -v`
Expected: FAIL with "No such command 'data-status'"

- [ ] **Step 3: Implement `data-status` command**

Add to `src/quidclaw/cli.py`, after the `fetch-prices` command:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `source .venv/bin/activate && pytest tests/test_cli.py::TestDataStatus -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_cli.py src/quidclaw/cli.py
git commit -m "feat: add data-status CLI command"
```

---

### Task 2: CLI Tests for Existing Commands

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write tests for init, accounts, transactions, balance, query**

Append to `tests/test_cli.py`:

```python
class TestInit:
    def test_init_creates_directories(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["init"], env={"QUIDCLAW_DATA_DIR": str(tmp_path)})
        assert result.exit_code == 0
        assert (tmp_path / "ledger" / "main.bean").exists()
        assert (tmp_path / "inbox").exists()
        assert (tmp_path / "notes").exists()
        assert (tmp_path / "documents").exists()
        assert (tmp_path / "CLAUDE.md").exists()

    def test_init_creates_default_accounts(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["init"], env={"QUIDCLAW_DATA_DIR": str(tmp_path)})
        assert result.exit_code == 0
        result = runner.invoke(main, ["list-accounts"], env={"QUIDCLAW_DATA_DIR": str(tmp_path)})
        assert "Assets:Bank:Checking" in result.output


class TestAccounts:
    def test_add_and_list_account(self, tmp_path):
        runner = _init_project(tmp_path)
        env = {"QUIDCLAW_DATA_DIR": str(tmp_path)}
        result = runner.invoke(main, ["add-account", "Assets:Bank:CMB:1234", "--currencies", "CNY"], env=env)
        assert result.exit_code == 0
        result = runner.invoke(main, ["list-accounts", "--type", "Assets"], env=env)
        assert "Assets:Bank:CMB:1234" in result.output

    def test_close_account(self, tmp_path):
        runner = _init_project(tmp_path)
        env = {"QUIDCLAW_DATA_DIR": str(tmp_path)}
        result = runner.invoke(main, ["close-account", "Assets:Cash"], env=env)
        assert result.exit_code == 0


class TestTransactions:
    def test_add_transaction(self, tmp_path):
        runner = _init_project(tmp_path)
        env = {"QUIDCLAW_DATA_DIR": str(tmp_path)}
        result = runner.invoke(main, [
            "add-txn",
            "--date", "2026-03-20",
            "--payee", "Restaurant",
            "--narration", "Lunch",
            "--posting", '{"account": "Expenses:Food", "amount": "50", "currency": "CNY"}',
            "--posting", '{"account": "Assets:Cash"}',
        ], env=env)
        assert result.exit_code == 0


class TestBalance:
    def test_balance_empty(self, tmp_path):
        runner = _init_project(tmp_path)
        env = {"QUIDCLAW_DATA_DIR": str(tmp_path)}
        result = runner.invoke(main, ["balance", "--json"], env=env)
        assert result.exit_code == 0

    def test_balance_after_transaction(self, tmp_path):
        runner = _init_project(tmp_path)
        env = {"QUIDCLAW_DATA_DIR": str(tmp_path)}
        runner.invoke(main, [
            "add-txn",
            "--date", "2026-03-20",
            "--payee", "Salary",
            "--posting", '{"account": "Assets:Bank:Checking", "amount": "10000", "currency": "CNY"}',
            "--posting", '{"account": "Income:Salary"}',
        ], env=env)
        result = runner.invoke(main, ["balance", "--account", "Assets:Bank:Checking", "--json"], env=env)
        assert result.exit_code == 0
        assert "10000" in result.output


class TestQuery:
    def test_query_bql(self, tmp_path):
        runner = _init_project(tmp_path)
        env = {"QUIDCLAW_DATA_DIR": str(tmp_path)}
        result = runner.invoke(main, ["query", "SELECT account, balance WHERE account ~ 'Assets'"], env=env)
        assert result.exit_code == 0
```

- [ ] **Step 2: Run all CLI tests**

Run: `source .venv/bin/activate && pytest tests/test_cli.py -v`
Expected: ALL PASS

- [ ] **Step 3: Fix any failures, then commit**

```bash
git add tests/test_cli.py
git commit -m "test: add CLI command tests"
```

---

### Task 3: Update Workflow Files — Replace MCP References

All 7 workflow files reference MCP-style tool calls. Update them to use CLI commands and native AI tools.

**Files:**
- Modify: `.quidclaw/workflows/onboarding.md`
- Modify: `.quidclaw/workflows/import-bills.md`
- Modify: `.quidclaw/workflows/reconcile.md`
- Modify: `.quidclaw/workflows/monthly-review.md`
- Modify: `.quidclaw/workflows/detect-anomalies.md`
- Modify: `.quidclaw/workflows/organize-documents.md`
- Modify: `.quidclaw/workflows/financial-memory.md`

**Replacement rules for ALL workflows:**

| Old (MCP) | New (CLI or native) |
|-----------|-------------------|
| Call `set_data_dir(path)` / check `is_active` | Not needed — CLI uses current directory |
| Call `init_ledger(accounts)` | Run `quidclaw init` via Bash |
| Call `add_transaction(...)` | Run `quidclaw add-txn --date ... --payee ... --posting '{...}'` via Bash |
| Call `add_account(...)` | Run `quidclaw add-account NAME --currencies X` via Bash |
| Call `query("SELECT ...")` | Run `quidclaw query "SELECT ..." --json` via Bash |
| Call `get_balance(account)` | Run `quidclaw balance --account X --json` via Bash |
| Call `balance_check(...)` | Run `quidclaw balance-check ACCT AMT` via Bash |
| Call `report(type)` | Run `quidclaw report income\|balance_sheet` via Bash |
| Call `get_data_status()` | Run `quidclaw data-status --json` via Bash |
| Call `monthly_summary(Y, M)` | Run `quidclaw monthly-summary Y M --json` via Bash |
| Call `spending_by_category(Y, M)` | Run `quidclaw spending-by-category Y M --json` via Bash |
| Call `month_comparison(Y, M)` | Run `quidclaw month-comparison Y M` via Bash |
| Call `largest_transactions(Y, M)` | Run `quidclaw largest-txns Y M` via Bash |
| Call `detect_anomalies()` | Run `quidclaw detect-anomalies --json` via Bash |
| Call `read_note(path)` | Read `notes/<path>` directly (Read tool) |
| Call `write_note(path, content)` | Write to `notes/<path>` directly (Write tool) |
| Call `list_notes()` | Glob `notes/**/*.md` |
| Call `search_notes(query)` | Grep across `notes/` |
| Call `append_note(path, section, content)` | Edit `notes/<path>` directly (Edit tool) |
| Call `list_inbox()` | Glob `inbox/*` |
| Call `move_to_documents(...)` | Bash `mkdir -p documents/YYYY/MM && mv inbox/file documents/YYYY/MM/newname` |
| Call `list_documents(...)` | Glob `documents/**/*` or `documents/YYYY/MM/*` |
| Call `find_related(topic)` | Grep across `notes/` + `documents/` + `quidclaw query` |
| Call `find_notes_by_tag(tag)` | Grep `tags:.*tag` across `notes/` |

Also remove from all workflows:
- Any SKILL.md frontmatter (`---` blocks with `name:`, `description:`, `allowed-tools:`)
- Any references to MCP resources (`quidclaw://accounts`, `quidclaw://status`, etc.)
- Any references to `ctx.request_context` or `AppContext`

- [ ] **Step 1: Update `onboarding.md`**

Key changes:
- Remove `set_data_dir` / `is_active` check → check if `ledger/main.bean` exists (Glob)
- Replace `init_ledger(accounts)` → `quidclaw init` via Bash
- Replace `write_note` → Write tool directly
- Remove SKILL.md frontmatter

- [ ] **Step 2: Update `import-bills.md`**

Key changes:
- Replace `add_transaction(...)` → `quidclaw add-txn` via Bash
- Replace `query(...)` for dedup → `quidclaw query` via Bash
- Replace `move_to_documents(...)` → `mv` via Bash
- Replace `write_note` / `append_note` → Write/Edit tool directly

- [ ] **Step 3: Update `reconcile.md`**

Key changes:
- Replace `get_data_status()` → `quidclaw data-status --json` via Bash
- Replace `get_balance(account)` → `quidclaw balance --account X --json` via Bash
- Replace `list_inbox()` → Glob `inbox/*`

- [ ] **Step 4: Update `monthly-review.md`**

Key changes:
- Replace `get_data_status()` → `quidclaw data-status --json` via Bash
- Replace `monthly_summary` → `quidclaw monthly-summary Y M --json` via Bash
- Replace `spending_by_category` → `quidclaw spending-by-category Y M --json` via Bash
- Replace `month_comparison` → `quidclaw month-comparison Y M` via Bash
- Replace `largest_transactions` → `quidclaw largest-txns Y M` via Bash
- Replace `detect_anomalies` → `quidclaw detect-anomalies --json` via Bash

- [ ] **Step 5: Update `detect-anomalies.md`**

Key changes:
- Replace `detect_anomalies()` → `quidclaw detect-anomalies --json` via Bash

- [ ] **Step 6: Update `organize-documents.md`**

Key changes:
- Replace `list_inbox()` → Glob `inbox/*`
- Replace `move_to_documents(...)` → `mv` via Bash

- [ ] **Step 7: Update `financial-memory.md`**

Key changes:
- Replace all note operations → native Read/Write/Edit/Glob/Grep tools

- [ ] **Step 8: Commit all workflow updates**

```bash
git add .quidclaw/workflows/
git commit -m "refactor: update all workflows from MCP tools to CLI + native tools"
```

---

### Task 4: Update Generated CLAUDE.md

The `_generate_claude_md()` function in `cli.py` needs to include the `data-status` command.

**Files:**
- Modify: `src/quidclaw/cli.py` (the `_generate_claude_md` function)

- [ ] **Step 1: Add `data-status` to the CLI commands list in generated CLAUDE.md**

In the `_generate_claude_md()` function, add this line to the commands section:

```
quidclaw data-status                 # Inbox count, last ledger update
```

- [ ] **Step 2: Commit**

```bash
git add src/quidclaw/cli.py
git commit -m "docs: add data-status to generated CLAUDE.md"
```

---

### Task 5: Write Developer CLAUDE.md

This is the CLAUDE.md for the quidclaw repo itself (for developers working on the tool), NOT the one generated for end users.

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Write CLAUDE.md**

```markdown
# QuidClaw

Zero-barrier personal CFO — AI-powered, local-first, powered by Beancount V3.

## Architecture

### Two Layers
- `src/quidclaw/core/` — Pure business logic. Depends on Beancount, nothing else.
- `src/quidclaw/cli.py` — Click CLI that wraps core functions. Thin adapter.

### User-Facing Components
- `.quidclaw/workflows/` — AI workflow instructions (markdown). Copied to user's project on `quidclaw init`.
- Generated `CLAUDE.md` — Created by `quidclaw init`, tells AI how to use the CLI and workflows.

## Development

\```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest                          # run all tests
pytest tests/core/              # core logic tests
pytest tests/test_cli.py        # CLI tests
\```

## CLI Commands (15)

| Command | Purpose |
|---------|---------|
| `init` | Initialize a financial project |
| `upgrade` | Update workflows to latest version |
| `add-account` | Open an account |
| `close-account` | Close an account |
| `list-accounts` | List accounts |
| `add-txn` | Record a transaction |
| `balance` | Query balances |
| `balance-check` | Reconciliation assertion |
| `query` | Execute BQL query |
| `report` | Income statement / balance sheet |
| `monthly-summary` | Monthly income/expenses/savings |
| `spending-by-category` | Category breakdown |
| `month-comparison` | Month-over-month changes |
| `largest-txns` | Top N expenses |
| `detect-anomalies` | Find duplicates, outliers, etc. |
| `data-status` | Inbox count, last ledger update |
| `fetch-prices` | Fetch asset prices |

## How to Add a New CLI Command

1. Add core logic in `src/quidclaw/core/<module>.py` with tests in `tests/core/`
2. Add Click command in `src/quidclaw/cli.py`:
   \```python
   @main.command("my-command")
   @click.argument("name")
   @click.option("--json", "as_json", is_flag=True)
   def my_command(name, as_json):
       """Description."""
       from quidclaw.core.module import Manager
       ledger = get_ledger()  # or get_config() for file-only ops
       mgr = Manager(ledger)
       result = mgr.method(name)
       if as_json:
           click.echo(json.dumps(result, indent=2, default=str))
       else:
           click.echo(result)
   \```
3. Add test in `tests/test_cli.py`
4. Update the command list in `_generate_claude_md()` so user projects get the new command

## How to Add a New Workflow

1. Create `.quidclaw/workflows/<name>.md`
2. Use CLI commands (via Bash) for Beancount operations
3. Use native AI tools (Read, Write, Glob, Grep) for file operations
4. Reference the workflow in `_generate_claude_md()` so CLAUDE.md includes it

## Conventions

- Core classes take `Ledger` (for ledger ops) or `QuidClawConfig` (for file ops) in constructor
- All CLI commands support `--json` where applicable
- Workflows never reference MCP tools — only CLI commands and native AI tools
- Tests use `tmp_path` fixture and `QUIDCLAW_DATA_DIR` env var
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add developer CLAUDE.md"
```

---

### Task 6: Write README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write README**

Content should cover:
- What QuidClaw is (1 paragraph)
- Quick start (pip install, quidclaw init, use with any AI tool)
- Supported AI tools (Claude Code, Gemini CLI, Codex, any tool with Bash access)
- CLI command reference (table)
- How it works (directory structure diagram)
- Privacy model (everything local, plain text)
- Contributing

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

### Task 7: Initial Git Commit for Existing Files

Before starting the above tasks, create the initial commit with all files already in place.

**NOTE: This task should be executed FIRST, before all other tasks.**

- [ ] **Step 1: Commit all existing files**

```bash
git add -A
git commit -m "feat: initial QuidClaw CLI — core logic + CLI + workflows

Migrated from MCP Plugin architecture to CLI + workflow markdown.
Core business logic unchanged. MCP replaced with Click CLI (15 commands).
Skills converted to .quidclaw/workflows/ markdown files."
```

---

## Execution Order

1. **Task 7** — Initial commit (existing files)
2. **Task 1** — Add `data-status` command
3. **Task 2** — CLI tests for all commands
4. **Task 3** — Update all 7 workflow files
5. **Task 4** — Update generated CLAUDE.md
6. **Task 5** — Developer CLAUDE.md
7. **Task 6** — README.md
