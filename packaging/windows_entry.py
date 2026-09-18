"""Entrada estável usada pelo empacotador Windows."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import traceback

from sped_mensal.desktop import main


def _report_startup_error(error: BaseException) -> None:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
    log_path = Path(base) / "Auto-SPED" / "startup-error.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    detail = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    log_path.write_text(detail, encoding="utf-8")
    if os.environ.get("AUTO_SPED_NO_DIALOG") != "1":
        ctypes.windll.user32.MessageBoxW(
            0,
            f"O Auto-SPED não conseguiu iniciar.\n\nDetalhes: {log_path}",
            "Auto-SPED",
            0x10,
        )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as error:
        _report_startup_error(error)
        raise SystemExit(1) from error
