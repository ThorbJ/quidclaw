---
name: quidclaw-review
description: >
  Financial review, reporting, and analysis. Generates monthly summaries,
  detects anomalies, and reconciles balances. Always reconcile before
  reporting. Use when user asks for "monthly report", "review", "anomalies",
  "reconcile", or "financial summary".
---

# Monthly Financial Review

Generate a comprehensive, plain-language monthly financial report.

Before generating any report, read `references/reconciliation.md` and run the pre-flight checks.

## Steps

### 1. Pre-Check Reconcile

Run `quidclaw data-status --json` via Bash to check for unprocessed files and data freshness. If data is incomplete, help the user fill gaps before generating the report.

### 2. Income Report

Run `quidclaw report income` via Bash for the target month. Present in plain language: "You made X and spent Y this month. That means you saved Z (or overspent by Z)."

### 3. Spending Breakdown

Run via Bash:
```bash
quidclaw query "SELECT root(account, 2) as category, sum(position) WHERE account ~ 'Expenses' AND year = YYYY AND month = MM GROUP BY category ORDER BY sum(position)" --json
```

Present as a ranked list: "Your biggest spending areas: 1. Food (X), 2. Housing (Y), ..."

### 4. Month-over-Month Comparison

Compare with the previous month. Highlight changes > 20%: "You spent 35% more on dining out compared to last month."

### 5. Notable Transactions

Flag the 3-5 largest individual transactions.

To scan for anomalies, read `references/anomaly-detection.md`.

### 6. Insights

Provide plain-language insights:
- Positive trends: "You spent less on shopping this month -- nice discipline!"
- Concerns: "Your food spending has been increasing for 3 months straight."
- Suggestions: Keep it actionable and brief.

### 7. Save Report

Save the full report to `reports/YYYY-MM-monthly-report.md`.

## Output Format

Monthly summary should be structured but readable in chat:
- Lead with the headline numbers
- Category breakdown as a simple list
- Flag anomalies and notable changes
- Keep under 1000 characters for the summary
- Offer to send detailed report if user wants

## Tone

- Celebratory when things are good
- Gentle and constructive when things aren't
- Never preachy or judgmental
- Use concrete numbers, not vague statements
