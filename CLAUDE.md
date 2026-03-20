# QuidClaw

Zero-barrier personal CFO. AI-powered, local-first, powered by Beancount V3.

## Architecture

- `src/quidclaw/core/` — Pure business logic. Depends only on Beancount, NOT on Click.
- `src/quidclaw/cli.py` — Thin Click CLI adapter. No business logic here.
- `src/quidclaw/workflows/` — AI workflow instructions (copied to user project on init).

See `docs/architecture.md` for module details, data flow diagrams, and design decisions.

## Development

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest                          # all tests
pytest tests/core/              # core logic tests
pytest tests/test_cli.py        # CLI tests
```

## CLI

17 commands across setup, ledger ops, reports, and anomaly detection.
See `docs/cli-reference.md` for the full command list.

## Conventions

- Core classes take `Ledger` (ledger data) or `QuidClawConfig` (file ops) in constructor
- All CLI commands support `--json` where applicable
- Workflows use CLI commands + native AI tools — never MCP tools
- Tests use `tmp_path` fixture for isolated data directories
- Data directory: cwd by default, override with `QUIDCLAW_DATA_DIR`
- Transactions go into monthly files: `ledger/YYYY/YYYY-MM.bean`
- Document naming: `{Source}-{Type}-{YYYY-MM}.{ext}`
- Account names: Beancount format, colon-separated, starting with Assets/Liabilities/Income/Expenses/Equity
- Account naming: use last 4 digits or identifiers (e.g., `Assets:Bank:CMB:1234`)

## Adding Features

See `docs/contributing.md` for how to add new CLI commands and workflows.
