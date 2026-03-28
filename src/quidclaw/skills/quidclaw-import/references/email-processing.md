# Email Processing

Steps for importing financial data from email sources. This extends the core import flow with email-specific handling.

## Sync New Emails

Run `quidclaw sync --json` via Bash to fetch new emails from all configured sources.

If no sources are configured, tell the user and suggest running onboarding or `quidclaw add-source`.

If new emails arrived, list them for the user showing sender, subject, and date.

## Process Each Unprocessed Email

For each source, check `sources/{source_name}/` for email directories. Read each `envelope.yaml` and look for `status: "unprocessed"`.

For each unprocessed email, complete ALL steps below before moving to the next.

### Understand Context

Read `envelope.yaml` first -- understand who sent the email, the subject, and when it arrived.

Read `body.txt` -- extract any inline financial information:
- Transaction notifications (amounts, dates, payees)
- Balance updates
- Payment due dates and amounts
- Account summaries

### Process Attachments

If the email has files in `attachments/`:
1. For PDFs and images -- use vision to read them
2. For CSVs and text files -- read them directly
3. Follow the same parse, dedup, confirm, record flow as the core import skill

### Record with Source Metadata

When recording transactions from email, ALWAYS include `--meta` for traceability. Use `--flag '!'` for uncertain transactions that need user confirmation:

```
quidclaw add-txn \
  --date YYYY-MM-DD \
  --payee "Payee" \
  --narration "Description" \
  --posting '{"account":"...","amount":"...","currency":"..."}' \
  --posting '{"account":"..."}' \
  --meta '{"source":"email:{source_name}/{email_dir}","source-file":"documents/YYYY/MM/archived-name.ext","import-id":"evt_ID"}'
```

### Write Processing Log

After processing each email, create a YAML log file in `logs/`:

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

### Archive and Mark Processed

1. Move attachment files to `documents/YYYY/MM/` using the naming convention `{Source}-{Type}-{YYYY-MM}.{ext}`
2. Link the archived document: `quidclaw add-document ACCOUNT documents/YYYY/MM/archived-name.ext --date YYYY-MM-DD`
3. Run `quidclaw mark-processed {source_name} {email_dir}` to update the status

## Summary

After processing all emails, report:
- How many emails were processed
- How many transactions were recorded
- Any issues or items needing follow-up

## When Blocked

If you cannot complete processing (missing password, unreadable file, ambiguous data):
1. Save a pending item to `notes/pending/{date}_{description}.yaml` with fields: created, type (blocked), reason, context, action
2. Notify the user what you need
3. Move on to the next item -- do not stop the entire workflow

## Rules

- ALWAYS read envelope.yaml + body.txt together before processing attachments -- context matters
- ALWAYS include --meta on every transaction for traceability
- ALWAYS create a processing log entry for each email processed
- ALWAYS mark emails as processed after completing all steps
- Process one email at a time, completely, before moving to the next
- If an email has no financial content (e.g., marketing), mark it as processed and skip
