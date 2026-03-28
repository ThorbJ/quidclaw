"""E2E tests: Reconciliation and data completeness scenarios."""

import pytest
from datetime import date
from tests.e2e.conftest import copy_fixture_to_inbox
from tests.e2e.helpers import (
    run_claude, load_ledger, count_transactions, ai_mentioned,
)


@pytest.mark.e2e
class TestDataCompleteness:
    """AI should check data completeness before answering questions."""

    def test_no_data_no_fabrication(self, data_dir):
        """With empty ledger, AI should not fabricate a balance."""
        result = run_claude("我现在有多少钱？", data_dir)

        assert ai_mentioned(result,
            "没有数据", "no data", "还没有", "需要先",
            "没有记录", "初始化", "开始记账"
        ), f"AI should not answer with no data. Got: {result.get('result', '')[:300]}"

    def test_stale_data_caveat(self, data_dir_with_accounts):
        """If only partial data exists, AI should caveat its answer."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")

        # Single prompt: process inbox then answer about missing month
        result = run_claude(
            "先处理inbox的账单，然后告诉我2月花了多少钱？",
            dd, timeout=600
        )

        assert ai_mentioned(result,
            "没有2月", "缺少", "不完整", "no data for february", "missing",
            "没有记录", "february", "没有二月", "2月没有", "暂无数据",
            "没有任何2月"
        ), f"AI should note February data is missing. Got: {result.get('result', '')[:300]}"

    def test_unprocessed_inbox_warning(self, data_dir_with_accounts):
        """If inbox has unprocessed files, AI should either process them or warn."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")

        result = run_claude("我这个月花了多少？", dd, timeout=600)

        entries, _ = load_ledger(dd)
        txn_count = count_transactions(entries)

        # AI either processed the inbox (good!) or warned about it (also good)
        if txn_count > 0:
            pass  # AI processed the files first — correct behavior
        else:
            assert ai_mentioned(result,
                "inbox", "未处理", "unprocessed", "新文件",
                "待处理", "先处理", "先导入"
            ), f"AI should mention unprocessed files. Got: {result.get('result', '')[:300]}"


@pytest.mark.e2e
class TestBalanceReconciliation:
    """AI should detect balance mismatches."""

    def test_balance_mismatch_detected(self, data_dir_with_accounts):
        """Import data then check with a deliberately wrong balance."""
        dd = data_dir_with_accounts

        # Single combined prompt — import then check
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")
        result = run_claude(
            "先帮我处理inbox里的账单，然后帮我核对一下，"
            "我的银行卡余额应该是999999元，这个数字对吗？",
            dd, timeout=600
        )

        assert ai_mentioned(result,
            "不一致", "不匹配", "差异", "不对", "discrepancy",
            "mismatch", "不符", "对不上", "999999"
        ), f"AI should detect mismatch. Got: {str(result)[:500]}"
