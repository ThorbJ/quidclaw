"""E2E tests: Phase 3 — Financial knowledge base."""

import pytest
from tests.e2e.conftest import copy_fixture_to_inbox
from tests.e2e.helpers import (
    run_claude, load_ledger, ai_mentioned, notes_count,
)


@pytest.mark.e2e
class TestFinancialMemory:
    """AI should capture financial info from conversations into notes."""

    def test_ai_captures_mortgage_info(self, data_dir_with_accounts):
        """Tell AI about mortgage — should create a note."""
        dd = data_dir_with_accounts

        run_claude(
            "我在xxx小区买了一套房，2024年6月买的，总价200万，"
            "中国银行贷款，利率3.1%，月供8500，贷款30年",
            dd
        )

        assert notes_count(dd) >= 1, "Should have created a note about the property"

    def test_ai_finds_info_from_notes(self, data_dir_with_accounts):
        """Create a note, then ask about it — AI should find the answer."""
        dd = data_dir_with_accounts

        # First: tell AI about insurance
        run_claude(
            "我有一份平安重疾险，保单号PA20230115001，年缴8600元，保额50万，"
            "2023年1月15号生效，缴费期20年，下次缴费日是2027年1月15号",
            dd
        )

        # Then: ask about it
        result = run_claude("我的保险什么时候需要续费？", dd)

        assert ai_mentioned(result,
            "2027", "1月", "january", "8600", "平安", "续费", "缴费"
        ), f"Should find insurance renewal info. Got: {str(result)[:500]}"


@pytest.mark.e2e
class TestCrossReference:
    """AI should find related info across notes, documents, and transactions."""

    def test_find_related_after_import_and_note(self, data_dir_with_accounts):
        """Import transactions + create note about same topic — AI should link them."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")

        # Import transactions and tell about a related fact
        run_claude(
            "先处理inbox的账单，然后记一下：星巴克是我每天上班路上买咖啡的地方，"
            "我的星巴克会员等级是金星级",
            dd
        )

        # Ask about Starbucks — should find both transaction and note
        result = run_claude("关于星巴克你知道些什么？", dd)

        assert ai_mentioned(result,
            "35.80", "金星", "咖啡", "会员", "starbucks"
        ), f"Should find both transaction and note info. Got: {str(result)[:500]}"
