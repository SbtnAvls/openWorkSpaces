"""
Workspace launcher - responsible for starting applications and arranging windows.
"""

import subprocess
import time
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from .models import Workspace, AppInstance
from .windows_api import (
    find_window_by_pid,
    move_window,
    bring_window_to_front,
    restore_window,
    is_window_responding
)
from .virtual_desktops import VirtualDesktopManager

logger = logging.getLogger(__name__)
console = Console(legacy_windows=True)  # Enable Windows legacy mode


@dataclass
class LaunchResult:
    """Result of launching an application."""
    app_id: str
    success: bool
    pid: Optional[int] = None
    hwnd: Optional[int] = None
    error: Optional[str] = None


class WorkspaceLauncher:
    """Launches and arranges workspace applications."""

    def __init__(self):
        """Initialize the workspace launcher."""
        self.vd_manager = VirtualDesktopManager()
        self.launch_results: List[LaunchResult] = []

    def launch_workspace(
        self,
        workspace: Workspace,
        dry_run: bool = False,
        sequential: bool = False
    ) -> bool:
        """
        Launch all applications in a workspace.

        Args:
            workspace: Workspace to launch
            dry_run: If True, only simulate launching
            sequential: If True, wait for each app before launching next

        Returns:
            True if all apps launched successfully
        """
        console.print(f"\n[bold cyan]Launching workspace: {workspace.name}[/bold cyan]")

        if workspace.description:
            console.print(f"[dim]{workspace.description}[/dim]")

        if not workspace.apps:
            console.print("[yellow]No applications defined in workspace[/yellow]")
            return True

        # Clear previous results
        self.launch_results = []

        # Ensure required desktops exist
        required_desktops = workspace.get_required_desktops()
        console.print(f"\n[dim]Ensuring {required_desktops} virtual desktop(s) exist...[/dim]")

        if not dry_run:
            if not self.vd_manager.ensure_desktop_count(required_desktops):
                console.print(
                    "[yellow]Warning: Could not create all required virtual desktops. "
                    "Windows may not be placed correctly.[/yellow]"
                )

        # Group apps by desktop for better organization
        apps_by_desktop = self._group_apps_by_desktop(workspace.apps)

        # Launch applications
        console.print(f"\n[bold]Launching {len(workspace.apps)} application(s)...[/bold]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:

            for desktop_idx in sorted(apps_by_desktop.keys()):
                apps = apps_by_desktop[desktop_idx]

                # Switch to this desktop once for all apps in this group
                if not dry_run and len(apps) > 0:
                    console.print(f"\n[dim]→ Switching to desktop {desktop_idx}[/dim]")
                    self.vd_manager.switch_to_desktop(desktop_idx)
                    time.sleep(0.5)  # Wait for desktop switch

                for app in apps:
                    task = progress.add_task(
                        f"Launching {app.id}...",
                        total=1
                    )

                    if dry_run:
                        console.print(f"[dim]DRY RUN: Would launch {app.id}[/dim]")
                        result = LaunchResult(
                            app_id=app.id,
                            success=True,
                            error="Dry run - not launched"
                        )
                    else:
                        # Pass skip_desktop_switch=True since we already switched
                        result = self._launch_app(app, desktop_idx, skip_desktop_switch=True)

                    self.launch_results.append(result)
                    progress.update(task, completed=1)

                    if result.success:
                        console.print(f"[green]✓[/green] {app.id} launched successfully")
                    else:
                        console.print(f"[red]✗[/red] {app.id} failed: {result.error}")

                    # Wait between apps if sequential mode
                    if sequential and not dry_run:
                        time.sleep(2.0)

        # Show summary
        self._show_launch_summary()

        # Return success if all critical apps launched
        critical_failures = [r for r in self.launch_results if not r.success]
        return len(critical_failures) == 0

    def _launch_app(self, app: AppInstance, desktop_index: int, skip_desktop_switch: bool = False) -> LaunchResult:
        """
        Launch a single application.

        Args:
            app: Application to launch
            desktop_index: Target desktop index
            skip_desktop_switch: If True, don't switch desktops (already done)

        Returns:
            LaunchResult object
        """
        try:
            # Validate executable
            exe_path = Path(app.exe)

            # Handle special cases (cmd, powershell, wt)
            if app.exe.lower() in ['cmd', 'cmd.exe', 'powershell', 'powershell.exe', 'wt', 'wt.exe']:
                # Use full path for built-in commands
                if app.exe.lower().startswith('cmd'):
                    exe_path = Path('C:/Windows/System32/cmd.exe')
                elif app.exe.lower().startswith('powershell'):
                    exe_path = Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
                elif app.exe.lower().startswith('wt'):
                    # Windows Terminal - search in PATH
                    import shutil
                    wt_found = shutil.which('wt.exe')
                    if wt_found:
                        # If wt.exe is in WindowsApps (special protected folder),
                        # use 'wt.exe' directly without path - subprocess will find it via PATH
                        if 'WindowsApps' in wt_found:
                            exe_path = 'wt.exe'  # Use string, not Path, so subprocess finds it in PATH
                            logger.debug(f"Using wt.exe from PATH (found at: {wt_found})")
                        else:
                            exe_path = Path(wt_found)
                            logger.debug(f"Found wt.exe at: {exe_path}")
                    else:
                        logger.warning("wt.exe not found in PATH")
                        exe_path = 'wt.exe'  # Try anyway

            # If exe_path is a Path object and doesn't exist, try to find it in PATH
            if isinstance(exe_path, Path):
                if not exe_path.exists() and not exe_path.is_absolute():
                    import shutil
                    found_path = shutil.which(str(exe_path))
                    if found_path:
                        exe_path = Path(found_path)
                        logger.debug(f"Found {app.exe} in PATH: {exe_path}")

                # Check if exe exists
                if not exe_path.exists() and not app.exe.lower().startswith(('http://', 'https://')):
                    logger.warning(f"Executable not found: {exe_path}")
                    # Continue anyway - subprocess might find it in PATH

            # Prepare launch command (exe_path can be string or Path)
            cmd = [str(exe_path)] + (app.args if app.args else [])

            # Prepare subprocess arguments
            subprocess_args = {}

            # Determine creation flags based on application type
            # Windows Terminal is a GUI app that hosts consoles, so use DETACHED_PROCESS
            # cmd.exe and powershell.exe are pure console apps that need CREATE_NEW_CONSOLE
            exe_str = str(exe_path) if isinstance(exe_path, Path) else exe_path
            exe_lower = exe_str.lower()

            if 'wt.exe' in exe_lower or 'wt' == exe_lower or 'windowsterminal' in exe_lower:
                # Windows Terminal is a GUI wrapper - use DETACHED_PROCESS
                subprocess_args['creationflags'] = subprocess.DETACHED_PROCESS
                logger.debug("Using DETACHED_PROCESS for Windows Terminal")
            elif any(name in exe_lower for name in ['cmd.exe', 'powershell.exe']):
                # Pure console apps need CREATE_NEW_CONSOLE
                subprocess_args['creationflags'] = subprocess.CREATE_NEW_CONSOLE
                logger.debug("Using CREATE_NEW_CONSOLE for console app")
            else:
                # Other GUI apps - use DETACHED_PROCESS
                subprocess_args['creationflags'] = subprocess.DETACHED_PROCESS
                logger.debug("Using DETACHED_PROCESS for GUI app")

            # Set working directory if specified
            if app.working_dir:
                work_dir = Path(app.working_dir)
                if work_dir.exists():
                    subprocess_args['cwd'] = str(work_dir)
                else:
                    logger.warning(f"Working directory not found: {work_dir}")

            # For wt.exe from WindowsApps, use shell=True as WindowsApps has special permissions
            use_shell = False
            is_windows_terminal = False
            if isinstance(exe_path, str) and exe_path.lower() == 'wt.exe':
                import shutil
                wt_location = shutil.which('wt.exe')
                if wt_location and 'WindowsApps' in wt_location:
                    # Windows Terminal in WindowsApps requires shell=True
                    use_shell = True
                    is_windows_terminal = True
                    logger.debug("Using shell=True for Windows Terminal in WindowsApps")

                    # Build command for Windows Terminal with proper arguments
                    # Windows Terminal supports -d argument for working directory
                    cmd_str = 'wt.exe'

                    # Add working directory as -d argument if specified
                    if app.working_dir and Path(app.working_dir).exists():
                        cmd_str += f' -d "{app.working_dir}"'
                        # Don't set cwd when using wt.exe -d argument
                        subprocess_args.pop('cwd', None)
                        logger.debug(f"Using wt.exe -d for working directory: {app.working_dir}")

                    # Add any additional arguments
                    if app.args:
                        # Filter out -d arguments if they're in args (we handle it above)
                        filtered_args = []
                        skip_next = False
                        for i, arg in enumerate(app.args):
                            if skip_next:
                                skip_next = False
                                continue
                            if arg == '-d':
                                skip_next = True  # Skip the next arg (the path)
                                continue
                            filtered_args.append(arg)

                        if filtered_args:
                            cmd_str += ' ' + ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in filtered_args)

                    cmd = cmd_str

            # STRATEGY: Switch to target desktop BEFORE launching (if not already done)
            # This helps the window appear on the correct desktop immediately
            if not skip_desktop_switch:
                logger.debug(f"Switching to desktop {desktop_index} before launching {app.id}")
                self.vd_manager.switch_to_desktop(desktop_index)
                time.sleep(0.3)  # Brief delay to ensure desktop switch completes

            # Get list of windows BEFORE launching (to detect new windows later)
            from .windows_api import enumerate_windows
            windows_before = {w.hwnd for w in enumerate_windows()}
            logger.debug(f"Windows before launch: {len(windows_before)}")

            # Launch the process
            if use_shell:
                # For shell commands, cmd is a string
                logger.debug(f"Launching with shell: {cmd}")
                process = subprocess.Popen(cmd, shell=True, **subprocess_args)
            else:
                # For normal commands, cmd is a list
                logger.debug(f"Launching: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
                process = subprocess.Popen(cmd, **subprocess_args)

            # Get process ID
            pid = process.pid
            logger.debug(f"Launched {app.id} with PID {pid}")

            # Wait for window to appear - try two strategies:
            # 1. Find by PID (works for most apps)
            # 2. Find NEW window (works for single-instance apps like Notepad)
            hwnd = None
            # Windows Terminal takes longer to create windows, increase timeout
            max_retries = 5 if is_windows_terminal else 3
            retry_delay = 2.0
            window_timeout = 3.0 if is_windows_terminal else 2.0

            for retry in range(max_retries):
                if retry > 0:
                    logger.debug(f"Retry {retry}/{max_retries} finding window for {app.id}")
                    time.sleep(retry_delay)

                # Strategy 1: Try to find by PID
                hwnd = find_window_by_pid(
                    pid,
                    timeout=window_timeout,
                    title_hint=None
                )

                if hwnd:
                    logger.debug(f"Found window {hwnd} for {app.id} by PID on attempt {retry + 1}")
                    break

                # Strategy 2: If not found by PID, look for new windows
                # (handles single-instance apps like Notepad)
                time.sleep(1.0)  # Brief wait for window creation
                windows_now = enumerate_windows()
                new_windows = [w for w in windows_now if w.hwnd not in windows_before]

                if new_windows:
                    # Found new window(s) - use the first one
                    hwnd = new_windows[0].hwnd
                    logger.debug(
                        f"Found new window {hwnd} for {app.id} "
                        f"(exe: {new_windows[0].exe_path}) on attempt {retry + 1}"
                    )
                    # Update windows_before for next app
                    windows_before.add(hwnd)
                    break

            if not hwnd:
                logger.warning(f"No window found for {app.id} (PID {pid}) after {max_retries} attempts")
                # Some apps might not create windows or run in background
                return LaunchResult(
                    app_id=app.id,
                    success=True,  # Still consider it success if process started
                    pid=pid,
                    hwnd=None,
                    error="Window not detected (app may be running in background or loading)"
                )

            # IMPORTANT: Move to correct desktop FIRST, before positioning
            # Windows appear on the current active desktop by default
            logger.debug(f"Moving {app.id} to desktop {desktop_index}")

            # Always move, regardless of desktop index
            # The window might have appeared on the wrong desktop
            move_success = self.vd_manager.move_window_to_desktop(hwnd, desktop_index)

            if not move_success:
                logger.warning(
                    f"Failed to move {app.id} to desktop {desktop_index}. "
                    "Window will remain on current desktop."
                )
            else:
                logger.debug(f"Successfully moved {app.id} to desktop {desktop_index}")

            # Wait for desktop move to complete
            time.sleep(0.5)

            # Now position and resize window on the correct desktop
            logger.debug(
                f"Positioning {app.id} at "
                f"({app.window.x}, {app.window.y}) "
                f"size {app.window.width}x{app.window.height}"
            )

            # Restore window first if needed (in case it's minimized)
            restore_window(hwnd)
            time.sleep(0.2)

            # Move and resize
            if not move_window(
                hwnd,
                app.window.x,
                app.window.y,
                app.window.width,
                app.window.height
            ):
                logger.warning(f"Failed to position window for {app.id}")

            # Check if window is responding
            if not is_window_responding(hwnd):
                logger.warning(f"Window for {app.id} is not responding")

            return LaunchResult(
                app_id=app.id,
                success=True,
                pid=pid,
                hwnd=hwnd
            )

        except FileNotFoundError as e:
            error_msg = f"Executable not found: {e}"
            logger.error(f"Failed to launch {app.id}: {error_msg}")
            return LaunchResult(
                app_id=app.id,
                success=False,
                error=error_msg
            )

        except PermissionError as e:
            error_msg = f"Permission denied: {e}"
            logger.error(f"Failed to launch {app.id}: {error_msg}")
            return LaunchResult(
                app_id=app.id,
                success=False,
                error=error_msg
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to launch {app.id}: {error_msg}")
            return LaunchResult(
                app_id=app.id,
                success=False,
                error=error_msg
            )

    def _group_apps_by_desktop(self, apps: List[AppInstance]) -> Dict[int, List[AppInstance]]:
        """
        Group applications by their target desktop.

        Args:
            apps: List of applications

        Returns:
            Dictionary mapping desktop index to list of apps
        """
        grouped = {}

        for app in apps:
            desktop = app.virtual_desktop
            if desktop not in grouped:
                grouped[desktop] = []
            grouped[desktop].append(app)

        return grouped

    def _show_launch_summary(self) -> None:
        """Display a summary of launch results."""
        if not self.launch_results:
            return

        console.print("\n[bold]Launch Summary[/bold]")

        # Create summary table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Application", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("PID", justify="right")
        table.add_column("Window", justify="right")
        table.add_column("Notes")

        for result in self.launch_results:
            status = "[green]✓ Success[/green]" if result.success else "[red]✗ Failed[/red]"
            pid = str(result.pid) if result.pid else "-"
            hwnd = f"0x{result.hwnd:X}" if result.hwnd else "-"
            notes = result.error or ""

            table.add_row(result.app_id, status, pid, hwnd, notes)

        console.print(table)

        # Summary statistics
        total = len(self.launch_results)
        successful = sum(1 for r in self.launch_results if r.success)
        failed = total - successful

        console.print(f"\n[bold]Total:[/bold] {total} | ", end="")
        console.print(f"[green]Successful:[/green] {successful} | ", end="")
        console.print(f"[red]Failed:[/red] {failed}")

    def get_failed_apps(self) -> List[str]:
        """
        Get list of app IDs that failed to launch.

        Returns:
            List of failed app IDs
        """
        return [r.app_id for r in self.launch_results if not r.success]

    def retry_failed_apps(self, workspace: Workspace) -> bool:
        """
        Retry launching failed applications.

        Args:
            workspace: Original workspace configuration

        Returns:
            True if all retried apps launched successfully
        """
        failed_ids = self.get_failed_apps()

        if not failed_ids:
            console.print("[green]No failed applications to retry[/green]")
            return True

        console.print(f"\n[yellow]Retrying {len(failed_ids)} failed application(s)...[/yellow]")

        # Get failed apps from workspace
        failed_apps = [app for app in workspace.apps if app.id in failed_ids]

        # Clear previous results for these apps
        self.launch_results = [
            r for r in self.launch_results
            if r.app_id not in failed_ids
        ]

        # Retry each failed app
        all_success = True

        for app in failed_apps:
            console.print(f"Retrying {app.id}...")
            result = self._launch_app(app, app.virtual_desktop)
            self.launch_results.append(result)

            if result.success:
                console.print(f"[green]✓[/green] {app.id} launched successfully on retry")
            else:
                console.print(f"[red]✗[/red] {app.id} failed again: {result.error}")
                all_success = False

            time.sleep(1.0)  # Brief pause between retries

        return all_success