"""Executor transacional e restrito para correções no ERP Firebird atual."""

from __future__ import annotations

import re
from uuid import uuid4

from ..database import DatabaseConnection
from ..services.corrections import CorrectionProposal, CorrectionTransaction


class CorrectionPreconditionError(RuntimeError):
    """O banco mudou desde que o plano foi revisado."""


class FirebirdCompraTransaction(CorrectionTransaction):
    """Transação com lista de campos e origem explicitamente permitidos."""

    _source_pattern = re.compile(r"^COMPRA:(?P<compra>\d+):item-(?P<item>\d+)$")
    _allowed_fields = {"CST_ICM", "CFOP", "QTD", "TOTAL_COMPRA", "BASE_ICMS", "ALIQ_ICMS", "VL_ICMS"}

    def __init__(self, connection: DatabaseConnection) -> None:
        self._database = connection
        self._closed = False

    def apply(self, proposal: CorrectionProposal) -> None:
        if self._closed:
            raise RuntimeError("Transação de correção já foi encerrada.")
        match = self._source_pattern.fullmatch(proposal.source_ref)
        if not match:
            raise ValueError("Origem de correção não permitida; use COMPRA:<id>:item-<número>.")
        if proposal.field not in self._allowed_fields:
            raise ValueError(f"Campo de correção não permitido: {proposal.field}.")

        compra_id = int(match.group("compra"))
        item = int(match.group("item"))
        cursor = self._database.connection.cursor()
        try:
            cursor.execute(
                f"""UPDATE COMPRA_ITENS
                    SET {proposal.field} = ?
                    WHERE FK_COMPRA = ? AND ITEM = ?
                      AND COALESCE(TRIM(CAST({proposal.field} AS VARCHAR(100))), '') = ?""",
                (proposal.proposed_value, compra_id, item, proposal.current_value.strip()),
            )
            if cursor.rowcount != 1:
                raise CorrectionPreconditionError(
                    "A pré-condição não corresponde mais ao banco ou o item não existe."
                )
        finally:
            cursor.close()

    def commit(self) -> str:
        if self._closed:
            raise RuntimeError("Transação de correção já foi encerrada.")
        try:
            self._database.connection.commit()
            return str(uuid4())
        finally:
            self._database.disconnect()
            self._closed = True

    def rollback(self) -> None:
        if self._closed:
            return
        try:
            self._database.connection.rollback()
        finally:
            self._database.disconnect()
            self._closed = True


class FirebirdCompraCorrectionExecutor:
    """Abre uma transação Firebird para um plano confirmado de compras."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def begin(self, source_id: str) -> FirebirdCompraTransaction:
        if source_id != "firebird-sao-pedro":
            raise ValueError(f"Fonte não suportada pelo executor Firebird: {source_id}.")
        database = DatabaseConnection(self.database_path)
        database.connect()
        return FirebirdCompraTransaction(database)
