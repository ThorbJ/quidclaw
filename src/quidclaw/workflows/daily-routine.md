# Daily Routine — Automated Financial Check

You are running the daily financial routine. This workflow gathers new data from all sources, processes it, and provides a summary.

## Step 1: Gather Data

### 1a: Sync External Sources

Run `quidclaw sync --json` via Bash to pull data from all configured sources (email, APIs, etc.).

Report what was fetched.

### 1b: Check Inbox

Run `quidclaw data-status --json` via Bash to check for manually dropped files in `inbox/`.

If there are files in the inbox, list them.

## Step 2: Process New Data

### 2a: Process New Emails

If Step 1a fetched new emails, process them following `.quidclaw/workflows/check-email.md`.

### 2b: Process Inbox Files

If Step 1b found files in inbox, process them following `.quidclaw/workflows/import-bills.md`.

## Step 3: Check & Remind

### 3a: Upcoming Payments

Read `notes/calendar.md` (if it exists) and check for any payments due in the next 7 days.

### 3b: Anomaly Check

Run `quidclaw detect-anomalies --json` via Bash. Report anything suspicious.

## Step 4: Summary

Provide a brief summary to the user:
- Data gathered: N new emails, N inbox files
- Transactions recorded: N
- Upcoming payments: list any due in next 7 days
- Anomalies: list any found
- Overall status: "Everything looks good" or specific action items

## When to Run

This workflow can be triggered:
- Manually by the user ("check my finances", "daily routine", "what's new")
- By a scheduled task (future feature)
- At the start of a conversation when the user has configured proactive mode
