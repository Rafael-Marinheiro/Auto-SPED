from datetime import date

import pytest

from sped_mensal.services.desktop_generation import GenerationRequest


def test_generation_request_exposes_iso_dates(tmp_path):
    database = tmp_path / "DADOS.FDB"
    database.write_bytes(b"placeholder")
    request = GenerationRequest(
        "firebird-sao-pedro",
        database,
        date(2026, 8, 1),
        date(2026, 8, 31),
        tmp_path / "saida.txt",
    )

    request.validate()
    assert request.start_date_iso == "2026-08-01"
    assert request.end_date_iso == "2026-08-31"


def test_generation_request_rejects_reversed_period(tmp_path):
    database = tmp_path / "DADOS.FDB"
    database.write_bytes(b"placeholder")
    request = GenerationRequest(
        "firebird-sao-pedro",
        database,
        date(2026, 9, 1),
        date(2026, 8, 31),
        tmp_path / "saida.txt",
    )

    with pytest.raises(ValueError, match="data inicial"):
        request.validate()
