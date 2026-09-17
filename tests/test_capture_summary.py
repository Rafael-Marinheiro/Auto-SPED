from decimal import Decimal

from sped_mensal.services import build_capture_summary


class SummaryProvider:
    provider_id = "summary"

    def get_company_info(self): return {"NOME": "Empresa", "CNPJ": "1", "UF": "RN", "IE": "", "COD_MUN": "2402709"}
    def get_products(self): return [{}, {}]
    def get_participants(self): return [{}]
    def get_invoices(self, start_date, end_date): return [{"NUM_DOC": "1", "VL_DOC": "10"}, {"NUM_DOC": "2", "VL_DOC": "2,50"}]


def test_capture_summary_is_read_only_and_ready_for_a_ui():
    summary = build_capture_summary(SummaryProvider(), "2026-08-01", "2026-08-31")

    assert summary.document_count == 2
    assert summary.document_total == Decimal("12.50")
    assert summary.product_count == 2
    assert summary.to_dict()["document_total"] == "12.50"
