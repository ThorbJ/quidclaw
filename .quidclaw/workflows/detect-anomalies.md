---
name: detect-anomalies
description: Analyze transactions for unusual patterns — duplicate charges, subscription price increases, unknown recurring charges, unusually large transactions. Triggers when user asks about unusual spending, suspicious charges, subscription review, or as part of monthly review.
---

# Anomaly Detection

Scan the user's transaction history for suspicious or unusual patterns.

## What to Look For

### 1. Duplicate Charges
Use `query` to find transactions with the same amount and similar payee within a 3-day window.
Flag any matches: "I found two charges of 35.80 to Starbucks on March 3 and March 4. Could one be a duplicate?"

### 2. Recurring Subscriptions
Use `query` to find payees that appear monthly with similar amounts:
```
SELECT payee, count(*) as times, sum(position) as total WHERE account ~ 'Expenses' GROUP BY payee HAVING count(*) >= 3 ORDER BY total
```
Present as a subscription summary with monthly cost.

### 3. Subscription Price Changes
For recurring charges, check if the amount changed recently.
Flag: "Netflix went from 88/month to 98/month starting February."

### 4. Unusually Large Transactions
Find transactions significantly larger than the user's average for that category.
Flag: "You spent 2,500 on dining on March 8 — that's 5x your usual dining expense."

### 5. Unknown Merchants
Flag payees that appear only once and don't match common categories:
"I see a charge of 199 to 'XYZ Tech Ltd' on March 12. Do you recognize this?"

### 6. Spending Spikes
Compare weekly spending to the monthly average. Flag weeks that are significantly higher.

## Presentation

- Group findings by severity: Likely issues, Worth checking, FYI
- For each finding, explain what you found and ask the user to confirm or dismiss
- Keep dismissed items in memory so you don't flag them again

## Tone

- Curious, not accusatory: "I noticed..." not "You were charged..."
- Helpful: "Want me to keep an eye on this subscription?"
- Brief: One finding per paragraph, with clear action items
