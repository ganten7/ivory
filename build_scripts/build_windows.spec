# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

a = Analysis(
    ['../ivory_v2.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../chord_detector_v2.py', '.'),
        ('../screenshots', 'screenshots'),
    ] + ([('../icons', 'icons')] if os.path.exists('../icons') else []),  # Include icons directory if it exists
    hiddenimports=[
        'chord_detector_v2',  # Explicit import for chord detector module
        'mido',
        'mido.backends.rtmidi',
        'rtmidi',
        # PyQt5 modules - explicit imports for better compatibility
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
    ] + collect_submodules('mido') + collect_submodules('rtmidi'),  # Collect all mido/rtmidi submodules
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Ivory',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # CRITICAL FIX: Disable UPX compression to prevent PKG archive corruption
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # TEMPORARY: Enable console to see error messages for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../screenshots/icon.ico' if os.path.exists('../screenshots/icon.ico') else None,
)
