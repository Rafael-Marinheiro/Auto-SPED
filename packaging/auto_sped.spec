from pathlib import Path


project_root = Path(SPECPATH).parent

analysis = Analysis(
    [str(project_root / "packaging" / "windows_entry.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / "README.md"), "."),
        (str(project_root / "docs" / "FIREBIRD_SETUP.md"), "docs"),
    ],
    hiddenimports=["fdb", "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["psycopg"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Auto-SPED",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Auto-SPED",
)
