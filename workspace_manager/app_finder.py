#!/usr/bin/env python3
"""
Module to find installed applications on Windows and extract their icons.
"""

import os
import winreg
from pathlib import Path
from typing import List, Dict, Optional, Generator
import threading
import win32com.client
import win32api
import win32con
import win32gui
import win32ui
from PIL import Image
import io


class AppInfo:
    """Information about an installed application"""

    def __init__(self, name: str, exe_path: str, icon_data: Optional[bytes] = None):
        self.name = name
        self.exe_path = exe_path
        self.icon_data = icon_data


def extract_icon_from_exe(exe_path: str, size: int = 32) -> Optional[bytes]:
    """Extract icon from executable file as PNG bytes"""
    try:
        # Get the icon from the executable
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)

        large, small = win32gui.ExtractIconEx(exe_path, 0)

        if not large and not small:
            return None

        # Use large icon if available, otherwise small
        hicon = large[0] if large else small[0]

        # Get icon info
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
        hdc_bitmap = hdc.CreateCompatibleDC()

        hdc_bitmap.SelectObject(hbmp)
        hdc_bitmap.DrawIcon((0, 0), hicon)

        # Convert to PIL Image
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGB',
            (ico_x, ico_y),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        # Resize if needed
        if size != ico_x:
            img = img.resize((size, size), Image.Resampling.LANCZOS)

        # Convert to PNG bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        icon_bytes = img_byte_arr.getvalue()

        # Cleanup
        win32gui.DestroyIcon(hicon)
        if large:
            for icon in large:
                win32gui.DestroyIcon(icon)
        if small:
            for icon in small:
                win32gui.DestroyIcon(icon)

        return icon_bytes

    except Exception as e:
        print(f"Error extracting icon from {exe_path}: {e}")
        return None


def find_programs_in_start_menu() -> Generator[AppInfo, None, None]:
    """Find programs in Start Menu"""
    start_menu_paths = [
        Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs',
        Path(os.environ.get('PROGRAMDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs'
    ]

    shell = win32com.client.Dispatch("WScript.Shell")

    for start_menu in start_menu_paths:
        if not start_menu.exists():
            continue

        for shortcut_file in start_menu.rglob('*.lnk'):
            try:
                shortcut = shell.CreateShortCut(str(shortcut_file))
                target_path = shortcut.Targetpath

                if target_path and target_path.lower().endswith('.exe') and os.path.exists(target_path):
                    app_name = shortcut_file.stem

                    # Skip uninstallers and system tools
                    if any(skip in app_name.lower() for skip in ['uninstall', 'remove', 'help', 'readme']):
                        continue

                    icon_data = extract_icon_from_exe(target_path, size=48)
                    yield AppInfo(app_name, target_path, icon_data)

            except Exception as e:
                # Skip problematic shortcuts
                continue


def find_programs_in_registry() -> Generator[AppInfo, None, None]:
    """Find programs registered in Windows Registry"""
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    seen_exes = set()

    for hkey, reg_path in registry_paths:
        try:
            key = winreg.OpenKey(hkey, reg_path)

            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)

                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]

                        # Extract exe path from icon path
                        exe_path = display_icon.split(',')[0].strip('"')

                        if exe_path and os.path.exists(exe_path) and exe_path.lower().endswith('.exe'):
                            if exe_path.lower() not in seen_exes:
                                seen_exes.add(exe_path.lower())
                                icon_data = extract_icon_from_exe(exe_path, size=48)
                                yield AppInfo(display_name, exe_path, icon_data)

                    except (FileNotFoundError, OSError):
                        pass
                    finally:
                        winreg.CloseKey(subkey)

                except Exception:
                    continue

            winreg.CloseKey(key)

        except Exception:
            continue


def find_programs_in_program_files() -> Generator[AppInfo, None, None]:
    """Find executables in Program Files directories"""
    program_dirs = [
        Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')),
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')),
    ]

    seen_exes = set()

    for program_dir in program_dirs:
        if not program_dir.exists():
            continue

        # Only search 2 levels deep to avoid going too deep
        for exe_file in program_dir.glob('*/*.exe'):
            try:
                if exe_file.name.lower() not in seen_exes:
                    # Skip uninstallers and system files
                    if any(skip in exe_file.name.lower() for skip in ['unins', 'uninst', 'helper', 'crash', 'update']):
                        continue

                    seen_exes.add(exe_file.name.lower())
                    app_name = exe_file.stem
                    icon_data = extract_icon_from_exe(str(exe_file), size=48)
                    yield AppInfo(app_name, str(exe_file), icon_data)

            except Exception:
                continue


def find_all_installed_programs() -> Generator[AppInfo, None, None]:
    """Find all installed programs from various sources"""
    seen_paths = set()

    # Priority: Start Menu (most reliable)
    for app in find_programs_in_start_menu():
        if app.exe_path.lower() not in seen_paths:
            seen_paths.add(app.exe_path.lower())
            yield app

    # Then registry
    for app in find_programs_in_registry():
        if app.exe_path.lower() not in seen_paths:
            seen_paths.add(app.exe_path.lower())
            yield app

    # Finally Program Files (can be noisy)
    # for app in find_programs_in_program_files():
    #     if app.exe_path.lower() not in seen_paths:
    #         seen_paths.add(app.exe_path.lower())
    #         yield app
