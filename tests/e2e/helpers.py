"""E2E test helpers — run claude CLI and verify data state."""

# System instruction prepended to all E2E prompts. In -p mode there's no
# second turn, so the AI must act autonomously without asking for confirmation.
E2E_SYSTEM = (
    "你正在自动化测试环境中运行，没有用户可以回复你。"
    "请直接执行所有操作，不要等待确认。"
    "如果需要做分类判断，请自行决定最合理的选项。"
)

import json
import os
import subprocess
from datetime import date
from decimal import Decimal
from pathlib import Path

from beancount import loader
from beancount.core import data, realization


def run_claude(
    prompt: str,
    data_dir: Path,
    max_turns: int = 20,
    timeout: int = 300,
) -> dict:
    """Run claude in print mode in the data directory (reads CLAUDE.md automatically)."""
    env = {**os.environ, "QUIDCLAW_DATA_DIR": str(data_dir)}
    full_prompt = f"{E2E_SYSTEM}\n\n{prompt}"

    result = subprocess.run(
        [
            "claude", "-p", full_prompt,
            "--output-format", "json",
            "--max-turns", str(max_turns),
            "--dangerously-skip-permissions",
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(data_dir),
        env=env,
    )

    if result.returncode != 0 and not result.stdout.strip():
        return {"result": result.stderr, "error": True, "returncode": result.returncode}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"result": result.stdout, "error": True, "returncode": result.returncode}


# --- Ledger verification ---

def load_ledger(data_dir: Path):
    """Load beancount ledger. Returns (entries, errors)."""
    main_bean = data_dir / "ledger" / "main.bean"
    if not main_bean.exists():
        return [], []
    entries, errors, options = loader.load_file(str(main_bean))
    return entries, errors


def get_transactions(entries, payee=None, date_from=None, date_to=None):
    """Get transactions, optionally filtered."""
    txns = [e for e in entries if isinstance(e, data.Transaction)]
    if payee:
        txns = [t for t in txns if payee.lower() in (t.payee or "").lower()]
    if date_from:
        txns = [t for t in txns if t.date >= date_from]
    if date_to:
        txns = [t for t in txns if t.date <= date_to]
    return txns


def count_transactions(entries, **kwargs):
    """Count transactions matching filters."""
    return len(get_transactions(entries, **kwargs))


def get_balance(entries, account):
    """Get balance for an account. Returns {currency: Decimal}."""
    real_root = realization.realize(entries)
    real_account = realization.get(real_root, account)
    if not real_account:
        return {}
    return {pos.units.currency: pos.units.number for pos in real_account.balance}


def get_accounts(entries):
    """Get all open account names."""
    return {e.account for e in entries if isinstance(e, data.Open)}


def total_expenses(entries, date_from=None, date_to=None):
    """Sum all expense postings. Returns {currency: Decimal}."""
    totals = {}
    for txn in get_transactions(entries, date_from=date_from, date_to=date_to):
        for posting in txn.postings:
            if posting.account.startswith("Expenses:") and posting.units:
                curr = posting.units.currency
                totals[curr] = totals.get(curr, Decimal(0)) + posting.units.number
    return totals


# --- Directory verification ---

def list_files(directory: Path) -> list[Path]:
    """List all non-hidden files recursively."""
    if not directory.exists():
        return []
    return sorted(f for f in directory.rglob("*") if f.is_file() and not f.name.startswith("."))


def inbox_is_empty(data_dir: Path) -> bool:
    return len(list_files(data_dir / "inbox")) == 0


def documents_count(data_dir: Path) -> int:
    return len(list_files(data_dir / "documents"))


def notes_count(data_dir: Path) -> int:
    return len(list_files(data_dir / "notes"))


# --- AI output verification ---

def _extract_text(result: dict) -> str:
    """Extract text from claude JSON output, checking multiple possible keys."""
    for key in ("result", "text", "content", "message", "output"):
        val = result.get(key, "")
        if val:
            return str(val).lower()
    # Fallback: stringify the entire result
    return str(result).lower()


def ai_mentioned(result: dict, *keywords: str) -> bool:
    """Check if AI output contains ANY of the keywords (case-insensitive)."""
    text = _extract_text(result)
    return any(kw.lower() in text for kw in keywords)


def ai_mentioned_all(result: dict, *keywords: str) -> bool:
    """Check if AI output contains ALL of the keywords."""
    text = _extract_text(result)
    return all(kw.lower() in text for kw in keywords)
