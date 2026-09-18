from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

from sped_mensal.providers.base import FiscalDataProvider


def _load_template_module():
    path = Path(__file__).parents[1] / "examples" / "connectors" / "template_provider.py"
    spec = spec_from_file_location("auto_sped_template_provider", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_template_implements_contract_and_filters_capture():
    module = _load_template_module()
    provider = module.TemplateProvider(
        company={"NOME": "EMPRESA EXEMPLO", "CNPJ": "00000000000000"},
        invoices=(
            {"DOC_ID": 1, "VENDA_ID": 10, "COD_MOD": "55", "DT_DOC": "2026-01-31"},
            {"DOC_ID": 2, "VENDA_ID": 20, "COD_MOD": "55", "DT_DOC": "2026-02-01"},
        ),
        invoice_items=(
            {"DOC_ID": 1, "VENDA_ID": 10, "COD_MOD": "55", "COD_ITEM": "A"},
            {"DOC_ID": 2, "VENDA_ID": 20, "COD_MOD": "55", "COD_ITEM": "B"},
        ),
    )

    assert isinstance(provider, FiscalDataProvider)
    module.assert_provider_contract(provider)
    assert provider.get_company_info()["NOME"] == "EMPRESA EXEMPLO"
    assert [row["DOC_ID"] for row in provider.get_invoices("2026-01-01", "2026-01-31")] == [1]
    assert provider.get_invoice_items_by_ids("55", "1", 10)[0]["COD_ITEM"] == "A"
    assert provider.describe_capture()[0].sped_targets == ("0000", "0005")


def test_template_rejects_invalid_period():
    module = _load_template_module()
    provider = module.TemplateProvider()

    try:
        provider.get_invoices("2026-02-01", "2026-01-01")
    except ValueError as exc:
        assert "período inválido" in str(exc)
    else:
        raise AssertionError("período invertido deveria ser rejeitado")
