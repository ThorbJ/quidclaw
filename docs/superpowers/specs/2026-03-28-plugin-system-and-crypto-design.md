# QuidClaw Skills Architecture & Plugin System Design

## Overview

QuidClaw's AI capabilities are currently delivered as platform-specific instruction files (CLAUDE.md, GEMINI.md, AGENTS.md) plus passive workflow markdown files. This spec replaces that with the open Agent Skills standard (agentskills.io), adopted by 30+ agents (Claude Code, Gemini CLI, Codex CLI, Cursor, GitHub Copilot, etc.).

On top of this skills foundation, a plugin system lets QuidClaw support non-universal features (crypto, tax, enterprise) without bloating the core.

## Problem Statement

1. **Workflows are passive.** The AI must be told to read a workflow file. There is no auto-discovery, no activation triggers, no progressive loading.
2. **Platform fragmentation.** QuidClaw generates CLAUDE.md, GEMINI.md, and AGENTS.md with overlapping content. Maintenance burden grows with each new platform.
3. **Feature bloat risk.** As QuidClaw expands (crypto, tax, enterprise), bundling everything into core creates dependency bloat, feature interference, and onboarding friction.

## Design Goals

1. **Skills-first** — all AI capabilities delivered as Agent Skills, auto-discovered by any compatible agent
2. **Progressive disclosure** — only load what the agent needs, when it needs it
3. **Cross-platform** — one set of skills works across all 30+ compatible agents
4. **Extensible** — plugins add skills, providers, and CLI commands without touching core
5. **Core stays lean** — installing QuidClaw without plugins gives a clean accounting tool

## Phased Execution

| Phase | Scope | Prerequisite |
|-------|-------|-------------|
| **Phase 1** | Convert workflows to Agent Skills | None |
| **Phase 2** | Build plugin system + crypto plugin | Phase 1 |

---

# Phase 1: Workflow → Agent Skills

## Agent Skills Standard (Summary)

Each skill is a directory containing a `SKILL.md` with YAML frontmatter:

```
skill-name/
  SKILL.md           # Required: frontmatter + markdown body
  references/        # Optional: loaded on-demand when SKILL.md references them
  scripts/           # Optional: executable code
  assets/            # Optional: templates, resources
```

Loading is progressive:
1. **Startup (~100 tokens/skill):** Only `name` + `description` from frontmatter
2. **Activation (<5000 tokens):** Full SKILL.md body when the agent decides the skill is relevant
3. **References (as needed):** Files in `references/` loaded only when SKILL.md explicitly tells the agent to read them

The `name` field must match the directory name. Lowercase letters, numbers, hyphens only. 1-64 characters.

**Installation paths:** Each agent scans its own directory (`.claude/skills/`, `.gemini/skills/`, `.agents/skills/`, etc.). The cross-platform convention is `.agents/skills/` — tools like `npx skills add` install there and symlink to agent-specific directories. QuidClaw's `init` command installs to the platform-appropriate directory based on the `--platform` flag (e.g., `.claude/skills/` for `--platform claude-code`). `upgrade` uses the stored platform setting.

## Current State → Target State

| Current | Target |
|---------|--------|
| `_build_instruction_body()` generates CLAUDE.md / GEMINI.md / AGENTS.md | `quidclaw` master skill + references |
| `src/quidclaw/workflows/onboarding.md` (355 lines) | `quidclaw-onboarding` skill + 3 references |
| `src/quidclaw/workflows/import-bills.md` (139 lines) | `quidclaw-import` skill + 2 references |
| `src/quidclaw/workflows/check-email.md` (104 lines) | → reference under `quidclaw-import` |
| `src/quidclaw/workflows/organize-documents.md` (54 lines) | → reference under `quidclaw-import` |
| `src/quidclaw/workflows/daily-routine.md` (68 lines) | `quidclaw-daily` skill |
| `src/quidclaw/workflows/monthly-review.md` (61 lines) | `quidclaw-review` skill + 2 references |
| `src/quidclaw/workflows/detect-anomalies.md` (44 lines) | → reference under `quidclaw-review` |
| `src/quidclaw/workflows/reconcile.md` (43 lines) | → reference under `quidclaw-review` |
| `src/quidclaw/workflows/financial-memory.md` (162 lines) | → reference under `quidclaw` |

## Skill Classification Rationale

**What becomes an independent skill:** operations a user would directly trigger.
**What becomes a reference:** sub-details that only matter within a parent skill's context.

| Current workflow | Decision | Reason |
|-----------------|----------|--------|
| onboarding | **Skill** | User triggers: "I'm new" / "set me up" |
| import-bills | **Skill** | User triggers: "import bills" / "process inbox" |
| check-email | Reference of `quidclaw-import` | Email is one import source, not an independent action |
| organize-documents | Reference of `quidclaw-import` | Document archival is the final step of import |
| daily-routine | **Skill** | User triggers: "daily check" / scheduled via cron |
| monthly-review | **Skill** | User triggers: "monthly report" / scheduled |
| detect-anomalies | Reference of `quidclaw-review` | Anomaly detection is one analysis within review |
| reconcile | Reference of `quidclaw-review` | Reconciliation is a pre-check before review |
| financial-memory | Reference of `quidclaw` | Notes structure guide, not independently triggered |

## Core Skills (5 total)

### 1. `quidclaw` — Master Skill

The entry point. Loaded when the agent enters a QuidClaw project.

```
quidclaw/
  SKILL.md
  references/
    cli-reference.md
    conventions.md
    notes-guide.md
```

**SKILL.md frontmatter:**

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

**SKILL.md body (~300 tokens):** Role definition ("You are a personal CFO..."), directory structure overview, first-thing-to-do routing logic, pointers to references.

- "Read `references/cli-reference.md` when you need to run a QuidClaw CLI command."
- "Read `references/conventions.md` when recording transactions or creating accounts."
- "Read `references/notes-guide.md` when capturing financial context outside the ledger."

**references/cli-reference.md:** Full CLI command list with examples. Currently embedded in `_build_instruction_body()`, extracted verbatim.

**references/conventions.md:** Accounting conventions, file naming, account naming patterns. Currently the `## Conventions` section of the instruction body.

**references/notes-guide.md:** Content from `financial-memory.md` — notes directory structure, living documents vs append-only logs, formatting standards.

### 2. `quidclaw-onboarding` — New User Setup

```
quidclaw-onboarding/
  SKILL.md
  references/
    email-setup.md
    backup-setup.md
    automation-setup.md
```

**SKILL.md frontmatter:**

```yaml
---
name: quidclaw-onboarding
description: >
  New user onboarding interview for QuidClaw. Guides through a multi-phase
  conversation to understand the user's financial life, then initializes
  accounts and notes. Use when operating_currency is not set in config, or
  user asks to set up / start fresh.
---
```

**SKILL.md body (~3000 tokens):** Core interview phases 1-10 (language selection through profile save). This is the longest skill body but justified — the onboarding interview is a single continuous flow that cannot be split without losing coherence.

- "After completing the interview, read `references/email-setup.md` if the user wants email integration."
- "Read `references/backup-setup.md` to set up Git backup."
- "Read `references/automation-setup.md` to configure scheduled tasks."

**references/email-setup.md:** AgentMail integration setup (Phase 9.5 from onboarding.md).

**references/backup-setup.md:** Git backup initialization and remote configuration (Phase 11).

**references/automation-setup.md:** Cron job setup for daily/monthly tasks (Phase 12). **Content must be updated** — the current `onboarding.md` hardcodes `--message "Follow .quidclaw/workflows/daily-routine.md"`. This must change to reference skills (e.g., `--message "Run /quidclaw-daily"` or the equivalent skill invocation syntax for the user's platform).

### 3. `quidclaw-import` — Data Import & Processing

```
quidclaw-import/
  SKILL.md
  references/
    email-processing.md
    document-archival.md
```

**SKILL.md frontmatter:**

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

**SKILL.md body (~2000 tokens):** Core 7-step import flow from `import-bills.md` (identify → parse → dedup → confirm → record → archive → log).

- "If processing email sources, read `references/email-processing.md` for email-specific steps."
- "After recording transactions, read `references/document-archival.md` to organize source files."

**references/email-processing.md:** Content from `check-email.md` — sync from email sources, extract attachments, mark processed.

**references/document-archival.md:** Content from `organize-documents.md` — classify files, apply naming convention, move to `documents/YYYY/MM/`.

### 4. `quidclaw-daily` — Daily Financial Routine

```
quidclaw-daily/
  SKILL.md
  references/
    import-steps.md
    anomaly-steps.md
```

**SKILL.md frontmatter:**

```yaml
---
name: quidclaw-daily
description: >
  Daily financial routine. Syncs all sources, processes new data, checks for
  anomalies, and provides a concise briefing. Use when user says "daily check",
  "what's new today", or as a scheduled daily task.
---
```

**SKILL.md body (~500 tokens):** Orchestration flow from `daily-routine.md` — sync, check inbox, process, detect anomalies, brief.

- "If there is new data to process, read `references/import-steps.md`."
- "To check for anomalies, read `references/anomaly-steps.md`."

Self-contained within its own directory — does not depend on other skills being installed. The references are condensed summaries of the import and anomaly detection flows, not full copies.

**references/import-steps.md:** Condensed import checklist (sync → parse → dedup → confirm → record → archive). The full `quidclaw-import` skill has more detail; this reference covers just what's needed for the daily routine.

**references/anomaly-steps.md:** Condensed anomaly checks (duplicates, spending spikes, large transactions). The full `quidclaw-review` skill has more detail; this reference covers the daily quick-scan.

### 5. `quidclaw-review` — Financial Review & Reporting

```
quidclaw-review/
  SKILL.md
  references/
    reconciliation.md
    anomaly-detection.md
```

**SKILL.md frontmatter:**

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

**SKILL.md body (~800 tokens):** Monthly review flow from `monthly-review.md` (data-status → income → breakdown → comparison → insights → save).

- "Before generating any report, read `references/reconciliation.md` and run the pre-flight checks."
- "To scan for anomalies, read `references/anomaly-detection.md`."

**references/reconciliation.md:** Content from `reconcile.md` — completeness check, gap detection, balance sanity check.

**references/anomaly-detection.md:** Content from `detect-anomalies.md` — duplicate detection, subscription tracking, spending spikes, outlier identification.

## Token Budget Summary

| Skill | Frontmatter (always) | Body (on activate) | References (on demand) |
|-------|---------------------|--------------------|-----------------------|
| `quidclaw` | ~80 | ~300 | cli-reference ~800, conventions ~300, notes-guide ~1500 |
| `quidclaw-onboarding` | ~80 | ~3000 | email ~400, backup ~300, automation ~400 |
| `quidclaw-import` | ~80 | ~2000 | email-processing ~1000, document-archival ~500 |
| `quidclaw-daily` | ~80 | ~800 | (none) |
| `quidclaw-review` | ~80 | ~800 | reconciliation ~500, anomaly-detection ~500 |
| **Total always loaded** | **~400** | | |

400 tokens for all 5 skill frontmatters — negligible. Each activation loads only the relevant skill body + on-demand references. Compared to the current approach of loading the entire `_build_instruction_body()` (~2500 tokens) into CLAUDE.md on every session, this is more efficient for most interactions.

## Changes to `init` and `upgrade`

### `init` command

Currently generates platform-specific instruction files. New behavior:

1. Install core skills to `.agents/skills/` (cross-platform)
2. Optionally generate a minimal platform file for compatibility:
   - CLAUDE.md: "QuidClaw skills are installed. See `.agents/skills/quidclaw*/`."
   - Or omit entirely — skills are auto-discovered

```python
# init: install skills to platform-appropriate directory
PLATFORM_SKILLS_DIR = {
    "claude-code": ".claude/skills",
    "openclaw": ".claude/skills",      # OpenClaw uses Claude Code's path
    "gemini": ".gemini/skills",
    "codex": ".agents/skills",
}
skills_source = Path(__file__).parent / "skills"
skills_dir_name = PLATFORM_SKILLS_DIR.get(platform, ".agents/skills")
skills_target = config.data_dir / skills_dir_name
if skills_source.exists():
    for skill_dir in skills_source.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            target = skills_target / skill_dir.name
            shutil.copytree(skill_dir, target, dirs_exist_ok=True)
```

### `upgrade` command

Currently updates workflows and platform instruction files. New behavior:

1. Update core skills in `.agents/skills/`
2. Update plugin skills from installed plugins
3. Keep legacy workflow update for backwards compatibility during transition

### Package structure change

```
src/quidclaw/
  skills/                           # NEW: replaces workflows/
    quidclaw/
      SKILL.md
      references/
        cli-reference.md
        conventions.md
        notes-guide.md
    quidclaw-onboarding/
      SKILL.md
      references/
        email-setup.md
        backup-setup.md
        automation-setup.md
    quidclaw-import/
      SKILL.md
      references/
        email-processing.md
        document-archival.md
    quidclaw-daily/
      SKILL.md
    quidclaw-review/
      SKILL.md
      references/
        reconciliation.md
        anomaly-detection.md
  workflows/                        # DEPRECATED: kept during transition
    ...
```

`pyproject.toml` build config updated:

```toml
[tool.hatch.build]
include = [
    "src/quidclaw/**/*.py",
    "src/quidclaw/skills/**/SKILL.md",
    "src/quidclaw/skills/**/references/*.md",
    "src/quidclaw/templates/*.md",
    "src/quidclaw/workflows/*.md",      # Keep during transition
]
```

## Phase 1 Changes Summary

| File / Directory | Change |
|-----------------|--------|
| `src/quidclaw/skills/` | **New** — 5 skill directories with SKILL.md + references |
| `src/quidclaw/workflows/` | Deprecated, kept during transition |
| `cli.py` (`init`) | Install skills to `.agents/skills/` instead of generating platform files |
| `cli.py` (`upgrade`) | Update skills instead of workflows + platform files |
| `cli.py` (`_build_instruction_body`) | Removed — content distributed across skills |
| `pyproject.toml` | Update build includes for skills |
| `src/quidclaw/templates/skill.md` | Removed — replaced by proper skills |

## Phase 1 Testing

- All existing tests pass (no core logic changes)
- New tests: verify skill files are installed correctly by `init` and `upgrade`
- Manual verification: start a Claude Code / Gemini CLI session in a QuidClaw project, confirm skills are auto-discovered

## Phase 1 Migration for Existing Users

`quidclaw upgrade` handles migration:
1. Installs skills to `.agents/skills/`
2. Keeps existing workflow files and platform instruction files (no deletion)
3. Users can manually delete old CLAUDE.md / workflows after confirming skills work

---

# Phase 2: Plugin System

Builds on Phase 1's skills foundation. Plugins ship skills (not workflows) alongside providers and CLI commands.

## Plugin Interface

```python
# src/quidclaw/core/plugins.py

import importlib.metadata
import warnings
from abc import ABC, abstractmethod

PLUGIN_API_VERSION = 1
PLUGIN_GROUP = "quidclaw.plugins"

class QuidClawPlugin(ABC):
    """Base class for all QuidClaw plugins."""

    plugin_api_version: int = 1

    @staticmethod
    @abstractmethod
    def name() -> str:
        """Unique plugin identifier, e.g. 'crypto', 'us-tax'."""
        ...

    @staticmethod
    @abstractmethod
    def description() -> str:
        """One-line human-readable description."""
        ...

    def register_commands(self, cli) -> None:
        """Register Click commands/groups onto the main CLI group."""
        pass

    def get_skills_dir(self) -> Path | None:
        """Return the path to this plugin's skills directory.

        The directory should contain skill subdirectories, each with
        a SKILL.md and optional references/. Example layout:
            skills/
              quidclaw-crypto/
                SKILL.md
                references/
                  exchange-binance.md

        Called by `quidclaw upgrade` to copy plugin skills into the
        user's skills directory. Returns None if the plugin has no skills.
        """
        return None
```

Key change from previous spec: `get_workflows()` → `get_skills_dir()`. Returns a `Path` to the plugin's skills directory, which is copied to the user's skills directory during `upgrade`. Simpler than returning content strings — just point to the directory.

## Plugin Discovery & Loading

Unchanged from previous spec — Python entry points, `warnings.warn()` on failure, API version check.

```python
def discover_plugins() -> list[QuidClawPlugin]:
    plugins = []
    eps = importlib.metadata.entry_points()
    for ep in eps.select(group=PLUGIN_GROUP):
        try:
            plugin_cls = ep.load()
            api_ver = getattr(plugin_cls, 'plugin_api_version', 1)
            if api_ver > PLUGIN_API_VERSION:
                warnings.warn(
                    f"Plugin '{ep.name}' requires API v{api_ver}, "
                    f"core is v{PLUGIN_API_VERSION}. Skipping.",
                    stacklevel=2,
                )
                continue
            plugins.append(plugin_cls())
        except Exception as e:
            warnings.warn(
                f"Plugin '{ep.name}' failed to load: {e}. Skipping.",
                stacklevel=2,
            )
    return plugins

def load_plugins(cli) -> list[QuidClawPlugin]:
    plugins = discover_plugins()
    for plugin in plugins:
        plugin.register_commands(cli)
    return plugins
```

## CLI Integration

### Startup

```python
from quidclaw.core.plugins import load_plugins

# At module level, after all built-in commands:
load_plugins(main)
```

**Delete** the two `try: import quidclaw.core.sources.agentmail` blocks in `sync()` (lines 627-630) and `add_source()` (lines 548-550). **Add** a single module-level import: `try: import quidclaw.core.sources.agentmail except ImportError: pass`.

### Plugin Management

```
quidclaw plugins                   # list installed plugins
```

### Upgrade Integration

```python
# upgrade command: after installing core skills
for plugin in discover_plugins():
    plugin_skills = plugin.get_skills_dir()
    if plugin_skills and plugin_skills.exists():
        for skill_dir in plugin_skills.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                target = skills_target / skill_dir.name
                shutil.copytree(skill_dir, target, dirs_exist_ok=True)
```

### `add-source` Extension

Add `--option KEY=VALUE` repeatable parameter **alongside** existing flags for backwards compatibility. See Phase 1 spec for details.

## Crypto Plugin: `quidclaw-crypto`

### Package Structure

```
quidclaw-crypto/
├── pyproject.toml
├── src/quidclaw_crypto/
│   ├── __init__.py
│   ├── plugin.py                  # CryptoPlugin entry point
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── evm_explorer.py        # @register_provider — EVM chains
│   │   └── ccxt_exchange.py       # @register_provider — CEX via CCXT
│   └── skills/
│       └── quidclaw-crypto/
│           ├── SKILL.md
│           └── references/
│               ├── exchange-binance.md
│               ├── exchange-okx.md
│               ├── chain-evm.md
│               └── accounting-model.md
└── tests/
```

### Crypto Skill

```yaml
---
name: quidclaw-crypto
description: >
  Cryptocurrency asset management for QuidClaw. Syncs on-chain wallet data
  and centralized exchange (CEX) balances/trades. Supports EVM chains
  (Ethereum, BSC, Polygon, etc.) and exchanges via CCXT (Binance, OKX,
  Coinbase, etc.). Use when user mentions crypto, blockchain, exchange,
  wallet, or token.
---
```

**SKILL.md body (~500 tokens):** Overview of crypto capabilities, setup flow (add sources, sync, review, record), routing to references:

- "For Binance-specific setup and sync details, read `references/exchange-binance.md`."
- "For OKX-specific setup and sync details, read `references/exchange-okx.md`."
- "For on-chain wallet sync (Ethereum, BSC, Polygon, etc.), read `references/chain-evm.md`."
- "For crypto accounting patterns in Beancount (cost basis, transfers, gas fees), read `references/accounting-model.md`."

**references/exchange-binance.md:** Binance API setup, sync flow, data format, common issues.

**references/exchange-okx.md:** OKX API setup (including passphrase), sync flow, data format.

**references/chain-evm.md:** EVM explorer setup (Etherscan API key, supported chains), transaction types (normal, internal, ERC-20), incremental sync via block numbers.

**references/accounting-model.md:** Crypto-specific Beancount patterns — commodity definitions, account structure (`Assets:Crypto:{Exchange}:{Token}`), buy/sell with cost basis, transfers between wallets, gas fee handling, staking rewards, airdrops.

### Data Source Providers

Unchanged from previous spec:

- **`EvmExplorerSource`** — `@register_provider`, syncs via block explorer REST APIs (Etherscan, BscScan, etc.)
- **`CcxtExchangeSource`** — `@register_provider`, syncs via CCXT (100+ exchanges)

Both follow the existing `DataSource` ABC and store raw JSON in `sources/{source_name}/`.

### pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "quidclaw-crypto"
version = "0.1.0"
description = "Cryptocurrency support for QuidClaw — on-chain and exchange sync"
dependencies = [
    "quidclaw>=0.4.0",
    "ccxt>=4.0",
    "requests>=2.28",
]

[project.entry-points."quidclaw.plugins"]
crypto = "quidclaw_crypto.plugin:CryptoPlugin"

[tool.hatch.build.targets.wheel]
packages = ["src/quidclaw_crypto"]

[tool.hatch.build.targets.wheel.force-include]
"src/quidclaw_crypto/skills" = "quidclaw_crypto/skills"

[tool.hatch.build.targets.sdist]
include = ["src/quidclaw_crypto/**/*.py", "src/quidclaw_crypto/skills/**/*.md"]
```

### CLI Commands

```
quidclaw crypto portfolio [--json]     # Aggregate crypto balances
```

Minimal by design — most crypto operations are handled by the `quidclaw-crypto` skill + existing CLI commands.

## Error Handling

- **Plugin fails to load**: `warnings.warn()` with plugin name and exception, skip, core continues
- **Plugin API version mismatch**: `warnings.warn()` with version info, skip
- **Provider sync fails**: Return `SyncResult` with errors list, never raise
- **API rate limits**: Providers implement exponential backoff
- **Invalid API keys**: Clear error during first `sync`, not during registration

## Testing Strategy

### Phase 1 Tests

- Verify skill files installed correctly by `init`
- Verify `upgrade` updates skills
- Existing test suite passes unchanged

### Phase 2 Tests — Plugin Framework (`tests/core/test_plugins.py`)

- `test_discover_plugins_empty` — no plugins, returns empty list
- `test_discover_plugins_finds_installed` — mock entry point, verify discovery
- `test_load_plugins_registers_commands` — verify CLI group has new commands
- `test_plugin_load_failure_skipped` — broken plugin doesn't crash core
- `test_plugin_api_version_mismatch` — incompatible plugin skipped with warning
- `test_plugin_skills_installed` — verify `get_skills()` content copied to `.agents/skills/`

### Phase 2 Tests — Crypto Plugin (`quidclaw-crypto/tests/`)

- Provider tests with mocked HTTP responses
- Fixtures with sample Etherscan/CCXT JSON
- Skill presence tests — verify `get_skills_dir()` returns valid directory with expected SKILL.md files

## Migration Path

### Existing Users

`quidclaw upgrade` is the migration path:
1. Installs skills to `.agents/skills/`
2. Keeps existing workflow files and platform instruction files (no deletion)
3. Skills take precedence over old instruction files — agents that support skills will use them; agents that don't fall back to CLAUDE.md etc.

### Plugin Developers

Documentation to write:
1. "Creating a QuidClaw Plugin" guide
2. Template repository: `quidclaw-plugin-template`
3. Plugin API reference + skill authoring guide

## Future Considerations

Out of scope for this spec:

- **Skill distribution via `npx skills`**: QuidClaw skills could be published to the skills.sh ecosystem for broader discovery.
- **AgentMail extraction**: The built-in agentmail provider could become `quidclaw-email` plugin.
- **Non-EVM chains**: Bitcoin, Solana etc. — additional references in the crypto skill, or separate plugins.
- **Enterprise plugins**: `quidclaw-us-tax`, `quidclaw-cn-tax`, multi-entity consolidation — same plugin pattern.
