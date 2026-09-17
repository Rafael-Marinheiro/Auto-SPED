"""Tela somente leitura do mapa entre o ERP e o arquivo SPED."""

from __future__ import annotations

from ..providers import FirebirdSaoPedroProvider
from ..services.capture_map import transformation_for

try:  # A interface é uma dependência opcional.
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


class CaptureMapDialog(QDialog):
    """Tabela de rastreabilidade: origem, transformação e destino SPED."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Auto-SPED — Mapa de captura")
        self.resize(1100, 620)
        mappings = FirebirdSaoPedroProvider("DADOS.FDB").describe_capture()

        table = QTableWidget(len(mappings), 4, self)
        table.setHorizontalHeaderLabels(("Dado fiscal", "Origem Firebird", "Transformação", "Destino SPED"))
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        for row, mapping in enumerate(mappings):
            values = (
                f"{mapping.entity}.{mapping.fiscal_field}",
                mapping.source,
                transformation_for(mapping.source),
                ", ".join(mapping.sped_targets),
            )
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)

        explanation = QLabel(
            "Consulta somente leitura: este mapa não abre nem altera o banco de dados."
        )
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(explanation)
        layout.addWidget(table)
        layout.addWidget(buttons)
        self.table = table
