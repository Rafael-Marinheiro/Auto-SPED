"""Casos de uso da aplicação Auto-SPED."""

from .capture_summary import CaptureSummary, build_capture_summary
from .corrections import (
    CorrectionConfirmationError,
    CorrectionPlan,
    CorrectionProposal,
    CorrectionReceipt,
    apply_confirmed_plan,
    apply_confirmed_plan_with_audit,
)
from .generation import GenerationResult, generate_sped
from .normalization import (
    digits_only,
    format_sped_decimal,
    normalize_access_key,
    normalize_cest,
    normalize_cfop,
    normalize_cst,
    normalize_document_status,
    normalize_fiscal_item_mapping,
    normalize_ipi_cst,
    normalize_product_mapping,
    normalize_sped_date,
    format_sped_money,
    normalize_municipality_code,
    normalize_ncm,
    normalize_person_ids,
    parse_fiscal_date,
    parse_sped_decimal,
    normalize_tax_rate,
    normalize_tipo_item,
)
from .revenue_code import (
    STATE_REVENUE_CODE_RULES,
    StateRevenueCodeRule,
    normalize_revenue_code,
    resolve_e116_revenue_code,
)

__all__ = [
    "CaptureSummary", "build_capture_summary", "CorrectionConfirmationError",
    "CorrectionPlan", "CorrectionProposal", "CorrectionReceipt", "apply_confirmed_plan", "apply_confirmed_plan_with_audit",
    "GenerationResult", "generate_sped", "digits_only", "format_sped_decimal", "normalize_access_key",
    "normalize_cest", "normalize_cfop", "normalize_cst",
    "normalize_document_status", "normalize_sped_date", "format_sped_money",
    "normalize_fiscal_item_mapping", "normalize_ipi_cst", "normalize_product_mapping",
    "normalize_municipality_code", "normalize_ncm", "normalize_person_ids",
    "parse_fiscal_date", "parse_sped_decimal",
    "normalize_tax_rate", "normalize_tipo_item",
    "STATE_REVENUE_CODE_RULES", "StateRevenueCodeRule",
    "normalize_revenue_code", "resolve_e116_revenue_code",
]
