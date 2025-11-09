# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Windows 11 Workspace Manager
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data files from customtkinter
customtkinter_datas = collect_data_files('customtkinter')

# Collect all submodules
hiddenimports = collect_submodules('pyvda') + \
                collect_submodules('win32com') + \
                collect_submodules('customtkinter') + \
                ['win32timezone', 'win32gui', 'win32api', 'win32con', 'win32ui']

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=customtkinter_datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WorkspaceManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',  # Application icon
    version_file='version_info.txt'  # Will be created by build script
)
