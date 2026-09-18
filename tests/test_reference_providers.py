from pathlib import Path

import pytest

from sped_mensal.providers.base import FiscalDataProvider
from sped_mensal.providers.reference import (
    CsvDirectoryProvider,
    PostgresProvider,
    PostgresQueries,
    XmlFileProvider,
)


def test_csv_directory_provider_reads_canonical_files(tmp_path: Path):
    (tmp_path / "company.csv").write_text("NOME;CNPJ\nEMPRESA;00000000000000\n", encoding="utf-8")
    (tmp_path / "invoices.csv").write_text(
        "DOC_ID;VENDA_ID;COD_MOD;DT_DOC\n1;10;55;2026-08-15\n2;20;55;2026-09-01\n",
        encoding="utf-8",
    )
    (tmp_path / "invoice_items.csv").write_text(
        "DOC_ID;VENDA_ID;COD_MOD;COD_ITEM\n1;10;55;A\n",
        encoding="utf-8",
    )

    provider = CsvDirectoryProvider(tmp_path)

    assert isinstance(provider, FiscalDataProvider)
    assert provider.get_company_info()["NOME"] == "EMPRESA"
    assert [row["DOC_ID"] for row in provider.get_invoices("2026-08-01", "2026-08-31")] == ["1"]
    assert provider.get_invoice_items_by_ids("55", 1, "10")[0]["COD_ITEM"] == "A"


def test_xml_provider_reads_canonical_xml_and_rejects_dtd(tmp_path: Path):
    xml_path = tmp_path / "sped.xml"
    xml_path.write_text(
        """<auto-sped>
        <company NOME="EMPRESA"><CNPJ>00000000000000</CNPJ></company>
        <invoices><row DOC_ID="1" VENDA_ID="10" COD_MOD="55" DT_DOC="2026-08-15" /></invoices>
        <invoice_items><row DOC_ID="1" VENDA_ID="10" COD_MOD="55" COD_ITEM="A" /></invoice_items>
        </auto-sped>""",
        encoding="utf-8",
    )

    provider = XmlFileProvider(xml_path)

    assert isinstance(provider, FiscalDataProvider)
    assert provider.get_company_info()["CNPJ"] == "00000000000000"
    assert provider.get_invoices("2026-08-01", "2026-08-31")[0]["DOC_ID"] == "1"

    unsafe = tmp_path / "unsafe.xml"
    unsafe.write_text("<!DOCTYPE x [<!ENTITY y 'z'>]><auto-sped />", encoding="utf-8")
    with pytest.raises(ValueError, match="DTD"):
        XmlFileProvider(unsafe)


class _FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.description = None
        self._rows = []

    def execute(self, query, params=()):
        self.connection.executions.append((query, params))
        if query != "SET TRANSACTION READ ONLY":
            self.description = (("DOC_ID",), ("DT_DOC",))
            self._rows = [(1, "2026-08-15")]

    def fetchall(self):
        return self._rows

    def close(self):
        self.connection.cursor_closed = True


class _FakeConnection:
    def __init__(self):
        self.executions = []
        self.cursor_closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def cursor(self):
        return _FakeCursor(self)


def test_postgres_provider_uses_read_only_transaction_and_parameters():
    connection = _FakeConnection()
    queries = PostgresQueries(*(f"SELECT {name}" for name in (
        "company", "accountant", "participants", "products", "units", "invoices", "items"
    )))
    provider = PostgresProvider(
        "postgresql://example",
        queries,
        connection_factory=lambda _dsn: connection,
    )

    rows = provider.get_invoices("2026-08-01", "2026-08-31")

    assert isinstance(provider, FiscalDataProvider)
    assert rows == [{"DOC_ID": 1, "DT_DOC": "2026-08-15"}]
    assert connection.executions == [
        ("SET TRANSACTION READ ONLY", ()),
        ("SELECT invoices", ("2026-08-01", "2026-08-31")),
    ]
    assert connection.cursor_closed is True
