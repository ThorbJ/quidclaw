"""E2E tests: Deduplication scenarios."""

import pytest
from datetime import date
from tests.e2e.conftest import copy_fixture_to_inbox
from tests.e2e.helpers import (
    run_claude, load_ledger, get_transactions, count_transactions,
)


@pytest.mark.e2e
class TestDeduplication:
    """Two data sources contain the same transaction — AI should deduplicate."""

    def test_same_transaction_two_files(self, data_dir_with_accounts):
        """CMB and Alipay both have 3/15 Starbucks 35.80 — should only appear once."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")
        copy_fixture_to_inbox(dd, "csv/alipay-2026-03.csv")

        run_claude("请帮我处理inbox里的所有账单文件，注意检查是否有重复的交易", dd)

        entries, _ = load_ledger(dd)
        starbucks = get_transactions(entries, payee="星巴克",
                                     date_from=date(2026, 3, 15),
                                     date_to=date(2026, 3, 15))

        assert len(starbucks) == 1, (
            f"Starbucks 3/15 should appear exactly once, got {len(starbucks)}"
        )

    def test_different_amounts_not_deduped(self, data_dir_with_accounts):
        """Two transactions on the same day with different amounts should both be kept."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")
        copy_fixture_to_inbox(dd, "csv/alipay-2026-03.csv")

        run_claude("请帮我处理inbox里的所有账单文件", dd)

        entries, _ = load_ledger(dd)
        mar16 = get_transactions(entries, date_from=date(2026, 3, 16),
                                 date_to=date(2026, 3, 16))
        assert len(mar16) >= 2, (
            f"Two different transactions on 3/16 should both exist, got {len(mar16)}"
        )

    def test_sequential_import_dedup(self, data_dir_with_accounts):
        """Import CMB first, then Alipay in a second call — should still deduplicate."""
        dd = data_dir_with_accounts

        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")
        run_claude("请帮我处理inbox里的账单", dd)

        copy_fixture_to_inbox(dd, "csv/alipay-2026-03.csv")
        run_claude("请帮我处理inbox里的新账单，注意和已有数据去重", dd)

        entries, _ = load_ledger(dd)
        starbucks = get_transactions(entries, payee="星巴克",
                                     date_from=date(2026, 3, 15),
                                     date_to=date(2026, 3, 15))
        assert len(starbucks) == 1, (
            f"Starbucks 3/15 should appear exactly once after sequential import, got {len(starbucks)}"
        )
