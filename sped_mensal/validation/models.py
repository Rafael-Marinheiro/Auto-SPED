"""Modelos de resultado da validação fiscal."""

from __future__ import annotations

from dataclasses import dataclass, field

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - compatibilidade com Python 3.10
    from enum import Enum

    class StrEnum(str, Enum):
        """Compatibilidade mínima com enum.StrEnum do Python 3.11+."""


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationIssue:
    """Uma inconsistência rastreável até a fonte e o registro SPED."""

    severity: ValidationSeverity
    code: str
    message: str
    sped_record: str
    field: str
    source_ref: str
    value: str = ""
    suggestion: str = ""


@dataclass
class ValidationReport:
    """Resultado serializável para CLI, interface e auditoria."""

    provider_id: str
    start_date: str
    end_date: str
    invoice_count: int
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(issue.severity == ValidationSeverity.ERROR for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == ValidationSeverity.WARNING for issue in self.issues)

    @property
    def is_valid(self) -> bool:
        return self.error_count == 0

    def add(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)

    def add_issue(self, **kwargs: object) -> None:
        """Atalho para validadores que constroem ocorrências por campo."""

        self.add(ValidationIssue(**kwargs))  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, object]:
        """Formato estável para interface, automações e auditoria local."""

        return {
            "provider_id": self.provider_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "invoice_count": self.invoice_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "is_valid": self.is_valid,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "code": issue.code,
                    "message": issue.message,
                    "sped_record": issue.sped_record,
                    "field": issue.field,
                    "source_ref": issue.source_ref,
                    "value": issue.value,
                    "suggestion": issue.suggestion,
                }
                for issue in self.issues
            ],
        }
