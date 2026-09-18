"""Projeto-base copiável para novos conectores do Auto-SPED.

Substitua as coleções em memória por consultas somente leitura e mantenha a
interface pública. O núcleo continuará independente da tecnologia da origem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from sped_mensal.providers.base import CaptureMapping, FiscalDataProvider, FiscalRow
from sped_mensal.services.normalization import parse_fiscal_date


def _copy_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return dict(row)


def _copy_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [_copy_row(row) for row in rows]


def _same_value(left: Any, right: Any) -> bool:
    return str(left if left is not None else "") == str(right if right is not None else "")


@dataclass
class TemplateProvider:
    """Implementa o contrato com dados anônimos ou carregados por outro meio."""

    provider_id = "template"
    display_name = "Conector de exemplo"

    company: Mapping[str, Any] = field(default_factory=dict)
    accountant: Mapping[str, Any] = field(default_factory=dict)
    participants: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    products: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    units: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    invoices: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    invoice_items: Sequence[Mapping[str, Any]] = field(default_factory=tuple)

    def describe_capture(self) -> Sequence[CaptureMapping]:
        return (
            CaptureMapping(
                "empresa",
                "identificação",
                "SUA_FONTE.EMPRESA",
                ("0000", "0005"),
                "Troque pela tabela, endpoint ou arquivo real.",
            ),
            CaptureMapping(
                "documento",
                "cabeçalho fiscal",
                "SUA_FONTE.DOCUMENTOS",
                ("C100",),
            ),
            CaptureMapping(
                "item",
                "produto, quantidade, valor e tributação",
                "SUA_FONTE.ITENS",
                ("C170", "C190"),
            ),
        )

    def get_company_info(self) -> FiscalRow:
        return _copy_row(self.company)

    def get_accountant_info(self) -> FiscalRow:
        return _copy_row(self.accountant)

    def get_participants(self) -> Sequence[FiscalRow]:
        return _copy_rows(self.participants)

    def get_products(self) -> Sequence[FiscalRow]:
        return _copy_rows(self.products)

    def get_units(self) -> Sequence[FiscalRow]:
        return _copy_rows(self.units)

    def get_invoices(self, start_date: str, end_date: str) -> Sequence[FiscalRow]:
        start = parse_fiscal_date(start_date)
        end = parse_fiscal_date(end_date)
        if start is None or end is None or start > end:
            raise ValueError("período inválido; use datas AAAA-MM-DD")

        selected: list[Mapping[str, Any]] = []
        for invoice in self.invoices:
            issue_date = parse_fiscal_date(invoice.get("DT_DOC"))
            if issue_date is not None and start <= issue_date <= end:
                selected.append(invoice)
        return _copy_rows(selected)

    def get_invoice_items_by_ids(
        self,
        cod_mod: str,
        doc_id: str | int,
        venda_id: str | int,
        ind_oper: str | None = None,
        origem: str | None = None,
    ) -> Sequence[FiscalRow]:
        selected = []
        for item in self.invoice_items:
            if not _same_value(item.get("COD_MOD"), cod_mod):
                continue
            if not _same_value(item.get("DOC_ID"), doc_id):
                continue
            if not _same_value(item.get("VENDA_ID"), venda_id):
                continue
            if ind_oper is not None and not _same_value(item.get("IND_OPER"), ind_oper):
                continue
            if origem is not None and not _same_value(item.get("ORIGEM"), origem):
                continue
            selected.append(item)
        return _copy_rows(selected)


def assert_provider_contract(provider: object) -> None:
    """Falha cedo quando a classe copiada deixa de implementar o contrato."""

    if not isinstance(provider, FiscalDataProvider):
        raise TypeError("o conector não implementa FiscalDataProvider")
