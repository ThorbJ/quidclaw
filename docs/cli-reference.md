# CLI Reference

All commands support `--help`. Most support `--json` for structured AI-friendly output.

## Setup & Config (5)

| Command | Purpose |
|---------|---------|
| `quidclaw init` | Initialize a new financial project: creates ledger, installs skills, generates entry file |
| `quidclaw upgrade` | Upgrade skills and entry file to latest version |
| `quidclaw set-config KEY VALUE` | Set a configuration value |
| `quidclaw get-config [KEY]` | Get configuration values (`--json`) |
| `quidclaw setup` | Create default accounts using configured operating currency |

## Ledger Operations (12)

| Command | Purpose |
|---------|---------|
| `quidclaw add-account NAME` | Open a new account (`--currencies`, `--date`, `--meta` for institution/account-number) |
| `quidclaw close-account NAME` | Close an account (`--date`) |
| `quidclaw list-accounts` | List all accounts (`--type` to filter, `--json`) |
| `quidclaw add-note ACCOUNT "text"` | Add a Beancount note to an account (`--date`) |
| `quidclaw add-txn` | Record a transaction (`--date`, `--payee`, `--posting`, `--flag`, `--tag`, `--link`, `--meta`) |
| `quidclaw add-document ACCOUNT PATH` | Link a document to an account (`--date`) |
| `quidclaw add-pad ACCOUNT` | Auto-fill balance gap to next assertion (`--source`, `--date`) |
| `quidclaw add-balance ACCOUNT` | Write a balance assertion to the ledger (`--amount`, `--currency`, `--date`) |
| `quidclaw balance` | Query account balances (`--account` to filter, `--json`) |
| `quidclaw balance-check ACCOUNT EXPECTED` | Reconciliation check — read-only (`--currency`) |
| `quidclaw query BQL` | Execute a BQL query (`--json`) |
| `quidclaw report income\|balance_sheet` | Generate a financial report (`--period`) |

## Reports & Analysis (5)

| Command | Purpose |
|---------|---------|
| `quidclaw monthly-summary YEAR MONTH` | Income, expenses, and savings for a month (`--json`) |
| `quidclaw spending-by-category YEAR MONTH` | Ranked category breakdown for a month (`--json`) |
| `quidclaw month-comparison YEAR MONTH` | Month-over-month comparison with percentages (`--json`) |
| `quidclaw largest-txns YEAR MONTH` | Top N largest expense transactions (`--limit`, `--json`) |
| `quidclaw detect-anomalies` | Run all anomaly checks (`--json`) |

## Data Sources (5)

| Command | Purpose |
|---------|---------|
| `quidclaw add-source NAME` | Add a new data source (`--provider`, `--api-key`, `--inbox-id`, `--username`, `--display-name`) |
| `quidclaw list-sources` | List configured data sources (`--json`) |
| `quidclaw remove-source NAME` | Remove a data source configuration (`--confirm`) |
| `quidclaw sync [SOURCE_NAME]` | Sync data from external sources; omit name to sync all (`--json`) |
| `quidclaw mark-processed SOURCE_NAME EMAIL_DIR` | Mark an email as processed |

## Backup (5)

| Command | Purpose |
|---------|---------|
| `quidclaw backup init` | Initialize Git backup in the data directory |
| `quidclaw backup status` | Show backup status (branch, remotes, uncommitted changes) |
| `quidclaw backup add-remote NAME URL` | Add a remote repository for backup |
| `quidclaw backup remove-remote NAME` | Remove a backup remote |
| `quidclaw backup push [--remote NAME]` | Push to all remotes, or a specific remote (`--remote`) |

## Data Management (3)

| Command | Purpose |
|---------|---------|
| `quidclaw data-status` | Data freshness: inbox count, last ledger update, and source sync status (`--json`) |
| `quidclaw add-commodity NAME` | Register a commodity (stock, fund, custom asset) for price tracking (`--source`, `--quote`, `--date`) |
| `quidclaw fetch-prices [COMMODITIES...]` | Fetch and record asset prices from configured sources (`--json`) |
