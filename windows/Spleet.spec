# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Spleet — Offline Stem Splitter."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent
SHARED = ROOT / "shared"

# Collect full packages
demucs_d, demucs_b, demucs_h = collect_all("demucs")
torch_d, torch_b, torch_h = collect_all("torch")
ta_d, ta_b, ta_h = collect_all("torchaudio")

a = Analysis(
    ["app.py"],
    pathex=[str(SHARED)],
    binaries=demucs_b + torch_b + ta_b,
    datas=demucs_d + torch_d + ta_d + [
        (str(SHARED / "models"), "models"),
        (str(SHARED / "assets"), "assets"),
    ],
    hiddenimports=demucs_h + torch_h + ta_h + [
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "scipy.tests", "tkinter",
        "pytest", "IPython", "notebook",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Spleet",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX can break torch DLLs
    console=False,       # No console window
    icon=str(SHARED / "assets" / "logo.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Spleet",
)
