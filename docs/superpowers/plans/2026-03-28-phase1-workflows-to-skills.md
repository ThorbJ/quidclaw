# Phase 1: Workflows → Agent Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert QuidClaw's 9 custom workflow files + platform-specific instruction body into 5 Agent Skills following the open agentskills.io standard.

**Architecture:** Skills are installed to platform-appropriate directories (`.claude/skills/`, `.gemini/skills/`, etc.) via `init` and `upgrade`. Each skill has a SKILL.md with YAML frontmatter + a `references/` directory for on-demand content loading. The `_build_instruction_body()` function and platform file generation (CLAUDE.md, GEMINI.md, AGENTS.md) are removed. Existing workflows are kept during transition but deprecated.

**Tech Stack:** Python 3.10+, Click CLI, pytest, YAML frontmatter

**Spec:** `docs/superpowers/specs/2026-03-28-plugin-system-and-crypto-design.md` (Phase 1 section)

---

## File Structure

### New files

```
src/quidclaw/skills/
  quidclaw/
    SKILL.md                                    # Master skill: role, routing, context
    references/
      cli-reference.md                          # CLI command list (from _build_instruction_body)
      conventions.md                            # Accounting conventions (from _build_instruction_body)
      notes-guide.md                            # Notes structure (from financial-memory.md)
  quidclaw-onboarding/
    SKILL.md                                    # Interview phases 1-10 (from onboarding.md)
    references/
      email-setup.md                            # AgentMail setup (from onboarding.md Phase 9.5)
      backup-setup.md                           # Git backup (from onboarding.md Phase 11)
      automation-setup.md                       # Cron jobs (from onboarding.md Phase 12)
  quidclaw-import/
    SKILL.md                                    # 7-step import flow (from import-bills.md)
    references/
      email-processing.md                       # Email sync + processing (from check-email.md)
      document-archival.md                      # File org (from organize-documents.md)
  quidclaw-daily/
    SKILL.md                                    # Daily orchestration (from daily-routine.md)
    references/
      import-steps.md                           # Condensed import checklist
      anomaly-steps.md                          # Condensed anomaly quick-scan
  quidclaw-review/
    SKILL.md                                    # Monthly review (from monthly-review.md)
    references/
      reconciliation.md                         # Pre-flight checks (from reconcile.md)
      anomaly-detection.md                      # Full anomaly rules (from detect-anomalies.md)

tests/test_cli.py                               # Modify: add skills tests to existing TestInit/TestUpgrade
```

### Modified files

```
src/quidclaw/cli.py                             # Modify: init, upgrade, remove _build_instruction_body
pyproject.toml                                   # Modify: build includes
```

### Deprecated (kept, not deleted)

```
src/quidclaw/workflows/*.md                     # 9 workflow files — kept for backwards compat
src/quidclaw/templates/skill.md                  # Old skill template — superseded
```

---

## Task 1: Create `quidclaw` Master Skill

**Files:**
- Create: `src/quidclaw/skills/quidclaw/SKILL.md`
- Create: `src/quidclaw/skills/quidclaw/references/cli-reference.md`
- Create: `src/quidclaw/skills/quidclaw/references/conventions.md`
- Create: `src/quidclaw/skills/quidclaw/references/notes-guide.md`
- Read: `src/quidclaw/cli.py:856-1004` (`_build_instruction_body`)
- Read: `src/quidclaw/workflows/financial-memory.md`

- [ ] **Step 1: Create SKILL.md**

Create `src/quidclaw/skills/quidclaw/SKILL.md`:

```yaml
---
name: quidclaw
description: >
  Personal CFO — AI-powered financial management via Beancount.
  Use when working in a QuidClaw project directory (has .quidclaw/ and ledger/).
  On first conversation, check .quidclaw/config.yaml: if operating_currency
  is missing, activate quidclaw-onboarding. If inbox/ has files, offer to
  process them.
---
```

Body content: extract from `_build_instruction_body()` (cli.py:864-891):
- Role definition ("You are a personal CFO...")
- First Thing to Do section (config check → onboarding → inbox → greet)
- Configuration section (operating_currency, config file path)
- Directory structure overview

Add reference pointers:
- "Read `references/cli-reference.md` when you need to run a QuidClaw CLI command."
- "Read `references/conventions.md` when recording transactions or naming accounts."
- "Read `references/notes-guide.md` when capturing financial context outside the ledger."

Keep the body under 500 tokens. All detail goes into references.

- [ ] **Step 2: Create references/cli-reference.md**

Extract from `_build_instruction_body()` (cli.py:892-960):
- `## Available CLI Commands` section (all commands with examples)
- `### Price Tracking` section (commodity examples)
- `### Source Traceability` section (meta examples)
- `## File Operations` section

This is a reference-only file, no frontmatter needed.

- [ ] **Step 3: Create references/conventions.md**

Extract from `_build_instruction_body()` (cli.py:992-1004):
- `## Conventions` section (verified data only, monthly files, document naming, account naming)
- `## Notes Structure` section (living documents vs append-only logs)

- [ ] **Step 4: Create references/notes-guide.md**

Convert `src/quidclaw/workflows/financial-memory.md` content into reference format.
Keep all content — directory structure guide, living vs append-only docs, formatting standards, capture guidelines. Remove any preamble that was specific to the workflow format.

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/skills/quidclaw/
git commit -m "feat(skills): add quidclaw master skill with references"
```

---

## Task 2: Create `quidclaw-onboarding` Skill

**Files:**
- Create: `src/quidclaw/skills/quidclaw-onboarding/SKILL.md`
- Create: `src/quidclaw/skills/quidclaw-onboarding/references/email-setup.md`
- Create: `src/quidclaw/skills/quidclaw-onboarding/references/backup-setup.md`
- Create: `src/quidclaw/skills/quidclaw-onboarding/references/automation-setup.md`
- Read: `src/quidclaw/workflows/onboarding.md`

- [ ] **Step 1: Create SKILL.md**

```yaml
---
name: quidclaw-onboarding
description: >
  New user onboarding interview for QuidClaw. Guides through a multi-phase
  conversation to understand the user's financial life, then initializes
  accounts and notes. Use when operating_currency is not set in config, or
  user asks to set up or start fresh.
---
```

Body: extract phases 1-10 from `onboarding.md` (the core interview flow: language selection through profile save). This is ~3000 tokens — the longest skill body, justified because the interview is a single continuous flow.

Add reference pointers:
- "After completing the interview, read `references/email-setup.md` if the user wants email integration."
- "Read `references/backup-setup.md` to set up Git backup."
- "Read `references/automation-setup.md` to configure scheduled tasks."

- [ ] **Step 2: Create references/email-setup.md**

Extract Phase 9.5 (email setup) from `onboarding.md`. Content: AgentMail `add-source` command, inbox provisioning, test sync.

- [ ] **Step 3: Create references/backup-setup.md**

Extract Phase 11 (backup setup) from `onboarding.md`. Content: `backup init`, `backup add-remote`, `backup push`.

- [ ] **Step 4: Create references/automation-setup.md**

Extract Phase 12 (automation setup) from `onboarding.md`. **Important:** update the cron message paths from `Follow .quidclaw/workflows/daily-routine.md` to `/quidclaw-daily` (skill invocation). Same for monthly-review → `/quidclaw-review`.

- [ ] **Step 5: Commit**

```bash
git add src/quidclaw/skills/quidclaw-onboarding/
git commit -m "feat(skills): add quidclaw-onboarding skill with references"
```

---

## Task 3: Create `quidclaw-import` Skill

**Files:**
- Create: `src/quidclaw/skills/quidclaw-import/SKILL.md`
- Create: `src/quidclaw/skills/quidclaw-import/references/email-processing.md`
- Create: `src/quidclaw/skills/quidclaw-import/references/document-archival.md`
- Read: `src/quidclaw/workflows/import-bills.md`
- Read: `src/quidclaw/workflows/check-email.md`
- Read: `src/quidclaw/workflows/organize-documents.md`

- [ ] **Step 1: Create SKILL.md**

```yaml
---
name: quidclaw-import
description: >
  Import and process financial data into the ledger. Handles files in inbox/,
  email attachments, and synced source data. Parses, deduplicates, confirms
  with user, records transactions, and archives originals. Use when user says
  "import", "process inbox", "check email", or when inbox/ has unprocessed files.
---
```

Body: the core 7-step import flow from `import-bills.md` (identify → parse → dedup → confirm → record → archive → log). ~2000 tokens.

Add reference pointers:
- "If processing email sources, read `references/email-processing.md` for email-specific steps."
- "After recording transactions, read `references/document-archival.md` to organize source files."

- [ ] **Step 2: Create references/email-processing.md**

Convert `check-email.md` content. Steps: sync from email sources, process each email (context → attachments → recording → logging → archiving), mark processed.

- [ ] **Step 3: Create references/document-archival.md**

Convert `organize-documents.md` content. Steps: scan inbox, classify files, confirm, move to `documents/YYYY/MM/` with naming convention, extract supplementary info.

- [ ] **Step 4: Commit**

```bash
git add src/quidclaw/skills/quidclaw-import/
git commit -m "feat(skills): add quidclaw-import skill with references"
```

---

## Task 4: Create `quidclaw-daily` Skill

**Files:**
- Create: `src/quidclaw/skills/quidclaw-daily/SKILL.md`
- Create: `src/quidclaw/skills/quidclaw-daily/references/import-steps.md`
- Create: `src/quidclaw/skills/quidclaw-daily/references/anomaly-steps.md`
- Read: `src/quidclaw/workflows/daily-routine.md`

- [ ] **Step 1: Create SKILL.md**

```yaml
---
name: quidclaw-daily
description: >
  Daily financial routine. Syncs all sources, processes new data, checks for
  anomalies, and provides a concise briefing. Use when user says "daily check",
  "what's new today", or as a scheduled daily task.
---
```

Body: orchestration flow from `daily-routine.md` (~500 tokens). Steps: sync all sources, check inbox, process new data, detect anomalies, calendar checks, briefing.

Reference pointers:
- "If there is new data to process, read `references/import-steps.md`."
- "To check for anomalies, read `references/anomaly-steps.md`."

- [ ] **Step 2: Create references/import-steps.md**

Condensed import checklist: sync → parse → dedup → confirm → record → archive. This is a quick-reference summary, not the full import skill. ~300 tokens.

- [ ] **Step 3: Create references/anomaly-steps.md**

Condensed anomaly checks from `detect-anomalies.md`: duplicates, spending spikes, large transactions. Quick-scan version for daily routine. ~300 tokens.

- [ ] **Step 4: Commit**

```bash
git add src/quidclaw/skills/quidclaw-daily/
git commit -m "feat(skills): add quidclaw-daily skill with references"
```

---

## Task 5: Create `quidclaw-review` Skill

**Files:**
- Create: `src/quidclaw/skills/quidclaw-review/SKILL.md`
- Create: `src/quidclaw/skills/quidclaw-review/references/reconciliation.md`
- Create: `src/quidclaw/skills/quidclaw-review/references/anomaly-detection.md`
- Read: `src/quidclaw/workflows/monthly-review.md`
- Read: `src/quidclaw/workflows/reconcile.md`
- Read: `src/quidclaw/workflows/detect-anomalies.md`

- [ ] **Step 1: Create SKILL.md**

```yaml
---
name: quidclaw-review
description: >
  Financial review, reporting, and analysis. Generates monthly summaries,
  detects anomalies, and reconciles balances. Always reconcile before
  reporting. Use when user asks for "monthly report", "review", "anomalies",
  "reconcile", or "financial summary".
---
```

Body: monthly review flow from `monthly-review.md` (~800 tokens). Steps: pre-check reconcile, income report, spending breakdown, month-over-month comparison, notable transactions, insights, save report.

Reference pointers:
- "Before generating any report, read `references/reconciliation.md` and run the pre-flight checks."
- "To scan for anomalies, read `references/anomaly-detection.md`."

- [ ] **Step 2: Create references/reconciliation.md**

Convert `reconcile.md` content. Steps: data-status check, gap detection (min/max date query), balance sanity check, confirm/collect missing data.

- [ ] **Step 3: Create references/anomaly-detection.md**

Convert `detect-anomalies.md` content. Full anomaly rules: duplicates, subscriptions, price changes, large transactions, unknown merchants, spending spikes. Group by severity.

- [ ] **Step 4: Commit**

```bash
git add src/quidclaw/skills/quidclaw-review/
git commit -m "feat(skills): add quidclaw-review skill with references"
```

---

## Task 6: Update `pyproject.toml` Build Config

**Files:**
- Modify: `pyproject.toml:52-53`

- [ ] **Step 1: Update build includes**

In `pyproject.toml`, update `[tool.hatch.build]` to include skills:

```toml
[tool.hatch.build]
include = [
    "src/quidclaw/**/*.py",
    "src/quidclaw/skills/**/SKILL.md",
    "src/quidclaw/skills/**/references/*.md",
    "src/quidclaw/templates/*.md",
    "src/quidclaw/workflows/*.md",
]
```

- [ ] **Step 2: Verify build**

Run: `pip install -e ".[dev]"`
Expected: installs successfully, skills directory included.

- [ ] **Step 3: Verify skills bundled**

```bash
python -c "from pathlib import Path; import quidclaw; p=Path(quidclaw.__file__).parent/'skills'; print(list(p.glob('*/SKILL.md')))"
```

Expected: lists all 5 SKILL.md files.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "build: include skills directory in package"
```

---

## Task 7: Write Failing Tests for Skill Installation

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add skill installation tests to TestInit**

Add to `tests/test_cli.py` inside `class TestInit`:

```python
def test_init_installs_skills_claude_code(self, tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main, ["init", "--platform", "claude-code"],
        catch_exceptions=False, env=_env(tmp_path),
    )
    assert result.exit_code == 0
    skills_dir = tmp_path / ".claude" / "skills"
    assert (skills_dir / "quidclaw" / "SKILL.md").exists()
    assert (skills_dir / "quidclaw-onboarding" / "SKILL.md").exists()
    assert (skills_dir / "quidclaw-import" / "SKILL.md").exists()
    assert (skills_dir / "quidclaw-daily" / "SKILL.md").exists()
    assert (skills_dir / "quidclaw-review" / "SKILL.md").exists()

def test_init_installs_skills_gemini(self, tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main, ["init", "--platform", "gemini"],
        catch_exceptions=False, env=_env(tmp_path),
    )
    assert result.exit_code == 0
    assert (tmp_path / ".gemini" / "skills" / "quidclaw" / "SKILL.md").exists()

def test_init_installs_skills_codex(self, tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main, ["init", "--platform", "codex"],
        catch_exceptions=False, env=_env(tmp_path),
    )
    assert result.exit_code == 0
    assert (tmp_path / ".agents" / "skills" / "quidclaw" / "SKILL.md").exists()

def test_init_skills_have_valid_frontmatter(self, tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main, ["init", "--platform", "claude-code"],
        catch_exceptions=False, env=_env(tmp_path),
    )
    assert result.exit_code == 0
    import yaml
    skill_md = (tmp_path / ".claude" / "skills" / "quidclaw" / "SKILL.md").read_text()
    # Extract YAML between --- delimiters
    parts = skill_md.split("---", 2)
    assert len(parts) >= 3, "SKILL.md must have YAML frontmatter"
    meta = yaml.safe_load(parts[1])
    assert meta["name"] == "quidclaw"
    assert "description" in meta

def test_init_skills_references_installed(self, tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main, ["init", "--platform", "claude-code"],
        catch_exceptions=False, env=_env(tmp_path),
    )
    assert result.exit_code == 0
    refs = tmp_path / ".claude" / "skills" / "quidclaw" / "references"
    assert (refs / "cli-reference.md").exists()
    assert (refs / "conventions.md").exists()
    assert (refs / "notes-guide.md").exists()
```

- [ ] **Step 2: Add skill update tests to TestUpgrade**

Add to `tests/test_cli.py` inside `class TestUpgrade`:

```python
def test_upgrade_updates_skills(self, tmp_path):
    runner = _init_project(tmp_path)
    skill_file = tmp_path / ".claude" / "skills" / "quidclaw" / "SKILL.md"
    assert skill_file.exists()
    skill_file.write_text("old content")
    result = runner.invoke(
        main, ["upgrade"], catch_exceptions=False,
        env=_env(tmp_path),
    )
    assert result.exit_code == 0
    assert skill_file.read_text() != "old content"

def test_upgrade_installs_new_skills(self, tmp_path):
    """If a skill was added in an upgrade, it appears."""
    runner = _init_project(tmp_path)
    # Delete one skill to simulate pre-upgrade state
    import shutil
    daily_dir = tmp_path / ".claude" / "skills" / "quidclaw-daily"
    if daily_dir.exists():
        shutil.rmtree(daily_dir)
    result = runner.invoke(
        main, ["upgrade"], catch_exceptions=False,
        env=_env(tmp_path),
    )
    assert result.exit_code == 0
    assert (daily_dir / "SKILL.md").exists()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::TestInit::test_init_installs_skills_claude_code tests/test_cli.py::TestUpgrade::test_upgrade_updates_skills -v`
Expected: FAIL — skills not installed yet by `init`/`upgrade`.

- [ ] **Step 4: Commit**

```bash
git add tests/test_cli.py
git commit -m "test: add failing tests for skill installation"
```

---

## Task 8: Implement Skill Installation in `init` and `upgrade`

**Files:**
- Modify: `src/quidclaw/cli.py:54-180` (init and upgrade commands)

- [ ] **Step 1: Add platform-to-skills-dir mapping**

Add near the top of `cli.py`, after the `PLATFORMS` list (line 51):

```python
PLATFORM_SKILLS_DIR = {
    "openclaw": ".claude/skills",
    "claude-code": ".claude/skills",
    "gemini": ".gemini/skills",
    "codex": ".agents/skills",
}
```

- [ ] **Step 2: Add `_install_skills` helper**

Add after `_try_backup` function (~line 39):

```python
def _install_skills(config: QuidClawConfig, platform: str) -> None:
    """Copy bundled skills to the platform-appropriate skills directory."""
    skills_source = Path(__file__).parent / "skills"
    if not skills_source.exists():
        return
    skills_dir_name = PLATFORM_SKILLS_DIR.get(platform, ".agents/skills")
    skills_target = Path(config.data_dir) / skills_dir_name
    for skill_dir in skills_source.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            target = skills_target / skill_dir.name
            shutil.copytree(skill_dir, target, dirs_exist_ok=True)
```

- [ ] **Step 3: Update `init` to install skills**

In the `init` function (cli.py:57), after `config.set_setting("platform", platform)` (line 83), add:

```python
    # Install skills
    _install_skills(config, platform)
```

Keep the existing workflow copy and platform file generation for backwards compatibility during transition. Add a comment: `# Legacy: kept for transition, will be removed`.

- [ ] **Step 4: Update `upgrade` to update skills**

In the `upgrade` function (cli.py:130), after the workflow copy block (line 140), add:

```python
    # Update skills
    platform = config.get_setting("platform", "claude-code")
    _install_skills(config, platform)
    click.echo("Updated skills")
```

Move the `platform = config.get_setting(...)` line that currently appears at line 146 up to be shared.

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_cli.py::TestInit tests/test_cli.py::TestUpgrade -v`
Expected: ALL PASS (including new skill tests and existing tests).

- [ ] **Step 6: Run full test suite**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: ALL PASS — no regressions.

- [ ] **Step 7: Commit**

```bash
git add src/quidclaw/cli.py
git commit -m "feat(skills): install skills via init and upgrade commands"
```

---

## Task 9: Remove Legacy Instruction Body

**Files:**
- Modify: `src/quidclaw/cli.py:856-1004` (remove `_build_instruction_body`)
- Modify: `src/quidclaw/cli.py:54-180` (simplify init and upgrade)
- Modify: `src/quidclaw/core/openclaw.py:11-30` (update `_AGENTS_AUTOMATION_SECTION`)
- Modify: `tests/test_cli.py` (update assertions)

- [ ] **Step 1: Update existing init tests**

Delete the following tests that are now redundant (covered by Task 7's skill tests):
- `test_init_with_platform_claude_code` — replaced by `test_init_installs_skills_claude_code`
- `test_init_with_platform_gemini` — replaced by `test_init_installs_skills_gemini`
- `test_init_with_platform_codex` — replaced by `test_init_installs_skills_codex`

Update `test_init_with_platform_openclaw_generates_templates` — OpenClaw still generates its template files (SOUL.md, HEARTBEAT.md, etc.) but AGENTS.md now contains only the automation section, not the full instruction body:

```python
def test_init_with_platform_openclaw_generates_templates(self, tmp_path):
    runner = CliRunner()
    from unittest.mock import patch
    with patch("quidclaw.core.openclaw.OpenClawSetup.is_available", return_value=False):
        result = runner.invoke(
            main, ["init", "--platform", "openclaw"],
            catch_exceptions=False, env=_env(tmp_path),
        )
    assert result.exit_code == 0
    assert (tmp_path / "SOUL.md").exists()
    assert (tmp_path / "HEARTBEAT.md").exists()
    assert (tmp_path / "BOOTSTRAP.md").exists()
    assert (tmp_path / "IDENTITY.md").exists()
    assert (tmp_path / "AGENTS.md").exists()
    assert "Automation" in (tmp_path / "AGENTS.md").read_text()
    # Skills also installed for openclaw
    assert (tmp_path / ".claude" / "skills" / "quidclaw" / "SKILL.md").exists()
```

Update `test_upgrade_updates_instruction_files` to test skills instead:

```python
def test_upgrade_updates_instruction_files(self, tmp_path):
    """upgrade refreshes skills for the stored platform."""
    runner = _init_project(tmp_path)
    skill = tmp_path / ".claude" / "skills" / "quidclaw" / "SKILL.md"
    skill.write_text("old")
    result = runner.invoke(
        main, ["upgrade"], catch_exceptions=False,
        env=_env(tmp_path),
    )
    assert result.exit_code == 0
    assert skill.read_text() != "old"
    assert "quidclaw" in skill.read_text()
```

**Note:** `test_init_creates_workflows` (line 111) should still pass — workflows are kept during transition. Do NOT delete the workflow copy block.

- [ ] **Step 2: Update OpenClaw's `_AGENTS_AUTOMATION_SECTION`**

In `src/quidclaw/core/openclaw.py`, update the hardcoded workflow paths in `_AGENTS_AUTOMATION_SECTION`:
- Change `Follow \`.quidclaw/workflows/daily-routine.md\`` → `Run /quidclaw-daily`
- Change `Follow \`.quidclaw/workflows/monthly-review.md\`` → `Run /quidclaw-review`

Update `generate_agents_md` to no longer require `instruction_body`:

```python
def generate_agents_md(self) -> None:
    """Generate AGENTS.md with OpenClaw automation section."""
    (self.data_dir / "AGENTS.md").write_text(_AGENTS_AUTOMATION_SECTION)
```

- [ ] **Step 3: Remove platform file generation from `init`**

Remove from `init`:
- The `body = _build_instruction_body(config)` call (line 86)
- The `data_dir = Path(config.data_dir)` line (line 87) — keep if still needed for openclaw
- The `elif platform == "claude-code"` block (lines 113-115)
- The `elif platform == "gemini"` block (lines 117-119)
- The `elif platform == "codex"` block (lines 121-123)

For the openclaw block: update `setup.generate_agents_md(body)` → `setup.generate_agents_md()` (no arg, per Step 2).

**Do NOT remove** the workflow copy block (lines 74-80) — kept for transition.

- [ ] **Step 4: Remove platform file generation from `upgrade`**

Remove from `upgrade`:
- The `body = _build_instruction_body(config)` call
- The `elif platform == "claude-code"` / `"gemini"` / `"codex"` write blocks
- The legacy SKILL.md update block (lines 166-177)

For openclaw: update `setup.generate_agents_md(body)` → `setup.generate_agents_md()`.

- [ ] **Step 5: Remove `_build_instruction_body` function**

Delete `_build_instruction_body()` (cli.py:856-1004). ~150 lines removed.

Verify no other code references this function:
```bash
grep -r "_build_instruction_body" src/
```
Expected: no matches.

- [ ] **Step 6: Run tests**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: ALL PASS.

- [ ] **Step 7: Commit**

```bash
git add src/quidclaw/cli.py src/quidclaw/core/openclaw.py tests/test_cli.py
git commit -m "refactor: remove legacy instruction body, skills are the source of truth"
```

---

## Task 10: Final Cleanup and Verification

**Files:**
- Read: `src/quidclaw/templates/skill.md` (to confirm it's superseded)

- [ ] **Step 1: Remove old skill template**

Delete `src/quidclaw/templates/skill.md` — it's superseded by the real skills in `src/quidclaw/skills/`. Check that nothing in `cli.py` references it.

Run: `grep -r "templates/skill" src/quidclaw/`

If any references found, update them. If not, safe to delete.

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v --ignore=tests/e2e`
Expected: ALL PASS.

- [ ] **Step 3: Manual smoke test**

```bash
cd $(mktemp -d)
export QUIDCLAW_DATA_DIR=$(pwd)
quidclaw init --platform claude-code
ls .claude/skills/
ls .claude/skills/quidclaw/
ls .claude/skills/quidclaw/references/
cat .claude/skills/quidclaw/SKILL.md | head -20
```

Expected: all 5 skill directories present, each with SKILL.md and appropriate references.

- [ ] **Step 4: Verify frontmatter validity**

For each skill, check that `name` field matches directory name and `description` is present:

```bash
for d in .claude/skills/quidclaw*; do
    echo "=== $(basename $d) ==="
    head -10 "$d/SKILL.md"
    echo
done
```

- [ ] **Step 5: Commit cleanup**

```bash
git add -A
git commit -m "chore: remove superseded skill template, finalize phase 1"
```
