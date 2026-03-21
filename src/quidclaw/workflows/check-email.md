# Check Email — Processing New Emails

You are checking email data sources for new messages and processing any financial documents found.

## Step 1: Sync New Emails

Run `quidclaw sync --json` via Bash to fetch new emails from all configured sources.

If no sources are configured, tell the user and suggest running onboarding or `quidclaw add-source`.

If new emails arrived, list them for the user showing sender, subject, and date.

## Step 2: Process Each Unprocessed Email

For each source, check `sources/{source_name}/` for email directories. Read each `envelope.yaml` and look for `status: "unprocessed"`.

For each unprocessed email:

### 2a: Understand Context

Read `envelope.yaml` first — understand who sent the email, the subject, and when it arrived.

Read `body.txt` — extract any inline financial information:
- Transaction notifications (amounts, dates, payees)
- Balance updates
- Payment due dates and amounts
- Account summaries

### 2b: Process Attachments

If the email has files in `attachments/`:
1. For PDFs and images — use vision to read them
2. For CSVs and text files — read them directly
3. Follow the same parse → dedup → confirm → record flow as `import-bills.md`

### 2c: Record with Source Metadata

When recording transactions, ALWAYS include `--meta` for traceability:

```
quidclaw add-txn \
  --date YYYY-MM-DD \
  --payee "Payee" \
  --narration "Description" \
  --posting '{"account":"...","amount":"...","currency":"..."}' \
  --posting '{"account":"..."}' \
  --meta '{"source":"email:{source_name}/{email_dir}","source-file":"documents/YYYY/MM/archived-name.ext","import-id":"evt_ID"}'
```

### 2d: Write Processing Log

After processing each email, create a YAML log file in `logs/` with this format:

```yaml
id: "evt_{timestamp}_{random}"
timestamp: "{ISO timestamp}"
action: "import"
source:
  type: "email"
  path: "sources/{source_name}/{email_dir}"
  provider: "{provider}"
  original_subject: "{subject}"
  original_from: "{from}"
input_files:
  - "sources/{source_name}/{email_dir}/attachments/filename.pdf"
extracted:
  transactions_found: N
  transactions_recorded: N
  transactions_rejected: N
archived_to:
  - "documents/YYYY/MM/filename.ext"
```

### 2e: Archive and Mark Processed

1. Move attachment files to `documents/YYYY/MM/` using the naming convention `{Source}-{Type}-{YYYY-MM}.{ext}`
2. Run `quidclaw mark-processed {source_name} {email_dir}` to update the status

## Step 3: Summary

After processing all emails, report:
- How many emails were processed
- How many transactions were recorded
- Any issues or items needing follow-up

## Important Rules

- ALWAYS read envelope.yaml + body.txt together before processing attachments — context matters
- ALWAYS include --meta on every transaction for traceability
- ALWAYS create a processing log entry for each email processed
- ALWAYS mark emails as processed after completing all steps
- Process one email at a time, completely, before moving to the next
- If an email has no financial content (e.g., marketing), mark it as processed and skip
