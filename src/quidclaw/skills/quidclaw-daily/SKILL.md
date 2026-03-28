---
name: quidclaw-daily
description: >
  Daily financial routine. Syncs all sources, processes new data, checks for
  anomalies, and provides a concise briefing. Use when user says "daily check",
  "what's new today", or as a scheduled daily task.
---

# Daily Financial Routine

Run the daily check: gather data, process it, scan for issues, and deliver a briefing.

## Step 1: Gather Data

### Sync External Sources

Run `quidclaw sync --json` via Bash to pull data from all configured sources (email, APIs, etc.). Report what was fetched.

### Check Inbox

Run `quidclaw data-status --json` via Bash to check for manually dropped files in `inbox/`. If there are files, list them.

## Step 2: Process New Data

If there is new data to process, read `references/import-steps.md`.

- **New emails**: For each email with attachments (statements, receipts), follow the import steps to extract, deduplicate, confirm, and record transactions.
- **Inbox files**: For each file in `inbox/`, follow the same import steps.

## Step 3: Check and Remind

### Upcoming Payments

Read `notes/calendar.md` (if it exists) and check for any payments due in the next 7 days.

### Anomaly Scan

To check for anomalies, read `references/anomaly-steps.md`.

Run `quidclaw detect-anomalies --json` via Bash and report anything suspicious.

## Step 4: Briefing

Provide a concise summary to the user:
- Data gathered: N new emails, N inbox files
- Transactions recorded: N
- Upcoming payments: list any due in next 7 days
- Anomalies: list any found
- Overall status: "Everything looks good" or specific action items

### Output Format

Keep the daily briefing concise and scannable:
- Use emoji as visual markers
- One line per item, no tables or code blocks
- Total length under 500 characters
- If nothing needs attention: "All clear"

## Triggers

This routine can be activated by:
- User request ("check my finances", "daily routine", "what's new")
- Scheduled task (daily at user's preferred time)
- Start of conversation when proactive mode is configured
