# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get project root - use current working directory
project_root = Path.cwd()

a = Analysis(
    ['app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / 'templates'), 'templates'),
        (str(project_root / 'static'), 'static'),
        (str(project_root / 'routes'), 'routes'),
        (str(project_root / 'services'), 'services'),
        (str(project_root / 'models.py'), '.'),
        (str(project_root / 'config.py'), '.'),
        (str(project_root / 'extensions.py'), '.'),
    ],
    hiddenimports=[],
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
