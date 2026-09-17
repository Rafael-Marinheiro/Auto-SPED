import json

from sped_mensal.cli import main_capture_map


def test_capture_map_is_available_without_a_database_connection(capsys):
    result = main_capture_map(["--format", "json"])

    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert any(
        row["source"] == "COMPRA_ITENS.CST_ICM, CFOP, BASE_ICMS, ALIQ_ICMS, VL_ICMS"
        and "C170.CST_ICMS" in row["sped_targets"]
        for row in payload
    )
