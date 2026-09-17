"""Caso de uso de geração independente do banco de origem."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..providers.base import FiscalDataProvider
from ..writer import SpedWriter


@dataclass(frozen=True)
class GenerationResult:
    """Resumo seguro para a interface, CLI e trilha de auditoria."""

    output_path: Path
    provider_id: str
    start_date: str
    end_date: str
    invoice_count: int


def generate_sped(
    provider: FiscalDataProvider,
    start_date: str,
    end_date: str,
    output_path: Path,
) -> GenerationResult:
    """Gera o arquivo usando uma fonte que implementa o contrato fiscal.

    A rotina mensal legado em ``main_fast.py`` continua sendo o caminho
    homologado até que seus tratamentos específicos estejam cobertos por testes
    de paridade nesta camada.
    """

    invoices = list(provider.get_invoices(start_date, end_date))
    writer = SpedWriter()
    writer.generate_sped_from_db(
        company_info=dict(provider.get_company_info()),
        accountant_info=dict(provider.get_accountant_info()),
        participants=[dict(row) for row in provider.get_participants()],
        products=[dict(row) for row in provider.get_products()],
        units=[dict(row) for row in provider.get_units()],
        invoices=[dict(row) for row in invoices],
        extractor=provider,
        start_date=start_date,
        end_date=end_date,
    )
    writer.write(output_path)
    return GenerationResult(
        output_path=output_path.resolve(),
        provider_id=provider.provider_id,
        start_date=start_date,
        end_date=end_date,
        invoice_count=len(invoices),
    )
