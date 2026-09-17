"""Planos de correção confirmáveis, independentes da tecnologia do banco."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Protocol


@dataclass(frozen=True)
class CorrectionProposal:
    source_ref: str
    field: str
    current_value: str
    proposed_value: str
    rationale: str
    precondition: str


@dataclass(frozen=True)
class CorrectionPlan:
    source_id: str
    period: str
    proposals: tuple[CorrectionProposal, ...]

    @property
    def confirmation_token(self) -> str:
        payload = "\n".join(
            (self.source_id, self.period)
            + tuple(
                "|".join((proposal.source_ref, proposal.field, proposal.current_value, proposal.proposed_value, proposal.precondition))
                for proposal in self.proposals
            )
        )
        return sha256(payload.encode("utf-8")).hexdigest()[:12].upper()


@dataclass(frozen=True)
class CorrectionReceipt:
    transaction_id: str
    plan_token: str
    applied_count: int
    committed_at: datetime


class CorrectionTransaction(Protocol):
    def apply(self, proposal: CorrectionProposal) -> None: ...
    def commit(self) -> str: ...
    def rollback(self) -> None: ...


class CorrectionExecutor(Protocol):
    def begin(self, source_id: str) -> CorrectionTransaction: ...


class CorrectionConfirmationError(ValueError):
    pass


def apply_confirmed_plan(executor: CorrectionExecutor, plan: CorrectionPlan, confirmation_token: str) -> CorrectionReceipt:
    """Executa o plano como unidade atômica após confirmação humana."""

    if confirmation_token.strip().upper() != plan.confirmation_token:
        raise CorrectionConfirmationError("Confirmação não corresponde ao plano revisado.")
    transaction = executor.begin(plan.source_id)
    try:
        for proposal in plan.proposals:
            transaction.apply(proposal)
        transaction_id = transaction.commit()
    except Exception:
        transaction.rollback()
        raise
    return CorrectionReceipt(transaction_id, plan.confirmation_token, len(plan.proposals), datetime.now(timezone.utc))
