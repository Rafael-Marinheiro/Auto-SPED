from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sped_mensal.writer import SpedWriter


class DummyExtractor:
    def get_invoice_items_by_ids(self, cod_mod, doc_id, venda_id):
        # Return items tied to DOC_ID for NFe (55) and none for NFC-e (65)
        if str(cod_mod) == "55" and str(doc_id) == "111":
            return [
                {
                    "NUM_ITEM": 1,
                    "COD_ITEM": "PROD001",
                    "QTD": "2.000",
                    "UNID": "UN",
                    "VL_ITEM": 100,
                    "VL_DESC": 0,
                    "CST_ICMS": "000",
                    "CFOP": "1102",
                    "VL_BC_ICMS": 100,
                    "ALIQ_ICMS": 18,
                    "VL_ICMS": 18,
                    "CST_IPI": "00",
                    "VL_IPI": 0,
                    "CST_PIS": "01",
                    "VL_BC_PIS": 100,
                    "ALIQ_PIS": 1.65,
                    "VL_PIS": 1.65,
                    "CST_COFINS": "01",
                    "VL_BC_COFINS": 100,
                    "ALIQ_COFINS": 7.6,
                    "VL_COFINS": 7.6,
                }
            ]
        return []


def parse(line: str) -> list[str]:
    return line.strip().strip("|").split("|")


def test_c170_items_match_invoice_by_id():
    writer = SpedWriter()

    company_info = {"NOME": "X", "CNPJ": "123", "UF": "SP", "IE": "", "COD_MUN": "3550308", "IND_ATIV": "1"}
    accountant_info = {"NOME": "Y", "CPF": "", "CRC": "", "CNPJ": "", "CEP": "", "END": "", "NUM": "", "COMPL": "", "BAIRRO": "", "FONE": "", "FAX": "", "EMAIL": "", "COD_MUN": "3550308"}
    participants = []
    products = [{
        "COD_ITEM": "PROD001",
        "DESCR_ITEM": "Produto Teste",
        "UNID_INV": "UN",
        "TIPO_ITEM": "00",
        "COD_NCM": "12345678",
        "ALIQ_ICMS": "18.00",
    }]
    units = [{"UNID": "UN", "DESCR": "UNIDADE"}]
    invoices = [
        {
            # NFe - deve gerar C170 com item PROD001
            "DOC_ID": "111",
            "VENDA_ID": "222",
            "IND_OPER": "0",
            "IND_EMIT": "1",
            "COD_PART": "",
            "COD_MOD": "55",
            "COD_SIT": "00",
            "SER": "1",
            "NUM_DOC": "5000",
            "CHV_NFE": "",
            "DT_DOC": "20240110",
            "DT_E_S": "20240110",
            "VL_DOC": 100,
            "IND_PGTO": "0",
            "VL_DESC": 0,
            "VL_ABAT_NT": 0,
            "VL_MERC": 100,
            "IND_FRT": "0",
            "VL_FRT": 0,
            "VL_SEG": 0,
            "VL_OUT_DA": 0,
            "VL_BC_ICMS": 100,
            "VL_ICMS": 18,
            "VL_BC_ICMS_ST": 0,
            "VL_ICMS_ST": 0,
            "VL_IPI": 0,
            "VL_PIS": 0,
            "VL_COFINS": 0,
            "VL_PIS_ST": 0,
            "VL_COFINS_ST": 0,
        },
        {
            # NFC-e - não deve gerar C170
            "DOC_ID": "333",
            "VENDA_ID": "444",
            "IND_OPER": "1",
            "IND_EMIT": "0",
            "COD_PART": "",
            "COD_MOD": "65",
            "COD_SIT": "00",
            "SER": "1",
            "NUM_DOC": "6000",
            "CHV_NFE": "",
            "DT_DOC": "20240110",
            "DT_E_S": "20240110",
            "VL_DOC": 50,
            "IND_PGTO": "0",
            "VL_DESC": 0,
            "VL_ABAT_NT": 0,
            "VL_MERC": 50,
            "IND_FRT": "0",
            "VL_FRT": 0,
            "VL_SEG": 0,
            "VL_OUT_DA": 0,
            "VL_BC_ICMS": 50,
            "VL_ICMS": 9,
            "VL_BC_ICMS_ST": 0,
            "VL_ICMS_ST": 0,
            "VL_IPI": 0,
            "VL_PIS": 0,
            "VL_COFINS": 0,
            "VL_PIS_ST": 0,
            "VL_COFINS_ST": 0,
        },
    ]

    extractor = DummyExtractor()

    writer.generate_sped_from_db(
        company_info=company_info,
        accountant_info=accountant_info,
        participants=participants,
        products=products,
        units=units,
        invoices=invoices,
        extractor=extractor,
        start_date="2024-01-01",
        end_date="2024-01-31",
    )

    lines = writer.to_lines()

    # Collect C170 lines
    c170 = [parse(l) for l in lines if l.startswith("|C170|")]
    # Deve ter apenas itens da NFe (55)
    assert len(c170) == 1
    assert c170[0][2] == "PROD001"

