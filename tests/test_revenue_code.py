import pytest

from sped_mensal.services.revenue_code import (
    STATE_REVENUE_CODE_RULES,
    resolve_e116_revenue_code,
)


def test_emission_revenue_code_has_priority_over_company_and_state_defaults():
    company = {"UF": "RN", "COD_REC": "1210"}

    assert resolve_e116_revenue_code(company, "1230") == "1230"


def test_uses_revenue_code_configured_for_company():
    company = {"UF": "SP", "COD_REC": "063-2"}

    assert resolve_e116_revenue_code(company) == "063-2"


def test_uses_confirmed_state_default_for_rio_grande_do_norte():
    assert resolve_e116_revenue_code({"UF": "rn"}) == "1210"


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("AP", "1111"),
        ("CE", "1015"),
        ("GO", "108"),
        ("PB", "1101"),
        ("PE", "005-1"),
        ("PR", "1015"),
        ("RJ", "021-3"),
        ("RN", "1210"),
        ("SC", "1449"),
        ("SP", "046-2"),
    ],
)
def test_uses_officially_verified_state_defaults(state, expected):
    assert resolve_e116_revenue_code({"UF": state}) == expected


def test_every_automatic_state_rule_keeps_its_official_source_and_verification_date():
    assert all(rule.source_url.startswith("https://") for rule in STATE_REVENUE_CODE_RULES.values())
    assert all(rule.verified_on for rule in STATE_REVENUE_CODE_RULES.values())


def test_requires_configuration_when_state_has_no_confirmed_default():
    with pytest.raises(ValueError, match="UF AL"):
        resolve_e116_revenue_code({"UF": "AL"})


@pytest.mark.parametrize("state", ["AC", "ES", "MG", "RS"])
def test_requires_company_configuration_when_state_has_multiple_normal_codes(state):
    with pytest.raises(ValueError, match=f"UF {state}"):
        resolve_e116_revenue_code({"UF": state})


@pytest.mark.parametrize("value", ["12|10", "12\n10", "12\t10", "   "])
def test_rejects_invalid_revenue_code(value):
    with pytest.raises(ValueError, match="Código de receita"):
        resolve_e116_revenue_code({"UF": "RN"}, value)
