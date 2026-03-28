"""CLI tests using Click's CliRunner."""

import json

from click.testing import CliRunner
from quidclaw.cli import main


def _init_project(tmp_path):
    """Initialize a QuidClaw project and return the runner."""
    runner = CliRunner()
    result = runner.invoke(
        main, ["init", "--platform", "claude-code"], catch_exceptions=False,
        env={"QUIDCLAW_DATA_DIR": str(tmp_path)},
    )
    assert result.exit_code == 0
    return runner


def _env(tmp_path):
    return {"QUIDCLAW_DATA_DIR": str(tmp_path)}


# --- Init ---


class TestInit:
    def test_init_with_platform_openclaw_generates_templates(self, tmp_path):
        runner = CliRunner()
        from unittest.mock import patch
        with patch("quidclaw.core.openclaw.OpenClawSetup.is_available", return_value=False):
            result = runner.invoke(
                main, ["init", "--platform", "openclaw"],
                catch_exceptions=False, env=_env(tmp_path),
            )
        assert result.exit_code == 0
        assert (tmp_path / "SOUL.md").exists()
        assert (tmp_path / "HEARTBEAT.md").exists()
        assert (tmp_path / "BOOTSTRAP.md").exists()
        assert (tmp_path / "IDENTITY.md").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert "Automation" in (tmp_path / "AGENTS.md").read_text()
        assert (tmp_path / ".claude" / "skills" / "quidclaw" / "SKILL.md").exists()
        assert not (tmp_path / "CLAUDE.md").exists()
        assert not (tmp_path / "GEMINI.md").exists()

    def test_init_stores_platform_in_config(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "claude-code"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        from quidclaw.config import QuidClawConfig
        config = QuidClawConfig(data_dir=tmp_path)
        assert config.get_setting("platform") == "claude-code"

    def test_init_openclaw_auto_enables_backup(self, tmp_path):
        runner = CliRunner()
        from unittest.mock import patch
        with patch("quidclaw.core.openclaw.OpenClawSetup.is_available", return_value=False):
            result = runner.invoke(
                main, ["init", "--platform", "openclaw"],
                catch_exceptions=False, env=_env(tmp_path),
            )
        assert result.exit_code == 0
        assert (tmp_path / ".git").is_dir()

    def test_init_creates_directories(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "claude-code"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / "ledger").is_dir()
        assert (tmp_path / "inbox").is_dir()
        assert (tmp_path / "notes" / "pending").is_dir()

    def test_init_idempotent(self, tmp_path):
        runner = CliRunner()
        env = _env(tmp_path)
        runner.invoke(main, ["init", "--platform", "claude-code"],
                      catch_exceptions=False, env=env)
        result = runner.invoke(main, ["init", "--platform", "claude-code"],
                               catch_exceptions=False, env=env)
        assert result.exit_code == 0

    def test_init_installs_skills_claude_code(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "claude-code"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        skills_dir = tmp_path / ".claude" / "skills"
        assert (skills_dir / "quidclaw" / "SKILL.md").exists()
        assert (skills_dir / "quidclaw-onboarding" / "SKILL.md").exists()
        assert (skills_dir / "quidclaw-import" / "SKILL.md").exists()
        assert (skills_dir / "quidclaw-daily" / "SKILL.md").exists()
        assert (skills_dir / "quidclaw-review" / "SKILL.md").exists()

    def test_init_installs_skills_gemini(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "gemini"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / ".gemini" / "skills" / "quidclaw" / "SKILL.md").exists()

    def test_init_installs_skills_codex(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "codex"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / ".agents" / "skills" / "quidclaw" / "SKILL.md").exists()

    def test_init_skills_have_valid_frontmatter(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "claude-code"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        import yaml
        skill_md = (tmp_path / ".claude" / "skills" / "quidclaw" / "SKILL.md").read_text()
        parts = skill_md.split("---", 2)
        assert len(parts) >= 3, "SKILL.md must have YAML frontmatter"
        meta = yaml.safe_load(parts[1])
        assert meta["name"] == "quidclaw"
        assert "description" in meta

    def test_init_skills_references_installed(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "claude-code"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        refs = tmp_path / ".claude" / "skills" / "quidclaw" / "references"
        assert (refs / "cli-reference.md").exists()
        assert (refs / "conventions.md").exists()
        assert (refs / "notes-guide.md").exists()

    def test_init_generates_claude_md(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "claude-code"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        claude_md = tmp_path / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "Personal CFO" in content
        assert "Skills" in content
        assert "quidclaw-import" in content
        # NOT the old huge file — should be concise
        assert len(content) < 1000

    def test_init_generates_gemini_md(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "gemini"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / "GEMINI.md").exists()
        assert "Skills" in (tmp_path / "GEMINI.md").read_text()

    def test_init_generates_agents_md_for_codex(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["init", "--platform", "codex"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / "AGENTS.md").exists()
        assert "Skills" in (tmp_path / "AGENTS.md").read_text()


# --- Upgrade ---


class TestUpgrade:
    def test_upgrade_updates_instruction_files(self, tmp_path):
        """upgrade refreshes both skills and platform entry file."""
        runner = _init_project(tmp_path)
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("old")
        result = runner.invoke(
            main, ["upgrade"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        content = claude_md.read_text()
        assert content != "old"
        assert "Personal CFO" in content

    def test_upgrade_updates_skills(self, tmp_path):
        runner = _init_project(tmp_path)
        skill_file = tmp_path / ".claude" / "skills" / "quidclaw" / "SKILL.md"
        assert skill_file.exists()
        skill_file.write_text("old content")
        result = runner.invoke(
            main, ["upgrade"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert skill_file.read_text() != "old content"

    def test_upgrade_installs_new_skills(self, tmp_path):
        runner = _init_project(tmp_path)
        import shutil
        daily_dir = tmp_path / ".claude" / "skills" / "quidclaw-daily"
        if daily_dir.exists():
            shutil.rmtree(daily_dir)
        result = runner.invoke(
            main, ["upgrade"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (daily_dir / "SKILL.md").exists()


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

    def test_data_status_includes_sources(self, tmp_path):
        runner = _init_project(tmp_path)
        import yaml as _yaml
        config_file = tmp_path / ".quidclaw" / "config.yaml"
        settings = _yaml.safe_load(config_file.read_text()) if config_file.exists() else {}
        settings["data_sources"] = {"test": {"provider": "agentmail", "inbox_id": "test@agentmail.to", "enabled": True}}
        config_file.write_text(_yaml.dump(settings))

        result = runner.invoke(
            main, ["data-status", "--json"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "sources" in data


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

    def test_add_account_with_metadata(self, tmp_path):
        runner = _init_project(tmp_path)
        meta = json.dumps({"institution": "CMB", "account-number": "1234"})
        result = runner.invoke(
            main, ["add-account", "Assets:Bank:CMB:1234", "--currencies", "CNY", "--meta", meta],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        content = (tmp_path / "ledger" / "accounts.bean").read_text()
        assert 'institution: "CMB"' in content

    def test_add_note(self, tmp_path):
        runner = _init_project(tmp_path)
        runner.invoke(
            main, ["add-account", "Assets:Bank:Test"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        result = runner.invoke(
            main, ["add-note", "Assets:Bank:Test", "Called bank about transfer", "--date", "2026-03-15"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        content = (tmp_path / "ledger" / "2026" / "2026-03.bean").read_text()
        assert 'note Assets:Bank:Test "Called bank about transfer"' in content


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

    def test_add_transaction_with_meta(self, tmp_path):
        runner = _init_project(tmp_path)
        posting1 = json.dumps({"account": "Expenses:Food", "amount": "50", "currency": "CNY"})
        posting2 = json.dumps({"account": "Assets:Bank:Checking", "amount": "-50", "currency": "CNY"})
        meta = json.dumps({"source": "test-source", "import-id": "evt_test"})
        result = runner.invoke(
            main, [
                "add-txn",
                "--date", "2026-03-15",
                "--payee", "Restaurant",
                "--narration", "Lunch",
                "--posting", posting1,
                "--posting", posting2,
                "--meta", meta,
            ],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        txn_file = tmp_path / "ledger" / "2026" / "2026-03.bean"
        content = txn_file.read_text()
        assert 'source: "test-source"' in content
        assert 'import-id: "evt_test"' in content

    def test_add_transaction_with_flag(self, tmp_path):
        runner = _init_project(tmp_path)
        posting1 = json.dumps({"account": "Expenses:Food", "amount": "50", "currency": "CNY"})
        posting2 = json.dumps({"account": "Assets:Bank:Checking"})
        result = runner.invoke(
            main, [
                "add-txn",
                "--date", "2026-03-15",
                "--payee", "Unknown",
                "--narration", "Unconfirmed",
                "--posting", posting1,
                "--posting", posting2,
                "--flag", "!",
            ],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        txn_file = tmp_path / "ledger" / "2026" / "2026-03.bean"
        assert '! "Unknown"' in txn_file.read_text()

    def test_add_transaction_with_tags_and_links(self, tmp_path):
        runner = _init_project(tmp_path)
        posting1 = json.dumps({"account": "Expenses:Food", "amount": "50", "currency": "CNY"})
        posting2 = json.dumps({"account": "Assets:Bank:Checking"})
        result = runner.invoke(
            main, [
                "add-txn",
                "--date", "2026-03-15",
                "--payee", "Restaurant",
                "--narration", "Team dinner",
                "--posting", posting1,
                "--posting", posting2,
                "--tag", "trip-beijing",
                "--tag", "tax-2026",
                "--link", "project-alpha",
            ],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        content = (tmp_path / "ledger" / "2026" / "2026-03.bean").read_text()
        assert "#trip-beijing" in content
        assert "#tax-2026" in content
        assert "^project-alpha" in content


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

    def test_add_balance_assertion(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        posting1 = json.dumps({"account": "Expenses:Food", "amount": "50", "currency": "CNY"})
        posting2 = json.dumps({"account": "Assets:Bank:Checking", "amount": "-50", "currency": "CNY"})
        runner.invoke(
            main, [
                "add-txn", "--date", "2026-03-15", "--payee", "Test",
                "--posting", posting1, "--posting", posting2,
            ],
            catch_exceptions=False, env=env,
        )
        result = runner.invoke(
            main, ["add-balance", "Assets:Bank:Checking", "--amount", "-50", "--currency", "CNY", "--date", "2026-03-16"],
            catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0
        assert "Balance assertion" in result.output
        content = (tmp_path / "ledger" / "2026" / "2026-03.bean").read_text()
        assert "balance Assets:Bank:Checking" in content

    def test_add_pad(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(
            main, ["add-account", "Equity:Opening-Balances"],
            catch_exceptions=False, env=env,
        )
        result = runner.invoke(
            main, ["add-pad", "Assets:Bank:Checking", "--date", "2026-03-01"],
            catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0
        assert "Pad" in result.output
        content = (tmp_path / "ledger" / "2026" / "2026-03.bean").read_text()
        assert "pad Assets:Bank:Checking" in content
        assert "Equity:Opening-Balances" in content

    def test_add_document(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        result = runner.invoke(
            main, [
                "add-document", "Assets:Bank:Checking",
                "documents/2026/03/BOC-Statement-2026-03.pdf",
                "--date", "2026-03-15",
            ],
            catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0
        assert "Document linked" in result.output
        content = (tmp_path / "ledger" / "2026" / "2026-03.bean").read_text()
        assert "document Assets:Bank:Checking" in content
        assert "BOC-Statement-2026-03.pdf" in content


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


# --- Sources ---


class TestSources:
    def test_list_sources_empty(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["list-sources"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "No data sources configured" in result.output

    def test_list_sources_json_empty(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["list-sources", "--json"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == {}

    def test_add_source_creates_config_entry(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["list-sources", "--json"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert json.loads(result.output) == {}

    def test_sync_no_sources(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["sync"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code != 0
        assert "No data sources" in result.output

    def test_sync_source_not_found(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["sync", "nonexistent"], catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code != 0

    def test_mark_processed(self, tmp_path):
        runner = _init_project(tmp_path)
        import yaml as _yaml
        email_dir = tmp_path / "sources" / "test" / "2026-03-21_bank"
        email_dir.mkdir(parents=True)
        (email_dir / "envelope.yaml").write_text(
            _yaml.dump({"status": "unprocessed", "message_id": "msg1"})
        )
        result = runner.invoke(
            main, ["mark-processed", "test", "2026-03-21_bank"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code == 0
        envelope = _yaml.safe_load((email_dir / "envelope.yaml").read_text())
        assert envelope["status"] == "processed"

    def test_mark_processed_not_found(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["mark-processed", "test", "nonexistent"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code != 0

    def test_remove_source_not_found(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["remove-source", "nonexistent", "--confirm"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code != 0

    def test_remove_source_requires_confirm(self, tmp_path):
        runner = _init_project(tmp_path)
        import yaml as _yaml
        config_file = tmp_path / ".quidclaw" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(_yaml.dump({"data_sources": {"test": {"provider": "fake"}}}))
        result = runner.invoke(
            main, ["remove-source", "test"],
            catch_exceptions=False, env=_env(tmp_path),
        )
        assert result.exit_code != 0
        assert "confirm" in result.output.lower() or "Missing" in result.output


# --- Backup ---


class TestBackup:
    def test_backup_init(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["backup", "init"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert (tmp_path / ".git").is_dir()

    def test_backup_init_already_initialized(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        result = runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        assert result.exit_code == 0
        assert "already" in result.output.lower()

    def test_backup_status_not_initialized(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["backup", "status"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "not initialized" in result.output.lower()

    def test_backup_status_initialized(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        result = runner.invoke(
            main, ["backup", "status"], catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0

    def test_backup_status_json(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        result = runner.invoke(
            main, ["backup", "status", "--json"], catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["initialized"] is True

    def test_backup_add_remote(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        result = runner.invoke(
            main, ["backup", "add-remote", "github", "https://github.com/u/r.git"],
            catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0
        assert "github" in result.output

    def test_backup_add_multiple_remotes(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        runner.invoke(
            main, ["backup", "add-remote", "github", "https://github.com/u/r.git"],
            catch_exceptions=False, env=env,
        )
        runner.invoke(
            main, ["backup", "add-remote", "gitee", "https://gitee.com/u/r.git"],
            catch_exceptions=False, env=env,
        )
        result = runner.invoke(
            main, ["backup", "status", "--json"], catch_exceptions=False, env=env,
        )
        data = json.loads(result.output)
        assert len(data["remotes"]) == 2

    def test_backup_remove_remote(self, tmp_path):
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        runner.invoke(
            main, ["backup", "add-remote", "github", "https://github.com/u/r.git"],
            catch_exceptions=False, env=env,
        )
        result = runner.invoke(
            main, ["backup", "remove-remote", "github"],
            catch_exceptions=False, env=env,
        )
        assert result.exit_code == 0

    def test_backup_push_no_init(self, tmp_path):
        runner = _init_project(tmp_path)
        result = runner.invoke(
            main, ["backup", "push"],
            env=_env(tmp_path),
        )
        assert result.exit_code != 0

    def test_add_txn_triggers_backup(self, tmp_path):
        import subprocess
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        posting1 = json.dumps({"account": "Expenses:Food", "amount": "50", "currency": "CNY"})
        posting2 = json.dumps({"account": "Assets:Bank:Checking", "amount": "-50", "currency": "CNY"})
        runner.invoke(
            main, [
                "add-txn", "--date", "2026-03-15", "--payee", "TestStore",
                "--posting", posting1, "--posting", posting2,
            ],
            catch_exceptions=False, env=env,
        )
        log = subprocess.run(
            ["git", "log", "--oneline"], cwd=tmp_path,
            capture_output=True, text=True,
        )
        assert "TestStore" in log.stdout

    def test_add_account_triggers_backup(self, tmp_path):
        import subprocess
        runner = _init_project(tmp_path)
        env = _env(tmp_path)
        runner.invoke(main, ["backup", "init"], catch_exceptions=False, env=env)
        runner.invoke(
            main, ["add-account", "Assets:Bank:Test:9999", "--currencies", "CNY"],
            catch_exceptions=False, env=env,
        )
        log = subprocess.run(
            ["git", "log", "--oneline"], cwd=tmp_path,
            capture_output=True, text=True,
        )
        assert "Assets:Bank:Test:9999" in log.stdout

    def test_backup_init_requires_git(self, tmp_path):
        runner = _init_project(tmp_path)
        from unittest.mock import patch
        with patch("quidclaw.core.backup.shutil.which", return_value=None):
            result = runner.invoke(
                main, ["backup", "init"],
                env=_env(tmp_path),
            )
        assert result.exit_code != 0
        assert "git" in result.output.lower()


# --- Plugins ---


class TestPlugins:
    def test_plugins_no_plugins(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            main, ["plugins"], catch_exceptions=False,
            env=_env(tmp_path),
        )
        assert result.exit_code == 0
        assert "No plugins installed" in result.output
