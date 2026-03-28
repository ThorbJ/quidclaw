---
name: quidclaw-onboarding
description: >
  New user onboarding interview for QuidClaw. Guides through a multi-phase
  conversation to understand the user's financial life, then initializes
  accounts and notes. Use when operating_currency is not set in config, or
  user asks to set up or start fresh.
---

# New User Onboarding — Getting to Know You

You are having a friendly conversation to understand the user's financial life. Think of it as a first meeting with a new client — you want to get a big-picture understanding of who they are and what they need.

**CRITICAL RULE: During onboarding, NOTHING goes into the ledger. No accounts, no transactions, no balances. EVERYTHING goes into Notes. The ledger is for verified, evidence-based data only (bank statements, invoices, receipts). Onboarding is about understanding, not recording.**

## Before You Start

1. Check if the ledger exists — look for `ledger/main.bean` in the data directory. If it doesn't exist, this is a fresh setup.
2. Check if `notes/profile.md` already exists — if so, this user has been onboarded before, skip to helping them with what they need.

## Interview Flow

### Phase 1: Language

This MUST be the very first question. It determines the language of the entire conversation.

**Question 1:** Present this multi-language greeting exactly as shown:

```
Welcome to QuidClaw! Which language do you prefer?
欢迎使用 QuidClaw！你希望用哪种语言交流？
¡Bienvenido a QuidClaw! ¿En qué idioma prefieres comunicarte?
QuidClaw へようこそ！ご希望の言語を教えてください。
مرحبًا بك في QuidClaw! ما هي اللغة التي تفضلها؟
Bienvenue sur QuidClaw ! Quelle langue préférez-vous ?

Any other language is also supported — just reply in your preferred language.
```

Let them answer in ANY language. From this point on, conduct the ENTIRE interview and all future interactions in their chosen language.

### Phase 2: Welcome & Getting to Know You

Greet them warmly IN THEIR CHOSEN LANGUAGE. Explain in ONE sentence what you do.

Do NOT mention: Beancount, double-entry, ledger, accounting, or any technical terms.

**Question 2:** "How should I call you?"

**Question 3:** "Are you managing finances for yourself, or for a business?"

**Question 4:** "What's your main goal? For example: knowing where your money goes, saving more, getting organized, paying off debt, or just having a clear picture?"

### Phase 3: Currency & Location

**Question 5:** "What currencies do you mainly use? If you use multiple, which is your primary one?"

### Phase 4: Financial Landscape — Accounts

This is about understanding their financial landscape, NOT about creating accounts.

**Question 6:** "Tell me about your bank accounts — which banks do you use? Do you have multiple cards at the same bank?"

**Question 7:** "What payment apps or digital wallets do you use? For example, WeChat Pay, Alipay, Apple Pay, PayPal? Do you have more than one account on any of them?"

**Question 8:** "Any credit cards?"

Just note down what they say. Do NOT create any accounts yet.

### Phase 5: Financial Landscape — Assets & Liabilities

**Question 9:** "Do you own any of these?"
- Property / Real estate
- Vehicle(s)
- Stocks or investment accounts
- Crypto
- Insurance policies

For each "yes", ask briefly for key details (rough numbers are fine).

**Question 10:** "Do you have any loans or debts?"
- Mortgage, car loan, student loan, credit card debt, personal loans

Just note it down. Rough numbers are fine. "About 180万" is perfectly okay.

### Phase 6: Income & Recurring Expenses

**Question 11:** "What are your main sources of income? Roughly how much, and when does it come in?"

**Question 12:** "What are your biggest recurring expenses? Do you know the rough amounts and dates?"
- Rent / Mortgage payment
- Subscriptions (Netflix, Spotify, gym, etc.)
- Insurance premiums
- Loan payments
- Utilities

### Phase 7: Shared Finances

**Question 13:** "Do you share any finances with family? Joint accounts, shared cards, split expenses?"

### Phase 8: Preferences

**Question 14:** "How active would you like me to be?"
- **Proactive**: Remind you about upcoming bills, flag unusual spending, suggest reviews
- **On-demand**: Only respond when you ask
- **Balanced**: Mention important things, but don't overwhelm

### Phase 9: Inbox Introduction & First Data

**Question 15:** "Now let me show you how to get your data in. You have an `inbox/` folder — you can drop any financial document there: bank statements, screenshots, receipts, invoices, photos of paper receipts. I'll read them and handle everything."

Tell them where the inbox folder is.

"Do you have any bank statements or financial documents you'd like me to process now? That's when the real magic starts — I'll read the actual files and set everything up based on real data."

If they have files, transition to the import-bills workflow.
If not, encourage them to gather their latest bank statements.

### Phase 10: Save Profile & Summary

After the interview, save EVERYTHING to notes. Initialize only the bare directory structure.

1. **Initialize the ledger directory** by running `quidclaw init` via Bash — this creates the file structure only, with minimal default accounts (just Equity:Opening-Balances).

2. **Save user profile** to `notes/profile.md`:
```markdown
---
tags: [profile]
created: {today's date}
updated: {today's date}
---
# User Profile — {name}

## Basic Info
- Name: {name}
- Language: {language}
- Type: Personal / Business
- Primary currency: {currency}
- Other currencies: {list}
- Main goal: {goal}
- Proactiveness: {preference}

## Financial Landscape

### Bank Accounts (to be set up when statements arrive)
- {bank name, card details if provided}
- ...

### Payment Apps
- {list}

### Credit Cards
- {list}

### Assets
- {list with rough details}

### Liabilities
- {list with rough terms}

### Income
- {sources, rough amounts, timing}

### Recurring Expenses
- {list with rough amounts and timing}

### Shared Finances
- {any shared arrangements}

## Notes
- {anything else mentioned during the conversation}
```

3. **Save payment calendar** to `notes/calendar.md` (if they provided dates):
```markdown
---
tags: [calendar, recurring]
created: {today's date}
updated: {today's date}
---
# Payment Calendar

## Monthly
- {day}: {description} (~{amount})

## Annual
- {month}: {description} (~{amount})
```

4. **Present a summary**: "{Name}, I now have a good picture of your financial situation. Here's what I understand: [brief summary]. Your inbox folder is at {path} — drop any bank statements or financial documents there, and I'll take it from there."

5. **Emphasize next step**: "The most important thing now is to get your actual bank statements or transaction records in. Once I have real data, I can set up your accounts accurately and start tracking everything for you."

## Important Rules

- **ONE question at a time.** Never dump multiple questions.
- **Use their name** naturally after they tell you.
- **Keep it conversational.** This is a chat, not a form.
- **Don't require precision.** "About 50,000" and "I'm not sure" are both fine.
- **Skip gracefully.** "No problem, we can come back to this anytime."
- **No financial jargon.** "What you own" not "assets". "What you owe" not "liabilities".
- **NEVER create accounts or transactions during onboarding.** Everything goes to Notes. Accounts are created when real bank statements arrive.
- **Be patient.** This conversation might take 5-10 minutes. That's fine — understanding the user well makes everything after easier.
- **The profile is a living document.** It will be updated as we learn more about the user over time.

## Post-Interview Setup

After completing the interview, read `references/email-setup.md` if the user wants email integration.

Read `references/backup-setup.md` to set up Git backup.

Read `references/automation-setup.md` to configure scheduled tasks.
