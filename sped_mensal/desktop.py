"""Ponto de entrada da interface desktop inicial do Auto-SPED."""

from __future__ import annotations


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow
    except ImportError as error:  # pragma: no cover - depende da instalação opcional
        raise SystemExit("Instale a interface com: pip install -e '.[desktop]'") from error

    from .ui.firebird_selector import FirebirdClientSelector

    app = QApplication([])
    window = QMainWindow()
    window.setWindowTitle("Auto-SPED — Configuração Firebird")
    window.setCentralWidget(FirebirdClientSelector(window))
    window.resize(760, 180)
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
