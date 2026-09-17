"""Tela inicial de emissão do Auto-SPED."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ..providers import FirebirdSaoPedroProvider
from ..services import build_capture_summary
from ..services.desktop_generation import GenerationRequest
from ..validation import validate_provider
from .capture_map_dialog import CaptureMapDialog
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
        QProgressBar,
        QPushButton,
        QTextEdit,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError as error:  # pragma: no cover - depende da instalação opcional
    raise RuntimeError("Instale a interface com: pip install -e '.[desktop]'") from error


class GenerationWorker(QObject):
    """Executa a emissão legada fora da thread visual."""

    status = Signal(str)
    progress = Signal(int)
    summary_ready = Signal(dict)
    preflight_ready = Signal(dict)
    completed = Signal(str)
    blocked = Signal(str)
    failed = Signal(str)

    def __init__(self, request: GenerationRequest) -> None:
        super().__init__()
        self.request = request

    @Slot()
    def run(self) -> None:
        try:
            self.progress.emit(5)
            self.status.emit("Capturando resumo do período…")
            provider = FirebirdSaoPedroProvider(
                str(self.request.database_path),
                str(self.request.client_library) if self.request.client_library else None,
            )
            summary = build_capture_summary(
                provider, self.request.start_date_iso, self.request.end_date_iso
            )
            self.summary_ready.emit(summary.to_dict())
            self.progress.emit(30)
            self.status.emit("Executando pré-validação fiscal…")
            report = validate_provider(
                provider, self.request.start_date_iso, self.request.end_date_iso
            )
            self.preflight_ready.emit(report.to_dict())
            self.progress.emit(55)
            if not report.is_valid:
                self.blocked.emit(
                    "A emissão foi bloqueada: corrija os erros da pré-validação e tente novamente."
                )
                return
            self.status.emit("Pré-validação aprovada. Gerando SPED pelo fluxo homologado…")
            from main_fast import main as generate_sped

            output = generate_sped(
                str(self.request.database_path),
                self.request.start_date_iso,
                self.request.end_date_iso,
                self.request.output_path,
                str(self.request.client_library) if self.request.client_library else None,
            )
            self.progress.emit(100)
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
        self.map_button = QPushButton("Ver mapa de captura")
        self.map_button.clicked.connect(self._show_capture_map)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        self.log.setPlaceholderText("O status da emissão aparecerá aqui.")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setPlaceholderText("O resumo da captura aparecerá antes da emissão.")
        self.report = QTextEdit()
        self.report.setReadOnly(True)
        self.report.setPlaceholderText("A pré-validação e suas inconsistências aparecerão aqui.")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(self._configuration_group())
        client_group = QGroupBox("Cliente Firebird")
        client_layout = QVBoxLayout(client_group)
        client_layout.addWidget(self.firebird_selector)
        layout.addWidget(client_group)
        actions = QHBoxLayout()
        actions.addWidget(self.emit_button)
        actions.addWidget(self.map_button)
        layout.addLayout(actions)
        layout.addWidget(self.progress)
        layout.addWidget(QLabel("Log da emissão"))
        layout.addWidget(self.log)
        tabs = QTabWidget()
        tabs.addTab(self.summary, "Resumo")
        tabs.addTab(self.report, "Pré-validação")
        layout.addWidget(tabs)
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

    def _show_capture_map(self) -> None:
        CaptureMapDialog(self).exec()

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
        self.summary.clear()
        self.report.clear()
        self.progress.setValue(0)
        self._append(f"Banco: {request.database_path}")
        self._append(f"Período: {request.start_date:%d/%m/%Y} a {request.end_date:%d/%m/%Y}")
        self._append(f"Cliente Firebird: {request.client_library or 'detecção automática'}")
        self._thread = QThread(self)
        self._worker = GenerationWorker(request)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.status.connect(self._append)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.summary_ready.connect(self._show_summary)
        self._worker.preflight_ready.connect(self._show_preflight)
        self._worker.completed.connect(self._completed)
        self._worker.blocked.connect(self._blocked)
        self._worker.failed.connect(self._failed)
        self._worker.completed.connect(self._thread.quit)
        self._worker.blocked.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    def _append(self, message: str) -> None:
        self.log.append(message)

    def _completed(self, output: str) -> None:
        self._append(f"Concluído: {output}")
        QMessageBox.information(self, "SPED emitido", f"Arquivo gerado com sucesso:\n{output}")

    def _blocked(self, message: str) -> None:
        self._append(message)
        QMessageBox.warning(self, "Emissão bloqueada", message)

    def _failed(self, message: str) -> None:
        self._append(f"Falha: {message}")
        QMessageBox.critical(self, "Emissão não concluída", message)

    def _show_summary(self, summary: dict) -> None:
        company = summary.get("company", {})
        self.summary.setPlainText(
            "\n".join(
                (
                    f"Empresa: {company.get('name', '')}",
                    f"CNPJ: {company.get('cnpj', '')}",
                    f"Período: {summary.get('start_date')} a {summary.get('end_date')}",
                    f"Participantes: {summary.get('participant_count', 0)}",
                    f"Produtos: {summary.get('product_count', 0)}",
                    f"Documentos: {summary.get('document_count', 0)}",
                    f"Total dos documentos: {summary.get('document_total', '0.00')}",
                )
            )
        )

    def _show_preflight(self, report: dict) -> None:
        errors = report.get("error_count", 0)
        warnings = report.get("warning_count", 0)
        lines = [
            f"Documentos analisados: {report.get('invoice_count', 0)}",
            f"Erros: {errors}",
            f"Avisos: {warnings}",
            "",
        ]
        for issue in report.get("issues", []):
            lines.append(
                "[{severity}] {record}.{field} em {source}: {message}".format(
                    severity=str(issue.get("severity", "")).upper(),
                    record=issue.get("sped_record", ""),
                    field=issue.get("field", ""),
                    source=issue.get("source_ref", ""),
                    message=issue.get("message", ""),
                )
            )
        self.report.setPlainText("\n".join(lines))

    def _cleanup_worker(self) -> None:
        if self._worker:
            self._worker.deleteLater()
        if self._thread:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None
        self.emit_button.setEnabled(True)
