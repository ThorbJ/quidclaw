# Contributing

## How to Add a New CLI Command

1. Add core logic in `src/quidclaw/core/<module>.py` with tests in `tests/core/`
2. Add a Click command in `src/quidclaw/cli.py` under the appropriate section
3. Add CLI test in `tests/test_cli.py`
4. Update the CLI reference in the skill (`src/quidclaw/skills/quidclaw/references/cli-reference.md`) and `docs/cli-reference.md`

Pattern:
```python
@main.command("my-command")
@click.argument("arg")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def my_command(arg, as_json):
    """One-line description."""
    from quidclaw.core.module import Manager
    ledger = get_ledger()  # or get_config() for non-ledger operations
    mgr = Manager(ledger)
    result = mgr.some_method(arg)
    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        click.echo(result)
```

## How to Add a New Skill

1. Create a new skill file in `src/quidclaw/skills/<name>.md`, or add a reference to an existing skill
2. Skill instructions should use CLI commands (via Bash) for Beancount operations
3. Use native AI tools (Read, Write, Glob, Grep) for file operations — never reference MCP tools
4. Register the skill in the installer so it is copied to platform directories at init/upgrade

## How to Add a New Data Source Provider

1. Create `src/quidclaw/core/sources/<provider>.py`
2. Subclass `DataSource` from `core/sources/base.py`
3. Implement `provider_name()`, `sync()`, `status()`, and optionally `provision()`
4. Use `@register_provider` decorator from `core/sources/registry.py`
5. Add tests in `tests/core/test_<provider>.py`
6. If the provider needs an external SDK, add it as an optional dependency in `pyproject.toml`

Pattern:
```python
from quidclaw.core.sources.base import DataSource, SyncResult
from quidclaw.core.sources.registry import register_provider

@register_provider
class MySource(DataSource):
    @staticmethod
    def provider_name() -> str:
        return "my-provider"

    def sync(self) -> SyncResult:
        # Pull data from external source
        # Store in self.config.source_dir(self.source_name)
        # Return SyncResult with items_fetched, items_stored, errors
        ...

    def status(self) -> dict:
        # Return {"last_sync": ..., "total_synced": ..., "unprocessed": ...}
        ...
```

Key rules:
- `sync()` must be idempotent — calling it twice must not duplicate data
- Store synced data in `sources/{source_name}/` as complete information packages
- External SDK imports must be lazy (inside methods, not at module level)
- The provider is registered automatically via the `@register_provider` decorator
