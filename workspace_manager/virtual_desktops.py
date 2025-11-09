"""
Virtual desktop management for Windows 11.
Wrapper around pyvda with fallback strategies.
"""

import time
import logging
from typing import Optional, List, Any
import subprocess

logger = logging.getLogger(__name__)

# Try to import pyvda, but handle gracefully if not available
try:
    import pyvda
    PYVDA_AVAILABLE = True
except ImportError:
    PYVDA_AVAILABLE = False
    logger.warning("pyvda not available. Virtual desktop features will be limited.")


class VirtualDesktopError(Exception):
    """Custom exception for virtual desktop operations."""
    pass


class VirtualDesktopManager:
    """Manages virtual desktops on Windows 11."""

    def __init__(self):
        """Initialize the virtual desktop manager."""
        self.pyvda_available = PYVDA_AVAILABLE
        self._warned_about_pyvda = False

        if not self.pyvda_available and not self._warned_about_pyvda:
            logger.warning(
                "pyvda is not installed. Install it with 'pip install pyvda' "
                "for full virtual desktop support."
            )
            self._warned_about_pyvda = True

    def get_desktop_count(self) -> int:
        """
        Get the number of virtual desktops.

        Returns:
            Number of virtual desktops

        Raises:
            VirtualDesktopError: If operation fails
        """
        if not self.pyvda_available:
            return 1  # Assume single desktop if pyvda not available

        try:
            desktops = pyvda.get_virtual_desktops()
            count = len(desktops)
            logger.debug(f"Found {count} virtual desktop(s)")
            return count

        except Exception as e:
            logger.error(f"Failed to get desktop count: {e}")
            raise VirtualDesktopError(f"Failed to get desktop count: {e}")

    def create_desktop(self) -> bool:
        """
        Create a new virtual desktop.

        Returns:
            True if successful

        Raises:
            VirtualDesktopError: If operation fails
        """
        if not self.pyvda_available:
            logger.warning("Cannot create virtual desktop without pyvda")
            return False

        try:
            # Get current count
            before_count = self.get_desktop_count()

            # Try using pyvda create first
            try:
                new_desktop = pyvda.VirtualDesktop.create()
                time.sleep(0.3)
            except (OSError, Exception) as create_error:
                # pyvda.create() has issues on some Windows 11 builds
                # Fallback to keyboard simulation using win32api
                logger.debug(f"pyvda.create() failed ({create_error}), using keyboard fallback")

                import win32api
                import win32con

                # Send Win+Ctrl+D keyboard shortcut
                # Press Win
                win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
                time.sleep(0.05)

                # Press Ctrl
                win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                time.sleep(0.05)

                # Press D
                win32api.keybd_event(0x44, 0, 0, 0)  # D key
                time.sleep(0.05)

                # Release D
                win32api.keybd_event(0x44, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)

                # Release Ctrl
                win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)

                # Release Win
                win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)

                # Wait for desktop creation
                time.sleep(0.5)

            # Verify creation
            after_count = self.get_desktop_count()

            if after_count > before_count:
                logger.info(f"Created new virtual desktop (total: {after_count})")
                return True
            else:
                logger.warning("Failed to create virtual desktop")
                return False

        except Exception as e:
            logger.error(f"Failed to create virtual desktop: {e}")
            return False

    def ensure_desktop_count(self, required_count: int) -> bool:
        """
        Ensure at least the specified number of desktops exist.

        Args:
            required_count: Minimum number of desktops needed

        Returns:
            True if successful

        Raises:
            VirtualDesktopError: If operation fails
        """
        if not self.pyvda_available:
            if required_count > 1:
                logger.warning(
                    f"Cannot ensure {required_count} desktops without pyvda. "
                    "Windows will be placed on the current desktop."
                )
            return required_count <= 1

        try:
            current_count = self.get_desktop_count()
            logger.debug(f"Current desktop count: {current_count}, required: {required_count}")

            if current_count >= required_count:
                return True

            # Create additional desktops
            desktops_to_create = required_count - current_count
            logger.info(f"Creating {desktops_to_create} additional desktop(s)")

            for i in range(desktops_to_create):
                if not self.create_desktop():
                    logger.error(f"Failed to create desktop {i + 1}/{desktops_to_create}")
                    return False

                # Small delay between creations
                if i < desktops_to_create - 1:
                    time.sleep(0.3)

            # Final verification
            final_count = self.get_desktop_count()
            success = final_count >= required_count

            if success:
                logger.info(f"Successfully ensured {required_count} desktop(s) exist")
            else:
                logger.warning(
                    f"Failed to create required desktops. "
                    f"Have {final_count}, need {required_count}"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to ensure desktop count: {e}")
            raise VirtualDesktopError(f"Failed to ensure desktop count: {e}")

    def move_window_to_desktop(self, hwnd: int, desktop_index: int) -> bool:
        """
        Move a window to a specific virtual desktop.

        Args:
            hwnd: Window handle
            desktop_index: Target desktop index (0-based)

        Returns:
            True if successful
        """
        if not self.pyvda_available:
            if desktop_index > 0:
                logger.warning(
                    f"Cannot move window to desktop {desktop_index} without pyvda. "
                    "Window will remain on current desktop."
                )
            return desktop_index == 0

        try:
            # Get list of desktops
            desktops = pyvda.get_virtual_desktops()

            if desktop_index >= len(desktops):
                logger.error(
                    f"Desktop index {desktop_index} out of range. "
                    f"Only {len(desktops)} desktop(s) available."
                )
                return False

            # Get target desktop (convert 0-indexed to 1-indexed)
            target_desktop = pyvda.VirtualDesktop(desktop_index + 1)

            # Try to move the window
            try:
                app_view = pyvda.AppView(hwnd)
                app_view.move(target_desktop)
                logger.debug(f"Moved window {hwnd} to desktop {desktop_index}")
            except (OSError, Exception) as move_error:
                logger.warning(
                    f"AppView.move() failed for window {hwnd}: {move_error}. "
                    "Some windows cannot be moved to different desktops."
                )
                return False

            # Small delay to ensure move completes
            time.sleep(0.2)

            # Don't verify - verification can fail even when move succeeds
            # Just return success if we got here
            return True

        except Exception as e:
            logger.error(f"Failed to move window {hwnd} to desktop {desktop_index}: {e}")
            return False

    def get_window_desktop(self, hwnd: int) -> int:
        """
        Get the virtual desktop index of a window.

        Args:
            hwnd: Window handle

        Returns:
            Desktop index (0-based) or -1 if error
        """
        if not self.pyvda_available:
            return 0  # Assume desktop 0 if pyvda not available

        try:
            # Try to get desktop via AppView
            try:
                app_view = pyvda.AppView(hwnd)
                window_desktop_number = app_view.desktop.number
                desktop_index = window_desktop_number - 1
                return desktop_index
            except (OSError, AttributeError) as e:
                # AppView.desktop can fail with access violations
                # Fallback: assume it's on the current desktop
                logger.debug(f"Could not determine desktop for window {hwnd}, assuming current desktop")
                return self.get_current_desktop()

        except Exception as e:
            logger.debug(f"Failed to get window desktop for {hwnd}: {e}")
            return 0  # Default to first desktop on error

    def get_current_desktop(self) -> int:
        """
        Get the index of the current virtual desktop.

        Returns:
            Current desktop index (0-based) or -1 if error
        """
        if not self.pyvda_available:
            return 0

        try:
            # Get current desktop using VirtualDesktop.current()
            current = pyvda.VirtualDesktop.current()

            # Get desktop number (1-indexed) and convert to 0-indexed
            desktop_index = current.number - 1

            return desktop_index

        except Exception as e:
            logger.error(f"Failed to get current desktop: {e}")
            return 0  # Default to first desktop on error

    def switch_to_desktop(self, desktop_index: int) -> bool:
        """
        Switch to a specific virtual desktop.

        Args:
            desktop_index: Target desktop index (0-based)

        Returns:
            True if successful
        """
        if not self.pyvda_available:
            if desktop_index > 0:
                logger.warning("Cannot switch desktops without pyvda")
            return desktop_index == 0

        try:
            desktops = pyvda.get_virtual_desktops()

            if desktop_index >= len(desktops):
                logger.error(f"Desktop index {desktop_index} out of range")
                return False

            # Convert 0-indexed to 1-indexed for VirtualDesktop
            desktop_number = desktop_index + 1

            # Create VirtualDesktop object and switch to it
            target_desktop = pyvda.VirtualDesktop(desktop_number)
            target_desktop.go()

            # Small delay for switch to complete
            time.sleep(0.2)

            # Verify switch
            current = self.get_current_desktop()
            if current == desktop_index:
                logger.debug(f"Switched to desktop {desktop_index}")
                return True
            else:
                logger.warning(f"Failed to switch to desktop {desktop_index}")
                return False

        except Exception as e:
            logger.error(f"Failed to switch to desktop {desktop_index}: {e}")
            return False

    def pin_window(self, hwnd: int) -> bool:
        """
        Pin a window to all desktops.

        Args:
            hwnd: Window handle

        Returns:
            True if successful
        """
        if not self.pyvda_available:
            logger.warning("Cannot pin window without pyvda")
            return False

        try:
            app_view = pyvda.AppView(hwnd)
            app_view.pin()
            logger.debug(f"Pinned window {hwnd} to all desktops")
            return True

        except Exception as e:
            logger.error(f"Failed to pin window {hwnd}: {e}")
            return False

    def unpin_window(self, hwnd: int) -> bool:
        """
        Unpin a window from all desktops.

        Args:
            hwnd: Window handle

        Returns:
            True if successful
        """
        if not self.pyvda_available:
            logger.warning("Cannot unpin window without pyvda")
            return False

        try:
            app_view = pyvda.AppView(hwnd)
            app_view.unpin()
            logger.debug(f"Unpinned window {hwnd}")
            return True

        except Exception as e:
            logger.error(f"Failed to unpin window {hwnd}: {e}")
            return False

    def is_window_pinned(self, hwnd: int) -> bool:
        """
        Check if a window is pinned to all desktops.

        Args:
            hwnd: Window handle

        Returns:
            True if pinned
        """
        if not self.pyvda_available:
            return False

        try:
            app_view = pyvda.AppView(hwnd)
            return app_view.is_pinned

        except Exception as e:
            logger.error(f"Failed to check if window {hwnd} is pinned: {e}")
            return False

    def _send_hotkey(self, hotkey: str) -> None:
        """
        Send a hotkey combination using PowerShell.

        Args:
            hotkey: Hotkey string (e.g., "win+ctrl+d")
        """
        try:
            # Create PowerShell script to send keys
            ps_script = f"""
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Keyboard {{
                    [DllImport("user32.dll")]
                    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, IntPtr dwExtraInfo);
                    public const int KEYEVENTF_KEYUP = 0x0002;
                }}
"@

            # Send {hotkey}
            [System.Windows.Forms.SendKeys]::SendWait('{hotkey}')
            """

            # Run PowerShell command
            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                check=False
            )

        except Exception as e:
            logger.error(f"Failed to send hotkey {hotkey}: {e}")

    def close_desktop(self, desktop_index: int) -> bool:
        """
        Close a virtual desktop (if it's not the last one).

        Args:
            desktop_index: Desktop index to close

        Returns:
            True if successful
        """
        if not self.pyvda_available:
            logger.warning("Cannot close desktop without pyvda")
            return False

        try:
            desktop_count = self.get_desktop_count()

            if desktop_count <= 1:
                logger.warning("Cannot close the last remaining desktop")
                return False

            if desktop_index >= desktop_count:
                logger.error(f"Desktop index {desktop_index} out of range")
                return False

            # Switch to the desktop to close
            self.switch_to_desktop(desktop_index)

            # Send Win+Ctrl+F4 to close current desktop
            self._send_hotkey("win+ctrl+{F4}")

            time.sleep(0.5)

            # Verify closure
            new_count = self.get_desktop_count()
            if new_count < desktop_count:
                logger.info(f"Closed desktop {desktop_index}")
                return True
            else:
                logger.warning(f"Failed to close desktop {desktop_index}")
                return False

        except Exception as e:
            logger.error(f"Failed to close desktop {desktop_index}: {e}")
            return False