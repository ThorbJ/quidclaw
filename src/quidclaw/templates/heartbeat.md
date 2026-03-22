# QuidClaw Heartbeat Checklist

Run these checks. If nothing needs attention, reply HEARTBEAT_OK.

1. Run `quidclaw list-sources --json` — if sources exist, run
   `quidclaw sync --json`. If new items synced, process them
   following `.quidclaw/workflows/check-email.md`
2. Check `notes/pending/` — if there are pending items that can now
   be resolved, process them
3. Check `notes/calendar.md` — if any payment is due within 3 days,
   alert the user
4. Run `quidclaw data-status --json` — if inbox has files, mention it
