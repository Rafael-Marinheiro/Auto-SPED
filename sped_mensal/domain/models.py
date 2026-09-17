"""Representações tipadas do domínio fiscal usadas por conectores e interface."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _decimal(value: Any) -> Decimal:
    raw = _text(value)
    if not raw:
        return Decimal("0")
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(",", ".")
    try:
        return Decimal(raw)
    except InvalidOperation:
        return Decimal("0")


@dataclass(frozen=True)
class Company:
    name: str
    cnpj: str
    cpf: str
    state: str
    state_registration: str
    municipality_code: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "Company":
        return cls(
            name=_text(row.get("NOME")),
            cnpj=_text(row.get("CNPJ")),
            cpf=_text(row.get("CPF")),
            state=_text(row.get("UF")),
            state_registration=_text(row.get("IE")),
            municipality_code=_text(row.get("COD_MUN")),
        )


@dataclass(frozen=True)
class TaxValues:
    cst_icms: str = ""
    cfop: str = ""
    icms_base: Decimal = Decimal("0")
    icms_rate: Decimal = Decimal("0")
    icms_value: Decimal = Decimal("0")
    icms_st_base: Decimal = Decimal("0")
    icms_st_value: Decimal = Decimal("0")
    cst_ipi: str = ""
    ipi_value: Decimal = Decimal("0")
    cst_pis: str = ""
    pis_value: Decimal = Decimal("0")
    cst_cofins: str = ""
    cofins_value: Decimal = Decimal("0")

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "TaxValues":
        return cls(
            cst_icms=_text(row.get("CST_ICMS")),
            cfop=_text(row.get("CFOP")),
            icms_base=_decimal(row.get("VL_BC_ICMS")),
            icms_rate=_decimal(row.get("ALIQ_ICMS")),
            icms_value=_decimal(row.get("VL_ICMS")),
            icms_st_base=_decimal(row.get("VL_BC_ICMS_ST")),
            icms_st_value=_decimal(row.get("VL_ICMS_ST")),
            cst_ipi=_text(row.get("CST_IPI")),
            ipi_value=_decimal(row.get("VL_IPI")),
            cst_pis=_text(row.get("CST_PIS")),
            pis_value=_decimal(row.get("VL_PIS")),
            cst_cofins=_text(row.get("CST_COFINS")),
            cofins_value=_decimal(row.get("VL_COFINS")),
        )


@dataclass(frozen=True)
class FiscalItem:
    number: str
    product_code: str
    description: str
    quantity: Decimal
    unit: str
    total: Decimal
    discount: Decimal
    taxes: TaxValues

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "FiscalItem":
        return cls(
            number=_text(row.get("NUM_ITEM")),
            product_code=_text(row.get("COD_ITEM")),
            description=_text(row.get("DESCR_COMPL")),
            quantity=_decimal(row.get("QTD")),
            unit=_text(row.get("UNID")),
            total=_decimal(row.get("VL_TOTAL", row.get("VL_ITEM"))),
            discount=_decimal(row.get("VL_DESC")),
            taxes=TaxValues.from_mapping(row),
        )


@dataclass(frozen=True)
class FiscalDocument:
    source_id: str
    origin: str
    operation: str
    model: str
    series: str
    number: str
    access_key: str
    issue_date: str
    entry_exit_date: str
    partner_code: str
    total: Decimal
    merchandise_total: Decimal
    taxes: TaxValues

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "FiscalDocument":
        return cls(
            source_id=_text(row.get("DOC_ID")),
            origin=_text(row.get("ORIGEM")),
            operation=_text(row.get("IND_OPER")),
            model=_text(row.get("COD_MOD")),
            series=_text(row.get("SER")),
            number=_text(row.get("NUM_DOC")),
            access_key=_text(row.get("CHV_NFE")),
            issue_date=_text(row.get("DT_DOC")),
            entry_exit_date=_text(row.get("DT_E_S")),
            partner_code=_text(row.get("COD_PART")),
            total=_decimal(row.get("VL_DOC")),
            merchandise_total=_decimal(row.get("VL_MERC")),
            taxes=TaxValues.from_mapping(row),
        )
