# QuidClaw Plugin System & Crypto Extension Design

## Overview

QuidClaw needs to support non-universal features (crypto, US tax, CN tax, enterprise) without bloating the core. This spec defines a plugin framework that lets QuidClaw stay lean while supporting diverse user needs, plus the first concrete plugin: `quidclaw-crypto`.

## Problem Statement

QuidClaw aims to manage "everything related to money" for both individuals and enterprises across jurisdictions. But:

- No single user needs all features (a Chinese individual doesn't need US tax forms; a traditional saver doesn't need DeFi tracking)
- Bundling everything into core creates: dependency bloat, feature interference, instability, high onboarding friction
- The project needs community contributions without requiring contributors to fork the entire codebase

## Design Goals

1. **Core stays lean** — installing QuidClaw without plugins gives a clean accounting tool
2. **Isolation** — a bug in the crypto plugin cannot crash tax reporting
3. **Low barrier for plugin authors** — especially for workflow-only extensions
4. **Automatic discovery** — install a plugin, it just works; no manual config
5. **Backwards compatible** — existing users, commands, and data are unaffected

## Architecture

### Two Types of Extensions

QuidClaw's AI-native architecture means many features are just knowledge (workflows), not code. Extensions split into:

| Type | What it is | Who creates | Example |
|------|-----------|-------------|---------|
| **Code Plugin** | Python package with providers, commands, workflows | Developers | `quidclaw-crypto` (exchange API sync) |
| **Workflow Pack** | Markdown workflow files only, no code | Anyone | CN tax filing guide for AI |

Code plugins can bundle workflow packs. Workflow packs can exist independently.

### Plugin Interface

```python
# src/quidclaw/core/plugins.py

import importlib.metadata
import warnings
from abc import ABC, abstractmethod

PLUGIN_API_VERSION = 1
PLUGIN_GROUP = "quidclaw.plugins"

class QuidClawPlugin(ABC):
    """Base class for all QuidClaw plugins."""

    plugin_api_version: int = 1  # Override if plugin needs a newer API

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
        """Register Click commands/groups onto the main CLI group.

        Called once at CLI startup. Plugins call cli.add_command()
        to attach their command groups.
        """
        pass

    def get_workflows(self) -> list[tuple[str, str]]:
        """Return workflow files as (filename, content) tuples.

        These are copied to the user's .quidclaw/workflows/ directory
        when `quidclaw upgrade` runs. Use importlib.resources to read
        bundled .md files from the plugin package.
        """
        return []
```

Design decisions:
- **No `register_providers` method.** Plugins register DataSource providers using the existing `@register_provider` decorator pattern — the same way the built-in agentmail provider works. When a plugin's provider module is imported (triggered by the entry point load), the decorator fires and registers the provider in the global `PROVIDERS` dict. This keeps one consistent registration mechanism.
- `register_commands` has a default no-op so workflow-only plugins need not override it
- `get_workflows` returns `(filename, content)` tuples. Plugins read their bundled `.md` files via `importlib.resources` inside this method (lazy, only called during `upgrade`)
- `plugin_api_version` defaults to 1 on the base class; plugins override only if they require a newer API
- The interface is intentionally small (4 methods + 1 class attr) to minimize the API surface for versioning

### Plugin Discovery

Uses Python's standard `importlib.metadata.entry_points` — the same mechanism pytest, black, and setuptools use.

```python
# src/quidclaw/core/plugins.py (continued)

def discover_plugins() -> list[QuidClawPlugin]:
    """Find and instantiate all installed QuidClaw plugins."""
    plugins = []
    eps = importlib.metadata.entry_points()
    for ep in eps.select(group=PLUGIN_GROUP):
        try:
            plugin_cls = ep.load()
            api_ver = getattr(plugin_cls, 'plugin_api_version', 1)
            if api_ver > PLUGIN_API_VERSION:
                warnings.warn(
                    f"Plugin '{ep.name}' requires API v{api_ver}, "
                    f"core is v{PLUGIN_API_VERSION}. Skipping. "
                    f"Upgrade QuidClaw to use this plugin.",
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
    """Discover and activate all plugins at CLI startup.

    Provider registration happens automatically when the plugin's
    provider modules are imported (via @register_provider decorator).
    This function only needs to handle CLI command registration.
    """
    plugins = discover_plugins()
    for plugin in plugins:
        plugin.register_commands(cli)
    return plugins
```

A plugin registers via its `pyproject.toml`:

```toml
[project.entry-points."quidclaw.plugins"]
crypto = "quidclaw_crypto.plugin:CryptoPlugin"
```

### CLI Integration

#### Startup

One line added to `cli.py` after the `main` group definition and all built-in commands:

```python
from quidclaw.core.plugins import load_plugins

# After all built-in @main.command() definitions:
load_plugins(main)
```

This replaces the manual `import quidclaw.core.sources.agentmail` blocks that currently exist inside `sync()` (lines 627-630) and `add_source()` (lines 548-550). **These two `try: import` blocks must be deleted** — plugin entry point loading handles provider registration at startup, before any command body runs.

#### Plugin Management Command

One new command:

```
quidclaw plugins                   # list installed plugins
```

Outputs each installed plugin's name and description. If no plugins are installed, prints a hint: `No plugins installed. Install with: pip install quidclaw-<name>`.

`install` and `uninstall` wrappers around pip are intentionally omitted — `pip install quidclaw-crypto` is clear enough, and wrapping pip introduces fragility (pipx environments, conda conflicts, module cache staleness). Users install plugins with pip directly. After installing, they must re-invoke QuidClaw (new process) for the plugin to take effect.

#### Upgrade Integration

The existing `upgrade` command gains a plugin loop:

```python
# After copying built-in workflows:
for plugin in discover_plugins():
    for filename, content in plugin.get_workflows():
        workflow_path = target_dir / filename
        workflow_path.write_text(content)
```

### Workflow Pack Mechanism

Workflow-only extensions (no Python code) are distributed as git repositories containing markdown files:

```
quidclaw-cn-tax-workflows/
  workflows/
    cn-tax-annual.md
    cn-tax-quarterly.md
  README.md
```

Installed via:

```
quidclaw install-workflow <git-url> [--confirm]
```

This clones the repo to a temporary directory and copies `workflows/*.md` into `.quidclaw/workflows/`. No entry points, no pyproject.toml required — minimal barrier for non-developers.

**Security note:** Workflow files control AI behavior over financial data. The `install-workflow` command:
- Requires `--confirm` flag (or interactive prompt) to proceed
- Prints a warning: "Workflow files control AI behavior over your financial data. Only install from sources you trust."
- Supports pinning to a specific commit: `<git-url>@<commit-sha>`

### Plugin API Versioning

`PLUGIN_API_VERSION` and `plugin_api_version` are defined in the Plugin Interface section above. The version check happens inside `discover_plugins()`:

```python
api_ver = getattr(plugin_cls, 'plugin_api_version', 1)
if api_ver > PLUGIN_API_VERSION:
    warnings.warn(...)
    continue
```

Breaking changes to `QuidClawPlugin` bump `PLUGIN_API_VERSION`. The policy: API version 1 is stable for the foreseeable future; breaking changes require a major QuidClaw release.

## Crypto Plugin: `quidclaw-crypto`

The first code plugin, providing on-chain and centralized exchange data sync.

### Package Structure

```
quidclaw-crypto/
├── pyproject.toml
├── src/quidclaw_crypto/
│   ├── __init__.py
│   ├── plugin.py                # CryptoPlugin entry point
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── evm_explorer.py      # EVM chain explorer (Etherscan, BscScan, etc.)
│   │   └── ccxt_exchange.py     # CEX via CCXT (Binance, OKX, Coinbase, etc.)
│   └── workflows/
│       ├── crypto-onboarding.md  # AI guide: set up crypto tracking
│       ├── crypto-sync.md        # AI guide: sync and review crypto data
│       └── crypto-reconcile.md   # AI guide: reconcile crypto balances
└── tests/
    ├── test_evm_explorer.py
    └── test_ccxt_exchange.py
```

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
    "quidclaw>=0.3.0",
    "ccxt>=4.0",
    "requests>=2.28",
]

[project.entry-points."quidclaw.plugins"]
crypto = "quidclaw_crypto.plugin:CryptoPlugin"

[tool.hatch.build.targets.wheel]
packages = ["src/quidclaw_crypto"]

[tool.hatch.build.targets.wheel.force-include]
"src/quidclaw_crypto/workflows" = "quidclaw_crypto/workflows"

[tool.hatch.build.targets.sdist]
include = ["src/quidclaw_crypto/**/*.py", "src/quidclaw_crypto/workflows/*.md"]
```

No dependency on `web3` — on-chain data is fetched via REST APIs to block explorers (Etherscan, BscScan, etc.), avoiding the heavy web3 dependency tree. `ccxt` handles all exchange APIs uniformly.

### Data Source Providers

#### EVM Explorer Provider

Syncs transaction history from EVM-compatible blockchains via block explorer APIs.

```python
from quidclaw.core.sources.base import DataSource, SyncResult
from quidclaw.core.sources.registry import register_provider

@register_provider
class EvmExplorerSource(DataSource):
    @staticmethod
    def provider_name() -> str:
        return "evm-explorer"

    def sync(self) -> SyncResult:
        # Config: address, chain (ethereum/bsc/polygon/...), api_key
        # Fetches: normal txs, internal txs, ERC-20 transfers
        # Stores raw JSON in sources/{source_name}/{block_range}/
        # Tracks last synced block in .state.yaml for incremental sync
        ...

    def status(self) -> dict:
        # Returns: address, chain, last_sync, last_block, unprocessed count
        ...
```

User setup:

```bash
quidclaw add-source my-eth --provider evm-explorer \
    --address 0x1234... --chain ethereum --api-key env:ETHERSCAN_KEY
```

Data storage follows the existing pattern:

```
sources/my-eth/
  .state.yaml                    # last_block, last_sync timestamp
  20260328_normal_txs/
    raw.json                     # Raw API response
    metadata.yaml                # Chain, address, block range, sync time
  20260328_erc20_transfers/
    raw.json
    metadata.yaml
```

Supported chains (via compatible APIs): Ethereum, BSC, Polygon, Arbitrum, Optimism, Base, Avalanche. Adding a new EVM chain = adding its explorer base URL to a config map.

#### CCXT Exchange Provider

Syncs trade history, balances, deposits, and withdrawals from centralized exchanges via CCXT.

```python
from quidclaw.core.sources.base import DataSource, SyncResult
from quidclaw.core.sources.registry import register_provider

@register_provider
class CcxtExchangeSource(DataSource):
    @staticmethod
    def provider_name() -> str:
        return "ccxt-exchange"

    def sync(self) -> SyncResult:
        # Config: exchange (binance/okx/coinbase/...), api_key, secret, [passphrase]
        # Fetches: trades, balances, deposits, withdrawals
        # Stores raw JSON in sources/{source_name}/{data_type}/
        # Tracks pagination cursor in .state.yaml for incremental sync
        ...

    def status(self) -> dict:
        # Returns: exchange, last_sync, trade count, unprocessed count
        ...
```

User setup:

```bash
quidclaw add-source my-binance --provider ccxt-exchange \
    --exchange binance --api-key env:BINANCE_KEY --secret env:BINANCE_SECRET
```

Data storage:

```
sources/my-binance/
  .state.yaml                    # last_trade_id, last_sync
  balances/
    20260328T120000.json         # Snapshot at sync time
  trades/
    20260328_batch_001.json      # Trade history batch
    metadata.yaml
  deposits/
    20260328_batch_001.json
  withdrawals/
    20260328_batch_001.json
```

CCXT supports 100+ exchanges. Users specify the exchange ID (e.g., `binance`, `okx`, `coinbase`, `kraken`). The provider validates that the exchange ID exists in CCXT.

#### Provider Configuration via `add-source`

The existing `add-source` command has provider-specific flags (`--api-key`, `--inbox-id`, etc.). To support plugin providers without hardcoding every possible flag, a catch-all `--option KEY=VALUE` parameter (repeatable) is **added alongside** the existing flags:

```bash
# Existing flags still work (backwards compatible):
quidclaw add-source my-email --provider agentmail --api-key env:AM_KEY

# Plugin providers use --option for provider-specific config:
quidclaw add-source my-okx --provider ccxt-exchange \
    --option exchange=okx \
    --option api_key=env:OKX_KEY \
    --option secret=env:OKX_SECRET \
    --option passphrase=env:OKX_PASSPHRASE
```

Existing named flags (`--api-key`, `--inbox-id`, etc.) are kept for backwards compatibility. `--option` entries are merged into the source config dict alongside them. If a key appears in both a named flag and `--option`, the named flag wins.

### CLI Commands

The crypto plugin registers a `crypto` command group:

```
quidclaw crypto portfolio                  # Aggregate balances across all crypto sources
quidclaw crypto portfolio --json           # JSON output
```

This is intentionally minimal. Most crypto operations (interpreting transactions, recording to ledger, reconciliation) are handled by workflows + existing QuidClaw commands (`add-txn`, `balance`, `query`). Following the architectural constraint: CLI does data movement, AI does interpretation.

### Workflows

#### crypto-onboarding.md

Guides the AI through setting up crypto tracking for a user:
1. Ask what exchanges/wallets the user has
2. Help configure data sources (API keys, wallet addresses)
3. Set up commodity definitions (`add-commodity BTC`, `add-commodity ETH`, etc.)
4. Create account structure (`Assets:Crypto:Binance:BTC`, `Assets:Crypto:Wallet:ETH`, etc.)
5. Run first sync

#### crypto-sync.md

Guides the AI through a sync-and-review cycle:
1. Run `quidclaw sync` for all crypto sources
2. Review raw synced data
3. Interpret transactions (buys, sells, transfers, staking rewards, airdrops)
4. Record as Beancount entries using `add-txn`
5. Verify balances match exchange/chain

#### crypto-reconcile.md

Guides the AI through reconciliation:
1. Fetch current on-chain balances / exchange balances
2. Compare with ledger balances via `quidclaw balance`
3. Identify discrepancies
4. Help user resolve (missing transactions, transfers between sources, etc.)

### Beancount Accounting Model

Crypto assets map naturally to Beancount:

```beancount
; Commodity definitions (in prices.bean)
2026-01-01 commodity BTC
  name: "Bitcoin"
  price: "USD:yahoo/BTC-USD"

2026-01-01 commodity ETH
  name: "Ethereum"
  price: "USD:yahoo/ETH-USD"

; Account structure
2026-01-01 open Assets:Crypto:Binance:BTC    BTC
2026-01-01 open Assets:Crypto:Binance:USDT   USDT
2026-01-01 open Assets:Crypto:Wallet:ETH     ETH

; Buy BTC on Binance
2026-03-15 * "Binance" "Buy BTC"
  Assets:Crypto:Binance:BTC      0.5 BTC {42000 USD}
  Assets:Crypto:Binance:USDT    -21000 USDT

; Transfer ETH to wallet
2026-03-16 * "Transfer" "Binance -> Wallet"
  Assets:Crypto:Wallet:ETH       2.0 ETH {}
  Assets:Crypto:Binance:ETH     -2.0 ETH {}
  Expenses:Crypto:Fees           0.001 ETH {}
```

The accounting model details (cost basis tracking, gas fee handling, DeFi-specific patterns) are documented in the workflows, not hardcoded — the AI interprets raw data and applies the appropriate patterns.

## Core Changes Summary

| File | Change | Lines |
|------|--------|-------|
| `core/plugins.py` | **New** — Plugin ABC, discovery, loading, API version check | ~80 |
| `cli.py` | Add `load_plugins(main)` call at module level after all commands | ~3 |
| `cli.py` | Add `plugins` list command | ~15 |
| `cli.py` | Add `install-workflow` command (with `--confirm` gate) | ~35 |
| `cli.py` | Add `--option` repeatable param to `add-source` (alongside existing flags) | ~10 |
| `cli.py` (upgrade) | Add plugin workflow copy loop | ~10 |
| `cli.py` (sync) | **Delete** `try: import quidclaw.core.sources.agentmail` block (lines 627-630) | -4 |
| `cli.py` (add-source) | **Delete** `try: import quidclaw.core.sources.agentmail` block (lines 548-550) | -3 |
| `cli.py` (module level) | **Add** `import quidclaw.core.sources.agentmail` at top with other imports | +4 |
| `pyproject.toml` | No changes needed | 0 |

Total core delta: ~155 lines added, 7 removed. The agentmail provider is a **built-in provider**, not a plugin — it has no entry point. The two lazy `try: import` blocks scattered inside `sync()` and `add_source()` bodies are replaced with a single module-level import at the top of `cli.py` (guarded by `try/except ImportError` since agentmail is an optional dependency). This ensures the `@register_provider` decorator fires once at startup, consistent with how plugin providers register.

## Error Handling

- **Plugin fails to load**: `warnings.warn()` with plugin name and exception message, skip plugin, core continues normally. This ensures users see the failure in stderr rather than silently missing a plugin.
- **Plugin API version mismatch**: `warnings.warn()` with version info and "Upgrade QuidClaw to use this plugin", skip plugin
- **Provider sync fails** (crypto-specific): Return `SyncResult` with errors list, never raise — partial sync is better than no sync
- **API rate limits** (crypto-specific): Providers implement exponential backoff; `SyncResult.errors` reports rate limit hits
- **Invalid API keys** (crypto-specific): Provider raises clear error during first `sync`, not during registration

## Testing Strategy

### Plugin Framework Tests (`tests/core/test_plugins.py`)

- `test_discover_plugins_empty` — no plugins installed, returns empty list
- `test_discover_plugins_finds_installed` — mock entry point, verify discovery
- `test_load_plugins_registers_providers` — verify providers appear in registry
- `test_load_plugins_registers_commands` — verify CLI group has new commands
- `test_plugin_load_failure_skipped` — broken plugin doesn't crash core
- `test_plugin_api_version_mismatch` — incompatible plugin is skipped with warning

### Crypto Plugin Tests (`quidclaw-crypto/tests/`)

- Provider tests with mocked HTTP responses (no real API calls in unit tests)
- Fixtures with sample Etherscan/CCXT JSON responses
- Integration tests (marked slow) with test API keys for Etherscan testnet
- Workflow presence tests — verify all workflow files are returned by `get_workflows()`

### Backwards Compatibility Tests

- Existing test suite passes unchanged (zero regressions)
- `sync` and `add-source` still work with agentmail provider

## Migration Path

### For Existing Users

Nothing changes. QuidClaw without plugins works exactly as before. The agentmail provider continues to work — it's still built-in, not moved to a plugin. Over time, it could optionally be extracted to a plugin, but that's not required.

### For Plugin Developers

Documentation to be written:
1. "Creating a QuidClaw Plugin" guide in docs/
2. Template repository: `quidclaw-plugin-template`
3. Plugin API reference

## Future Considerations

These are explicitly out of scope for this spec but worth noting:

- **Plugin marketplace/registry**: For now, plugins are discovered via PyPI search or documentation. A `quidclaw search <keyword>` command could be added later.
- **AgentMail extraction**: The built-in agentmail provider could be extracted to `quidclaw-email` plugin for consistency, but there's no urgency.
- **Plugin settings UI**: Plugins could declare their required configuration schema for guided setup. Not needed for v1.
- **Non-EVM chains**: Bitcoin, Solana, etc. would be additional providers in the crypto plugin or separate plugins. The architecture supports both.
- **Enterprise features**: Tax modules (`quidclaw-us-tax`, `quidclaw-cn-tax`), multi-entity consolidation, audit trails — all follow the same plugin pattern.
