"""Consulta do histórico operacional local do Auto-SPED."""

from __future__ import annotations

from ..services.history import LocalHistoryStore

try:  # A camada desktop é opcional.
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QHeaderView,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )
except ImportError as error:  # pragma: no cover - depende da instalação opcional
    raise RuntimeError("Instale a interface com: pip install -e '.[desktop]'") from error


class HistoryDialog(QDialog):
    """Mostra emissões e correções sem expor dados das notas fiscais."""

    def __init__(self, parent=None, store: LocalHistoryStore | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Auto-SPED — Histórico local")
        self.resize(1050, 500)
        self._store = store or LocalHistoryStore()
        events = self._store.list_events()
        table = QTableWidget(len(events), 7, self)
        table.setHorizontalHeaderLabels(("Data/hora (UTC)", "Operação", "Status", "Capturador", "Período", "Destino/ID", "Detalhe"))
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for row, event in enumerate(events):
            for column, value in enumerate((event.timestamp, event.kind, event.status, event.provider_id, event.period, event.target, event.detail)):
                table.setItem(row, column, QTableWidgetItem(value))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Arquivo local: {self._store.path}"))
        layout.addWidget(table)
        layout.addWidget(buttons)
        self.table = table
