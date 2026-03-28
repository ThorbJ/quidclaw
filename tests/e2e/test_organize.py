"""E2E tests: File organization scenarios."""

import pytest
from tests.e2e.conftest import copy_fixture_to_inbox
from tests.e2e.helpers import (
    run_claude, inbox_is_empty, documents_count, notes_count, list_files,
)


@pytest.mark.e2e
class TestFileOrganization:
    """AI should organize inbox files into documents/."""

    def test_file_moved_to_documents(self, data_dir_with_accounts):
        """After processing, file should be in documents/ not inbox/."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")

        run_claude("请帮我整理inbox里的文件", dd)

        assert inbox_is_empty(dd), "Inbox should be empty"
        assert documents_count(dd) >= 1, "File should be in documents/"

    def test_documents_organized_by_date(self, data_dir_with_accounts):
        """Files should be organized into YYYY/MM subdirectories."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "csv/cmb-credit-card-2026-03.csv")

        run_claude("请帮我整理inbox里的文件", dd)

        doc_files = list_files(dd / "documents")
        assert len(doc_files) >= 1, "At least one file should be archived to documents/"
        for f in doc_files:
            rel = f.relative_to(dd / "documents")
            parts = rel.parts
            assert len(parts) >= 2, (
                f"File should be in YYYY/MM/ structure, got: {rel}"
            )

    def test_insurance_document_processed(self, data_dir_with_accounts):
        """Insurance document should be processed — archived and/or key info extracted to notes."""
        dd = data_dir_with_accounts
        copy_fixture_to_inbox(dd, "text/insurance-summary.txt")

        run_claude("处理inbox里的文件，提取关键信息", dd)

        assert notes_count(dd) >= 1 or documents_count(dd) >= 1, (
            "Insurance document should be processed (note created or file archived)"
        )
