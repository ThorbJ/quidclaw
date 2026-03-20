"""E2E tests: Phase 2 — Monthly reports and anomaly detection."""

import pytest
from datetime import date
from tests.e2e.conftest import copy_fixture_to_inbox
from tests.e2e.helpers import (
    run_claude, load_ledger, count_transactions, ai_mentioned,
)


@pytest.mark.e2e
class TestMonthlyReport:
    """AI should generate accurate monthly summaries."""

    def test_monthly_summary_with_categories(self, data_dir_with_accounts):
        """Import 3 months of data, ask for March summary with breakdown."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/three-months-2026-q1.csv")
        run_claude("处理inbox里的账单", dd)

        result = run_claude("帮我总结一下2026年3月的财务情况，包括分类支出", dd)

        # AI should mention spending categories
        assert ai_mentioned(result,
            "食", "餐", "购物", "通讯", "订阅", "entertainment",
            "food", "shopping"
        ), f"Should mention spending categories. Got: {str(result)[:500]}"

    def test_month_comparison(self, data_dir_with_accounts):
        """AI should compare March vs February spending."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/three-months-2026-q1.csv")
        run_claude("处理inbox里的账单", dd)

        result = run_claude("和2月相比，我3月的花费有什么变化？", dd)

        # AI should mention some comparison (increase/decrease/change)
        assert ai_mentioned(result,
            "增", "减", "多", "少", "变化", "increase", "decrease",
            "more", "less", "change", "比", "%", "上升", "下降"
        ), f"Should compare months. Got: {str(result)[:500]}"

    def test_largest_transactions(self, data_dir_with_accounts):
        """AI should identify the biggest transactions."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/three-months-2026-q1.csv")

        result = run_claude(
            "先处理inbox里的账单，然后告诉我3月最大的几笔花费是什么",
            dd
        )

        # Should mention the 1500 restaurant charge
        assert ai_mentioned(result,
            "1500", "1,500", "高级餐厅", "餐厅"
        ), f"Should mention the 1500 restaurant charge. Got: {str(result)[:500]}"


@pytest.mark.e2e
class TestAnomalyDetection:
    """AI should detect financial anomalies."""

    def test_detect_recurring_subscription(self, data_dir_with_accounts):
        """Netflix appears 3 months — should be identified as subscription."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/three-months-2026-q1.csv")
        run_claude("处理inbox里的账单", dd)

        result = run_claude("帮我检查一下有没有什么异常或者订阅扣款", dd)

        assert ai_mentioned(result,
            "Netflix", "netflix", "订阅", "recurring", "subscription", "每月"
        ), f"Should detect Netflix subscription. Got: {str(result)[:500]}"

    def test_detect_price_change(self, data_dir_with_accounts):
        """Netflix went from 88 to 98 in March — should flag price change."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/three-months-2026-q1.csv")
        run_claude("处理inbox里的账单", dd)

        result = run_claude("帮我检查订阅服务有没有涨价", dd)

        assert ai_mentioned(result,
            "88", "98", "涨", "increase", "change", "Netflix", "netflix", "变"
        ), f"Should detect Netflix price change 88->98. Got: {str(result)[:500]}"

    def test_detect_large_outlier(self, data_dir_with_accounts):
        """1500 restaurant charge is way above average — should be flagged."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/three-months-2026-q1.csv")
        run_claude("处理inbox里的账单", dd)

        result = run_claude("帮我找找有没有异常大额的消费", dd)

        assert ai_mentioned(result,
            "1500", "1,500", "高级餐厅", "异常", "大额", "unusual", "large",
            "outlier", "高于", "平均"
        ), f"Should flag 1500 restaurant as outlier. Got: {str(result)[:500]}"

    def test_detect_unknown_merchant(self, data_dir_with_accounts):
        """神秘科技有限公司 appears only once — should be flagged."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/three-months-2026-q1.csv")
        run_claude("处理inbox里的账单", dd)

        result = run_claude("帮我看看有没有我不认识的商户扣款", dd)

        assert ai_mentioned(result,
            "神秘", "科技", "199", "未知", "unknown", "一次", "不认识",
            "only once", "陌生"
        ), f"Should flag unknown merchant. Got: {str(result)[:500]}"
