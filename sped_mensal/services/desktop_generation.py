"""Contrato de solicitação da emissão usado pela interface desktop."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..output_encoding import normalize_output_encoding
from .revenue_code import normalize_revenue_code


@dataclass(frozen=True)
class GenerationRequest:
    """Parâmetros explícitos, sem credenciais, para uma emissão SPED."""

    provider_id: str
    database_path: Path
    start_date: date
    end_date: date
    output_path: Path
    client_library: Path | None = None
    output_encoding: str = "utf-8"
    revenue_code: str | None = None

    def validate(self) -> None:
        if self.provider_id != "firebird-sao-pedro":
            raise ValueError(f"Capturador não suportado: {self.provider_id}.")
        if not self.database_path.is_file():
            raise FileNotFoundError(f"Banco Firebird não encontrado: {self.database_path}")
        if self.start_date > self.end_date:
            raise ValueError("A data inicial não pode ser posterior à data final.")
        if self.client_library is not None and not self.client_library.is_file():
            raise FileNotFoundError(f"Biblioteca Firebird não encontrada: {self.client_library}")
        normalize_output_encoding(self.output_encoding)
        if self.revenue_code is not None:
            normalize_revenue_code(self.revenue_code)

    @property
    def start_date_iso(self) -> str:
        return self.start_date.isoformat()

    @property
    def end_date_iso(self) -> str:
        return self.end_date.isoformat()
