"""Contrato de solicitação da emissão usado pela interface desktop."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class GenerationRequest:
    """Parâmetros explícitos, sem credenciais, para uma emissão SPED."""

    provider_id: str
    database_path: Path
    start_date: date
    end_date: date
    output_path: Path
    client_library: Path | None = None

    def validate(self) -> None:
        if self.provider_id != "firebird-sao-pedro":
            raise ValueError(f"Capturador não suportado: {self.provider_id}.")
        if not self.database_path.is_file():
            raise FileNotFoundError(f"Banco Firebird não encontrado: {self.database_path}")
        if self.start_date > self.end_date:
            raise ValueError("A data inicial não pode ser posterior à data final.")
        if self.client_library is not None and not self.client_library.is_file():
            raise FileNotFoundError(f"Biblioteca Firebird não encontrada: {self.client_library}")

    @property
    def start_date_iso(self) -> str:
        return self.start_date.isoformat()

    @property
    def end_date_iso(self) -> str:
        return self.end_date.isoformat()
