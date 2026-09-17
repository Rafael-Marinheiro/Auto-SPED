from sped_mensal.validation.models import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
)


def test_validation_report_serializes_issues_for_the_interface():
    report = ValidationReport("provider", "2026-08-01", "2026-08-31", 1)
    report.add(
        ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="item.cst.required",
            message="CST obrigatório.",
            sped_record="C170",
            field="CST_ICMS",
            source_ref="COMPRA:1:item-1",
            suggestion="Preencha o CST.",
        )
    )

    payload = report.to_dict()

    assert payload["is_valid"] is False
    assert payload["error_count"] == 1
    assert payload["issues"][0]["severity"] == "error"
