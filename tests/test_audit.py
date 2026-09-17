import json

from sped_mensal.services.audit import JsonlAuditStore
from sped_mensal.services.corrections import CorrectionPlan, CorrectionProposal, CorrectionReceipt
from datetime import datetime, timezone


def test_audit_store_persists_a_receipt_and_plan(tmp_path):
    path = tmp_path / "audit.jsonl"
    proposal = CorrectionProposal("COMPRA:1:item-1", "CST_ICM", "", "60", "r", "p")
    plan = CorrectionPlan("firebird-sao-pedro", "2026-08", (proposal,))
    receipt = CorrectionReceipt("tx", plan.confirmation_token, 1, datetime.now(timezone.utc))

    JsonlAuditStore(path).append(receipt, plan)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["receipt"]["transaction_id"] == "tx"
    assert payload["plan"]["proposals"][0]["proposed_value"] == "60"
