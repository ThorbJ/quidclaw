# First Run Setup

This is your first time running. Follow these steps:

1. Check `.quidclaw/config.yaml` for `bootstrapped: true`. If set, skip
   and delete this file.
2. Read `.quidclaw/workflows/onboarding.md` and start the onboarding
   conversation with the user
3. After onboarding completes, set up automation:
   - Configure a cron job for daily routine (ask user preferred time)
   - Configure a cron job for monthly report (1st of each month)
4. Set `bootstrapped: true` in `.quidclaw/config.yaml`
5. Delete this file
