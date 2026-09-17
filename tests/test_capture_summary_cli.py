from decimal import Decimal

from sped_mensal.domain import Company, FiscalDocument, TaxValues
from sped_mensal.services.capture_summary import CaptureSummary


def test_capture_summary_cli_writes_json(monkeypatch, tmp_path, capsys):
    from sped_mensal import cli

    summary = CaptureSummary(
        provider_id="fake", start_date="2026-08-01", end_date="2026-08-31",
        company=Company("Empresa", "1", "", "RN", "", "2402709"),
        product_count=1, participant_count=1, document_count=1, document_total=Decimal("10"),
        documents=(FiscalDocument("1", "COMPRA", "0", "55", "1", "10", "", "2026-08-01", "", "1", Decimal("10"), Decimal("10"), TaxValues()),),
    )
    monkeypatch.setattr(cli, "build_capture_summary", lambda *args: summary)
    destination = tmp_path / "summary.json"

    result = cli.main_capture_summary([
        "--database", "DADOS.FDB", "--start-date", "2026-08-01", "--end-date", "2026-08-31",
        "--format", "json", "--output", str(destination),
    ])

    assert result == 0
    assert destination.exists()
    assert '"document_count": 1' in capsys.readouterr().out
