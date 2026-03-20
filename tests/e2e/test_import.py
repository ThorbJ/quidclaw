"""E2E tests: Bill import scenarios."""

import pytest
from datetime import date
from decimal import Decimal
from tests.e2e.conftest import copy_fixture_to_inbox
from tests.e2e.helpers import (
    run_claude, load_ledger, count_transactions, get_transactions,
    inbox_is_empty, documents_count,
)


@pytest.mark.e2e
class TestSingleCSVImport:
    """Import a single CSV bank statement — one claude call, multiple assertions."""

    def test_full_import_workflow(self, data_dir_with_accounts):
        """AI should parse CSV, record transactions, archive file, clear inbox."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")

        result = run_claude("请帮我处理inbox里的账单文件", dd)

        entries, errors = load_ledger(dd)

        # 1. All 5 transactions should be recorded
        txn_count = count_transactions(entries, date_from=date(2026, 3, 1))
        assert txn_count >= 5, (
            f"Expected at least 5 transactions, got {txn_count}. "
            f"AI output: {result.get('result', '')[:500]}"
        )

        # 2. Amounts should be exact
        txns = get_transactions(entries, date_from=date(2026, 3, 1))
        amounts = set()
        for txn in txns:
            for posting in txn.postings:
                if posting.account.startswith("Expenses:") and posting.units:
                    amounts.add(abs(posting.units.number))

        expected = {Decimal("35.80"), Decimal("28.50"), Decimal("299.00"),
                    Decimal("58.00"), Decimal("156.30")}
        assert expected.issubset(amounts), f"Missing amounts. Expected {expected}, got: {amounts}"

        # 3. Inbox should be cleared (file archived)
        assert inbox_is_empty(dd), "Inbox should be empty after processing"

        # 4. File should be in documents/
        assert documents_count(dd) >= 1, "File should be archived to documents/"


@pytest.mark.e2e
class TestMultiCurrencyImport:
    """Import a CSV with multiple currencies (USD, CNY, AED)."""

    def test_multi_currency_workflow(self, data_dir_with_accounts):
        """AI should handle different currencies correctly."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/multi-currency-2026-03.csv")

        result = run_claude("请帮我处理inbox里的账单文件", dd)

        entries, _ = load_ledger(dd)
        txns = get_transactions(entries, date_from=date(2026, 3, 1))

        # Should have recorded at least 3 transactions
        assert len(txns) >= 3, (
            f"Expected at least 3 transactions, got {len(txns)}. "
            f"AI output: {result.get('result', '')[:500]}"
        )

        # Check currencies
        currencies_seen = set()
        for txn in txns:
            for posting in txn.postings:
                if posting.units:
                    currencies_seen.add(posting.units.currency)

        assert len(currencies_seen) >= 2, (
            f"Expected at least 2 different currencies, got: {currencies_seen}"
        )
