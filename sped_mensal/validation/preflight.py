"""Regras de pré-validação que independem do ERP de origem."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from inspect import signature
from typing import Any, Mapping, Sequence

from ..providers.base import FiscalDataProvider
from .models import ValidationIssue, ValidationReport, ValidationSeverity


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _digits(value: Any) -> str:
    return "".join(char for char in _text(value) if char.isdigit())


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


def _source_ref(invoice: Mapping[str, Any], item_number: Any = None) -> str:
    document = _text(invoice.get("NUM_DOC")) or _text(invoice.get("DOC_ID")) or "sem-documento"
    origin = _text(invoice.get("ORIGEM")) or "documento"
    return f"{origin}:{document}" + (f":item-{item_number}" if item_number is not None else "")


def _issue(
    report: ValidationReport,
    *,
    code: str,
    message: str,
    sped_record: str,
    field: str,
    source_ref: str,
    value: Any = "",
    suggestion: str = "",
    severity: ValidationSeverity = ValidationSeverity.ERROR,
) -> None:
    report.add(
        ValidationIssue(
            severity=severity,
            code=code,
            message=message,
            sped_record=sped_record,
            field=field,
            source_ref=source_ref,
            value=_text(value),
            suggestion=suggestion,
        )
    )


def _get_items(provider: FiscalDataProvider, invoice: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    getter = provider.get_invoice_items_by_ids
    doc_id = invoice.get("DOC_ID", "")
    venda_id = invoice.get("VENDA_ID", "")
    if len(signature(getter).parameters) >= 5:
        return getter(
            _text(invoice.get("COD_MOD")),
            doc_id,
            venda_id,
            _text(invoice.get("IND_OPER")),
            _text(invoice.get("ORIGEM")),
        )
    return getter(_text(invoice.get("COD_MOD")), doc_id, venda_id)


def _validate_product(report: ValidationReport, product: Mapping[str, Any]) -> None:
    source_ref = f"produto:{_text(product.get('COD_ITEM')) or 'sem-codigo'}"
    if not _text(product.get("COD_ITEM")):
        _issue(report, code="product.code.required", message="Código do produto não informado.", sped_record="0200", field="COD_ITEM", source_ref=source_ref)
    if not _text(product.get("UNID_INV")):
        _issue(report, code="product.unit.required", message="Unidade de inventário não informada.", sped_record="0200", field="UNID_INV", source_ref=source_ref)
    ncm = _digits(product.get("COD_NCM"))
    if ncm and len(ncm) != 8:
        _issue(report, code="product.ncm.invalid", message="NCM deve ter oito dígitos quando informado.", sped_record="0200", field="COD_NCM", source_ref=source_ref, value=product.get("COD_NCM"))
    cest = _digits(product.get("CEST"))
    if cest and len(cest) != 7:
        _issue(report, code="product.cest.invalid", message="CEST deve ter sete dígitos quando informado.", sped_record="0200", field="CEST", source_ref=source_ref, value=product.get("CEST"))


def _validate_invoice_header(report: ValidationReport, invoice: Mapping[str, Any], known_keys: set[tuple[str, ...]]) -> None:
    source_ref = _source_ref(invoice)
    num_doc = _text(invoice.get("NUM_DOC"))
    if not num_doc:
        _issue(report, code="invoice.number.required", message="Número do documento não informado.", sped_record="C100", field="NUM_DOC", source_ref=source_ref)

    key = tuple(_text(invoice.get(field)) for field in ("IND_OPER", "NUM_DOC", "COD_MOD", "COD_SIT", "SER", "CHV_NFE", "COD_PART"))
    if key in known_keys:
        _issue(report, code="invoice.key.duplicate", message="Chave de documento duplicada.", sped_record="C100", field="NUM_DOC", source_ref=source_ref, value=num_doc)
    known_keys.add(key)

    for field in ("VL_DOC", "VL_MERC", "VL_BC_ICMS", "VL_ICMS"):
        if _decimal(invoice.get(field)) < 0:
            _issue(report, code="invoice.amount.negative", message="Valor fiscal não pode ser negativo.", sped_record="C100", field=field, source_ref=source_ref, value=invoice.get(field))


def _validate_invoice_items(report: ValidationReport, provider: FiscalDataProvider, invoice: Mapping[str, Any]) -> None:
    if _text(invoice.get("COD_MOD")) == "65":
        return
    try:
        items = _get_items(provider, invoice)
    except Exception as exc:
        _issue(report, code="item.capture.failed", message="Não foi possível capturar os itens do documento.", sped_record="C170", field="NUM_ITEM", source_ref=_source_ref(invoice), value=type(exc).__name__)
        return

    total_items = Decimal("0")
    for item in items:
        source_ref = _source_ref(invoice, item.get("NUM_ITEM"))
        cst = _digits(item.get("CST_ICMS"))
        if not cst or len(cst) > 3:
            _issue(report, code="item.cst.required", message="CST ICMS obrigatório ou inválido.", sped_record="C170", field="CST_ICMS", source_ref=source_ref, value=item.get("CST_ICMS"), suggestion="Informe o CST conforme a tributação do item.")
        cfop = _digits(item.get("CFOP"))
        if len(cfop) != 4:
            _issue(report, code="item.cfop.invalid", message="CFOP deve conter quatro dígitos.", sped_record="C170", field="CFOP", source_ref=source_ref, value=item.get("CFOP"))
        if not _text(item.get("COD_ITEM")):
            _issue(report, code="item.product.required", message="Código do item não informado.", sped_record="C170", field="COD_ITEM", source_ref=source_ref)
        if not _text(item.get("UNID")):
            _issue(report, code="item.unit.required", message="Unidade do item não informada.", sped_record="C170", field="UNID", source_ref=source_ref)
        if _decimal(item.get("QTD")) <= 0:
            _issue(report, code="item.quantity.invalid", message="Quantidade deve ser maior que zero.", sped_record="C170", field="QTD", source_ref=source_ref, value=item.get("QTD"))
        value = _decimal(item.get("VL_ITEM"))
        if value < 0:
            _issue(report, code="item.amount.negative", message="Valor do item não pode ser negativo.", sped_record="C170", field="VL_ITEM", source_ref=source_ref, value=item.get("VL_ITEM"))
        total_items += value

    expected = _decimal(invoice.get("VL_MERC"))
    if items and expected and abs(total_items - expected) > Decimal("0.02"):
        _issue(report, code="invoice.items.total.divergent", message="Soma dos itens diverge do valor das mercadorias.", sped_record="C100", field="VL_MERC", source_ref=_source_ref(invoice), value=invoice.get("VL_MERC"), suggestion=f"Itens somam {total_items:.2f}.", severity=ValidationSeverity.WARNING)


def validate_provider(provider: FiscalDataProvider, start_date: str, end_date: str) -> ValidationReport:
    """Executa validações antes de gravar o TXT, sem alterar a fonte de dados."""

    invoices = list(provider.get_invoices(start_date, end_date))
    report = ValidationReport(provider.provider_id, start_date, end_date, len(invoices))
    for product in provider.get_products():
        _validate_product(report, product)

    keys: set[tuple[str, ...]] = set()
    for invoice in invoices:
        _validate_invoice_header(report, invoice, keys)
        _validate_invoice_items(report, provider, invoice)
    return report
