"""Histórico local, sem conteúdo fiscal, de operações do Auto-SPED."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .corrections import CorrectionPlan, CorrectionReceipt
    from .desktop_generation import GenerationRequest


@dataclass(frozen=True)
class HistoryEvent:
    timestamp: str
    kind: str
    status: str
    provider_id: str
    period: str
    target: str = ""
    detail: str = ""


def default_history_path() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".auto-sped")
    return Path(base) / "Auto-SPED" / "history.jsonl"


class LocalHistoryStore:
    """Armazena metadados operacionais em JSONL com escrita durável."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else default_history_path()

    def append(self, event: HistoryEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(asdict(event), ensure_ascii=False, separators=(",", ":")) + "\n")
            output.flush()
            os.fsync(output.fileno())

    def record_emission(
        self, request: "GenerationRequest", status: str, target: str | Path = "", detail: str = ""
    ) -> None:
        self.append(
            HistoryEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                kind="emissão",
                status=status,
                provider_id=request.provider_id,
                period=f"{request.start_date_iso} a {request.end_date_iso}",
                target=Path(target).name if target else request.output_path.name,
                detail=detail,
            )
        )

    def record_correction(self, receipt: "CorrectionReceipt", plan: "CorrectionPlan") -> None:
        self.append(
            HistoryEvent(
                timestamp=receipt.committed_at.isoformat(),
                kind="correção",
                status="confirmada",
                provider_id=plan.source_id,
                period=plan.period,
                target=receipt.transaction_id,
                detail=f"{receipt.applied_count} alteração(ões); plano {receipt.plan_token}",
            )
        )

    def list_events(self, limit: int = 200) -> list[HistoryEvent]:
        if not self.path.is_file() or limit <= 0:
            return []
        events: list[HistoryEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
                events.append(HistoryEvent(**item))
            except (json.JSONDecodeError, TypeError):
                continue
        return list(reversed(events[-limit:]))
