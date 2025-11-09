#!/usr/bin/env python3
"""
cx_Freeze setup script for creating MSI installer
"""

import sys
from cx_Freeze import setup, Executable
from pathlib import Path

# Import version info
sys.path.insert(0, str(Path(__file__).parent))
from workspace_manager.__version__ import __version__, __app_name__, __description__, __author__

# Dependencies are automatically detected, but some modules need help
build_exe_options = {
    "packages": [
        "workspace_manager",
        "pyvda",
        "win32com",
        "win32api",
        "win32con",
        "win32gui",
        "win32ui",
        "customtkinter",
        "PIL",
        "psutil",
        "rich",
    ],
    "includes": [
        "win32timezone",
    ],
    "excludes": [
        "test",
        "unittest",
        "email",
        "html",
        "http",
        "urllib",
        "xml",
        "pydoc_data",
    ],
    "include_files": [
        ("README.md", "README.md"),
        ("workspaces.example.json", "workspaces.example.json"),
    ],
    "optimize": 2,
}

# MSI-specific options
bdist_msi_options = {
    "add_to_path": True,  # Add to system PATH
    "initial_target_dir": r"[ProgramFilesFolder]\WorkspaceManager",
    "install_icon": None,  # Add icon path here if available
    "upgrade_code": "{12345678-1234-1234-1234-123456789012}",  # GUID for upgrades
    "all_users": False,  # Install for current user only (no admin required)
}

# Base for GUI application (no console window)
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Executable configuration
executables = [
    Executable(
        "main.py",
        base=base,
        target_name="WorkspaceManager.exe",
        icon=None,  # Add icon path here if available: "assets/icon.ico"
        shortcut_name="Workspace Manager",
        shortcut_dir="ProgramMenuFolder",
    )
]

setup(
    name=__app_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
