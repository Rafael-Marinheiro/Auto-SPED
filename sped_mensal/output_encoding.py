"""Codificações permitidas para arquivos TXT do SPED."""

from __future__ import annotations

SUPPORTED_OUTPUT_ENCODINGS = ("utf-8", "iso-8859-1", "cp1252")

_ALIASES = {
    "utf8": "utf-8",
    "utf-8": "utf-8",
    "latin1": "iso-8859-1",
    "latin-1": "iso-8859-1",
    "iso8859-1": "iso-8859-1",
    "iso-8859-1": "iso-8859-1",
    "cp1252": "cp1252",
    "windows-1252": "cp1252",
}


def normalize_output_encoding(value: str) -> str:
    """Retorna o nome canônico de uma codificação de saída suportada."""

    normalized = _ALIASES.get(str(value).strip().lower())
    if normalized is None:
        choices = ", ".join(SUPPORTED_OUTPUT_ENCODINGS)
        raise ValueError(f"Codificação de saída não suportada: {value}. Use: {choices}.")
    return normalized
