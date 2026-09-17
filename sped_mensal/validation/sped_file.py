"""Validador estrutural do TXT SPED, independente do banco de dados."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from .models import ValidationReport, ValidationSeverity


BLOCK_ORDER = ("0", "B", "C", "D", "E", "G", "H", "K", "1", "9")


def _parts(line: str) -> list[str]:
    return line.strip().strip("|").split("|")


def _number(parts: list[str], index: int) -> int | None:
    try:
        return int(parts[index])
    except (IndexError, TypeError, ValueError):
        return None


def _decimal(parts: list[str], index: int) -> Decimal:
    raw = parts[index].strip() if len(parts) > index else ""
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


def _rate_key(parts: list[str], index: int, cst: str) -> str:
    if cst in {"040", "041", "050", "051"}:
        return ""
    return f"{_decimal(parts, index):.2f}"


def _add(report: ValidationReport, line_number: int, code: str, message: str, record: str, field: str, value: str = "") -> None:
    report.add_issue(
        severity=ValidationSeverity.ERROR,
        code=code,
        message=message,
        sped_record=record,
        field=field,
        source_ref=f"linha:{line_number}",
        value=value,
    )


def _validate_c190_totals(
    report: ValidationReport,
    c100_line: int,
    c170_lines: list[tuple[int, list[str]]],
    c190_lines: list[tuple[int, list[str]]],
) -> None:
    """Compara a consolidação C190 com os itens C170 do mesmo C100."""

    if not c170_lines:
        return
    expected: dict[tuple[str, str, str], list[Decimal]] = {}
    for _, fields in c170_lines:
        cst = fields[9] if len(fields) > 9 else ""
        cfop = fields[10] if len(fields) > 10 else ""
        key = (cst, cfop, _rate_key(fields, 13, cst))
        values = expected.setdefault(key, [Decimal("0")] * 6)
        item_value = _decimal(fields, 6)
        values[0] += max(item_value - _decimal(fields, 7), Decimal("0"))  # VL_OPR
        values[1] += _decimal(fields, 12)  # VL_BC_ICMS
        values[2] += _decimal(fields, 14)  # VL_ICMS
        values[3] += _decimal(fields, 15)  # VL_BC_ICMS_ST
        values[4] += _decimal(fields, 17)  # VL_ICMS_ST
        if cst == "020":
            values[5] += max(item_value - _decimal(fields, 12), Decimal("0"))

    actual: dict[tuple[str, str, str], list[Decimal]] = {}
    actual_line: dict[tuple[str, str, str], int] = {}
    for line_number, fields in c190_lines:
        cst = fields[1] if len(fields) > 1 else ""
        cfop = fields[2] if len(fields) > 2 else ""
        key = (cst, cfop, _rate_key(fields, 3, cst))
        values = actual.setdefault(key, [Decimal("0")] * 6)
        for target_index, source_index in enumerate((4, 5, 6, 7, 8, 9)):
            values[target_index] += _decimal(fields, source_index)
        actual_line[key] = line_number

    labels = ("VL_OPR", "VL_BC_ICMS", "VL_ICMS", "VL_BC_ICMS_ST", "VL_ICMS_ST", "VL_RED_BC")
    for key, expected_values in expected.items():
        actual_values = actual.get(key)
        if actual_values is None:
            _add(report, c100_line, "c190.group.missing", "Totalizador C190 ausente para os itens C170.", "C190", "CST_ICMS", "|".join(key))
            continue
        for label, expected_value, actual_value in zip(labels, expected_values, actual_values):
            if abs(expected_value - actual_value) > Decimal("0.02"):
                _add(
                    report,
                    actual_line[key],
                    "c190.total.divergent",
                    f"{label} do C190 diverge da soma dos C170.",
                    "C190",
                    label,
                    f"esperado={expected_value:.2f}; informado={actual_value:.2f}",
                )


def validate_sped_lines(lines: Iterable[str]) -> ValidationReport:
    """Valida requisitos estruturais que podem ser conferidos sem o PVA."""

    content = [line for line in lines if line.strip()]
    report = ValidationReport("sped-file", "", "", 0)
    parsed = [_parts(line) for line in content]
    c100_keys: set[tuple[str, ...]] = set()
    started_blocks: list[str] = []
    current_c100_line = 0
    current_c170: list[tuple[int, list[str]]] = []
    current_c190: list[tuple[int, list[str]]] = []

    for line_number, fields in enumerate(parsed, start=1):
        if not fields or not fields[0]:
            continue
        record = fields[0]
        if record == "C100":
            _validate_c190_totals(report, current_c100_line, current_c170, current_c190)
            current_c100_line = line_number
            current_c170 = []
            current_c190 = []
            report.invoice_count += 1
            num_doc = fields[7] if len(fields) > 7 else ""
            if not num_doc:
                _add(report, line_number, "c100.num_doc.required", "NUM_DOC obrigatório não informado.", record, "NUM_DOC")
            key_indexes = (1, 7, 4, 5, 6, 8, 3)
            key = tuple(fields[index] if len(fields) > index else "" for index in key_indexes)
            if key in c100_keys:
                _add(report, line_number, "c100.key.duplicate", "Chave de C100 duplicada.", record, "NUM_DOC", num_doc)
            c100_keys.add(key)
        elif record == "C170":
            current_c170.append((line_number, fields))
            cst = fields[9] if len(fields) > 9 else ""
            if not cst:
                _add(report, line_number, "c170.cst.required", "CST_ICMS obrigatório não informado.", record, "CST_ICMS")
        elif record == "C190":
            current_c190.append((line_number, fields))
            cst = fields[1] if len(fields) > 1 else ""
            if not cst:
                _add(report, line_number, "c190.cst.required", "CST_ICMS obrigatório não informado.", record, "CST_ICMS")
        elif record.endswith("001") and len(record) == 4:
            started_blocks.append(record[0])

    _validate_c190_totals(report, current_c100_line, current_c170, current_c190)

    positions = {block: index for index, block in enumerate(BLOCK_ORDER)}
    block_indexes = [positions.get(block, -1) for block in started_blocks]
    if block_indexes != sorted(block_indexes):
        _add(report, 0, "block.order.invalid", "Blocos fora da ordem oficial do SPED.", "BLOCO", "REG")

    for block in dict.fromkeys(started_blocks):
        opener = f"{block}001"
        closer = f"{block}990"
        if block in {"0", "9"}:
            continue
        if not any(fields and fields[0] == closer for fields in parsed):
            _add(report, 0, "block.closer.missing", f"Fechamento {closer} não encontrado para {opener}.", opener, "REG")

    indexes = {fields[0]: index for index, fields in enumerate(parsed) if fields}
    if "9999" not in indexes:
        _add(report, 0, "file.9999.missing", "Registro 9999 não encontrado.", "9999", "REG")
    else:
        expected_total = len(parsed)
        reported_total = _number(parsed[indexes["9999"]], 1)
        if reported_total != expected_total:
            _add(report, indexes["9999"] + 1, "file.9999.count.invalid", "Total do 9999 diverge da quantidade de linhas.", "9999", "QTD_LIN_9", str(reported_total))

    if "9001" not in indexes or "9990" not in indexes:
        _add(report, 0, "block9.required.missing", "Registros 9001 ou 9990 não encontrados.", "9990", "REG")
    else:
        block9_lines = len(parsed[indexes["9001"]:])
        reported_block9 = _number(parsed[indexes["9990"]], 1)
        if reported_block9 != block9_lines:
            _add(report, indexes["9990"] + 1, "block9.count.invalid", "QTD_LIN_9 diverge das linhas do bloco 9.", "9990", "QTD_LIN_9", str(reported_block9))
    return report


def validate_sped_file(path: str | Path) -> ValidationReport:
    path = Path(path)
    return validate_sped_lines(path.read_text(encoding="utf-8-sig", errors="replace").splitlines())
