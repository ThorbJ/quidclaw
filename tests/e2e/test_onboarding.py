"""E2E tests: New user onboarding scenarios."""

import pytest
from tests.e2e.helpers import run_claude, load_ledger, get_accounts


@pytest.mark.e2e
class TestOnboarding:
    """New user with empty data directory."""

    def test_fresh_start_creates_ledger(self, data_dir):
        """Asking to get started should create accounts."""
        run_claude("我想开始记账，帮我设置一下", data_dir)

        entries, _ = load_ledger(data_dir)
        accounts = get_accounts(entries)
        assert len(accounts) > 0, "Should have created accounts"

    def test_custom_banks_recognized(self, data_dir):
        """AI should create accounts for specific banks mentioned."""
        run_claude(
            "帮我开始记账。我有招商银行储蓄卡和工商银行信用卡，还经常用微信支付",
            data_dir
        )

        entries, _ = load_ledger(data_dir)
        accounts = get_accounts(entries)

        has_cmb = any("cmb" in a.lower() or "招商" in a.lower() or "zhaoshang" in a.lower()
                      for a in accounts)
        has_icbc = any("icbc" in a.lower() or "工商" in a.lower() or "gongshang" in a.lower()
                       for a in accounts)
        has_wechat = any("wechat" in a.lower() or "微信" in a.lower() or "weixin" in a.lower()
                         for a in accounts)

        assert has_cmb or has_icbc or has_wechat, (
            f"Should have created at least one named account. Got: {accounts}"
        )
