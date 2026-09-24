# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = [
    'backend',
    'ui',
    'dashboard_client',
    'clr',
    'clr_loader',
]
hiddenimports += collect_submodules('webview')


a = Analysis(
    ['desktop\\app.py'],
    pathex=['e:\\ServerHealthMonitor', 'e:\\ServerHealthMonitor\\desktop'],
    binaries=[('build\\server-health-monitor-console.exe', '.')],
    datas=[],
    hiddenimports=hiddenimports,
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
    name='ServerHealthMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
