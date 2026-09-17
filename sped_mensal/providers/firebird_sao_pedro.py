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
            CaptureMapping("empresa", "NOME", "EMPRESA.RAZAO", ("0000.NOME",)),
            CaptureMapping("empresa", "CNPJ", "EMPRESA.CNPJ", ("0000.CNPJ",)),
            CaptureMapping("empresa", "IE", "EMPRESA.IE", ("0000.IE",)),
            CaptureMapping("empresa", "COD_MUN", "EMPRESA.ID_CIDADE", ("0000.COD_MUN",)),
            CaptureMapping("empresa", "endereço", "EMPRESA.ENDERECO, NUMERO, BAIRRO", ("0005",)),
            CaptureMapping("contador", "dados cadastrais", "CONTADOR", ("0100",)),
            CaptureMapping("participante", "cadastro", "PESSOA", ("0150",)),
            CaptureMapping("produto", "cadastro e tributação", "PRODUTO", ("0190", "0200")),
            CaptureMapping("NF-e", "NUM_DOC", "NFE_MASTER.NUMERO", ("C100.NUM_DOC",)),
            CaptureMapping("NF-e", "chave", "NFE_MASTER.CHAVE", ("C100.CHV_NFE",)),
            CaptureMapping("NF-e", "valores", "NFE_MASTER.TOTAL, BASEICMS, TOTALICMS", ("C100",)),
            CaptureMapping("NFC-e", "NUM_DOC", "NFCE_MASTER.NUMERO", ("C100.NUM_DOC",)),
            CaptureMapping("NFC-e", "valores", "NFCE_MASTER.TOTAL, BASEICMS, TOTALICMS", ("C100", "C190")),
            CaptureMapping("compra", "NUM_DOC", "COMPRA.NR_NOTA", ("C100.NUM_DOC",)),
            CaptureMapping("compra", "datas e totais", "COMPRA.DTEMISSAO, DTENTRADA, TOTAL", ("C100",)),
            CaptureMapping("item NF-e", "produto e valor", "NFE_DETALHE.ID_PRODUTO, QTD, TOTAL", ("C170.COD_ITEM", "C170.QTD", "C170.VL_ITEM")),
            CaptureMapping("item NF-e", "tributação", "NFE_DETALHE.CST, CFOP, BASE_ICMS, ALIQ_ICMS, VALOR_ICMS", ("C170.CST_ICMS", "C170.CFOP", "C170", "C190")),
            CaptureMapping("item NFC-e", "tributação", "NFCE_DETALHE.CST, CFOP, BASE_ICMS, ALIQ_ICMS, VALOR_ICMS", ("C190",)),
            CaptureMapping("item compra", "produto e valor", "COMPRA_ITENS.FK_PRODUTO, QTD, TOTAL_COMPRA", ("C170.COD_ITEM", "C170.QTD", "C170.VL_ITEM")),
            CaptureMapping("item compra", "tributação", "COMPRA_ITENS.CST_ICM, CFOP, BASE_ICMS, ALIQ_ICMS, VL_ICMS", ("C170.CST_ICMS", "C170.CFOP", "C170", "C190")),
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
