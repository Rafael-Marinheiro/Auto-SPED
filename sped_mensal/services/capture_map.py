"""Explicações reutilizáveis para o mapa de rastreabilidade fiscal."""

from __future__ import annotations


def transformation_for(source: str) -> str:
    """Explica a transformação sem esconder a origem física do campo."""
    fiscal_fields = ("CST", "CFOP", "NCM", "CEST", "ALIQ")
    if any(field in source.upper() for field in fiscal_fields):
        return "Normalização fiscal (formato, dígitos e casas decimais)"
    return "Captura direta"
