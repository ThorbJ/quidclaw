import datetime
from quidclaw.config import QuidClawConfig
from quidclaw.core.ledger import Ledger
from quidclaw.core.accounts import AccountManager
from quidclaw.core.documents import DocumentManager


def make_ledger(tmp_path):
    config = QuidClawConfig(data_dir=tmp_path / "testdata")
    ledger = Ledger(config)
    ledger.init()
    acct = AccountManager(ledger)
    acct.add_account("Liabilities:CreditCard:CMB:1234", currencies=["CNY"], open_date=datetime.date(2026, 1, 1))
    return ledger


def test_add_document(tmp_path):
    ledger = make_ledger(tmp_path)
    mgr = DocumentManager(ledger)
    # Create the actual file — Beancount validates document paths exist
    doc_path = ledger.config.data_dir / "documents" / "2026" / "03"
    doc_path.mkdir(parents=True, exist_ok=True)
    (doc_path / "招商银行-信用卡账单-2026-03.pdf").write_bytes(b"pdf")
    # Use absolute path for the directive
    abs_doc = str(doc_path / "招商银行-信用卡账单-2026-03.pdf")
    mgr.add_document(
        "Liabilities:CreditCard:CMB:1234",
        abs_doc,
        datetime.date(2026, 3, 15),
    )
    month_file = ledger.config.month_bean(2026, 3)
    content = month_file.read_text()
    assert "document Liabilities:CreditCard:CMB:1234" in content
    assert "招商银行-信用卡账单-2026-03.pdf" in content
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
    doc_entries = [e for e in entries if e.__class__.__name__ == "Document"]
    assert len(doc_entries) == 1


def test_add_document_default_date(tmp_path):
    ledger = make_ledger(tmp_path)
    mgr = DocumentManager(ledger)
    doc_file = ledger.config.documents_dir / "receipt.pdf"
    doc_file.write_bytes(b"pdf")
    mgr.add_document(
        "Liabilities:CreditCard:CMB:1234",
        str(doc_file),
    )
    entries, errors, _ = ledger.load()
    assert len(errors) == 0
