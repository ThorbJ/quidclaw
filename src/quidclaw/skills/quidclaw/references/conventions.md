# QuidClaw Conventions

## Data Integrity

- Only verified data (bank statements, receipts) goes into the ledger
- Always reconcile before generating reports or answering financial questions

## File Naming

- Transactions go into monthly files: `ledger/YYYY/YYYY-MM.bean`
- Document naming: `{Source}-{Type}-{YYYY-MM}.{ext}`

## Account Naming

- Account naming: use last 4 digits or identifiers (e.g., `Assets:Bank:CMB:1234`)

## Notes Structure

- **Living documents** (`profile.md`, `calendar.md`, `assets/`, `accounts/`, etc.) — always reflect current state
- **Append-only logs** (`decisions/`, `journal/`) — historical record, only grows
