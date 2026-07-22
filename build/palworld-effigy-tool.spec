# -*- mode: python ; coding: utf-8 -*-
# Single-exe distribution build: windowed GUI (grant_gui) with palsav, the
# palooz Oodle extension, relic_master.json and the Cattiva icon bundled. v1.2
# Copyright © 2026 AvenisLabs (https://avenislabs.com)
# for KarasWorlds.com (https://karasworlds.com). All rights reserved.

a = Analysis(
    ['..\\grant_gui.py'],
    pathex=['F:/Workspace/Palworld_effigy', 'F:/Workspace/palworld/tools/paldex_import/cache/PalworldSaveTools/src/palsav', 'F:/Workspace/palworld/tools/paldex_import/cache/PalworldSaveTools/src/palsav/palooz/build/lib.win-amd64-cpython-312'],
    binaries=[],
    datas=[('F:/Workspace/Palworld_effigy/relic_master.json', '.'),
           ('F:/Workspace/Palworld_effigy/assets/cattiva.ico', '.')],
    hiddenimports=['palooz'],
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
    name='PalworldEffigyTool',
    icon='F:/Workspace/Palworld_effigy/assets/cattiva.ico',
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
