# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Remind.
Build with: pyinstaller remind.spec
"""

a = Analysis(
    ['remind/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['remind', 'remind.cli', 'remind.db', 'remind.config', 'remind.models', 'remind.scheduler', 'remind.notifications', 'remind.premium', 'remind.ai', 'remind.plugins'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='remind',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
