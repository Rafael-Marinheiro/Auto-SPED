"""Normalizações fiscais compartilhadas entre conectores e geração."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


def digits_only(value: Any) -> str:
    """Remove formatação, preservando somente dígitos."""

    return "".join(char for char in ("" if value is None else str(value)) if char.isdigit())


def normalize_tipo_item(value: Any) -> str:
    digits = digits_only(value)
    return digits[-2:].zfill(2) if digits else ""


def normalize_ncm(value: Any) -> str:
    digits = digits_only(value)
    return digits if len(digits) == 8 and digits != "00000000" else ""


def normalize_cest(value: Any) -> str:
    digits = digits_only(value)
    return digits if len(digits) == 7 and digits != "0000000" else ""


def normalize_cfop(value: Any) -> str:
    """Padroniza CFOP curto sem inventar classificação tributária."""

    digits = digits_only(value)
    return digits.zfill(4) if digits else ""


def normalize_cst(value: Any, width: int = 3) -> str:
    """Normaliza CST para a largura esperada, usando os dígitos finais."""

    digits = digits_only(value)
    if len(digits) > width:
        digits = digits[-width:]
    return digits.zfill(width) if digits else ""


def normalize_tax_rate(value: Any) -> str:
    """Retorna alíquota com duas casas ou vazio quando a origem for inválida."""

    raw = "" if value is None else str(value).strip()
    if not raw:
        return ""
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(",", ".")
    try:
        decimal = Decimal(raw)
    except InvalidOperation:
        return ""
    return str(decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
