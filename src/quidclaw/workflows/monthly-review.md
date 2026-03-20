# Monthly Financial Review

Generate a comprehensive, plain-language monthly financial report.

## Pre-Check

First, invoke the reconcile workflow mentally:
1. Run `quidclaw data-status --json` via Bash — are there unprocessed files?
2. If data is incomplete, help the user fill gaps before generating the report

## Report Generation

### Income vs Spending
Run `quidclaw report income` via Bash for the target month.
Present in plain language: "You made X and spent Y this month. That means you saved Z (or overspent by Z)."

### Spending Breakdown
Run `quidclaw query "SELECT root(account, 2) as category, sum(position) WHERE account ~ 'Expenses' AND year = YYYY AND month = MM GROUP BY category ORDER BY sum(position)" --json` via Bash.

Present as a ranked list: "Your biggest spending areas: 1. Food (X), 2. Housing (Y), ..."

### Month-over-Month Comparison
Compare with the previous month. Highlight changes > 20%:
"You spent 35% more on dining out compared to last month."

### Notable Transactions
Flag the 3-5 largest individual transactions.

### Insights (Plain Language)
- Positive trends: "You spent less on shopping this month — nice discipline!"
- Concerns: "Your food spending has been increasing for 3 months straight."
- Suggestions: Keep it actionable and brief.

## Save Report

Save the full report to `reports/YYYY-MM-monthly-report.md`.

## Tone

- Celebratory when things are good
- Gentle and constructive when things aren't
- Never preachy or judgmental
- Use concrete numbers, not vague statements
