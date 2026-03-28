# Import Steps — Quick Reference

Condensed checklist for processing new financial data during the daily routine.

## 1. Sync

Confirm data source is available. For email: `quidclaw sync --json`. For inbox: check `inbox/` contents via `quidclaw data-status --json`.

## 2. Parse

Read and interpret each document (PDF statement, receipt image, CSV export). Extract: date, payee, amount, currency, account. Use AI to interpret — the CLI does not parse documents.

## 3. Deduplicate

Before recording, run `quidclaw query` to check if transactions already exist in the ledger. Match on date + payee + amount within a 3-day window. Skip any that are already recorded.

## 4. Confirm

Present extracted transactions to the user for review. Show: date, payee, amount, suggested category. Ask user to confirm, edit, or skip each batch.

## 5. Record

For each confirmed transaction, run:
```bash
quidclaw add-txn --date DATE --payee PAYEE --from ACCOUNT --to ACCOUNT --amount AMOUNT --currency CUR --json
```

## 6. Archive

Move processed files from `inbox/` to `documents/` using:
```bash
quidclaw archive-doc PATH --json
```

Log the processing result to `logs/`.
