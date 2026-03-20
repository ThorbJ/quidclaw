# Contributing

## How to Add a New CLI Command

1. Add core logic in `src/quidclaw/core/<module>.py` with tests in `tests/core/`
2. Add a Click command in `src/quidclaw/cli.py` under the appropriate section
3. Add CLI test in `tests/test_cli.py`
4. Update the command list in `_generate_claude_md()` so user-facing CLAUDE.md stays current

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

## How to Add a New Workflow

1. Create `src/quidclaw/workflows/<name>.md` (bundled copy, shipped with package)
2. Workflow instructions should use CLI commands (via Bash) for Beancount operations
3. Use native AI tools (Read, Write, Glob, Grep) for file operations — never reference MCP tools
4. Reference the new workflow in `_generate_claude_md()` so users know it exists
