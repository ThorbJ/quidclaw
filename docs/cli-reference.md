# CLI Reference

All commands support `--help`. Most support `--json` for structured AI-friendly output.

## Setup (2)

| Command | Purpose |
|---------|---------|
| `quidclaw init` | Initialize a new financial project (`--no-template` to skip default accounts) |
| `quidclaw upgrade` | Upgrade workflow files and CLAUDE.md to latest version |

## Ledger Operations (7)

| Command | Purpose |
|---------|---------|
| `quidclaw add-account NAME` | Open a new account |
| `quidclaw close-account NAME` | Close an account |
| `quidclaw list-accounts` | List all accounts (filter with `--type`) |
| `quidclaw add-txn` | Record a transaction (requires `--date`, `--payee`, `--posting`) |
| `quidclaw balance` | Query account balances (filter with `--account`) |
| `quidclaw balance-check ACCT AMT` | Reconciliation: assert an account balance (`--currency`) |
| `quidclaw fetch-prices [COMMODITIES...]` | Fetch and record asset prices *(not yet implemented)* |

## Reports & Queries (6)

| Command | Purpose |
|---------|---------|
| `quidclaw query "SELECT ..."` | Execute a BQL query |
| `quidclaw report income\|balance_sheet` | Generate a financial report |
| `quidclaw monthly-summary YYYY MM` | Income, expenses, and savings for a month |
| `quidclaw spending-by-category YYYY MM` | Ranked category breakdown for a month |
| `quidclaw month-comparison YYYY MM` | Month-over-month comparison with percentages |
| `quidclaw largest-txns YYYY MM` | Top N largest expense transactions |

## Data & Anomalies (2)

| Command | Purpose |
|---------|---------|
| `quidclaw detect-anomalies` | Run all anomaly checks (duplicates, outliers, subscriptions, unknown merchants) |
| `quidclaw data-status` | Data freshness: inbox count, last ledger update |
