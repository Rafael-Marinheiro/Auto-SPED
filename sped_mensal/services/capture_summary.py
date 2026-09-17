"""Resumo tipado da captura, preparado para a CLI e a interface desktop."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..domain import Company, FiscalDocument
from ..providers.base import FiscalDataProvider


@dataclass(frozen=True)
class CaptureSummary:
    provider_id: str
    start_date: str
    end_date: str
    company: Company
    product_count: int
    participant_count: int
    document_count: int
    document_total: Decimal
    documents: tuple[FiscalDocument, ...]


def build_capture_summary(
    provider: FiscalDataProvider, start_date: str, end_date: str
) -> CaptureSummary:
    """Carrega uma visão padronizada, sem gerar SPED nem alterar a origem."""

    documents = tuple(
        FiscalDocument.from_mapping(row)
        for row in provider.get_invoices(start_date, end_date)
    )
    return CaptureSummary(
        provider_id=provider.provider_id,
        start_date=start_date,
        end_date=end_date,
        company=Company.from_mapping(provider.get_company_info()),
        product_count=len(provider.get_products()),
        participant_count=len(provider.get_participants()),
        document_count=len(documents),
        document_total=sum((document.total for document in documents), Decimal("0")),
        documents=documents,
    )
