"""Contrato estável entre o motor SPED e fontes de dados fiscais.

O motor recebe estruturas fiscais padronizadas e nunca deve depender dos
nomes das tabelas de um ERP. Cada conector traduz sua fonte para este contrato.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


FiscalRow = Mapping[str, Any]


@dataclass(frozen=True)
class CaptureMapping:
    """Explica a origem de um dado e os campos SPED que ele abastece."""

    entity: str
    fiscal_field: str
    source: str
    sped_targets: tuple[str, ...]
    note: str = ""


@runtime_checkable
class FiscalDataProvider(Protocol):
    """Fonte de dados necessária para emitir EFD ICMS/IPI.

    Os dicionários retornados usam os nomes fiscais atuais do ``SpedWriter``.
    Isso mantém compatibilidade enquanto os modelos tipados são introduzidos
    gradualmente, sem interromper as emissões mensais já homologadas.
    """

    provider_id: str
    display_name: str

    def describe_capture(self) -> Sequence[CaptureMapping]: ...

    def get_company_info(self) -> FiscalRow: ...

    def get_accountant_info(self) -> FiscalRow: ...

    def get_participants(self) -> Sequence[FiscalRow]: ...

    def get_products(self) -> Sequence[FiscalRow]: ...

    def get_units(self) -> Sequence[FiscalRow]: ...

    def get_invoices(self, start_date: str, end_date: str) -> Sequence[FiscalRow]: ...

    def get_invoice_items_by_ids(
        self,
        cod_mod: str,
        doc_id: str | int,
        venda_id: str | int,
        ind_oper: str | None = None,
        origem: str | None = None,
    ) -> Sequence[FiscalRow]: ...
