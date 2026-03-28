---
name: quidclaw-import
description: >
  Import and process financial data into the ledger. Handles files in inbox/,
  email attachments, and synced source data. Parses, deduplicates, confirms
  with user, records transactions, and archives originals. Use when user says
  "import", "process inbox", "check email", or when inbox/ has unprocessed files.
---

# Import Financial Data

You are importing financial documents into QuidClaw. The user may have uploaded files in chat, dropped them into inbox/, or have new emails from configured sources.

Process one file at a time, completely, before moving to the next. Never leave a file half-processed.

## Step 1: Identify What to Process

- Run `ls inbox/` via Bash to find unprocessed files
- Check if the user has uploaded or pasted files in the current conversation
- List what you found and confirm the processing order

## Step 2: Parse the Document

For each file:

1. Read the file content (text/CSV files directly, vision for images/PDFs)
2. Identify the document type: bank statement, credit card bill, receipt, invoice, etc.
3. Extract ALL transactions: date, amount, currency, payee, description
4. Handle both Chinese and English format documents
5. If this is the first time seeing this bank/account, check `notes/profile.md` for context about the user's accounts

## Step 3: Deduplicate

Before recording, check for existing duplicates:

1. Run `quidclaw query "SELECT date, payee, position WHERE ..." --json` via Bash to find existing transactions near the same dates
2. Compare by: date (+/- 2 days) + amount (exact match) + payee (similar)
3. If a likely duplicate is found, flag it and ask the user
4. NEVER silently skip a transaction -- always confirm with the user

## Step 4: Confirm with User

Present the extracted transactions in a clear, readable format:

- Group by date
- Show: date, payee, amount, suggested category
- Mark uncertain items with `?`
- Mark potential duplicates with `(possible duplicate)`

Ask the user to confirm before recording. They can approve all, remove specific items, correct details, or add notes.

If the user has asked you to import without confirmation, or if you are in an automated environment, skip this step and proceed directly.

## Step 5: Record Transactions

For each confirmed transaction:

1. Create accounts if they don't exist yet -- use the naming convention:
   - Banks: `Assets:Bank:{BankName}:{Last4}` (ask user for last 4 if not known)
   - Credit cards: `Liabilities:CreditCard:{BankName}:{Last4}`
   - Payment apps: `Assets:{AppName}` or `Assets:{AppName}:{Identifier}`
2. Run `quidclaw add-account NAME --currencies CUR` via Bash for any new accounts
3. Run `quidclaw add-txn` via Bash for each transaction:
   ```
   quidclaw add-txn --date YYYY-MM-DD --payee "Payee" --narration "Description" \
     --posting '{"account":"...","amount":"...","currency":"..."}' \
     --posting '{"account":"..."}' \
     --meta '{"source":"inbox_file:{FILENAME}","source-file":"documents/YYYY/MM/{ARCHIVED_NAME}"}'
   ```
4. Use descriptive narrations the user will understand later
5. Match the currency from the document -- do NOT default, use what the document says
6. One posting must auto-balance: omit the amount on the funding source posting

## Step 6: Archive the File

Right after recording transactions from a file, archive it IMMEDIATELY before doing anything else.

```bash
mkdir -p documents/YYYY/MM && mv inbox/filename documents/YYYY/MM/new-name
```

Naming convention: `{Source}-{Type}-{YYYY-MM}.{ext}`

Examples:
- `招商银行-信用卡账单-2026-03.csv`
- `支付宝-交易记录-2026-03.csv`
- `Amazon-Statement-2026-03.csv`

Then verify: run `ls inbox/` to confirm the file is gone. If it's still there, try again.

## Step 7: Write Processing Log and Finish

After archiving, write a YAML processing log to `logs/`:

```yaml
id: "evt_{timestamp}_{random6hex}"
timestamp: "{ISO timestamp}"
action: "import"
source:
  type: "inbox_file"
  path: "inbox/{original_filename}"
input_files:
  - "inbox/{original_filename}"
extracted:
  transactions_found: {count}
  transactions_recorded: {count}
archived_to:
  - "documents/YYYY/MM/{archived_name}"
```

If the document contains non-transaction information (account numbers, interest rates, credit limits, policy terms), save it to the appropriate `notes/` path.

After ALL files are processed, run `ls inbox/` one final time. If the inbox is NOT empty, process the remaining files. Then report to the user: files processed, transactions recorded, archive locations, and any items needing follow-up.

## When Blocked

If you cannot complete processing (encrypted PDF, ambiguous transaction, missing account info):

1. Save a pending item to `notes/pending/{date}_{description}.yaml` with fields: created, type (blocked), reason, context, action
2. Notify the user what you need
3. Move on to the next file -- do not stop the entire workflow

## References

- If processing email sources, read `references/email-processing.md` for email-specific steps.
- After recording transactions, read `references/document-archival.md` to organize source files.

## Rules

- **Process one file at a time, completely.** Parse, record, archive, then next file.
- **Never guess amounts.** If you can't read a number clearly, ask.
- **Ask about unknown payees.** "I see a charge from 'XYZ Tech' -- do you know what this is?"
- **Respect the document's currency.** Use what the document says, do NOT default.
- **Inbox must be empty when you're done.** Every processed file must be archived.
- **Create accounts on the fly** from real data -- this is the proper way to set up accounts.
