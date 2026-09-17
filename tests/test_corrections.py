import pytest

from sped_mensal.services import (
    CorrectionConfirmationError,
    CorrectionPlan,
    CorrectionProposal,
    apply_confirmed_plan,
)


class Transaction:
    def __init__(self, fail=False):
        self.fail = fail
        self.committed = False
        self.rolled_back = False

    def apply(self, proposal):
        if self.fail:
            raise RuntimeError("falha")

    def commit(self):
        self.committed = True
        return "tx-1"

    def rollback(self):
        self.rolled_back = True


class Executor:
    def __init__(self, transaction): self.transaction = transaction
    def begin(self, source_id): return self.transaction


def plan():
    return CorrectionPlan("firebird", "2026-08", (
        CorrectionProposal("COMPRA:1:item-1", "CST_ICM", "", "60", "Histórico", "valor atual vazio"),
    ))


def test_correction_requires_confirmation_and_commits_once():
    reviewed_plan = plan()
    transaction = Transaction()

    receipt = apply_confirmed_plan(Executor(transaction), reviewed_plan, reviewed_plan.confirmation_token)

    assert transaction.committed is True
    assert transaction.rolled_back is False
    assert receipt.applied_count == 1


def test_correction_rolls_back_when_any_change_fails():
    reviewed_plan = plan()
    transaction = Transaction(fail=True)

    with pytest.raises(RuntimeError):
        apply_confirmed_plan(Executor(transaction), reviewed_plan, reviewed_plan.confirmation_token)

    assert transaction.committed is False
    assert transaction.rolled_back is True


def test_correction_rejects_a_token_from_another_plan():
    with pytest.raises(CorrectionConfirmationError):
        apply_confirmed_plan(Executor(Transaction()), plan(), "OUTRO-PLANO")
