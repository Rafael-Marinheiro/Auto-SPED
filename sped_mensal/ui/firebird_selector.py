"""Seletor PySide6 do cliente Firebird usado em uma emissão."""

from __future__ import annotations

from pathlib import Path

from ..services.firebird_client import (
    FirebirdClientOption,
    detect_installed_clients,
    download_official_client,
    official_client_options,
    python_architecture,
)


try:  # Mantém o núcleo utilizável sem a dependência opcional de desktop.
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QFileDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QProgressDialog,
        QVBoxLayout,
        QWidget,
    )
except ImportError as error:  # pragma: no cover - depende da instalação opcional
    raise RuntimeError("Instale a interface com: pip install -e '.[desktop]'") from error


class FirebirdClientSelector(QWidget):
    """Escolhe uma DLL local ou baixa um ZIP oficial para o perfil do usuário."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manual_path: Path | None = None
        self._installed = list(detect_installed_clients())
        self._downloads = list(official_client_options())

        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._update_status)
        self.status = QLabel()
        self.status.setWordWrap(True)
        browse = QPushButton("Escolher DLL…")
        browse.clicked.connect(self._choose_file)
        download = QPushButton("Baixar versão selecionada")
        download.clicked.connect(self._download_selected)
        refresh = QPushButton("Atualizar instalações")
        refresh.clicked.connect(self._refresh)

        buttons = QHBoxLayout()
        buttons.addWidget(browse)
        buttons.addWidget(download)
        buttons.addWidget(refresh)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("Cliente Firebird:", self.combo)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.status)
        self._populate()

    def selected_path(self) -> str | None:
        """Caminho que deve ser passado a ``--fbclient`` na emissão."""
        option = self.combo.currentData(Qt.ItemDataRole.UserRole)
        if isinstance(option, FirebirdClientOption) and option.path:
            return str(option.path)
        return str(self._manual_path) if self._manual_path else None

    def _populate(self) -> None:
        current = self.selected_path()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem("Selecionar uma DLL instalada ou uma versão para baixar", None)
        for option in self._installed:
            self.combo.addItem(option.label, option)
        self.combo.insertSeparator(self.combo.count())
        for option in self._downloads:
            self.combo.addItem(option.label, option)
        self.combo.blockSignals(False)
        if current:
            for index in range(self.combo.count()):
                option = self.combo.itemData(index, Qt.ItemDataRole.UserRole)
                if isinstance(option, FirebirdClientOption) and option.path and str(option.path) == current:
                    self.combo.setCurrentIndex(index)
                    break
        self._update_status()

    def _refresh(self) -> None:
        self._installed = list(detect_installed_clients())
        self._populate()

    def _choose_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Selecionar fbclient.dll", "", "Firebird client (fbclient.dll)")
        if filename:
            path = Path(filename)
            option = FirebirdClientOption("manual", 0, path=path)
            self._installed.append(option)
            self._manual_path = path
            self._populate()
            self.combo.setCurrentIndex(self.combo.findData(option, Qt.ItemDataRole.UserRole))

    def _download_selected(self) -> None:
        option = self.combo.currentData(Qt.ItemDataRole.UserRole)
        if not isinstance(option, FirebirdClientOption) or not option.source_url:
            QMessageBox.information(self, "Firebird", "Selecione uma versão marcada como download oficial.")
            return
        if option.architecture != python_architecture():
            QMessageBox.warning(self, "Arquitetura incompatível", f"Este Python é {python_architecture()} bits. Selecione a DLL da mesma arquitetura.")
            return
        progress = QProgressDialog("Baixando kit oficial Firebird…", "", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        def on_progress(received: int, total: int | None) -> None:
            if total:
                progress.setValue(min(99, round(received * 100 / total)))

        try:
            path = download_official_client(option, progress=on_progress)
        except Exception as error:
            QMessageBox.critical(self, "Download não concluído", str(error))
            return
        finally:
            progress.close()
        self._installed = list(detect_installed_clients())
        self._manual_path = path
        self._populate()
        QMessageBox.information(self, "Firebird", f"Cliente disponível em:\n{path}")

    def _update_status(self) -> None:
        option = self.combo.currentData(Qt.ItemDataRole.UserRole)
        if not isinstance(option, FirebirdClientOption):
            self.status.setText(f"Python atual: {python_architecture()} bits. A DLL deve ter a mesma arquitetura.")
        elif option.path:
            architecture = option.architecture or "não identificada"
            self.status.setText(f"Usará: {option.path}\nArquitetura identificada: {architecture}.")
        else:
            warning = " Esta versão está fora de suporte." if option.end_of_life else ""
            self.status.setText(f"Será baixado do projeto oficial Firebird.{warning}")
