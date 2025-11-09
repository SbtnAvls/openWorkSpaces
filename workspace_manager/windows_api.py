"""
Windows API wrapper functions for window manipulation and process management.
"""

import time
import logging
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
import win32gui
import win32con
import win32api
import win32process
import psutil
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    """Information about a window."""
    hwnd: int
    title: str
    class_name: str
    rect: Tuple[int, int, int, int]  # left, top, right, bottom
    pid: int
    exe_path: Optional[str] = None
    is_visible: bool = True


class WindowsAPIError(Exception):
    """Custom exception for Windows API errors."""
    pass


def get_window_text_safe(hwnd: int) -> str:
    """
    Safely get window text.

    Args:
        hwnd: Window handle

    Returns:
        Window text or empty string if error
    """
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""


def get_class_name_safe(hwnd: int) -> str:
    """
    Safely get window class name.

    Args:
        hwnd: Window handle

    Returns:
        Class name or empty string if error
    """
    try:
        return win32gui.GetClassName(hwnd)
    except Exception:
        return ""


def is_alt_tab_window(hwnd: int) -> bool:
    """
    Check if window should appear in Alt+Tab.
    Filters out tool windows, hidden windows, etc.

    Args:
        hwnd: Window handle

    Returns:
        True if window should be shown to user
    """
    try:
        # Window must be visible
        if not win32gui.IsWindowVisible(hwnd):
            return False

        # Get window style
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

        # Skip if no visible style
        if not (style & win32con.WS_VISIBLE):
            return False

        # Skip tool windows
        if ex_style & win32con.WS_EX_TOOLWINDOW:
            return False

        # Skip child windows
        if style & win32con.WS_CHILD:
            return False

        # Must have a title or be app window
        title = get_window_text_safe(hwnd)
        if not title and not (ex_style & win32con.WS_EX_APPWINDOW):
            return False

        # Get window rect
        try:
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            # Skip windows that are too small (likely hidden)
            if width < 50 or height < 50:
                return False

        except Exception:
            return False

        return True

    except Exception:
        return False


def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
    """
    Get information about a process.

    Args:
        pid: Process ID

    Returns:
        Dictionary with process info or None if error
    """
    try:
        process = psutil.Process(pid)
        return {
            'name': process.name(),
            'exe': process.exe(),
            'cmdline': process.cmdline(),
            'cwd': process.cwd(),
            'create_time': process.create_time()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None


def enumerate_windows() -> List[WindowInfo]:
    """
    Enumerate all windows that would appear in Alt+Tab.

    Returns:
        List of WindowInfo objects
    """
    windows = []

    def enum_callback(hwnd, _):
        try:
            if is_alt_tab_window(hwnd):
                title = get_window_text_safe(hwnd)
                class_name = get_class_name_safe(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)

                # Try to get exe path
                exe_path = None
                proc_info = get_process_info(pid)
                if proc_info:
                    exe_path = proc_info.get('exe')

                window = WindowInfo(
                    hwnd=hwnd,
                    title=title,
                    class_name=class_name,
                    rect=rect,
                    pid=pid,
                    exe_path=exe_path,
                    is_visible=True
                )
                windows.append(window)

        except Exception as e:
            logger.debug(f"Error processing window {hwnd}: {e}")

        return True  # Continue enumeration

    try:
        win32gui.EnumWindows(enum_callback, None)
    except Exception as e:
        logger.error(f"Error enumerating windows: {e}")

    return windows


def find_window_by_pid(pid: int, timeout: float = 10.0, title_hint: str = None) -> Optional[int]:
    """
    Find a window handle by process ID.

    Args:
        pid: Process ID
        timeout: Maximum time to wait in seconds
        title_hint: Optional title substring to match

    Returns:
        Window handle or None if not found
    """
    start_time = time.time()
    check_interval = 0.5

    logger.debug(f"Looking for window with PID {pid}, title hint: {title_hint}")

    while time.time() - start_time < timeout:
        windows = enumerate_windows()

        for window in windows:
            if window.pid == pid:
                # If no title hint, return first window
                if not title_hint:
                    logger.debug(f"Found window {window.hwnd} for PID {pid}")
                    return window.hwnd

                # Check if title contains hint
                if title_hint.lower() in window.title.lower():
                    logger.debug(f"Found window {window.hwnd} for PID {pid} with title '{window.title}'")
                    return window.hwnd

        time.sleep(check_interval)

    logger.warning(f"No window found for PID {pid} within {timeout} seconds")
    return None


def find_windows_by_exe(exe_name: str) -> List[WindowInfo]:
    """
    Find all windows belonging to an executable.

    Args:
        exe_name: Name or path of executable

    Returns:
        List of WindowInfo objects
    """
    exe_name_lower = Path(exe_name).name.lower()
    matching_windows = []

    for window in enumerate_windows():
        if window.exe_path:
            window_exe_name = Path(window.exe_path).name.lower()
            if window_exe_name == exe_name_lower:
                matching_windows.append(window)

    return matching_windows


def move_window(hwnd: int, x: int, y: int, width: int, height: int) -> bool:
    """
    Move and resize a window.
    Handles special cases for console windows which behave differently.

    Args:
        hwnd: Window handle
        x: Left position
        y: Top position
        width: Window width
        height: Window height

    Returns:
        True if successful
    """
    try:
        # Check if this is a console window
        class_name = get_class_name_safe(hwnd)
        # Console classes: cmd.exe, PowerShell console, Windows Terminal
        console_classes = [
            'ConsoleWindowClass',      # cmd.exe, PowerShell
            'PseudoConsoleWindow',      # Newer console windows
            'CASCADIA_HOSTING_WINDOW_CLASS',  # Windows Terminal
            'Cascadia_HOSTING_WINDOW_CLASS',  # Windows Terminal variant
        ]
        is_console = class_name in console_classes

        # For console windows, be more lenient (within 100 pixels)
        # For regular windows, stricter (within 50 pixels)
        tolerance = 100 if is_console else 50

        # Ensure window is restored (not minimized or maximized)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.15)

        # For console windows, we need special handling
        if is_console:
            logger.debug(f"Detected console window (class: {class_name}), using special positioning")

            # Console windows are difficult - they need multiple attempts and verification
            # Retry positioning up to 3 times
            for attempt in range(3):
                if attempt > 0:
                    logger.debug(f"Console positioning retry {attempt}/3")
                    time.sleep(0.2)

                # Bring window to front first (helps with positioning)
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.05)
                except Exception:
                    pass

                # Method 1: MoveWindow first (direct positioning)
                try:
                    win32gui.MoveWindow(hwnd, x, y, width, height, True)
                    time.sleep(0.15)
                except Exception as e1:
                    logger.debug(f"MoveWindow failed: {e1}")

                # Method 2: SetWindowPos with NO activation (prevents Windows from interfering)
                try:
                    win32gui.SetWindowPos(
                        hwnd,
                        0,  # Don't change Z-order
                        x, y, width, height,
                        win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER
                    )
                    time.sleep(0.15)
                except Exception as e2:
                    logger.debug(f"SetWindowPos noactivate failed: {e2}")

                # Method 3: Force with FRAMECHANGED and NOMOVE to force size first
                try:
                    # First set size
                    win32gui.SetWindowPos(
                        hwnd,
                        win32con.HWND_TOP,
                        0, 0, width, height,
                        win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE
                    )
                    time.sleep(0.1)
                    # Then set position
                    win32gui.SetWindowPos(
                        hwnd,
                        0,
                        x, y, 0, 0,
                        win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER
                    )
                    time.sleep(0.15)
                except Exception as e3:
                    logger.debug(f"SetWindowPos split failed: {e3}")

                # Check if position is now correct
                check_rect = win32gui.GetWindowRect(hwnd)
                position_ok = (abs(check_rect[0] - x) < tolerance and
                             abs(check_rect[1] - y) < tolerance)

                if position_ok:
                    logger.debug(f"Console positioned correctly on attempt {attempt + 1}")
                    break
                else:
                    logger.debug(f"Console position still off on attempt {attempt + 1}: "
                               f"expected ({x}, {y}), got ({check_rect[0]}, {check_rect[1]})")

        else:
            # Standard window - use normal SetWindowPos
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOP,
                x, y, width, height,
                win32con.SWP_SHOWWINDOW
            )
            time.sleep(0.1)

        # Verify the move
        time.sleep(0.15)
        new_rect = win32gui.GetWindowRect(hwnd)

        position_ok = (abs(new_rect[0] - x) < tolerance and abs(new_rect[1] - y) < tolerance)
        size_ok = (abs((new_rect[2] - new_rect[0]) - width) < tolerance and
                   abs((new_rect[3] - new_rect[1]) - height) < tolerance)

        if position_ok and size_ok:
            logger.debug(
                f"Successfully moved window {hwnd} to ({x}, {y}, {width}x{height}). "
                f"Actual: ({new_rect[0]}, {new_rect[1]}, {new_rect[2]-new_rect[0]}x{new_rect[3]-new_rect[1]})"
            )
            return True
        elif size_ok and not position_ok:
            logger.warning(
                f"Window {hwnd} size OK but position off. "
                f"Expected ({x}, {y}), got ({new_rect[0]}, {new_rect[1]})"
            )
            # For console windows, accept size-only success
            return is_console
        else:
            logger.warning(
                f"Window {hwnd} move verification failed. "
                f"Expected ({x}, {y}, {width}x{height}), "
                f"got ({new_rect[0]}, {new_rect[1]}, {new_rect[2]-new_rect[0]}x{new_rect[3]-new_rect[1]})"
            )
            return False

    except Exception as e:
        logger.error(f"Failed to move window {hwnd}: {e}")
        return False


def bring_window_to_front(hwnd: int) -> bool:
    """
    Bring a window to the foreground.

    Args:
        hwnd: Window handle

    Returns:
        True if successful
    """
    try:
        # First restore if minimized
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        # Set as foreground window
        win32gui.SetForegroundWindow(hwnd)

        # Bring to top
        win32gui.BringWindowToTop(hwnd)

        return True

    except Exception as e:
        logger.error(f"Failed to bring window {hwnd} to front: {e}")
        return False


def minimize_window(hwnd: int) -> bool:
    """
    Minimize a window.

    Args:
        hwnd: Window handle

    Returns:
        True if successful
    """
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        return True
    except Exception as e:
        logger.error(f"Failed to minimize window {hwnd}: {e}")
        return False


def maximize_window(hwnd: int) -> bool:
    """
    Maximize a window.

    Args:
        hwnd: Window handle

    Returns:
        True if successful
    """
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        return True
    except Exception as e:
        logger.error(f"Failed to maximize window {hwnd}: {e}")
        return False


def restore_window(hwnd: int) -> bool:
    """
    Restore a window to normal state.

    Args:
        hwnd: Window handle

    Returns:
        True if successful
    """
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        return True
    except Exception as e:
        logger.error(f"Failed to restore window {hwnd}: {e}")
        return False


def close_window(hwnd: int, force: bool = False) -> bool:
    """
    Close a window.

    Args:
        hwnd: Window handle
        force: If True, forcefully terminate the process

    Returns:
        True if successful
    """
    try:
        if not force:
            # Send WM_CLOSE message
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        else:
            # Get process ID and terminate
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process.terminate()

        return True

    except Exception as e:
        logger.error(f"Failed to close window {hwnd}: {e}")
        return False


def get_window_rect(hwnd: int) -> Optional[Tuple[int, int, int, int]]:
    """
    Get window rectangle.

    Args:
        hwnd: Window handle

    Returns:
        Tuple of (left, top, right, bottom) or None if error
    """
    try:
        return win32gui.GetWindowRect(hwnd)
    except Exception as e:
        logger.error(f"Failed to get window rect for {hwnd}: {e}")
        return None


def get_monitor_info() -> List[Dict[str, Any]]:
    """
    Get information about all monitors.

    Returns:
        List of monitor info dictionaries
    """
    monitors = []

    def monitor_enum_callback(hmon, hdc, rect, _):
        try:
            info = win32api.GetMonitorInfo(hmon)
            monitors.append({
                'handle': hmon,
                'rect': rect,
                'work_area': info['Work'],
                'is_primary': info['Flags'] == 1,
                'device': info.get('Device', '')
            })
        except Exception as e:
            logger.error(f"Error getting monitor info: {e}")

        return True

    try:
        win32api.EnumDisplayMonitors(None, None, monitor_enum_callback, None)
    except Exception as e:
        logger.error(f"Error enumerating monitors: {e}")

    return monitors


def get_primary_monitor_rect() -> Tuple[int, int, int, int]:
    """
    Get the primary monitor's work area.

    Returns:
        Tuple of (left, top, right, bottom)
    """
    monitors = get_monitor_info()

    for monitor in monitors:
        if monitor['is_primary']:
            work_area = monitor['work_area']
            return work_area

    # Fallback to first monitor
    if monitors:
        return monitors[0]['work_area']

    # Last resort fallback
    return (0, 0, 1920, 1080)


def is_window_responding(hwnd: int, timeout: float = 5.0) -> bool:
    """
    Check if a window is responding.

    Args:
        hwnd: Window handle
        timeout: Timeout in seconds

    Returns:
        True if window is responding
    """
    try:
        # Use SendMessageTimeout to check if window responds
        result = win32gui.SendMessageTimeout(
            hwnd,
            win32con.WM_NULL,
            0,
            0,
            win32con.SMTO_ABORTIFHUNG,
            int(timeout * 1000)
        )
        return result is not None

    except Exception:
        return False