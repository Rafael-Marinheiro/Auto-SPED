from pathlib import Path


def test_desktop_window_contains_summary_and_preflight_renderers():
    source = Path("sped_mensal/ui/main_window.py").read_text(encoding="utf-8")

    assert "def _show_summary" in source
    assert "def _show_preflight" in source
    assert "A emissão foi bloqueada" in source
