from datetime import date, datetime, timezone

from sped_mensal.services.corrections import CorrectionPlan, CorrectionReceipt
from sped_mensal.services.desktop_generation import GenerationRequest
from sped_mensal.services.history import LocalHistoryStore


def test_history_records_emissions_without_full_local_paths(tmp_path):
    database = tmp_path / "DADOS.FDB"
    database.write_bytes(b"placeholder")
    request = GenerationRequest("firebird-sao-pedro", database, date(2026, 8, 1), date(2026, 8, 31), tmp_path / "saida.txt")
    store = LocalHistoryStore(tmp_path / "history.jsonl")

    store.record_emission(request, "concluída", tmp_path / "saida.txt")

    event = store.list_events()[0]
    assert event.kind == "emissão"
    assert event.target == "saida.txt"
    assert str(tmp_path) not in store.path.read_text(encoding="utf-8")


def test_history_records_correction_receipt(tmp_path):
    store = LocalHistoryStore(tmp_path / "history.jsonl")
    plan = CorrectionPlan("firebird-sao-pedro", "2026-08", ())
    receipt = CorrectionReceipt("tx-1", plan.confirmation_token, 2, datetime.now(timezone.utc))

    store.record_correction(receipt, plan)

    event = store.list_events()[0]
    assert event.kind == "correção"
    assert event.status == "confirmada"
    assert event.target == "tx-1"
