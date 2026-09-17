from sped_mensal.validation import ValidationSeverity, validate_provider


class InvalidProvider:
    provider_id = "fake"

    def get_products(self):
        return [{"COD_ITEM": "", "UNID_INV": "", "COD_NCM": "123"}]

    def get_invoices(self, start_date, end_date):
        return [
            {
                "DOC_ID": "1", "VENDA_ID": "1", "ORIGEM": "COMPRA", "IND_OPER": "0",
                "NUM_DOC": "", "COD_MOD": "55", "COD_SIT": "00", "SER": "1", "CHV_NFE": "", "COD_PART": "1",
                "VL_DOC": "10", "VL_MERC": "10", "VL_BC_ICMS": "0", "VL_ICMS": "0",
            },
            {
                "DOC_ID": "2", "VENDA_ID": "2", "ORIGEM": "COMPRA", "IND_OPER": "0",
                "NUM_DOC": "", "COD_MOD": "55", "COD_SIT": "00", "SER": "1", "CHV_NFE": "", "COD_PART": "1",
                "VL_DOC": "10", "VL_MERC": "10", "VL_BC_ICMS": "0", "VL_ICMS": "0",
            },
        ]

    def get_invoice_items_by_ids(self, cod_mod, doc_id, venda_id, ind_oper=None, origem=None):
        return [{"NUM_ITEM": 1, "COD_ITEM": "P", "QTD": 1, "UNID": "UN", "VL_ITEM": 10, "CST_ICMS": "", "CFOP": "102"}]


def test_preflight_reports_source_and_sped_fields():
    report = validate_provider(InvalidProvider(), "2026-08-01", "2026-08-31")

    codes = {issue.code for issue in report.issues}
    assert report.error_count >= 6
    assert "invoice.number.required" in codes
    assert "invoice.key.duplicate" in codes
    assert "item.cst.required" in codes
    assert "item.cfop.invalid" in codes
    assert any(issue.severity == ValidationSeverity.ERROR for issue in report.issues)
