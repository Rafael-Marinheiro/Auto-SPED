"""Capturador do ERP São Pedro armazenado em Firebird.

Este adaptador preserva a lógica e as consultas já homologadas em
``SpedDataExtractor``. Ele é a referência para futuros conectores de outros
ERPs, bancos ou APIs.
"""

from __future__ import annotations

from typing import Any, Sequence

from ..database import SpedDataExtractor
from .base import CaptureMapping, FiscalDataProvider


class FirebirdSaoPedroProvider(FiscalDataProvider):
    """Traduz o banco Firebird atual para o contrato fiscal compartilhado."""

    provider_id = "firebird-sao-pedro"
    display_name = "Firebird — ERP São Pedro"

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self._extractor = SpedDataExtractor(database_path)

    def describe_capture(self) -> Sequence[CaptureMapping]:
        return (
            CaptureMapping("empresa", "identificação", "EMPRESA", ("0000", "0005")),
            CaptureMapping("contador", "dados cadastrais", "CONTADOR", ("0100",)),
            CaptureMapping("participante", "cadastro", "PESSOA", ("0150",)),
            CaptureMapping("produto", "cadastro e tributação", "PRODUTO", ("0190", "0200")),
            CaptureMapping("NF-e", "cabeçalho", "NFE_MASTER", ("C100",)),
            CaptureMapping("NFC-e", "cabeçalho", "NFCE_MASTER", ("C100", "C190")),
            CaptureMapping("compra", "cabeçalho", "COMPRA", ("C100",)),
            CaptureMapping("item NF-e", "tributação", "NFE_DETALHE", ("C170", "C190")),
            CaptureMapping("item NFC-e", "tributação", "NFCE_DETALHE", ("C190",)),
            CaptureMapping("item compra", "tributação", "COMPRA_ITENS", ("C170", "C190")),
        )

    def get_company_info(self) -> dict[str, Any]:
        return self._extractor.get_company_info()

    def get_accountant_info(self) -> dict[str, Any]:
        return self._extractor.get_accountant_info()

    def get_participants(self) -> list[dict[str, Any]]:
        return self._extractor.get_participants()

    def get_products(self) -> list[dict[str, Any]]:
        return self._extractor.get_products()

    def get_units(self) -> list[dict[str, Any]]:
        return self._extractor.get_units()

    def get_invoices(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        return self._extractor.get_invoices(start_date, end_date)

    def get_invoice_items_by_ids(
        self,
        cod_mod: str,
        doc_id: str | int,
        venda_id: str | int,
        ind_oper: str | None = None,
        origem: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._extractor.get_invoice_items_by_ids(
            cod_mod, doc_id, venda_id, ind_oper, origem
        )
