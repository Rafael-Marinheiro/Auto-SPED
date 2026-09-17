"""Tela inicial de emissão do Auto-SPED."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ..services.desktop_generation import GenerationRequest
from .firebird_selector import FirebirdClientSelector

try:  # A camada desktop é opcional para uso via CLI.
    from PySide6.QtCore import QDate, QObject, QThread, Signal, Slot
    from PySide6.QtWidgets import (
        QComboBox,
        QDateEdit,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError as error:  # pragma: no cover - depende da instalação opcional
    raise RuntimeError("Instale a interface com: pip install -e '.[desktop]'") from error


class GenerationWorker(QObject):
    """Executa a emissão legada fora da thread visual."""

    status = Signal(str)
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, request: GenerationRequest) -> None:
        super().__init__()
        self.request = request

    @Slot()
    def run(self) -> None:
        try:
            self.status.emit("Iniciando emissão pelo fluxo homologado…")
            from main_fast import main as generate_sped

            output = generate_sped(
                str(self.request.database_path),
                self.request.start_date_iso,
                self.request.end_date_iso,
                self.request.output_path,
                str(self.request.client_library) if self.request.client_library else None,
            )
            self.completed.emit(str(output.resolve()))
        except Exception as error:  # A interface apresenta a causa ao operador.
            self.failed.emit(str(error))


class AutoSpedMainWindow(QMainWindow):
    """Formulário de emissão que mantém configurações explícitas e revisáveis."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Auto-SPED — Emissão")
        self._thread: QThread | None = None
        self._worker: GenerationWorker | None = None

        today = date.today()
        self.provider = QComboBox()
        self.provider.addItem("Firebird — ERP São Pedro", "firebird-sao-pedro")
        self.database = QLineEdit()
        self.output = QLineEdit(f"saida_sped_out_{today:%Y-%m}.txt")
        self.start_date = QDateEdit(QDate(today.year, today.month, 1))
        self.end_date = QDateEdit(QDate(today.year, today.month, today.day))
        for control in (self.start_date, self.end_date):
            control.setCalendarPopup(True)
            control.setDisplayFormat("dd/MM/yyyy")

        self.firebird_selector = FirebirdClientSelector()
        self.emit_button = QPushButton("Emitir SPED")
        self.emit_button.clicked.connect(self._emit)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        self.log.setPlaceholderText("O status da emissão aparecerá aqui.")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(self._configuration_group())
        client_group = QGroupBox("Cliente Firebird")
        client_layout = QVBoxLayout(client_group)
        client_layout.addWidget(self.firebird_selector)
        layout.addWidget(client_group)
        layout.addWidget(self.emit_button)
        layout.addWidget(QLabel("Log da emissão"))
        layout.addWidget(self.log)
        self.setCentralWidget(content)
        self.resize(820, 660)

    def _configuration_group(self) -> QGroupBox:
        group = QGroupBox("Dados da emissão")
        form = QFormLayout(group)
        form.addRow("Capturador:", self.provider)
        form.addRow("Banco Firebird:", self._path_field(self.database, self._choose_database))
        form.addRow("Data inicial:", self.start_date)
        form.addRow("Data final:", self.end_date)
        form.addRow("Arquivo SPED:", self._path_field(self.output, self._choose_output))
        return group

    @staticmethod
    def _path_field(field: QLineEdit, callback) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        button = QPushButton("Procurar…")
        button.clicked.connect(callback)
        layout.addWidget(field)
        layout.addWidget(button)
        return wrapper

    def _choose_database(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Selecionar banco Firebird", "", "Firebird (*.fdb *.FDB);;Todos (*.*)")
        if filename:
            self.database.setText(filename)

    def _choose_output(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar arquivo SPED", self.output.text(), "SPED (*.txt)")
        if filename:
            self.output.setText(filename)

    def _request(self) -> GenerationRequest:
        client = self.firebird_selector.selected_path()
        return GenerationRequest(
            provider_id=str(self.provider.currentData()),
            database_path=Path(self.database.text().strip()),
            start_date=self.start_date.date().toPython(),
            end_date=self.end_date.date().toPython(),
            output_path=Path(self.output.text().strip()),
            client_library=Path(client) if client else None,
        )

    @Slot()
    def _emit(self) -> None:
        try:
            request = self._request()
            request.validate()
        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "Revise a emissão", str(error))
            return

        self.emit_button.setEnabled(False)
        self.log.clear()
        self._append(f"Banco: {request.database_path}")
        self._append(f"Período: {request.start_date:%d/%m/%Y} a {request.end_date:%d/%m/%Y}")
        self._append(f"Cliente Firebird: {request.client_library or 'detecção automática'}")
        self._thread = QThread(self)
        self._worker = GenerationWorker(request)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.status.connect(self._append)
        self._worker.completed.connect(self._completed)
        self._worker.failed.connect(self._failed)
        self._worker.completed.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    def _append(self, message: str) -> None:
        self.log.append(message)

    def _completed(self, output: str) -> None:
        self._append(f"Concluído: {output}")
        QMessageBox.information(self, "SPED emitido", f"Arquivo gerado com sucesso:\n{output}")

    def _failed(self, message: str) -> None:
        self._append(f"Falha: {message}")
        QMessageBox.critical(self, "Emissão não concluída", message)

    def _cleanup_worker(self) -> None:
        if self._worker:
            self._worker.deleteLater()
        if self._thread:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None
        self.emit_button.setEnabled(True)
