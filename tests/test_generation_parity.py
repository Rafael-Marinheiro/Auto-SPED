from __future__ import annotations

from copy import deepcopy

from main_fast import main as generate_legacy_sped
from sped_mensal.services.generation import generate_sped


class AnonymizedEmptyPeriodProvider:
    provider_id = "anonymized-fixture"
    display_name = "Período anonimizável sem movimento"

    def get_company_info(self):
        return {
            "NOME": "EMPRESA EXEMPLO LTDA",
            "CNPJ": "12.345.678/0001-90",
            "UF": "SP",
            "IE": "123.456.789.000",
            "COD_MUN": "3550308",
            "IND_ATIV": "1",
            "COD_REC": "1210",
        }

    def get_accountant_info(self):
        return {
            "NOME": "CONTADOR EXEMPLO",
            "CPF": "123.456.789-01",
            "CRC": "SP000000",
            "COD_MUN": "3550308",
        }

    def get_participants(self):
        return []

    def get_products(self):
        return []

    def get_units(self):
        return []

    def get_invoices(self, start_date, end_date):
        return []

    def get_invoice_items(self, document_number):
        return []

    def get_invoice_items_by_ids(
        self, cod_mod, doc_id, venda_id, ind_oper=None, origem=None
    ):
        return []


class AnonymizedSalesPeriodProvider(AnonymizedEmptyPeriodProvider):
    display_name = "Período anonimizável com NF-e e NFC-e"

    def get_participants(self):
        return [
            {
                "COD_PART": "CLI001",
                "NOME": "CLIENTE EXEMPLO",
                "COD_PAIS": "01058",
                "CNPJ": "98.765.432/0001-10",
                "IE": "ISENTO",
                "COD_MUN": "2408102",
            }
        ]

    def get_products(self):
        return [
            {
                "COD_ITEM": "ITEM001",
                "DESCR_ITEM": "PRODUTO EXEMPLO",
                "UNID_INV": "UN",
                "TIPO_ITEM": "00",
                "COD_NCM": "22021000",
                "ALIQ_ICMS": "18.00",
            }
        ]

    def get_units(self):
        return [{"UNID": "UN", "DESCR": "UNIDADE"}]

    def get_invoices(self, start_date, end_date):
        return deepcopy(
            [
                {
                    "DOC_ID": "101",
                    "VENDA_ID": "201",
                    "IND_OPER": "1",
                    "COD_PART": "CLI001",
                    "COD_MOD": "55",
                    "COD_SIT": "00",
                    "SER": "1",
                    "NUM_DOC": "1001",
                    "CHV_NFE": "",
                    "DT_DOC": "20260110",
                    "DT_E_S": "20260110",
                    "VL_DOC": "100.00",
                    "VL_MERC": "100.00",
                    "VL_BC_ICMS": "100.00",
                    "VL_ICMS": "18.00",
                },
                {
                    "DOC_ID": "102",
                    "VENDA_ID": "202",
                    "IND_OPER": "1",
                    "COD_PART": "",
                    "COD_MOD": "65",
                    "COD_SIT": "00",
                    "SER": "1",
                    "NUM_DOC": "1002",
                    "CHV_NFE": "",
                    "DT_DOC": "20260111",
                    "DT_E_S": "20260111",
                    "VL_DOC": "50.00",
                    "VL_MERC": "50.00",
                    "VL_BC_ICMS": "50.00",
                    "VL_ICMS": "9.00",
                },
            ]
        )

    def get_invoice_items_by_ids(
        self, cod_mod, doc_id, venda_id, ind_oper=None, origem=None
    ):
        if str(cod_mod) == "55" and str(doc_id) == "101":
            return deepcopy(
                [
                    {
                        "COD_ITEM": "ITEM001",
                        "QTD": "1.000",
                        "UNID": "UN",
                        "VL_ITEM": "100.00",
                        "VL_TOTAL": "100.00",
                        "VL_DESC": "0.00",
                        "CST_ICMS": "000",
                        "CFOP": "5102",
                        "VL_BC_ICMS": "100.00",
                        "ALIQ_ICMS": "18.00",
                        "VL_ICMS": "18.00",
                        "CST_IPI": "99",
                        "VL_IPI": "0.00",
                        "CST_PIS": "01",
                        "VL_BC_PIS": "100.00",
                        "ALIQ_PIS": "1.65",
                        "VL_PIS": "1.65",
                        "CST_COFINS": "01",
                        "VL_BC_COFINS": "100.00",
                        "ALIQ_COFINS": "7.60",
                        "VL_COFINS": "7.60",
                    }
                ]
            )
        return []


class AnonymizedPurchasePeriodProvider(AnonymizedSalesPeriodProvider):
    display_name = "Período anonimizável com compra"

    def get_invoices(self, start_date, end_date):
        return deepcopy(
            [
                {
                    "DOC_ID": "301",
                    "VENDA_ID": "",
                    "IND_OPER": "0",
                    "ORIGEM": "COMPRA",
                    "COD_PART": "CLI001",
                    "COD_MOD": "55",
                    "COD_SIT": "00",
                    "SER": "1",
                    "NUM_DOC": "2001",
                    "CHV_NFE": "",
                    "DT_DOC": "20260112",
                    "DT_E_S": "20260112",
                    "VL_DOC": "80.00",
                    "VL_MERC": "80.00",
                    "VL_BC_ICMS": "80.00",
                    "VL_ICMS": "14.40",
                }
            ]
        )

    def get_invoice_items_by_ids(
        self, cod_mod, doc_id, venda_id, ind_oper=None, origem=None
    ):
        if str(cod_mod) == "55" and str(doc_id) == "301":
            item = super().get_invoice_items_by_ids("55", "101", "201")[0]
            item.update(
                {
                    "VL_ITEM": "80.00",
                    "VL_TOTAL": "80.00",
                    "CFOP": "1102",
                    "VL_BC_ICMS": "80.00",
                    "ALIQ_ICMS": "18.00",
                    "VL_ICMS": "14.40",
                    "CST_IPI": "49",
                    "VL_BC_PIS": "80.00",
                    "VL_PIS": "1.32",
                    "VL_BC_COFINS": "80.00",
                    "VL_COFINS": "6.08",
                }
            )
            return [item]
        return []


def test_new_generation_matches_legacy_for_anonymized_empty_period(
    tmp_path, monkeypatch
):
    provider = AnonymizedEmptyPeriodProvider()
    monkeypatch.setattr("main_fast.SpedDataExtractor", lambda *args, **kwargs: provider)
    legacy_path = tmp_path / "legacy.txt"
    new_path = tmp_path / "new.txt"

    generate_legacy_sped(
        "ANONYMIZED.FDB", "2026-01-01", "2026-01-31", legacy_path
    )
    generate_sped(provider, "2026-01-01", "2026-01-31", new_path)

    legacy_lines = legacy_path.read_text(encoding="utf-8").splitlines()
    new_lines = new_path.read_text(encoding="utf-8").splitlines()
    assert new_lines == legacy_lines


def test_new_generation_matches_legacy_for_anonymized_nfe_and_nfce_period(
    tmp_path, monkeypatch
):
    legacy_provider = AnonymizedSalesPeriodProvider()
    new_provider = AnonymizedSalesPeriodProvider()
    monkeypatch.setattr(
        "main_fast.SpedDataExtractor", lambda *args, **kwargs: legacy_provider
    )
    legacy_path = tmp_path / "legacy-sales.txt"
    new_path = tmp_path / "new-sales.txt"

    generate_legacy_sped(
        "ANONYMIZED.FDB", "2026-01-01", "2026-01-31", legacy_path
    )
    generate_sped(new_provider, "2026-01-01", "2026-01-31", new_path)

    legacy_lines = legacy_path.read_text(encoding="utf-8").splitlines()
    new_lines = new_path.read_text(encoding="utf-8").splitlines()
    assert new_lines == legacy_lines
    assert sum(line.startswith("|C100|") for line in new_lines) == 2
    assert sum(line.startswith("|C190|") for line in new_lines) == 2
    assert any(line.startswith("|E110|27,00|") for line in new_lines)


def test_new_generation_matches_legacy_for_anonymized_purchase_period(
    tmp_path, monkeypatch
):
    legacy_provider = AnonymizedPurchasePeriodProvider()
    new_provider = AnonymizedPurchasePeriodProvider()
    monkeypatch.setattr(
        "main_fast.SpedDataExtractor", lambda *args, **kwargs: legacy_provider
    )
    legacy_path = tmp_path / "legacy-purchase.txt"
    new_path = tmp_path / "new-purchase.txt"

    generate_legacy_sped(
        "ANONYMIZED.FDB", "2026-01-01", "2026-01-31", legacy_path
    )
    generate_sped(new_provider, "2026-01-01", "2026-01-31", new_path)

    legacy_lines = legacy_path.read_text(encoding="utf-8").splitlines()
    new_lines = new_path.read_text(encoding="utf-8").splitlines()
    assert new_lines == legacy_lines
    assert sum(line.startswith("|C170|") for line in new_lines) == 1
    assert any(
        line.startswith("|E110|0,00|0,00|0,00|0,00|14,40|")
        for line in new_lines
    )
