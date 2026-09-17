"""Validador estrutural do TXT SPED, independente do banco de dados."""

from __future__ import annotations

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


def validate_sped_lines(lines: Iterable[str]) -> ValidationReport:
    """Valida requisitos estruturais que podem ser conferidos sem o PVA."""

    content = [line for line in lines if line.strip()]
    report = ValidationReport("sped-file", "", "", 0)
    parsed = [_parts(line) for line in content]
    c100_keys: set[tuple[str, ...]] = set()
    started_blocks: list[str] = []

    for line_number, fields in enumerate(parsed, start=1):
        if not fields or not fields[0]:
            continue
        record = fields[0]
        if record == "C100":
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
            cst = fields[9] if len(fields) > 9 else ""
            if not cst:
                _add(report, line_number, "c170.cst.required", "CST_ICMS obrigatório não informado.", record, "CST_ICMS")
        elif record == "C190":
            cst = fields[1] if len(fields) > 1 else ""
            if not cst:
                _add(report, line_number, "c190.cst.required", "CST_ICMS obrigatório não informado.", record, "CST_ICMS")
        elif record.endswith("001") and len(record) == 4:
            started_blocks.append(record[0])

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
