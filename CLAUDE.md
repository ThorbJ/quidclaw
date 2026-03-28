# QuidClaw

Zero-barrier personal CFO. AI-powered, local-first, powered by Beancount V3.

## Architecture

- `src/quidclaw/core/` — Pure business logic. Depends only on Beancount, NOT on Click.
- `src/quidclaw/cli.py` — Thin Click CLI adapter. No business logic here.
- `src/quidclaw/skills/` — Agent Skills (agentskills.io standard, installed to user project on init).

See `docs/architecture.md` for module details, data flow diagrams, and design decisions.

## Project Stage

This project is in active development (alpha). Refactoring happens frequently. Do NOT add backwards-compatibility shims, deprecation warnings, migration paths, or legacy fallbacks. Keep one clean, current version of everything. Delete what's replaced.

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

35 commands across setup, config, ledger ops (including document/pad/balance directives), reports, prices, anomaly detection, data sources, and backup.
See `docs/cli-reference.md` for the full command list.

## Conventions

- Core classes take `Ledger` (ledger data) or `QuidClawConfig` (file ops) in constructor
- All CLI commands support `--json` where applicable
- Skills use CLI commands + native AI tools — never MCP tools
- Tests use `tmp_path` fixture for isolated data directories
- Data directory: cwd by default, override with `QUIDCLAW_DATA_DIR`
- Transactions go into monthly files: `ledger/YYYY/YYYY-MM.bean`
- Document naming: `{Source}-{Type}-{YYYY-MM}.{ext}`
- Account names: Beancount format, colon-separated, starting with Assets/Liabilities/Income/Expenses/Equity
- Account naming: use last 4 digits or identifiers (e.g., `Assets:Bank:CMB:1234`)

## Architectural Constraints

These are non-negotiable. Any feature proposal that violates these is wrong.

- **Local-first, no server**: QuidClaw runs entirely on the user's machine. No backend, no cloud service, no public endpoints. All external data is acquired by pulling (polling/sync), never by receiving pushes (webhooks, callbacks). If a feature requires a server to receive inbound requests, it does not belong in QuidClaw.
- **AI is the intelligence layer**: Parsing, understanding, and interpreting documents (PDFs, images, CSVs, emails) is the AI's job via skills. The CLI/core layer does NOT parse or interpret financial documents — it only performs deterministic operations (accounting math, file I/O, API calls for data retrieval). Never duplicate AI capabilities in the CLI layer.
- **CLI = data movement + accounting operations**: The CLI moves data between systems (sync from email, fetch prices) and performs structured accounting operations (add transactions, query balances). It does not make decisions about what data means.

## Adding Features

See `docs/contributing.md` for how to add new CLI commands and skills.
