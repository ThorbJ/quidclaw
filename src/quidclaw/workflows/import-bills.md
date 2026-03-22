# Bill Import Workflow

You are importing financial documents into QuidClaw. The user may have uploaded files in chat or dropped them into their inbox/ folder.

## Overview

For EACH file, you must complete ALL of these steps in order:
1. Parse → 2. Dedup → 3. Confirm → 4. Record → 5. Archive the file → 6. Write processing log → 7. Capture extra info

**Do NOT move to the next file until the current file is fully archived.**

## Step 1: Identify What to Process

- Run `ls inbox/` via Bash to find unprocessed files
- Check if the user has uploaded or pasted files in the current conversation
- List what you found

## For Each File, Do Steps 2-8:

### Step 2: Parse the Document

1. Read the file content (text/CSV files directly, vision for images/PDFs)
2. Identify the document type (bank statement, credit card bill, receipt, etc.)
3. Extract ALL transactions: date, amount, currency, payee, description
4. Handle both Chinese and English format documents
5. If this is the first time seeing this bank/account, check `notes/profile.md` for context about the user's accounts

### Step 3: Deduplicate

Before recording, check for duplicates:
1. Run `quidclaw query "SELECT date, payee, position WHERE ..." --json` via Bash to find existing transactions near the same dates
2. Compare by: date (±2 days) + amount (exact match) + payee (similar)
3. If a likely duplicate is found, flag it and ask the user
4. NEVER silently skip a transaction — always confirm with the user

### Step 4: Confirm with User

Present the extracted transactions in a clear, readable format:
- Group by date
- Show: date, payee, amount, suggested category
- Mark any uncertain items with ?
- Mark any potential duplicates with (possible duplicate)

Ask the user to confirm before recording. They can:
- Approve all
- Remove specific items
- Correct details
- Add notes

**If the user has asked you to import without confirmation, or if you are in an automated environment, skip this step and proceed directly.**

### Step 5: Record Transactions

For each confirmed transaction:
1. Create accounts if they don't exist yet — use the account naming convention:
   - Banks: `Assets:Bank:{BankName}:{Last4}` (ask user for last 4 if not known)
   - Credit cards: `Liabilities:CreditCard:{BankName}:{Last4}`
   - Payment apps: `Assets:{AppName}` or `Assets:{AppName}:{Identifier}`
2. Run `quidclaw add-account NAME --currencies CUR` via Bash for any new accounts
3. Run `quidclaw add-txn --date D --payee P --narration N --posting '{"account":"...","amount":"...","currency":"..."}'` via Bash for each transaction
4. Use descriptive narrations the user will understand later
5. Match the currency from the document (do NOT default — use what the document says)
6. Include source metadata for traceability:
   `--meta '{"source":"inbox_file:{FILENAME}","source-file":"documents/YYYY/MM/{ARCHIVED_NAME}"}'`
   This enables tracing any transaction back to its source document.

### Step 6: Archive This File — IMMEDIATELY

**Right after recording transactions from a file, archive it IMMEDIATELY before doing anything else.**

Use Bash to archive the file:
```bash
mkdir -p documents/YYYY/MM && mv inbox/filename documents/YYYY/MM/new-name
```

Naming: `{Source}-{Type}-{YYYY-MM}.{ext}`
Examples:
- `招商银行-信用卡账单-2026-03.csv`
- `支付宝-交易记录-2026-03.csv`
- `Amazon-Statement-2026-03.csv`
- `NBD-BankStatement-2026-03.png`

**Then verify**: Run `ls inbox/` to confirm the file is gone. If it's still there, try again.

### Step 7: Write Processing Log

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

### Step 8: Capture Extra Info (if applicable)

If the document contains non-transaction information (account numbers, interest rates, credit limits, policy terms):
- Save it to the appropriate `notes/` path, or append to an existing note
- Example: bank account details → `notes/accounts/招商银行-信用卡.md`

## After All Files Are Processed

Run `ls inbox/` one final time. If the inbox is NOT empty, something was missed — process the remaining files.

Report to the user:
- How many files were processed
- How many transactions were recorded
- Where the files were archived to
- Any issues or items that need follow-up

## When Blocked

If you cannot complete processing (encrypted PDF, ambiguous transaction,
missing account info):
1. Save a pending item to `notes/pending/{date}_{description}.yaml` with fields:
   created, type (blocked), reason, context, action
2. Notify the user what you need
3. Move on to the next file — do not stop the entire workflow
4. The pending item will be picked up on the next heartbeat

## Important Rules

- **Process one file at a time, completely.** Parse → Record → Archive → Next file.
- **Never guess amounts.** If you can't read a number clearly, ask.
- **Ask about unknown payees.** "I see a charge from 'XYZ Tech' — do you know what this is?"
- **Respect the document's currency.** Use what the document says, do NOT default.
- **One posting must auto-balance** — omit the amount on the funding source posting.
- **Inbox must be empty when you're done.** Every processed file must be archived.
- **Create accounts on the fly** from real data — this is the proper way to set up accounts (not during onboarding).
