import datetime

from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.notes import NotesManager


def _setup(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    return config


def test_list_notes_empty(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    assert mgr.list_notes() == []


def test_write_and_read_note(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("assets/房产-xxx小区.md", "# 房产信息\n\n购买价格: 200万")
    content = mgr.read_note("assets/房产-xxx小区.md")
    assert "购买价格: 200万" in content


def test_write_note_creates_subdirectory(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("insurance/平安-重疾险.md", "保单内容")
    assert (config.notes_dir / "insurance" / "平安-重疾险.md").exists()


def test_list_notes_with_files(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("assets/房产.md", "content1")
    mgr.write_note("insurance/保险.md", "content2")
    notes = mgr.list_notes()
    assert len(notes) == 2
    paths = {n["path"] for n in notes}
    assert "assets/房产.md" in paths
    assert "insurance/保险.md" in paths


def test_read_nonexistent_note(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    import pytest
    with pytest.raises(FileNotFoundError):
        mgr.read_note("nope.md")


def test_overwrite_existing_note(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("test.md", "v1")
    mgr.write_note("test.md", "v2")
    assert mgr.read_note("test.md") == "v2"


# --- search_notes ---

def test_search_notes_finds_match(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("assets/house.md", "# My House\n\nMortgage rate is 3.1% with BOC\nMonthly payment: 8500")
    mgr.write_note("insurance/car.md", "# Car Insurance\n\nProvider: PICC\nPremium: 3000/year")

    results = mgr.search_notes("mortgage")
    assert len(results) >= 1
    assert any("house" in r["path"] for r in results)
    assert any("3.1%" in m for r in results for m in r["matches"])


def test_search_notes_case_insensitive(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("test.md", "BOC mortgage details")

    results = mgr.search_notes("boc")
    assert len(results) >= 1


def test_search_notes_no_match(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("test.md", "some content")

    results = mgr.search_notes("nonexistent")
    assert results == []


# --- append_note ---

def test_append_note_to_existing_section(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("house.md", "# House\n\n## History\n- 2024-06: Purchased\n\n## Notes\nSome notes")

    mgr.append_note("house.md", "History", "- 2026-03: Rent increased to 8000")

    content = mgr.read_note("house.md")
    assert "2024-06: Purchased" in content  # old content preserved
    assert "2026-03: Rent increased to 8000" in content  # new content added
    assert "## Notes" in content  # other sections preserved


def test_append_note_creates_section_if_missing(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("house.md", "# House\n\n## Key Facts\n- Price: 2M")

    mgr.append_note("house.md", "History", "- 2026-03: Something happened")

    content = mgr.read_note("house.md")
    assert "## History" in content
    assert "2026-03: Something happened" in content
    assert "## Key Facts" in content  # existing section preserved


def test_append_note_creates_file_if_missing(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)

    mgr.append_note("new-topic.md", "History", "- 2026-03: First entry")

    content = mgr.read_note("new-topic.md")
    assert "## History" in content
    assert "First entry" in content


# --- find_by_tag ---

def test_find_by_tag(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("house.md", "---\ntags: [房产, 贷款, BOC]\n---\n# House")
    mgr.write_note("car.md", "---\ntags: [车辆, 贷款]\n---\n# Car")
    mgr.write_note("insurance.md", "---\ntags: [保险]\n---\n# Insurance")

    results = mgr.find_by_tag("贷款")
    assert len(results) == 2
    paths = {r["path"] for r in results}
    assert "house.md" in paths
    assert "car.md" in paths


def test_find_by_tag_no_match(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("house.md", "---\ntags: [房产]\n---\n# House")

    results = mgr.find_by_tag("不存在")
    assert results == []


def test_find_by_tag_no_frontmatter(tmp_path):
    config = _setup(tmp_path)
    mgr = NotesManager(config)
    mgr.write_note("plain.md", "# Just a plain note\nNo frontmatter here")

    results = mgr.find_by_tag("anything")
    assert results == []


# --- find_related ---

def test_find_related_notes_and_documents(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()

    mgr = NotesManager(config)
    mgr.write_note("assets/house-xincheng.md", "# Xincheng House\nMortgage with BOC")

    # Put a document in documents/
    doc_dir = config.documents_dir / "2024" / "06"
    doc_dir.mkdir(parents=True)
    (doc_dir / "xincheng-购房合同-2024-06.pdf").write_bytes(b"fake")

    result = mgr.find_related("xincheng")
    assert len(result["notes"]) >= 1
    assert len(result["documents"]) >= 1


def test_find_related_with_transactions(tmp_path):
    from quidclaw.core.init import LedgerInitializer
    from quidclaw.core.transactions import TransactionManager

    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()
    LedgerInitializer(ledger).init_with_template()
    txn = TransactionManager(ledger)
    txn.add_transaction(
        date=datetime.date(2026, 3, 1), payee="BOC Mortgage", narration="Monthly payment",
        postings=[
            {"account": "Expenses:Housing", "amount": "8500", "currency": "CNY"},
            {"account": "Assets:Bank:Checking"},
        ],
    )

    mgr = NotesManager(config)
    mgr.write_note("assets/house.md", "# House\nMortgage with BOC, monthly 8500")

    result = mgr.find_related("BOC", ledger=ledger)
    assert len(result["notes"]) >= 1
    assert len(result["transactions"]) >= 1


def test_find_related_no_matches(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path)
    ledger = Ledger(config)
    ledger.init()

    mgr = NotesManager(config)
    result = mgr.find_related("nonexistent")
    assert result["notes"] == []
    assert result["documents"] == []
    assert result["transactions"] == []
