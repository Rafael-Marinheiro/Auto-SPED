"""Adaptadores de referência para arquivos canônicos e PostgreSQL."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
import xml.etree.ElementTree as ET

from .base import CaptureMapping, FiscalRow
from ..services.declarative_mapping import DeclarativeMapping
from ..services.normalization import parse_fiscal_date


_FILE_ENTITIES = {
    "company": "company",
    "accountant": "accountant",
    "participants": "participant",
    "products": "product",
    "units": "unit",
    "invoices": "invoice",
    "invoice_items": "invoice_item",
}


def _copy_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _same(left: Any, right: Any) -> bool:
    return str(left if left is not None else "") == str(right if right is not None else "")


class CanonicalDatasetProvider:
    """Implementa o contrato sobre um conjunto de entidades em memória."""

    provider_id = "canonical-dataset"
    display_name = "Conjunto de dados canônico"

    def __init__(
        self,
        dataset: Mapping[str, Sequence[Mapping[str, Any]]],
        mapping: DeclarativeMapping | None = None,
    ) -> None:
        self._mapping = mapping
        self._dataset = {
            entity: self._map_rows(entity, rows)
            for entity, rows in dataset.items()
        }

    def _map_rows(
        self,
        entity: str,
        rows: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        if self._mapping is not None and entity in self._mapping.entities:
            return self._mapping.map_rows(entity, rows)
        return _copy_rows(rows)

    def _rows(self, entity: str) -> list[dict[str, Any]]:
        return _copy_rows(self._dataset.get(entity, ()))

    def describe_capture(self) -> Sequence[CaptureMapping]:
        return (
            CaptureMapping("empresa", "identificação", "dataset.company", ("0000", "0005")),
            CaptureMapping("participante", "cadastro", "dataset.participant", ("0150",)),
            CaptureMapping("produto", "cadastro", "dataset.product", ("0200",)),
            CaptureMapping("documento", "cabeçalho", "dataset.invoice", ("C100",)),
            CaptureMapping("item", "item e tributação", "dataset.invoice_item", ("C170", "C190")),
        )

    def get_company_info(self) -> FiscalRow:
        rows = self._rows("company")
        return rows[0] if rows else {}

    def get_accountant_info(self) -> FiscalRow:
        rows = self._rows("accountant")
        return rows[0] if rows else {}

    def get_participants(self) -> Sequence[FiscalRow]:
        return self._rows("participant")

    def get_products(self) -> Sequence[FiscalRow]:
        return self._rows("product")

    def get_units(self) -> Sequence[FiscalRow]:
        return self._rows("unit")

    def get_invoices(self, start_date: str, end_date: str) -> Sequence[FiscalRow]:
        start = parse_fiscal_date(start_date)
        end = parse_fiscal_date(end_date)
        if start is None or end is None or start > end:
            raise ValueError("período inválido; use datas AAAA-MM-DD")
        return [
            row
            for row in self._rows("invoice")
            if (issue_date := parse_fiscal_date(row.get("DT_DOC"))) is not None
            and start <= issue_date <= end
        ]

    def get_invoice_items_by_ids(
        self,
        cod_mod: str,
        doc_id: str | int,
        venda_id: str | int,
        ind_oper: str | None = None,
        origem: str | None = None,
    ) -> Sequence[FiscalRow]:
        selected = []
        for row in self._rows("invoice_item"):
            if not _same(row.get("COD_MOD"), cod_mod):
                continue
            if not _same(row.get("DOC_ID"), doc_id) or not _same(row.get("VENDA_ID"), venda_id):
                continue
            if ind_oper is not None and not _same(row.get("IND_OPER"), ind_oper):
                continue
            if origem is not None and not _same(row.get("ORIGEM"), origem):
                continue
            selected.append(row)
        return selected


class CsvDirectoryProvider(CanonicalDatasetProvider):
    """Lê um diretório de CSVs, um por entidade fiscal."""

    provider_id = "csv-directory"
    display_name = "Diretório CSV canônico"

    def __init__(
        self,
        directory: str | Path,
        mapping: DeclarativeMapping | None = None,
        *,
        encoding: str = "utf-8-sig",
        delimiter: str = ";",
    ) -> None:
        base = Path(directory)
        if not base.is_dir():
            raise FileNotFoundError(f"diretório CSV não encontrado: {base}")
        dataset: dict[str, list[dict[str, str]]] = {}
        for filename, entity in _FILE_ENTITIES.items():
            path = base / f"{filename}.csv"
            if not path.exists():
                dataset[entity] = []
                continue
            with path.open("r", encoding=encoding, newline="") as stream:
                dataset[entity] = [dict(row) for row in csv.DictReader(stream, delimiter=delimiter)]
        super().__init__(dataset, mapping)


class XmlFileProvider(CanonicalDatasetProvider):
    """Lê XML canônico simples, sem DTD nem entidades externas."""

    provider_id = "xml-file"
    display_name = "Arquivo XML canônico"

    def __init__(
        self,
        path: str | Path,
        mapping: DeclarativeMapping | None = None,
        *,
        max_bytes: int = 50 * 1024 * 1024,
    ) -> None:
        xml_path = Path(path)
        content = xml_path.read_bytes()
        if len(content) > max_bytes:
            raise ValueError("arquivo XML excede o limite configurado")
        upper_content = content.upper()
        if b"<!DOCTYPE" in upper_content or b"<!ENTITY" in upper_content:
            raise ValueError("DTD e entidades não são permitidas no XML")
        root = ET.fromstring(content)
        if root.tag != "auto-sped":
            raise ValueError("raiz XML esperada: <auto-sped>")

        dataset: dict[str, list[dict[str, str]]] = {}
        for container_name, entity in _FILE_ENTITIES.items():
            container = root.find(container_name)
            if container is None:
                dataset[entity] = []
                continue
            if container_name in {"company", "accountant"}:
                dataset[entity] = [_xml_row(container)]
            else:
                dataset[entity] = [_xml_row(row) for row in container.findall("row")]
        super().__init__(dataset, mapping)


def _xml_row(element: ET.Element) -> dict[str, str]:
    row = dict(element.attrib)
    for child in element:
        if child.tag == "field" and child.get("name"):
            row[child.get("name", "")] = child.text or ""
        else:
            row[child.tag] = child.text or ""
    return row


@dataclass(frozen=True)
class PostgresQueries:
    """Consultas parametrizadas exigidas pelo adaptador PostgreSQL."""

    company: str
    accountant: str
    participants: str
    products: str
    units: str
    invoices: str
    invoice_items: str


ConnectionFactory = Callable[[str], Any]


class PostgresProvider:
    """Adaptador DB-API com transações explicitamente somente leitura."""

    provider_id = "postgresql"
    display_name = "PostgreSQL"

    def __init__(
        self,
        dsn: str,
        queries: PostgresQueries,
        mapping: DeclarativeMapping | None = None,
        connection_factory: ConnectionFactory | None = None,
    ) -> None:
        self._dsn = dsn
        self._queries = queries
        self._mapping = mapping
        self._connection_factory = connection_factory or _psycopg_connect

    def describe_capture(self) -> Sequence[CaptureMapping]:
        return (
            CaptureMapping("empresa", "identificação", "PostgreSQL: company", ("0000", "0005")),
            CaptureMapping("participante", "cadastro", "PostgreSQL: participants", ("0150",)),
            CaptureMapping("produto", "cadastro", "PostgreSQL: products", ("0200",)),
            CaptureMapping("documento", "cabeçalho", "PostgreSQL: invoices", ("C100",)),
            CaptureMapping("item", "item e tributação", "PostgreSQL: invoice_items", ("C170", "C190")),
        )

    def _fetch(self, entity: str, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._connection_factory(self._dsn) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute(query, params)
                columns = [description[0] for description in cursor.description or ()]
                rows = []
                for raw_row in cursor.fetchall():
                    rows.append(dict(raw_row) if isinstance(raw_row, Mapping) else dict(zip(columns, raw_row)))
            finally:
                cursor.close()
        if self._mapping is not None and entity in self._mapping.entities:
            return self._mapping.map_rows(entity, rows)
        return rows

    def get_company_info(self) -> FiscalRow:
        rows = self._fetch("company", self._queries.company)
        return rows[0] if rows else {}

    def get_accountant_info(self) -> FiscalRow:
        rows = self._fetch("accountant", self._queries.accountant)
        return rows[0] if rows else {}

    def get_participants(self) -> Sequence[FiscalRow]:
        return self._fetch("participant", self._queries.participants)

    def get_products(self) -> Sequence[FiscalRow]:
        return self._fetch("product", self._queries.products)

    def get_units(self) -> Sequence[FiscalRow]:
        return self._fetch("unit", self._queries.units)

    def get_invoices(self, start_date: str, end_date: str) -> Sequence[FiscalRow]:
        return self._fetch("invoice", self._queries.invoices, (start_date, end_date))

    def get_invoice_items_by_ids(
        self,
        cod_mod: str,
        doc_id: str | int,
        venda_id: str | int,
        ind_oper: str | None = None,
        origem: str | None = None,
    ) -> Sequence[FiscalRow]:
        return self._fetch(
            "invoice_item",
            self._queries.invoice_items,
            (cod_mod, doc_id, venda_id, ind_oper, origem),
        )


def _psycopg_connect(dsn: str) -> Any:
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "instale o suporte PostgreSQL com: pip install -e '.[postgres]'"
        ) from exc
    return psycopg.connect(dsn)
