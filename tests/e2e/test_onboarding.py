"""E2E tests: New user onboarding scenarios.

Onboarding is an interview that captures the user's financial profile into
notes/. No accounts or transactions are created during onboarding — the ledger
structure is initialized but accounts are only created when real bank statements
arrive later.
"""

import pytest
from tests.e2e.helpers import run_claude, load_ledger, get_accounts, notes_count


@pytest.mark.e2e
class TestOnboarding:
    """New user with empty data directory."""

    def test_fresh_start_creates_ledger(self, data_dir):
        """Asking to get started should initialize ledger structure (no accounts)."""
        run_claude("我想开始记账，帮我设置一下", data_dir)

        # Ledger directory structure should exist
        assert (data_dir / "ledger" / "main.bean").exists(), "main.bean should exist"
        assert (data_dir / "ledger" / "accounts.bean").exists(), "accounts.bean should exist"

    def test_onboarding_saves_profile_to_notes(self, data_dir):
        """Onboarding info should be saved to notes, not to the ledger."""
        run_claude(
            "帮我开始记账。我叫小明，我有招商银行储蓄卡和工商银行信用卡，还经常用微信支付",
            data_dir
        )

        # Profile info should go to notes, NOT create accounts
        assert notes_count(data_dir) >= 1, (
            "Onboarding should save user profile to notes/"
        )
