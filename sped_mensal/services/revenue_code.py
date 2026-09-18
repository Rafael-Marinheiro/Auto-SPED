"""Seleção segura do código de receita estadual do registro E116."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StateRevenueCodeRule:
    """Código geral de apuração mensal confirmado em publicação oficial."""

    code: str
    description: str
    source_url: str
    verified_on: str


# Só entram aqui códigos gerais e inequívocos para a apuração própria mensal.
# UFs com códigos dependentes de atividade/regime permanecem fora do mapa.
STATE_REVENUE_CODE_RULES: dict[str, StateRevenueCodeRule] = {
    "AP": StateRevenueCodeRule(
        "1111", "ICMS normal — declaração",
        "https://sefaz.portal.ap.gov.br/conteudo/orientacoes/codigos-de-receitas",
        "2026-09-17",
    ),
    "CE": StateRevenueCodeRule(
        "1015", "ICMS regime mensal de apuração",
        "https://sefazlegis.sefaz.ce.gov.br/api/openFile?id=61b80fab-6f46-4663-a08b-5ccdaf5e4052",
        "2026-09-17",
    ),
    "GO": StateRevenueCodeRule(
        "108", "ICMS normal",
        "https://orientacaotributaria.economia.go.gov.br/spo-web/perguntasfrequentes/perguntafrequente/20469",
        "2026-09-17",
    ),
    "PB": StateRevenueCodeRule(
        "1101", "ICMS normal",
        "https://www.sefaz.pb.gov.br/info/79-servicos/1297-emissao-do-dar",
        "2026-09-17",
    ),
    "PE": StateRevenueCodeRule(
        "005-1", "ICMS normal",
        "https://www.sefaz.pe.gov.br/Servicos/Programa-de-Conformidade-e-Autorregularizacao-Coopera/Paginas/validacao-preliminar-EFD.aspx",
        "2026-09-17",
    ),
    "PR": StateRevenueCodeRule(
        "1015", "Regime mensal de apuração",
        "https://atendimento.fazenda.pr.gov.br/sacsefa/portal/assuntosReferente/12",
        "2026-09-17",
    ),
    "RJ": StateRevenueCodeRule(
        "021-3", "ICMS normal",
        "https://portal.fazenda.rj.gov.br/fisco-facil/wp-content/uploads/sites/28/2023/09/manual-Fisco-Facil-versao11.pdf",
        "2026-09-17",
    ),
    "RN": StateRevenueCodeRule(
        "1210", "ICMS regime mensal de apuração",
        "https://webdisk.diariooficial.rn.gov.br/Jornal/12022-08-19.pdf",
        "2026-09-17",
    ),
    "SC": StateRevenueCodeRule(
        "1449", "ICMS normal",
        "https://legislacao.sef.sc.gov.br/html/portarias/2024/port_24_017.htm",
        "2026-09-17",
    ),
    "SP": StateRevenueCodeRule(
        "046-2", "Regime periódico de apuração",
        "https://legislacao.fazenda.sp.gov.br/Paginas/pcat1472009.aspx",
        "2026-09-17",
    ),
}
_COMPANY_FIELDS = ("COD_REC_E116", "E116_COD_REC", "COD_REC")


def normalize_revenue_code(value: Any) -> str:
    """Valida um código textual sem alterar a classificação definida pela UF."""

    code = "" if value is None else str(value).strip()
    if not code or len(code) > 32 or "|" in code or not code.isprintable():
        raise ValueError("Código de receita E116 inválido.")
    return code


def resolve_e116_revenue_code(
    company_info: Mapping[str, Any], emission_code: Any | None = None
) -> str:
    """Resolve o código pela emissão, empresa e, por fim, padrão confirmado da UF."""

    if emission_code is not None:
        return normalize_revenue_code(emission_code)

    for field in _COMPANY_FIELDS:
        configured = company_info.get(field)
        if configured is not None and str(configured).strip():
            return normalize_revenue_code(configured)

    state = str(company_info.get("UF") or "").strip().upper()
    state_rule = STATE_REVENUE_CODE_RULES.get(state)
    if state_rule is not None:
        return state_rule.code

    state_label = state or "não informada"
    raise ValueError(
        "Código de receita E116 não configurado para a empresa/UF "
        f"{state_label}. Informe o código de receita desta emissão."
    )
