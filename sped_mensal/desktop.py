"""Ponto de entrada da interface desktop inicial do Auto-SPED."""

from __future__ import annotations


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as error:  # pragma: no cover - depende da instalação opcional
        raise SystemExit("Instale a interface com: pip install -e '.[desktop]'") from error

    from .ui.main_window import AutoSpedMainWindow

    app = QApplication([])
    window = AutoSpedMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
