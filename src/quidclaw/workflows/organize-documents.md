# Document Organization Workflow

You are organizing the user's financial documents from their messy inbox into a clean, structured archive.

## Step 1: Scan Inbox

Run `ls inbox/` via Bash to see all unprocessed files.

## Step 2: Process Each File

For each file:
1. Read/view the file to understand what it is
2. Classify it: bank statement, credit card bill, invoice, contract, insurance, receipt, tax doc, etc.
3. Determine the source (who issued it) and date
4. Propose a new filename following the naming convention:
   `{Source}-{Type}-{YYYY-MM}.{ext}`

## Step 3: Confirm with User

Present the proposed organization:
```
inbox/CMB-March-2026.pdf -> documents/2026/03/招商银行-信用卡账单-2026-03.pdf
inbox/receipt-photo.jpg -> documents/2026/03/星巴克-收据-2026-03-15.jpg
inbox/insurance.pdf -> documents/2023/01/平安保险-重疾险保单-2023-01.pdf
```

Ask the user to confirm or adjust.

## Step 4: Move Files

Run via Bash for each confirmed file: `mkdir -p documents/YYYY/MM && mv inbox/filename documents/YYYY/MM/new-name`

## Step 5: Capture Key Information

For documents that contain important non-transaction info (contracts, insurance policies):
- Extract key details (dates, terms, amounts, parties)
- Save to the appropriate notes path:
  - Contract -> `notes/assets/` or `notes/liabilities/`
  - Insurance -> `notes/insurance/`
  - Other -> `notes/` root

## Rules

- Never move a file without user confirmation
- If you can't identify a file, ask the user what it is
- After organizing, give a brief summary: "Organized X files. Y had transactions that were recorded."
