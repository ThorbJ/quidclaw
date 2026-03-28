# QuidClaw CLI Reference

Run these in the shell for Beancount engine operations:

```
# Setup
quidclaw init                        # Initialize ledger structure
quidclaw set-config KEY VALUE        # Set a configuration value
quidclaw get-config [KEY]            # Read configuration
quidclaw setup                       # Create default accounts (requires operating_currency)
quidclaw upgrade                     # Update workflows to latest version

# Accounts
quidclaw add-account NAME [--currencies X]  # Open account
quidclaw close-account NAME          # Close account
quidclaw list-accounts [--type X]    # List accounts

# Transactions
quidclaw add-txn --date D --payee P --posting '{...}'  # Record transaction

# Queries & Reports
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

# Price Tracking
quidclaw add-commodity NAME --source SOURCE --quote CURRENCY  # Register price source
quidclaw fetch-prices [COMMODITY...] # Fetch prices for registered commodities

# Data Sources
quidclaw add-source NAME --provider PROVIDER [--api-key KEY]  # Add data source
quidclaw list-sources                    # List configured sources
quidclaw remove-source NAME --confirm    # Remove a data source
quidclaw sync [SOURCE]                   # Sync from external sources
quidclaw mark-processed SOURCE DIR       # Mark email as processed

# Backup
quidclaw backup init                    # Initialize Git backup
quidclaw backup status                  # Show backup status
quidclaw backup add-remote NAME URL     # Add remote for backup
quidclaw backup remove-remote NAME      # Remove a remote
quidclaw backup push [--remote NAME]    # Push to remotes
```

## Price Tracking

When you encounter a new currency, crypto, or investment asset, register it with `add-commodity`:

```
# Fiat currencies — ticker format: {BASE}{QUOTE}=X
quidclaw add-commodity USD --source yahoo/USDCNY=X --quote CNY

# Crypto — ticker format: {BASE}-{QUOTE}
quidclaw add-commodity BTC --source yahoo/BTC-CNY --quote CNY

# Stocks/funds — ticker is the symbol, quote is trading currency
quidclaw add-commodity AAPL --source yahoo/AAPL --quote USD
quidclaw add-commodity 600519 --source yahoo/600519.SS --quote CNY
```

Then `quidclaw fetch-prices` will fetch all registered prices automatically.

## Source Traceability

When recording transactions from imported files or emails, include source metadata:
```
quidclaw add-txn ... --meta '{"source":"email:source-name/email-dir","import-id":"evt_ID"}'
```
This enables tracing any transaction back to its source document.

Most commands support `--json` for structured output.

## File Operations

For file operations, use your native tools directly:
- Read/write notes in `notes/*.md`
- List inbox: `inbox/*`
- Search notes across `notes/`
- List documents: `documents/**/*`
