import pytest

from sped_mensal.providers.reference import CanonicalDatasetProvider
from sped_mensal.services.provider_certification import (
    assert_provider_certified,
    certify_provider,
)


def _valid_provider():
    return CanonicalDatasetProvider({
        "company": [{"NOME": "EMPRESA TESTE", "CNPJ": "00000000000000"}],
        "accountant": [{}],
        "participant": [],
        "product": [],
        "unit": [],
        "invoice": [{
            "DOC_ID": 1,
            "VENDA_ID": 10,
            "ORIGEM": "TESTE",
            "IND_OPER": "1",
            "COD_MOD": "55",
            "COD_SIT": "00",
            "SER": "1",
            "NUM_DOC": "100",
            "CHV_NFE": "1" * 44,
            "COD_PART": "P1",
            "DT_DOC": "2026-08-15",
        }],
        "invoice_item": [{
            "DOC_ID": 1,
            "VENDA_ID": 10,
            "ORIGEM": "TESTE",
            "IND_OPER": "1",
            "COD_MOD": "55",
            "COD_ITEM": "A",
        }],
    })


def test_certifies_valid_provider_and_serializes_report():
    report = assert_provider_certified(_valid_provider(), "2026-08-01", "2026-08-31")

    assert report.passed is True
    assert report.checked_documents == 1
    assert report.to_dict() == {
        "provider_id": "canonical-dataset",
        "passed": True,
        "checked_documents": 1,
        "findings": [],
    }


def test_reports_contract_and_fiscal_identity_errors():
    class NotAProvider:
        provider_id = "broken"

    contract_report = certify_provider(NotAProvider(), "2026-08-01", "2026-08-31")
    assert contract_report.passed is False
    assert contract_report.findings[0].code == "contract"

    provider = _valid_provider()
    provider._dataset["company"] = [{"NOME": ""}]
    report = certify_provider(provider, "2026-08-01", "2026-08-31")
    assert {finding.code for finding in report.findings} >= {"company-name", "company-document"}
    with pytest.raises(AssertionError, match="company-name"):
        assert_provider_certified(provider, "2026-08-01", "2026-08-31")


def test_reports_duplicates_and_out_of_period_documents():
    class LeakyProvider(CanonicalDatasetProvider):
        def get_invoices(self, start_date, end_date):
            return self._rows("invoice")

    valid = _valid_provider()
    provider = LeakyProvider(valid._dataset)
    invoice = dict(provider._dataset["invoice"][0])
    invoice["DOC_ID"] = 2
    invoice["DT_DOC"] = "2026-09-01"
    provider._dataset["invoice"].append(invoice)

    report = certify_provider(provider, "2026-08-01", "2026-08-31")

    codes = {finding.code for finding in report.findings}
    assert "invoice-period" in codes
    assert "invoice-duplicate" in codes


def test_rejects_invalid_certification_period_and_sample_size():
    with pytest.raises(ValueError, match="período"):
        certify_provider(_valid_provider(), "2026-09-01", "2026-08-01")
    with pytest.raises(ValueError, match="max_documents"):
        certify_provider(_valid_provider(), "2026-08-01", "2026-08-31", max_documents=0)
