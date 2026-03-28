# Automation Setup (OpenClaw only)

Check if running in OpenClaw by looking for HEARTBEAT.md in the workspace root.
If not present, skip this phase.

## Step 1: Daily Routine

Ask user: "I can automatically check your email, remind you about
upcoming payments, and give you a daily briefing. What time works best?"

Based on their answer, run via Bash:
```
openclaw cron add --name "QuidClaw daily" \
  --cron "0 {hour} * * *" --tz "{user_timezone}" \
  --session isolated \
  --message "Run /quidclaw-daily"
```

Record in notes/profile.md under ## Automation:
  "Daily briefing: {time} {timezone}"

If user declines:
  Record in notes/profile.md: "Daily briefing: declined"
  Append to notes/decisions/{year}.md: "{date}: User declined daily automation. Reason: {reason if given}."

## Step 2: Monthly Report

Ask user: "I'll send you a monthly financial summary on the 1st of
each month. Same time as daily briefing, or different?"

Run via Bash:
```
openclaw cron add --name "QuidClaw monthly" \
  --cron "0 {hour} 1 * *" --tz "{user_timezone}" \
  --session isolated \
  --message "Run /quidclaw-review"
```

Record in notes/profile.md under ## Automation:
  "Monthly report: 1st of each month at {time}"

If user declines:
  Record in notes/profile.md: "Monthly report: declined"
  Append to notes/decisions/{year}.md: "{date}: User declined monthly report automation. Reason: {reason if given}."

## Step 3: Confirm

"All set! Here's what I'll do automatically:
 - Every day at {time}: check email, process new items, briefing
 - Every month on the 1st: financial summary
 - Anytime: alert you about urgent items (large charges, overdue payments)

 You can change these anytime by telling me."

Record all automation settings in notes/profile.md.
