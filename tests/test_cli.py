"""CLI tests using Click's CliRunner."""

import json

from click.testing import CliRunner
from quidclaw.cli import main


def _init_project(tmp_path):
    """Initialize a QuidClaw project and return the runner."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["init"], catch_exceptions=False,
        env={"QUIDCLAW_DATA_DIR": str(tmp_path)},
    )
    assert result.exit_code == 0
    return runner


def _env(tmp_path):
    return {"QUIDCLAW_DATA_DIR": str(tmp_path)}


# --- Init ---


class TestInit:
    def test_creates_directories(self, tmp_path):
        _init_project(tmp_path)
        assert (tmp_path / "ledger").is_dir()
        assert (tmp_path / "inbox").is_dir()
        assert (tmp_path / "documents").is_dir()
        assert (tmp_path / "notes").is_dir()

    def test_creates_empty_accounts_file(self, tmp_path):
        _init_project(tmp_path)
        accounts_bean = tmp_path / "ledger" / "accounts.bean"
        assert accounts_bean.exists()

    def test_setup_creates_default_accounts(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        # Set operating currency first
        runner.invoke(main, ["set-config", "operating_currency", "CNY"], env=env)
        result = runner.invoke(main, ["setup"], catch_exceptions=False, env=env)
        assert result.exit_code == 0
        content = (tmp_path / "ledger" / "accounts.bean").read_text()
        assert "Assets" in content
        assert "Expenses" in content
        assert "Income" in content

    def test_creates_claude_md(self, tmp_path):
        _init_project(tmp_path)
        claude_md = tmp_path / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "QuidClaw" in content

    def test_init_idempotent(self, tmp_path):
        """Running init twice should not fail."""
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["init"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0


# --- Upgrade ---


class TestUpgrade:
    def test_upgrade_updates_workflows(self, tmp_path):
        runner = _init_project(tmp_path)
        # Verify workflows exist after init
        workflows_dir = tmp_path / ".quidclaw" / "workflows"
        assert workflows_dir.is_dir()
        assert (workflows_dir / "onboarding.md").exists()

        # Simulate a stale workflow by truncating a file
        (workflows_dir / "onboarding.md").write_text("old content")

        # Run upgrade
        result = runner.invoke(
            main, ["upgrade"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0

        # Verify workflow was refreshed (no longer "old content")
        content = (workflows_dir / "onboarding.md").read_text()
        assert content != "old content"
        assert "onboarding" in content.lower() or "Onboarding" in content

    def test_upgrade_updates_claude_md(self, tmp_path):
        runner = _init_project(tmp_path)
        claude_md = tmp_path / "CLAUDE.md"
        assert claude_md.exists()

        # Truncate CLAUDE.md
        claude_md.write_text("old")

        # Run upgrade
        result = runner.invoke(
            main, ["upgrade"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0

        # Verify CLAUDE.md was refreshed
        content = claude_md.read_text()
        assert "QuidClaw" in content
        assert "quidclaw" in content


# --- Data Status ---


class TestDataStatus:
    def test_empty_inbox(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["data-status"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "Inbox files: 0" in result.output

    def test_with_inbox_files(self, tmp_path):
        runner = _init_project(tmp_path)
        # Drop files in inbox
        (tmp_path / "inbox" / "statement.csv").write_text("data")
        (tmp_path / "inbox" / "receipt.pdf").write_bytes(b"pdf")
        result = runner.invoke(
            main, ["data-status"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "Inbox files: 2" in result.output
        assert "receipt.pdf" in result.output
        assert "statement.csv" in result.output

    def test_json_output(self, tmp_path):
        runner = _init_project(tmp_path)
        (tmp_path / "inbox" / "test.csv").write_text("data")
        result = runner.invoke(
            main, ["data-status", "--json"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["inbox_count"] == 1
        assert "test.csv" in data["inbox_files"]
        assert data["last_modified"] is not None  # ledger exists from init

    def test_last_modified_shown(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["data-status"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "Last modified:" in result.output
        # After init, there should be a last_modified value (not N/A)
        assert "N/A" not in result.output


# --- Accounts ---


class TestAccounts:
    def test_add_and_list(self, tmp_path):
        runner = _init_project(tmp_path)
        # Add account
        result = runner.invoke(
            main, ["add-account", "Assets:Bank:Test:1234", "--currencies", "CNY,USD"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0

        # List accounts
        result = runner.invoke(
            main, ["list-accounts"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "Assets:Bank:Test:1234" in result.output

    def test_list_accounts_json(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["add-account", "Assets:Bank:Test", "--currencies", "CNY"], env=env)
        result = runner.invoke(
            main, ["list-accounts", "--json"], catch_exceptions=False,
            env=env,
        )
        assert result.exit_code == 0
        accounts = json.loads(result.output)
        assert isinstance(accounts, list)
        assert len(accounts) > 0

    def test_list_accounts_filter_by_type(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["list-accounts", "--type", "Assets"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        for line in result.output.strip().splitlines():
            assert line.startswith("Assets")

    def test_close_account(self, tmp_path):
        runner = _init_project(tmp_path)
        # Add then close
        runner.invoke(
            main, ["add-account", "Assets:Bank:ToClose"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        result = runner.invoke(
            main, ["close-account", "Assets:Bank:ToClose"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0


# --- Transactions ---


class TestTransactions:
    def test_add_transaction(self, tmp_path):
        runner = _init_project(tmp_path)
        posting1 = json.dumps({"account": "Expenses:Food", "amount": "50", "currency": "CNY"})
        posting2 = json.dumps({"account": "Assets:Bank:Checking", "amount": "-50", "currency": "CNY"})
        result = runner.invoke(
            main, [
                "add-txn",
                "--date", "2026-03-15",
                "--payee", "Restaurant",
                "--narration", "Lunch",
                "--posting", posting1,
                "--posting", posting2,
            ],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        # Verify the transaction file was created
        txn_file = tmp_path / "ledger" / "2026" / "2026-03.bean"
        assert txn_file.exists()
        content = txn_file.read_text()
        assert "Restaurant" in content
        assert "Lunch" in content


# --- Balance ---


class TestBalance:
    def test_empty_balance(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["balance", "--account", "Assets:Bank:Checking"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0

    def test_balance_after_transaction(self, tmp_path):
        runner = _init_project(tmp_path)
        posting1 = json.dumps({"account": "Expenses:Food", "amount": "50", "currency": "CNY"})
        posting2 = json.dumps({"account": "Assets:Bank:Checking", "amount": "-50", "currency": "CNY"})
        runner.invoke(
            main, [
                "add-txn",
                "--date", "2026-03-15",
                "--payee", "Restaurant",
                "--posting", posting1,
                "--posting", posting2,
            ],
            catch_exceptions=False, env=_env(tmp_path),
        )
        result = runner.invoke(
            main, ["balance", "--json"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "Expenses:Food" in data


# --- Query ---


class TestQuery:
    def test_bql_query(self, tmp_path):
        runner = _init_project(tmp_path)
        # Add a transaction to query
        posting1 = json.dumps({"account": "Expenses:Food", "amount": "100", "currency": "CNY"})
        posting2 = json.dumps({"account": "Assets:Bank:Checking", "amount": "-100", "currency": "CNY"})
        runner.invoke(
            main, [
                "add-txn",
                "--date", "2026-03-10",
                "--payee", "Supermarket",
                "--posting", posting1,
                "--posting", posting2,
            ],
            catch_exceptions=False, env=_env(tmp_path),
        )
        result = runner.invoke(
            main, ["query", "SELECT DISTINCT account, sum(position) WHERE account ~ 'Expenses' GROUP BY account"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "Expenses:Food" in result.output

    def test_bql_query_json(self, tmp_path):
        runner = _init_project(tmp_path)
        posting1 = json.dumps({"account": "Expenses:Food", "amount": "75", "currency": "CNY"})
        posting2 = json.dumps({"account": "Assets:Bank:Checking", "amount": "-75", "currency": "CNY"})
        runner.invoke(
            main, [
                "add-txn",
                "--date", "2026-03-10",
                "--payee", "Cafe",
                "--posting", posting1,
                "--posting", posting2,
            ],
            catch_exceptions=False, env=_env(tmp_path),
        )
        result = runner.invoke(
            main, ["query", "--json", "SELECT DISTINCT account WHERE account ~ 'Expenses'"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert any("Expenses:Food" in row.get("account", "") for row in data)
