from __future__ import annotations

from datetime import date

import pytest

from sped_mensal.services.fiscal_versioning import (
    SUPPORTED_LAYOUT_VERSIONS,
    normalize_layout_version,
    resolve_fiscal_rule_set,
    resolve_layout_version,
)
from sped_mensal.writer import SpedWriter


@pytest.mark.parametrize(
    ("period", "expected"),
    [
        (("2024-01-01", "2024-12-31"), "018"),
        (("2025-01-01", "2025-12-31"), "019"),
        (("2026-01-01", "2026-12-31"), "020"),
    ],
)
def test_resolves_layout_from_period(period, expected):
    assert resolve_layout_version(*period) == expected


def test_catalog_exposes_supported_versions_in_order():
    assert SUPPORTED_LAYOUT_VERSIONS == ("018", "019", "020")


def test_normalizes_short_explicit_version():
    assert normalize_layout_version("20") == "020"


def test_rejects_explicit_layout_incompatible_with_period():
    with pytest.raises(ValueError, match="não é válido"):
        resolve_fiscal_rule_set("2026-08-01", "2026-08-31", "019")


def test_rejects_period_across_rule_sets():
    with pytest.raises(ValueError, match="único conjunto"):
        resolve_fiscal_rule_set("2025-12-01", "2026-01-31")


def test_rejects_period_not_yet_cataloged():
    with pytest.raises(ValueError, match="catálogo atual"):
        resolve_fiscal_rule_set(date(2027, 1, 1), date(2027, 1, 31))


@pytest.mark.parametrize(
    ("start_date", "end_date", "expected"),
    [
        ("2025-08-01", "2025-08-31", "019"),
        ("2026-08-01", "2026-08-31", "020"),
    ],
)
def test_writer_records_resolved_layout_in_0000(start_date, end_date, expected):
    writer = SpedWriter()
    writer.generate_sped_from_db(
        company_info={
            "NOME": "EMPRESA TESTE",
            "CNPJ": "12345678000190",
            "UF": "RN",
            "IE": "123456789",
            "COD_MUN": "2408102",
        },
        accountant_info={},
        participants=[],
        products=[],
        units=[],
        invoices=[],
        extractor=object(),
        start_date=start_date,
        end_date=end_date,
    )

    opening = next(line for line in writer.to_lines() if line.startswith("|0000|"))
    assert opening.split("|")[2] == expected
