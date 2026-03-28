# Git Backup Setup

After the main onboarding is complete, help the user set up automatic backup.

**IMPORTANT: Record ALL decisions in this phase — whether the user enables or declines backup, and their reasons. Follow the same principle as the rest of onboarding: every piece of information goes into Notes.**

## Step 1: Check Git Availability

Run `quidclaw backup status --json` via Bash.

If git is not available:
- Inform user: "Git is not installed. Installing Git enables automatic backup of your financial data."
- Provide platform-specific install instructions
- If user declines:
  - Record in `notes/profile.md` under `## Data & Backup`: "Git backup: not available (git not installed)"
  - Append to `notes/decisions/{year}.md`: "{date}: User declined to install Git for backup. Reason: {reason if given}. Can revisit later with `quidclaw backup init`."
  - Skip the rest of this phase

## Step 2: Initialize Git Backup

If git is available but backup not initialized:
- Ask: "Would you like to enable automatic backup for your data? Every change will be versioned locally."
- If yes: Run `quidclaw backup init` via Bash
- If no:
  - Record in `notes/profile.md` under `## Data & Backup`: "Git backup: declined (git available but not enabled)"
  - Append to `notes/decisions/{year}.md`: "{date}: User declined Git backup. Reason: {reason if given}. Can enable later with `quidclaw backup init`."
  - Skip the rest of this phase

## Step 3: Remote Backup (Optional)

Ask if user wants remote backup:
- "You can back up to a private repository on any Git hosting service:"
  - **GitHub** (github.com) — most popular, free private repos
  - **Gitee** (gitee.com) — popular in China, free private repos
  - **GitLab** (gitlab.com) — free private repos
  - **Self-hosted** — Gitea, etc.
- "This keeps your data safe even if your computer is lost or damaged."
- "You can set up multiple remotes for redundant backup."

If user wants remote backup:
1. Ask for the remote name (e.g., "github", "gitee") and repository URL
2. Run `quidclaw backup add-remote NAME URL` via Bash
3. **IMPORTANT:** Remind user:
   - "Make sure the repository is set to **Private** — this is your financial data!"
   - Provide platform-specific instructions for creating a private repo and setting up authentication (SSH key or HTTPS token)
4. Ask: "Would you like to add another remote for redundant backup?" (repeat if yes)
5. Once all remotes are set, try `quidclaw backup push` to verify connectivity

If user declines remote backup:
- Record in `notes/profile.md` under `## Data & Backup`: "Git backup: local only (no remote)"
- Append to `notes/decisions/{year}.md`: "{date}: User enabled local Git backup but declined remote backup. Reason: {reason if given}."

After setup is complete (whether local-only or with remotes):
- Update `notes/profile.md` under `## Data & Backup` with the final state:
  ```
  ## Data & Backup
  - Git backup: enabled
  - Remotes: github (github.com/user/repo), gitee (gitee.com/user/repo)
  - LFS: installed / not installed
  ```

## Step 4: LFS (if applicable)

If git-lfs is not installed but backup is enabled:
- Suggest: "Installing git-lfs would improve storage efficiency for PDF and image files."
- Provide install command: `brew install git-lfs` (macOS) or `apt install git-lfs` (Linux)
- This is optional — backup works without LFS, just less efficiently for binary files.
- Record the user's choice in `notes/profile.md` under `## Data & Backup`.
