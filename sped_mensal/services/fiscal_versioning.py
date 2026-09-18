"""Catálogo versionado de leiautes e regras fiscais da EFD ICMS/IPI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class FiscalRuleSet:
    """Identifica um conjunto auditável de regras aplicável a uma competência."""

    rule_set_id: str
    layout_version: str
    guide_version: str
    technical_note: str
    effective_from: date
    effective_to: date
    official_url: str

    def covers(self, start_date: date, end_date: date) -> bool:
        return self.effective_from <= start_date and end_date <= self.effective_to


FISCAL_RULE_SETS: tuple[FiscalRuleSet, ...] = (
    FiscalRuleSet(
        rule_set_id="efd-icms-ipi-2024.1",
        layout_version="018",
        guide_version="3.1",
        technical_note="Nota Técnica 2023.001 v1.2",
        effective_from=date(2024, 1, 1),
        effective_to=date(2024, 12, 31),
        official_url="https://sped.rfb.gov.br/item/show/1573",
    ),
    FiscalRuleSet(
        rule_set_id="efd-icms-ipi-2025.1",
        layout_version="019",
        guide_version="3.1",
        technical_note="Nota Técnica 2024.001 v1.0",
        effective_from=date(2025, 1, 1),
        effective_to=date(2025, 12, 31),
        official_url="https://sped.rfb.gov.br/item/show/1573",
    ),
    FiscalRuleSet(
        rule_set_id="efd-icms-ipi-2026.1",
        layout_version="020",
        guide_version="3.2.2",
        technical_note="Nota Técnica 2025.001 v1.0",
        effective_from=date(2026, 1, 1),
        effective_to=date(2026, 12, 31),
        official_url="https://sped.rfb.gov.br/item/show/7819",
    ),
)

SUPPORTED_LAYOUT_VERSIONS: tuple[str, ...] = tuple(
    rule_set.layout_version for rule_set in FISCAL_RULE_SETS
)


def _parse_period_date(value: str | date, field_name: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} deve estar no formato YYYY-MM-DD.") from error


def normalize_layout_version(value: str) -> str:
    """Normaliza uma versão informada e recusa versões não cadastradas."""

    text = str(value).strip()
    if not text.isdigit() or len(text) > 3:
        raise ValueError("Versão do leiaute deve conter até três dígitos.")
    normalized = text.zfill(3)
    if normalized not in SUPPORTED_LAYOUT_VERSIONS:
        supported = ", ".join(SUPPORTED_LAYOUT_VERSIONS)
        raise ValueError(
            f"Versão do leiaute {normalized} não cadastrada. Versões disponíveis: {supported}."
        )
    return normalized


def resolve_fiscal_rule_set(
    start_date: str | date,
    end_date: str | date,
    requested_layout: str | None = None,
) -> FiscalRuleSet:
    """Resolve a regra pela competência e bloqueia combinações fiscais inseguras."""

    period_start = _parse_period_date(start_date, "Data inicial")
    period_end = _parse_period_date(end_date, "Data final")
    if period_start > period_end:
        raise ValueError("A data inicial não pode ser posterior à data final.")

    rule_set = next(
        (rule for rule in FISCAL_RULE_SETS if rule.covers(period_start, period_end)),
        None,
    )
    if rule_set is None:
        first = FISCAL_RULE_SETS[0].effective_from.isoformat()
        last = FISCAL_RULE_SETS[-1].effective_to.isoformat()
        raise ValueError(
            "Não há um único conjunto de regras fiscais cadastrado para todo o período "
            f"{period_start.isoformat()} a {period_end.isoformat()}. "
            f"O catálogo atual cobre competências entre {first} e {last}."
        )

    if requested_layout is not None:
        normalized = normalize_layout_version(requested_layout)
        if normalized != rule_set.layout_version:
            raise ValueError(
                f"O leiaute {normalized} não é válido para o período informado; "
                f"use o leiaute {rule_set.layout_version}."
            )
    return rule_set


def resolve_layout_version(
    start_date: str | date,
    end_date: str | date,
    requested_layout: str | None = None,
) -> str:
    """Retorna somente o COD_VER aplicável ao período."""

    return resolve_fiscal_rule_set(start_date, end_date, requested_layout).layout_version
