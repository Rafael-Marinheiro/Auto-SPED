from sped_mensal.services.normalization import (
    digits_only,
    normalize_cest,
    normalize_cfop,
    normalize_cst,
    normalize_ncm,
    normalize_tax_rate,
    normalize_tipo_item,
)


def test_normalizes_fiscal_codes_without_changing_the_legacy_rules():
    assert digits_only("CFOP 1.102") == "1102"
    assert normalize_cfop("102") == "0102"
    assert normalize_cst("ICMS 60") == "060"
    assert normalize_cst("1234") == "234"
    assert normalize_tipo_item("tipo 100") == "00"
    assert normalize_ncm("2202.10.00") == "22021000"
    assert normalize_ncm("00000000") == ""
    assert normalize_cest("03.012.34") == "0301234"


def test_normalizes_rates_using_brazilian_decimal_notation():
    assert normalize_tax_rate("17,5") == "17.50"
    assert normalize_tax_rate("1.234,56") == "1234.56"
    assert normalize_tax_rate("inválido") == ""
