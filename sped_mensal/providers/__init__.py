"""Adaptadores para a captura de dados fiscais por ERP ou fonte."""

from .base import CaptureMapping, FiscalDataProvider
from .firebird_sao_pedro import FirebirdSaoPedroProvider

__all__ = ["CaptureMapping", "FiscalDataProvider", "FirebirdSaoPedroProvider"]
