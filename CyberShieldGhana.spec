# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Get project root - use current working directory
project_root = Path.cwd()

# Firebase Admin SDK ships data files (JSON service configs) and has many
# submodules; collect them explicitly so the bundled exe works offline.
firebase_datas, firebase_binaries, firebase_hiddenimports = collect_all('firebase_admin')
firestore_datas, firestore_binaries, firestore_hiddenimports = collect_all('google.cloud.firestore')

a = Analysis(
    ['app.py'],
    pathex=[str(project_root)],
    binaries=firebase_binaries + firestore_binaries,
    datas=[
        (str(project_root / 'templates'), 'templates'),
        (str(project_root / 'static'), 'static'),
        (str(project_root / 'routes'), 'routes'),
        (str(project_root / 'services'), 'services'),
        (str(project_root / 'models.py'), '.'),
        (str(project_root / 'config.py'), '.'),
        (str(project_root / 'extensions.py'), '.'),
    ] + firebase_datas + firestore_datas,
    hiddenimports=[
        'firebase_admin.credentials',
        'firebase_admin.firestore',
        'firebase_admin.auth',
        'firebase_admin._token_gen',
        'google.cloud.firestore',
        'grpc',
        'grpc._channel',
    ] + firebase_hiddenimports + firestore_hiddenimports + collect_submodules('google.api_core'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CyberShieldGhana',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
