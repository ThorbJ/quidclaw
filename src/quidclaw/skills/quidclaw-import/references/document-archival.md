# Document Archival

Steps for organizing financial documents from inbox/ into the structured archive. Use this after recording transactions to properly file source documents, or when the user asks to organize documents without importing transactions.

## Scan Inbox

Run `ls inbox/` via Bash to see all unprocessed files.

## Process Each File

For each file:

1. Read or view the file to understand what it is
2. Classify it: bank statement, credit card bill, invoice, contract, insurance policy, receipt, tax document, etc.
3. Determine the source (who issued it) and the relevant date
4. Propose a new filename following the naming convention: `{Source}-{Type}-{YYYY-MM}.{ext}`

## Confirm with User

Present the proposed organization:

```
inbox/CMB-March-2026.pdf    -> documents/2026/03/招商银行-信用卡账单-2026-03.pdf
inbox/receipt-photo.jpg     -> documents/2026/03/星巴克-收据-2026-03-15.jpg
inbox/insurance.pdf         -> documents/2023/01/平安保险-重疾险保单-2023-01.pdf
```

Ask the user to confirm or adjust before moving anything.

## Move Files

Run via Bash for each confirmed file:

```bash
mkdir -p documents/YYYY/MM && mv inbox/filename documents/YYYY/MM/new-name
```

## Capture Key Information

For documents that contain important non-transaction information (contracts, insurance policies, terms):

- Extract key details: dates, terms, amounts, parties involved
- Save to the appropriate notes path:
  - Contracts -> `notes/assets/` or `notes/liabilities/`
  - Insurance -> `notes/insurance/`
  - Other -> `notes/` root

## When Blocked

If you cannot identify a document and the user is not available:
1. Save a pending item to `notes/pending/{date}_{description}.yaml`
2. Leave the file in inbox/
3. Move on to the next file

## Rules

- Never move a file without user confirmation
- If you can't identify a file, ask the user what it is
- After organizing, give a brief summary: "Organized X files. Y had transactions that were recorded."
