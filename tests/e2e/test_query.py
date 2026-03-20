"""E2E tests: Financial question scenarios."""

import pytest
from datetime import date
from tests.e2e.conftest import copy_fixture_to_inbox
from tests.e2e.helpers import run_claude, load_ledger, ai_mentioned


@pytest.mark.e2e
class TestFinancialQuestions:
    """User asks financial questions — AI should answer accurately."""

    def test_spending_total_accurate(self, data_dir_with_accounts):
        """After importing data, spending total should be close to correct."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")
        run_claude("处理inbox的账单", dd)

        result = run_claude("我3月总共花了多少钱？", dd)

        assert ai_mentioned(result, "577", "578"), (
            "AI should report spending close to 577.60"
        )

    def test_category_breakdown(self, data_dir_with_accounts):
        """AI should be able to break down spending by category."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")
        run_claude("处理inbox的账单", dd)

        result = run_claude("我的钱都花在哪了？帮我分类看看", dd)

        assert ai_mentioned(result,
            "食", "餐", "购物", "通讯", "food", "shopping",
            "外卖", "商城", "移动"
        ), "AI should break down spending into categories"
