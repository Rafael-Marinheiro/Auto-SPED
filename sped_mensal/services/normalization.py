"""Normalizações fiscais compartilhadas entre conectores e geração."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date, datetime
from collections.abc import Mapping
from typing import Any


def digits_only(value: Any) -> str:
    """Remove formatação, preservando somente dígitos."""

    return "".join(char for char in ("" if value is None else str(value)) if char.isdigit())


def normalize_person_ids(cnpj_value: Any, cpf_value: Any) -> tuple[str, str]:
    """Posiciona CNPJ e CPF válidos nos campos fiscais correspondentes."""

    cnpj = digits_only(cnpj_value)
    cpf = digits_only(cpf_value)
    if len(cnpj) == 14:
        return cnpj, cpf if len(cpf) == 11 else ""
    if len(cnpj) == 11 and len(cpf) != 11:
        return "", cnpj
    if len(cpf) == 14 and len(cnpj) != 14:
        return cpf, ""
    if len(cpf) == 11:
        return "", cpf
    return "", ""


def normalize_municipality_code(value: Any) -> str:
    """Remove formatação e omite códigos municipais vazios ou zerados."""

    digits = digits_only(value)
    return "" if digits in {"", "0"} else digits


def normalize_access_key(value: Any) -> str:
    """Aceita somente chaves de acesso de NF-e/NFC-e com 44 dígitos."""

    digits = digits_only(value)
    return digits if len(digits) == 44 else ""


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


def normalize_sped_date(value: Any) -> str:
    """Converte os formatos aceitos pelo legado para DDMMAAAA."""

    raw = "" if value is None else str(value)
    if not raw:
        return ""
    for date_format in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y", "%d%m%Y"):
        try:
            return datetime.strptime(raw, date_format).strftime("%d%m%Y")
        except ValueError:
            continue
    return raw.replace("-", "")


def parse_fiscal_date(value: Any) -> date | None:
    """Converte datas aceitas pelo legado para comparação de períodos."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = "" if value is None else str(value).strip()
    for date_format in ("%d%m%Y", "%Y-%m-%d", "%Y%m%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, date_format).date()
        except ValueError:
            continue
    return None


def normalize_document_status(value: Any) -> str:
    """Mapeia situações do ERP para o COD_SIT do documento fiscal."""

    status = "" if value is None else str(value).strip().upper()
    if status in {"00", "01", "02", "03", "04", "05", "06", "07", "08"}:
        return status
    if status in {"C", "CANC", "CANCEL", "CANCELADA", "CANCELADO"}:
        return "02"
    if status.startswith("DENEG") or status in {"D", "DEN"}:
        return "04"
    if status.startswith("INUTIL") or status == "I":
        return "05"
    return "00"


def format_sped_money(value: Any) -> str:
    """Formata valor monetário com duas casas, preservando a regra do legado."""

    if isinstance(value, Decimal):
        decimal = value
    else:
        raw = "" if value is None else str(value).strip()
        if "," in raw and "." in raw:
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", ".")
        try:
            decimal = Decimal(raw or "0")
        except InvalidOperation:
            decimal = Decimal("0")
    return str(decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def normalize_product_mapping(product: Mapping[str, Any]) -> dict[str, Any]:
    """Normaliza os campos do registro 0200 sem depender do ERP de origem."""

    normalized = dict(product)
    if "DESCR_ITEM" in normalized:
        normalized["DESCR_ITEM"] = str(normalized["DESCR_ITEM"]).strip()
    if "UNID_INV" in normalized:
        normalized["UNID_INV"] = str(normalized["UNID_INV"]).strip()
    if "TIPO_ITEM" in normalized:
        normalized["TIPO_ITEM"] = normalize_tipo_item(normalized.get("TIPO_ITEM"))
    if "COD_NCM" in normalized:
        normalized["COD_NCM"] = normalize_ncm(normalized.get("COD_NCM"))
    if "CEST" in normalized:
        normalized["CEST"] = normalize_cest(normalized.get("CEST"))
    if "ALIQ_ICMS" in normalized:
        normalized["ALIQ_ICMS"] = normalize_tax_rate(normalized.get("ALIQ_ICMS"))
    return normalized


def normalize_ipi_cst(value: Any, cfop: Any) -> str | None:
    """Aplica a regra homologada de CST de IPI conforme entrada ou saída."""

    digits = digits_only(value)
    if not digits:
        return None
    normalized_cfop = normalize_cfop(cfop)
    numeric_cst = int(digits)
    if normalized_cfop.startswith(("1", "2", "3")) and numeric_cst >= 50:
        return "00"
    if normalized_cfop.startswith(("5", "6", "7")) and numeric_cst < 97:
        return "99"
    return str(numeric_cst).zfill(2)


def normalize_fiscal_item_mapping(item: Mapping[str, Any]) -> dict[str, Any]:
    """Normaliza códigos fiscais do item preservando valores e campos extras."""

    normalized = dict(item)
    normalized["CFOP"] = normalize_cfop(normalized.get("CFOP"))
    normalized["CST_ICMS"] = normalize_cst(normalized.get("CST_ICMS"))
    cst_ipi = normalize_ipi_cst(normalized.get("CST_IPI"), normalized["CFOP"])
    if cst_ipi is not None:
        normalized["CST_IPI"] = cst_ipi
    return normalized


def parse_sped_decimal(value: Any) -> Decimal:
    """Interpreta números do ERP com separador brasileiro ou internacional."""

    if isinstance(value, Decimal):
        return value
    raw = "0" if value is None else str(value).strip() or "0"
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return Decimal(raw)
    except InvalidOperation:
        return Decimal("0")


def format_sped_decimal(value: Any) -> str:
    """Formata números com duas casas e vírgula como separador do SPED."""

    numeric = float(parse_sped_decimal(value))
    return f"{numeric:.2f}".replace(".", ",")
