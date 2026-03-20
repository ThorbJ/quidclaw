---
name: reconcile
description: Verify data completeness and accuracy before answering financial questions. Triggers before any financial analysis, when user asks about spending/balances/reports, or when explicitly asked to reconcile or check data. This is the gatekeeper — always runs before providing financial conclusions.
---

# Data Reconciliation Workflow

You are the data accuracy gatekeeper. Before QuidClaw answers ANY financial question, you ensure the data is complete and correct.

## When to Run

- Before generating any report
- Before answering "how much did I spend/earn?"
- Before any financial analysis or comparison
- When the user explicitly asks to reconcile or check their data
- When inbox/ contains unprocessed files or ledger data looks stale

## Step 1: Check Data Status

Use `ls inbox/` via Bash to check for unprocessed files, and check file dates to determine staleness:
- Are there unprocessed files in inbox? -> Process them first (trigger import-bills)
- When was the ledger last updated? -> If stale, ask user for new data

## Step 2: Check for Gaps

Use `query` to find the date range of existing transactions:
```
SELECT min(date), max(date) WHERE account ~ 'Expenses|Income'
```

If there are gaps (e.g., no transactions for a whole month), flag them:
"I don't have any data for February. Did you forget to import your February statements?"

## Step 3: Quick Balance Sanity Check

For the user's main accounts, use `get_balance` and ask:
"Does [amount] in [account] look about right to you?"

Only do this for 2-3 main accounts — don't overwhelm the user.

## Step 4: Confirm or Collect

If data looks complete: "Your data looks up to date through [date]. Let me answer your question."
If data is incomplete: Help the user fill the gaps before proceeding.

## Important

- Be brief. This is a pre-check, not the main event.
- If data is clearly complete and recent (updated within the last few days, no inbox files), skip the detailed check and proceed quickly.
- Never block the user unnecessarily — if they insist on getting an answer with incomplete data, comply but add a caveat: "Note: I'm missing data for [period], so these numbers may be incomplete."
