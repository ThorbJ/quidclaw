# Anomaly Checks — Quick Reference

Quick-scan checklist for the daily routine anomaly pass.

## 1. Duplicate Charges

Query for transactions with the same amount and similar payee within a 3-day window. Flag potential duplicates and ask the user to confirm or dismiss.

## 2. Spending Spikes

Compare this week's spending to the monthly average per category. Flag any category where spending is significantly above normal (e.g., 2x+ the average).

## 3. Large Transactions

Find transactions significantly larger than the user's average for that expense category. Flag with context: amount, category, and how it compares to typical spending.

## 4. Unknown Merchants

Flag payees that appear only once and don't match common categories. Ask the user if they recognize the charge.

## 5. Subscription Changes

For recurring charges (same payee, 3+ occurrences), check if the most recent amount differs from the previous pattern. Flag any price increases.

## Presentation

- Group by severity: **Likely issues** > **Worth checking** > **FYI**
- One finding per paragraph with a clear action item
- Tone: curious, not accusatory ("I noticed..." not "You were charged...")
- Remember dismissed items so they are not flagged again
