# QuidClaw Skills Architecture & Plugin System Design

## Overview

QuidClaw's AI capabilities are delivered as Agent Skills (agentskills.io standard), adopted by 30+ agents (Claude Code, Gemini CLI, Codex CLI, Cursor, GitHub Copilot, etc.). Phase 1 (skills conversion) is complete; this spec now tracks Phase 2 (plugin system).

On top of this skills foundation, a plugin system lets QuidClaw support non-universal features (crypto, tax, enterprise) without bloating the core.

## Problem Statement

As QuidClaw expands (crypto, tax, enterprise), bundling everything into core creates dependency bloat, feature interference, and onboarding friction. Different users need different features — a plugin system lets the core stay lean while supporting diverse needs.

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

# Phase 1: Workflow → Agent Skills — COMPLETE

Phase 1 is done. 5 core skills implemented, workflows deleted, `_build_instruction_body()` removed. `init` installs skills + generates minimal entry file. `upgrade` updates both.

### Core Skills

| Skill | Body tokens | References |
|-------|------------|------------|
| `quidclaw` | ~300 | cli-reference, conventions, notes-guide |
| `quidclaw-onboarding` | ~3000 | email-setup, backup-setup, automation-setup |
| `quidclaw-import` | ~2000 | email-processing, document-archival |
| `quidclaw-daily` | ~500 | import-steps, anomaly-steps |
| `quidclaw-review` | ~800 | reconciliation, anomaly-detection |

### Token Budget

| Skill | Frontmatter (always) | Body (on activate) | References (on demand) |
|-------|---------------------|--------------------|-----------------------|
| `quidclaw` | ~80 | ~300 | cli-reference ~800, conventions ~300, notes-guide ~1500 |
| `quidclaw-onboarding` | ~80 | ~3000 | email ~400, backup ~300, automation ~400 |
| `quidclaw-import` | ~80 | ~2000 | email-processing ~1000, document-archival ~500 |
| `quidclaw-daily` | ~80 | ~800 | import-steps ~300, anomaly-steps ~300 |
| `quidclaw-review` | ~80 | ~800 | reconciliation ~500, anomaly-detection ~500 |
| **Total always loaded** | **~400** | | |

400 tokens for all 5 skill frontmatters — negligible. Each activation loads only the relevant skill body + on-demand references.

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

Design notes:
- `get_skills_dir()` returns a `Path` to the plugin's skills directory, copied to the user's skills directory during `init` and `upgrade`.
- **Provider registration:** Plugins import their provider modules in `__init__`, triggering `@register_provider` at instantiation time. When `discover_plugins()` calls `plugin_cls()`, the providers register automatically. Example:

```python
class CryptoPlugin(QuidClawPlugin):
    def __init__(self):
        import quidclaw_crypto.providers.evm_explorer      # @register_provider fires
        import quidclaw_crypto.providers.ccxt_exchange      # @register_provider fires
```

The built-in agentmail provider follows the same pattern: a single module-level `try: import quidclaw.core.sources.agentmail except ImportError: pass` in `cli.py` replaces the scattered lazy imports in `sync()` and `add_source()`.

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

**Delete** the two `try: import quidclaw.core.sources.agentmail` blocks in `sync()` and `add_source()`. **Add** a single module-level import: `try: import quidclaw.core.sources.agentmail except ImportError: pass`.

### Plugin Management

```
quidclaw plugins                   # list installed plugins
```

### Plugin Skills Installation

Both `init` and `upgrade` install plugin skills (same logic as core skills):

```python
# shared by init and upgrade — after installing core skills
for plugin in discover_plugins():
    plugin_skills = plugin.get_skills_dir()
    if plugin_skills and plugin_skills.exists():
        for skill_dir in plugin_skills.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                target = skills_target / skill_dir.name
                shutil.copytree(skill_dir, target, dirs_exist_ok=True)
```

### Dynamic Entry File

`_build_entry_file()` includes plugin skills in the skills list:

```python
# After listing core skills, append plugin skills
for plugin in discover_plugins():
    plugin_skills = plugin.get_skills_dir()
    if plugin_skills and plugin_skills.exists():
        for skill_dir in plugin_skills.iterdir():
            if (skill_dir / "SKILL.md").exists():
                # Read name from frontmatter
                skills_list.append(f"- `{skill_dir.name}` — {plugin.description()}")
```

### Source Setup via Plugin Commands

Plugins provide their own setup commands with proper flags, help text, and completion — NOT a generic `--option` parameter. Example:

```bash
quidclaw crypto add-exchange binance --api-key xxx --secret xxx
quidclaw crypto add-wallet 0x1234 --chain ethereum --api-key xxx
```

Plugin commands call `config.add_source()` internally. The existing `quidclaw sync` and `quidclaw list-sources` work with any source regardless of how it was added.

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
quidclaw crypto add-exchange NAME --exchange ID --api-key KEY --secret SECRET [--passphrase PP]
quidclaw crypto add-wallet NAME --address ADDR --chain CHAIN [--api-key KEY]
quidclaw crypto portfolio [--json]
```

Setup commands (`add-exchange`, `add-wallet`) provide proper flags with help text. Internally they call `config.add_source()` with the correct provider config. `portfolio` aggregates balances across all crypto sources. Most crypto operations (interpreting transactions, recording to ledger) are handled by the `quidclaw-crypto` skill + existing CLI commands.

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
- `test_plugin_skills_installed` — verify `get_skills_dir()` content copied to `.agents/skills/`

### Phase 2 Tests — Crypto Plugin (`quidclaw-crypto/tests/`)

- Provider tests with mocked HTTP responses
- Fixtures with sample Etherscan/CCXT JSON
- Skill presence tests — verify `get_skills_dir()` returns valid directory with expected SKILL.md files

## Installation

No migration needed. `pip install quidclaw-crypto` + `quidclaw upgrade` installs everything.

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
