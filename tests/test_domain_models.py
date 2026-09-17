from decimal import Decimal

from sped_mensal.domain import Company, FiscalDocument, FiscalItem


def test_typed_models_convert_the_current_fiscal_mapping():
    company = Company.from_mapping({"NOME": "Empresa", "CNPJ": "12", "UF": "RN", "IE": "1", "COD_MUN": "2402709"})
    document = FiscalDocument.from_mapping({
        "DOC_ID": 1, "ORIGEM": "COMPRA", "IND_OPER": 0, "COD_MOD": 55,
        "SER": 1, "NUM_DOC": 10, "VL_DOC": "1.234,56", "VL_MERC": "1200",
        "CST_ICMS": "00", "CFOP": "1102", "ALIQ_ICMS": "20,00", "VL_ICMS": "240",
    })
    item = FiscalItem.from_mapping({"NUM_ITEM": 1, "COD_ITEM": 2, "QTD": "3", "UNID": "UN", "VL_ITEM": "10,5", "CST_ICMS": "60", "CFOP": "1102"})

    assert company.name == "Empresa"
    assert document.total == Decimal("1234.56")
    assert document.taxes.cfop == "1102"
    assert item.quantity == Decimal("3")
    assert item.total == Decimal("10.5")
