"""Adaptadores para a captura de dados fiscais por ERP ou fonte."""

from .base import CaptureMapping, FiscalDataProvider
from .firebird_sao_pedro import FirebirdSaoPedroProvider
from .firebird_corrections import FirebirdCompraCorrectionExecutor
from .reference import (
    CanonicalDatasetProvider,
    CsvDirectoryProvider,
    PostgresProvider,
    PostgresQueries,
    XmlFileProvider,
)

__all__ = [
    "CaptureMapping", "FiscalDataProvider", "FirebirdSaoPedroProvider",
    "FirebirdCompraCorrectionExecutor", "CanonicalDatasetProvider",
    "CsvDirectoryProvider", "XmlFileProvider", "PostgresProvider", "PostgresQueries",
]
