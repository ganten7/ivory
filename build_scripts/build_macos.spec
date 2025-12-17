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
        'PyQt5.QtBluetooth',
        'PyQt5.QtNfc',
        'PyQt5.QtWebSockets',
        'PyQt5.QtWebEngine',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtQuick',
        'PyQt5.QtQml',
        'PyQt5.Qt3D',
        'PyQt5.QtGamepad',
        'PyQt5.QtLocation',
        'PyQt5.QtPositioning',
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
    [],
    exclude_binaries=True,
    name='Ivory',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # CRITICAL FIX: Disable UPX compression to prevent PKG archive corruption
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # CRITICAL FIX: Disable UPX compression in COLLECT as well
    upx_exclude=[],
    name='Ivory',
)

app = BUNDLE(
    coll,
    name='Ivory.app',
    icon='../screenshots/icon.icns' if os.path.exists('../screenshots/icon.icns') else None,
    bundle_identifier='com.ivory.midikeyboard',
    info_plist={
        'CFBundleName': 'Ivory',
        'CFBundleDisplayName': 'Ivory',
        'CFBundleVersion': '1.0.1',
        'CFBundleShortVersionString': '1.0.1',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13',
        'LSApplicationCategoryType': 'public.app-category.music',
        'NSHumanReadableCopyright': 'Copyright © 2025',
        'CFBundlePackageType': 'APPL',
        'CFBundleExecutable': 'Ivory',
    },
)
