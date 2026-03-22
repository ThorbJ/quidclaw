# OpenClaw Integration Design

## Overview

Make OpenClaw the primary and recommended way to use QuidClaw. Redesign `quidclaw init` to support multiple platforms, generate platform-specific files, and auto-install dependencies. Add OpenClaw-specific templates (SOUL.md, HEARTBEAT.md, BOOTSTRAP.md, IDENTITY.md) for a dedicated financial agent. Add async task handling for headless/messaging environments. Simplify README.

## 1. Multi-Platform `quidclaw init`

### 1.1 Platform Selection

`quidclaw init` becomes platform-aware. Two modes:

**Interactive (no args):**
```
$ quidclaw init

Which platform are you using?
  1. OpenClaw (recommended)
  2. Claude Code
  3. Gemini CLI
  4. Codex
  5. Other

> _
```

**Non-interactive (AI-callable):**
```bash
quidclaw init --platform openclaw
quidclaw init --platform claude-code
quidclaw init --platform gemini
quidclaw init --platform codex
```

### 1.2 Per-Platform File Generation

Each platform generates only the files it needs. No platform generates files for other platforms.

| File | OpenClaw | Claude Code | Gemini | Codex / Other |
|------|----------|-------------|--------|---------------|
| SOUL.md | Yes | — | — | — |
| AGENTS.md | Yes (OpenClaw version) | — | — | Yes |
| HEARTBEAT.md | Yes | — | — | — |
| BOOTSTRAP.md | Yes | — | — | — |
| IDENTITY.md | Yes | — | — | — |
| CLAUDE.md | — | Yes | — | — |
| GEMINI.md | — | — | Yes | — |
| .quidclaw/workflows/ | Yes | Yes | Yes | Yes |
| notes/pending/ | Yes (created by init) | Yes (created by init) | Yes (created by init) | Yes (created by init) |
| Git backup | Auto-enabled (init runs `backup init` without asking) | Onboarding decides | Onboarding decides | Onboarding decides |

### 1.3 Dependency Detection and Install Assistance

When a required dependency is missing, detect it, attempt to install it, and fall back to showing the user the exact install command if auto-install fails.

**Dependencies:**
- `git` — required for backup (all platforms when backup enabled, always for OpenClaw)
- `git-lfs` — optional, improves binary file storage
- `openclaw` — required for `--platform openclaw`

**Strategy:**
1. Check if binary is on PATH
2. If missing, attempt install:
   - macOS: try `brew install <pkg>`
   - Linux: try `apt-get install -y <pkg>` (may need sudo), fallback to `yum install -y <pkg>`
3. If auto-install fails (no brew, no sudo, etc.): print the exact command for the user/AI to run manually, and continue with init (don't block)
4. For optional dependencies (git-lfs): note as recommendation, never block

**Implementation:** Add a `check_and_install(name, brew_pkg, apt_pkg)` helper in a new `core/deps.py` module. This module handles detection and install attempts. The CLI calls it; the logic lives in core.

### 1.4 OpenClaw Agent Creation

When platform is `openclaw`, after creating the data directory and files, a core module (`core/openclaw.py`) handles agent setup:

1. Run `openclaw agents add quidclaw --workspace <data_dir>`
2. Set identity: `openclaw agents set-identity --agent quidclaw --name "QuidClaw" --emoji "💰"`
3. Print instructions for channel binding:
   ```
   Agent created. Connect it to your messaging app:
     openclaw agents bind --agent quidclaw --bind telegram:<account_id>

   Run 'openclaw agents bindings' to see available channels.
   ```

**Architecture note:** The OpenClaw agent creation logic lives in `core/openclaw.py`, not in the CLI layer. The CLI calls `OpenClawSetup(config).create_agent()`. This keeps the CLI thin per the project's architecture constraints.

### 1.5 Backward Compatibility and Migration

The existing `quidclaw init` (no args, no `--platform`) shows the interactive prompt. This replaces the old behavior of generating all platform files at once.

`quidclaw upgrade` continues to work — it updates workflows and regenerates instruction files for the platform that was originally selected. The platform choice is stored in `.quidclaw/config.yaml` as `platform: openclaw|claude-code|gemini|codex`.

**Migration for existing users:** When `upgrade` finds no `platform` in config, it defaults to `claude-code` (since that was the only fully-supported platform before this change) and stores the choice. Users can switch platforms via `quidclaw init --platform <new>` which regenerates files and cleans up old platform files.

**"Other" platform:** Interactive option 5 ("Other") maps to `--platform codex` internally. Both generate AGENTS.md + workflows. The stored config value is `codex`.

## 2. OpenClaw Template Files

### 2.1 SOUL.md

```markdown
You are a personal CFO — a dedicated financial assistant managing
the user's complete financial life.

## Personality
- Warm, professional, patient
- Speak the user's language (auto-detect from first message)
- Never use accounting jargon — say "你花了多少" not "借方金额"
- Proactive — surface important things without being asked
- Concise in daily briefings, detailed when the user asks

## Boundaries
- You ONLY handle financial matters
- You inform and recommend, never decide for the user
- All data stays local on this machine
- Never share financial data outside this conversation

## When You Don't Know
- If you lack information to complete a task, ask the user
- Record their answer in notes so you never ask again
- If the user doesn't respond immediately, save a pending item
  and follow up next heartbeat
```

### 2.2 HEARTBEAT.md

```markdown
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
```

### 2.3 BOOTSTRAP.md

```markdown
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
```

### 2.4 IDENTITY.md

```markdown
name: QuidClaw
emoji: 💰
```

### 2.5 AGENTS.md (OpenClaw Version)

Same content as the shared instruction body (`_build_instruction_body()`), but with additional OpenClaw-specific sections at the end:

```markdown
## Automation

You have cron jobs and heartbeat configured. Follow these rules:

### Heartbeat
- Read HEARTBEAT.md and follow it strictly
- If nothing needs attention, reply HEARTBEAT_OK
- For urgent items (large unusual charges, overdue payments), alert immediately

### Daily Routine (Cron)
- Follow `.quidclaw/workflows/daily-routine.md`
- Output format: concise, emoji-marked, under 500 characters
- If nothing to report: "一切正常 ✅"

### Monthly Review (Cron)
- Follow `.quidclaw/workflows/monthly-review.md`
- Deliver as a structured summary to the user

### Pending Items
- When a task is blocked (missing info, encrypted PDF, etc.):
  1. Save to `notes/pending/` as YAML
  2. Notify the user what you need
  3. Continue with other tasks
  4. Heartbeat will check pending items and resume when possible
```

## 3. Async Pending Mechanism

### 3.1 Pending Item Format

When a workflow encounters a blocker, write a YAML file to `notes/pending/`:

```yaml
# notes/pending/2026-03-22_cmb_statement_password.yaml
created: "2026-03-22T10:30:00"
type: blocked
reason: "PDF password unknown"
context:
  source: "sources/my-email/20260322_招商银行/"
  file: "attachments/招商银行-信用卡账单-2026-03.pdf"
  hint: "Email says password is last 2 chars of name + birth MMDD"
  missing: "user birthday"
action: "Decrypt PDF and import transactions after obtaining birthday"
```

### 3.2 Lifecycle

1. **Creation:** Any workflow that hits a blocker writes a pending item
2. **Notification:** The workflow tells the user what's needed (via chat message)
3. **Resolution:** On next heartbeat (or when user provides info), agent checks `notes/pending/`, resolves items where possible
4. **Cleanup:** Delete the pending YAML after successful resolution
5. **Logging:** Record resolution in `notes/journal/` for audit trail

### 3.3 Workflow Updates

Add pending-item awareness to these workflows:
- `check-email.md` — encrypted PDFs, unrecognized formats
- `import-bills.md` — ambiguous transactions, missing account info
- `organize-documents.md` — unidentifiable documents

Add a standard section to each:

```markdown
## When Blocked

If you cannot complete processing (missing password, unreadable file,
ambiguous data):
1. Save a pending item to `notes/pending/{date}_{description}.yaml`
2. Notify the user what you need
3. Move on to the next item — do not stop the entire workflow
4. The pending item will be picked up on the next heartbeat
```

## 4. Onboarding Automation Setup

### 4.1 New Phase in Onboarding Workflow

After Git Backup Setup, add a new phase (OpenClaw only):

```markdown
## Phase: Automation Setup (OpenClaw only)

Check if running in OpenClaw by looking for HEARTBEAT.md in the workspace root.
If not present, skip this phase.

### Step 1: Daily Routine

Ask user: "I can automatically check your email, remind you about
upcoming payments, and give you a daily briefing. What time works best?"

Based on their answer, run:
  openclaw cron add --name "QuidClaw daily" \
    --cron "0 {hour} * * *" --tz "{user_timezone}" \
    --session isolated \
    --message "Follow .quidclaw/workflows/daily-routine.md"

Record in notes/profile.md under ## Automation:
  "Daily briefing: {time} {timezone}"

### Step 2: Monthly Report

Ask user: "I'll send you a monthly financial summary on the 1st of
each month. Same time as daily briefing, or different?"

Run:
  openclaw cron add --name "QuidClaw monthly" \
    --cron "0 {hour} 1 * *" --tz "{user_timezone}" \
    --session isolated \
    --message "Follow .quidclaw/workflows/monthly-review.md"

Record in notes/profile.md under ## Automation:
  "Monthly report: 1st of each month at {time}"

### Step 3: Confirm

"All set! Here's what I'll do automatically:
 - Every day at {time}: check email, process new items, briefing
 - Every month on the 1st: financial summary
 - Anytime: alert you about urgent items (large charges, overdue payments)

 You can change these anytime by telling me."
```

### 4.2 Detection Logic

How to detect OpenClaw environment:
- Check for `HEARTBEAT.md` in workspace root, OR
- Check if `openclaw` is in PATH and `platform` config is `openclaw`

## 5. Output Format for Messaging

### 5.1 Daily Routine Output

Add to `daily-routine.md`:

```markdown
## Output Format

Keep the daily briefing concise and scannable for messaging apps:
- Use emoji as visual markers (📬 📊 ⚠️ ✅)
- One line per item, no tables or code blocks
- Total length under 500 characters
- If nothing needs attention: "一切正常 ✅"

Example:
  📬 2 new emails processed (招商银行, 电费通知)
  💳 信用卡账单已导入: ¥8,523 (47 笔)
  ⏰ 房租 ¥5,000 后天到期
  ✅ 其余一切正常
```

### 5.2 Monthly Review Output

Add to `monthly-review.md`:

```markdown
## Output Format

Monthly summary should be structured but readable in chat:
- Lead with the headline numbers
- Category breakdown as a simple list
- Flag anomalies and notable changes
- Keep under 1000 characters for the summary
- Offer to send detailed report if user wants
```

## 6. README Simplification

### 6.1 Remove from README
- Complete CLI Reference table (50+ lines of command details)
- Complete Workflows table

### 6.2 Replace With
- One-line description + link to `docs/cli-reference.md`
- One-line description + link to docs

### 6.3 Add to README
- OpenClaw as the primary Quick Start method
- Restructured Quick Start section:
  1. OpenClaw (recommended)
  2. Claude Code
  3. Other AI Tools

### 6.4 Target
- From ~248 lines to ~150 lines
- Focus on: what is it, how to install, where to find docs

## 7. SKILL.md (ClawHub Distribution)

The existing SKILL.md (for ClawHub/shared-bot use) stays functional but adds a recommendation note:

```markdown
---
name: quidclaw
description: Personal CFO — AI-powered financial management via Beancount
metadata:
  openclaw:
    requires:
      bins: [quidclaw]
---

> **Recommended:** For the best experience, create a dedicated QuidClaw
> agent with `quidclaw init --platform openclaw`. This gives you isolated
> context, dedicated automation, and a cleaner financial management
> experience.

{shared instruction body}
```

## 8. File Changes Summary

### New Files
- `src/quidclaw/core/deps.py` — dependency detection and auto-install helpers
- `src/quidclaw/templates/soul.md` — SOUL.md template
- `src/quidclaw/templates/heartbeat.md` — HEARTBEAT.md template
- `src/quidclaw/templates/bootstrap.md` — BOOTSTRAP.md template
- `src/quidclaw/templates/identity.md` — IDENTITY.md template
- `tests/core/test_deps.py` — dependency helper tests

### Modified Files
- `src/quidclaw/cli.py` — rewrite `init` command (platform selection, per-platform generation), update `upgrade` command
- `src/quidclaw/config.py` — add `platform` setting
- `src/quidclaw/workflows/onboarding.md` — add Automation Setup phase
- `src/quidclaw/workflows/check-email.md` — add "When Blocked" section
- `src/quidclaw/workflows/import-bills.md` — add "When Blocked" section
- `src/quidclaw/workflows/organize-documents.md` — add "When Blocked" section
- `src/quidclaw/workflows/daily-routine.md` — add Output Format section
- `src/quidclaw/workflows/monthly-review.md` — add Output Format section
- `README.md` — simplify, add OpenClaw as primary
- `tests/test_cli.py` — update init tests for platform flag

### New Core Files
- `src/quidclaw/core/openclaw.py` — OpenClaw agent creation logic

### Unchanged
- `src/quidclaw/core/backup.py` — no changes
- All other core modules unchanged
- All 31 CLI commands unchanged (init and upgrade are modified but not new)
