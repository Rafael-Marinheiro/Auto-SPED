"""Persistência local e durável de recibos de correção."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .corrections import CorrectionPlan, CorrectionReceipt


class JsonlAuditStore:
    """Grava um evento por linha com flush e fsync após o commit do banco.

    O arquivo é uma trilha de auditoria local. A atomicidade da alteração fiscal
    fica no Firebird; se esta gravação falhar após o commit, a aplicação precisa
    sinalizar reconciliação em vez de tentar desfazer uma transação já confirmada.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, receipt: "CorrectionReceipt", plan: "CorrectionPlan") -> None:
        payload = {
            "receipt": {
                "transaction_id": receipt.transaction_id,
                "plan_token": receipt.plan_token,
                "applied_count": receipt.applied_count,
                "committed_at": receipt.committed_at.isoformat(),
            },
            "plan": {
                "source_id": plan.source_id,
                "period": plan.period,
                "proposals": [asdict(proposal) for proposal in plan.proposals],
            },
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
            output.flush()
            os.fsync(output.fileno())
