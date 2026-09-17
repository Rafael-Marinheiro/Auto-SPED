"""Casos de uso da aplicação Auto-SPED."""

from .capture_summary import CaptureSummary, build_capture_summary
from .corrections import (
    CorrectionConfirmationError,
    CorrectionPlan,
    CorrectionProposal,
    CorrectionReceipt,
    apply_confirmed_plan,
)
from .generation import GenerationResult, generate_sped
from .normalization import (
    digits_only,
    normalize_cest,
    normalize_cfop,
    normalize_cst,
    normalize_ncm,
    normalize_tax_rate,
    normalize_tipo_item,
)

__all__ = [
    "CaptureSummary", "build_capture_summary", "CorrectionConfirmationError",
    "CorrectionPlan", "CorrectionProposal", "CorrectionReceipt", "apply_confirmed_plan",
    "GenerationResult", "generate_sped", "digits_only", "normalize_cest",
    "normalize_cfop", "normalize_cst", "normalize_ncm", "normalize_tax_rate",
    "normalize_tipo_item",
]
