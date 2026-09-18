from sped_mensal.services.normalization import (
    digits_only,
    normalize_access_key,
    normalize_cest,
    normalize_cfop,
    normalize_cst,
    normalize_municipality_code,
    normalize_ncm,
    normalize_person_ids,
    parse_fiscal_date,
    parse_sped_decimal,
    normalize_tax_rate,
    normalize_tipo_item,
    normalize_sped_date,
    normalize_document_status,
    normalize_fiscal_item_mapping,
    normalize_ipi_cst,
    normalize_product_mapping,
    format_sped_money,
    format_sped_decimal,
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


def test_places_cnpj_and_cpf_in_their_correct_fields():
    assert normalize_person_ids("12.345.678/0001-90", "") == (
        "12345678000190",
        "",
    )
    assert normalize_person_ids("123.456.789-01", "") == (
        "",
        "12345678901",
    )
    assert normalize_person_ids("", "12.345.678/0001-90") == (
        "12345678000190",
        "",
    )
    assert normalize_person_ids("inválido", "123.456.789-01") == (
        "",
        "12345678901",
    )


def test_normalizes_municipality_code_and_invoice_access_key():
    access_key = "3526 0912 3456 7800 0190 5500 1000 0001 2312 3456 7890"

    assert normalize_municipality_code("35.503-08") == "3550308"
    assert normalize_municipality_code("0") == ""
    assert normalize_access_key(access_key) == "35260912345678000190550010000001231234567890"
    assert normalize_access_key("123") == ""


def test_normalizes_dates_used_by_sped_records():
    assert normalize_sped_date("2026-09-17") == "17092026"
    assert normalize_sped_date("17/09/2026") == "17092026"
    assert normalize_sped_date(None) == ""


def test_maps_legacy_document_statuses():
    assert normalize_document_status("cancelada") == "02"
    assert normalize_document_status("DENEGADO") == "04"
    assert normalize_document_status("inutilizada") == "05"
    assert normalize_document_status("autorizada") == "00"
    assert normalize_document_status("07") == "07"


def test_formats_sped_money_with_brazilian_input_and_two_decimals():
    assert format_sped_money("1.234,565") == "1234.57"
    assert format_sped_money(None) == "0.00"
    assert format_sped_money("inválido") == "0.00"


def test_parses_fiscal_dates_for_period_comparison():
    assert parse_fiscal_date("2026-09-17").isoformat() == "2026-09-17"
    assert parse_fiscal_date("17092026").isoformat() == "2026-09-17"
    assert parse_fiscal_date("inválida") is None


def test_parses_decimal_values_shared_by_legacy_adjustments():
    assert str(parse_sped_decimal("1.234,56")) == "1234.56"
    assert str(parse_sped_decimal("18.50")) == "18.50"
    assert str(parse_sped_decimal("inválido")) == "0"
    assert format_sped_decimal("1.234,5") == "1234,50"
    assert format_sped_decimal("2,675") == "2,68"
    assert format_sped_decimal("1,005") == "1,01"
    assert format_sped_decimal("1,2345", decimal_places=3) == "1,235"


def test_rejects_invalid_sped_decimal_scale():
    try:
        format_sped_decimal("1", decimal_places=-1)
    except ValueError as exc:
        assert "decimal_places" in str(exc)
    else:
        raise AssertionError("escala negativa deveria ser rejeitada")


def test_normalizes_product_mapping_without_mutating_the_source():
    source = {
        "COD_ITEM": "1",
        "DESCR_ITEM": " PRODUTO ",
        "UNID_INV": " UN ",
        "TIPO_ITEM": "0",
        "COD_NCM": "2202.10.00",
        "CEST": "03.012.34",
        "ALIQ_ICMS": "18,5",
    }

    normalized = normalize_product_mapping(source)

    assert normalized == {
        "COD_ITEM": "1",
        "DESCR_ITEM": "PRODUTO",
        "UNID_INV": "UN",
        "TIPO_ITEM": "00",
        "COD_NCM": "22021000",
        "CEST": "0301234",
        "ALIQ_ICMS": "18.50",
    }
    assert source["DESCR_ITEM"] == " PRODUTO "


def test_normalizes_item_codes_and_ipi_direction_rule():
    source = {"CFOP": "5102", "CST_ICMS": "60", "CST_IPI": "50"}

    normalized = normalize_fiscal_item_mapping(source)

    assert normalized["CFOP"] == "5102"
    assert normalized["CST_ICMS"] == "060"
    assert normalized["CST_IPI"] == "99"
    assert normalize_ipi_cst("99", "1102") == "00"
    assert normalize_ipi_cst("", "5102") is None
