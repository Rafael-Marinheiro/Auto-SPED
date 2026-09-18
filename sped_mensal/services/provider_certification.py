"""Suíte de conformidade para conectores de terceiros."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from ..providers.base import CaptureMapping, FiscalDataProvider
from .normalization import digits_only, parse_fiscal_date


@dataclass(frozen=True)
class CertificationFinding:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class CertificationReport:
    provider_id: str
    checked_documents: int
    findings: tuple[CertificationFinding, ...]

    @property
    def passed(self) -> bool:
        return not any(finding.severity == "error" for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "passed": self.passed,
            "checked_documents": self.checked_documents,
            "findings": [asdict(finding) for finding in self.findings],
        }


def certify_provider(
    provider: object,
    start_date: str,
    end_date: str,
    *,
    max_documents: int = 25,
) -> CertificationReport:
    """Executa checks somente leitura sobre uma amostra do conector."""

    findings: list[CertificationFinding] = []
    provider_id = str(getattr(provider, "provider_id", provider.__class__.__name__))
    if max_documents < 1:
        raise ValueError("max_documents deve ser maior que zero")
    start = parse_fiscal_date(start_date)
    end = parse_fiscal_date(end_date)
    if start is None or end is None or start > end:
        raise ValueError("período de certificação inválido")

    if not isinstance(provider, FiscalDataProvider):
        findings.append(_error("contract", "O objeto não implementa FiscalDataProvider."))
        return CertificationReport(provider_id, 0, tuple(findings))

    mappings = _safe_call(provider.describe_capture, "describe_capture", findings)
    if mappings is not None:
        if not _is_row_sequence(mappings) or not all(isinstance(row, CaptureMapping) for row in mappings):
            findings.append(_error("capture-map-type", "describe_capture deve retornar CaptureMapping."))
        elif not mappings:
            findings.append(_error("capture-map-empty", "O mapa de captura não pode ser vazio."))
        else:
            for index, mapping in enumerate(mappings, 1):
                if not mapping.source.strip() or not mapping.sped_targets:
                    findings.append(_error(
                        "capture-map-incomplete",
                        f"Mapeamento {index} não informa origem e destinos SPED.",
                    ))

    company = _safe_call(provider.get_company_info, "get_company_info", findings)
    if company is not None:
        if not isinstance(company, Mapping):
            findings.append(_error("company-type", "get_company_info deve retornar um dicionário."))
        else:
            if not str(company.get("NOME", "")).strip():
                findings.append(_error("company-name", "A empresa não possui NOME."))
            cnpj = digits_only(company.get("CNPJ"))
            cpf = digits_only(company.get("CPF"))
            if len(cnpj) != 14 and len(cpf) != 11:
                findings.append(_error("company-document", "A empresa não possui CNPJ ou CPF válido."))

    accountant = _safe_call(provider.get_accountant_info, "get_accountant_info", findings)
    if accountant is not None and not isinstance(accountant, Mapping):
        findings.append(_error("accountant-type", "get_accountant_info deve retornar um dicionário."))

    for method_name in ("get_participants", "get_products", "get_units"):
        rows = _safe_call(getattr(provider, method_name), method_name, findings)
        if rows is not None:
            _check_rows(method_name, rows, findings)

    invoices = _safe_call(
        lambda: provider.get_invoices(start_date, end_date),
        "get_invoices",
        findings,
    )
    if invoices is None or not _check_rows("get_invoices", invoices, findings):
        return CertificationReport(provider_id, 0, tuple(findings))
    if not invoices:
        findings.append(CertificationFinding(
            "warning", "period-without-documents", "O período não retornou documentos para amostragem."
        ))

    seen_keys: set[tuple[str, ...]] = set()
    checked = 0
    for index, invoice in enumerate(invoices[:max_documents], 1):
        if not _check_invoice(invoice, index, start, end, seen_keys, findings):
            continue
        checked += 1
        items = _safe_call(
            lambda row=invoice: provider.get_invoice_items_by_ids(
                str(row.get("COD_MOD", "")),
                row.get("DOC_ID", ""),
                row.get("VENDA_ID", ""),
                str(row.get("IND_OPER", "")) or None,
                str(row.get("ORIGEM", "")) or None,
            ),
            f"get_invoice_items_by_ids(documento {index})",
            findings,
        )
        if items is not None:
            _check_rows(f"itens do documento {index}", items, findings)

    return CertificationReport(provider_id, checked, tuple(findings))


def assert_provider_certified(
    provider: object,
    start_date: str,
    end_date: str,
    *,
    max_documents: int = 25,
) -> CertificationReport:
    """Integra a certificação diretamente a uma suíte pytest/unittest."""

    report = certify_provider(provider, start_date, end_date, max_documents=max_documents)
    if not report.passed:
        errors = "; ".join(
            f"{finding.code}: {finding.message}"
            for finding in report.findings
            if finding.severity == "error"
        )
        raise AssertionError(f"conector {report.provider_id!r} reprovado: {errors}")
    return report


def _safe_call(call: Any, name: str, findings: list[CertificationFinding]) -> Any:
    try:
        return call()
    except Exception as exc:
        findings.append(_error("provider-exception", f"{name} falhou: {exc}"))
        return None


def _check_rows(name: str, rows: Any, findings: list[CertificationFinding]) -> bool:
    if not _is_row_sequence(rows):
        findings.append(_error("row-sequence", f"{name} deve retornar uma sequência de dicionários."))
        return False
    if not all(isinstance(row, Mapping) for row in rows):
        findings.append(_error("row-type", f"{name} contém uma linha que não é dicionário."))
        return False
    return True


def _is_row_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _check_invoice(
    invoice: Mapping[str, Any],
    index: int,
    start: Any,
    end: Any,
    seen_keys: set[tuple[str, ...]],
    findings: list[CertificationFinding],
) -> bool:
    has_source_id = str(invoice.get("DOC_ID", "")).strip() or str(invoice.get("VENDA_ID", "")).strip()
    if not has_source_id:
        findings.append(_error("invoice-source-id", f"Documento {index} não possui DOC_ID nem VENDA_ID."))
        return False
    for field in ("COD_MOD", "DT_DOC"):
        if not str(invoice.get(field, "")).strip():
            findings.append(_error("invoice-required", f"Documento {index} não possui {field}."))
            return False

    issue_date = parse_fiscal_date(invoice.get("DT_DOC"))
    if issue_date is None or not start <= issue_date <= end:
        findings.append(_error("invoice-period", f"Documento {index} está fora do período solicitado."))

    key = tuple(str(invoice.get(field, "")).strip() for field in (
        "IND_OPER", "NUM_DOC", "COD_MOD", "COD_SIT", "SER", "CHV_NFE", "COD_PART"
    ))
    if key in seen_keys:
        findings.append(_error("invoice-duplicate", f"Documento {index} duplica a chave fiscal de outro documento."))
    seen_keys.add(key)
    return True


def _error(code: str, message: str) -> CertificationFinding:
    return CertificationFinding("error", code, message)
