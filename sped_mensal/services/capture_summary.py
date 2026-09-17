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

    def to_dict(self) -> dict[str, object]:
        """Formato seguro para CLI, interface e relatório local."""

        return {
            "provider_id": self.provider_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "company": {
                "name": self.company.name,
                "cnpj": self.company.cnpj,
                "state": self.company.state,
                "municipality_code": self.company.municipality_code,
            },
            "product_count": self.product_count,
            "participant_count": self.participant_count,
            "document_count": self.document_count,
            "document_total": f"{self.document_total:.2f}",
            "documents": [
                {
                    "source_id": document.source_id,
                    "origin": document.origin,
                    "operation": document.operation,
                    "model": document.model,
                    "series": document.series,
                    "number": document.number,
                    "issue_date": document.issue_date,
                    "partner_code": document.partner_code,
                    "total": f"{document.total:.2f}",
                }
                for document in self.documents
            ],
        }


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
