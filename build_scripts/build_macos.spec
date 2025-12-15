# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

a = Analysis(
    ['../ivory_v2.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../chord_detector_v2.py', '.'),
        ('../screenshots', 'screenshots'),
    ],
    hiddenimports=[
        'mido',
        'mido.backends.rtmidi',
        'rtmidi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    upx=True,
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
    upx=True,
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
    },
)
