"""
Workspace capture - captures current window state into a workspace configuration.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.text import Text

from .models import Workspace, AppInstance, WindowConfig
from .windows_api import (
    enumerate_windows,
    WindowInfo,
    get_process_info
)
from .virtual_desktops import VirtualDesktopManager

logger = logging.getLogger(__name__)
console = Console(legacy_windows=True)  # Enable Windows legacy mode


class WorkspaceCapturer:
    """Captures current system state into a workspace configuration."""

    def __init__(self):
        """Initialize the workspace capturer."""
        self.vd_manager = VirtualDesktopManager()
        self.captured_windows: List[WindowInfo] = []
        self.selected_windows: List[WindowInfo] = []

    def capture_workspace(
        self,
        workspace_name: str = None,
        interactive: bool = True,
        include_all: bool = False
    ) -> Optional[Workspace]:
        """
        Capture current window state into a workspace.

        Args:
            workspace_name: Name for the workspace (will prompt if not provided)
            interactive: If True, allow user to select windows interactively
            include_all: If True, include all windows without asking

        Returns:
            Workspace object or None if cancelled
        """
        console.print("\n[bold cyan]Capturing Current Workspace State[/bold cyan]\n")

        # Get workspace name
        if not workspace_name:
            workspace_name = Prompt.ask("[bold]Enter workspace name")

            if not workspace_name:
                console.print("[red]Workspace name is required[/red]")
                return None

        # Get description
        description = ""
        if interactive:
            description = Prompt.ask(
                "Enter workspace description (optional)",
                default=""
            )

        # Enumerate all windows
        console.print("[dim]Discovering windows...[/dim]")
        self.captured_windows = enumerate_windows()

        if not self.captured_windows:
            console.print("[yellow]No windows found to capture[/yellow]")
            return None

        console.print(f"Found [bold]{len(self.captured_windows)}[/bold] window(s)\n")

        # Select windows to include
        if include_all:
            self.selected_windows = self.captured_windows
        elif interactive:
            self.selected_windows = self._select_windows_interactive()
        else:
            # Default: include all non-system windows
            self.selected_windows = self._filter_system_windows(self.captured_windows)

        if not self.selected_windows:
            console.print("[yellow]No windows selected[/yellow]")
            return None

        # Create workspace from selected windows
        workspace = self._create_workspace_from_windows(
            workspace_name,
            description,
            self.selected_windows,
            interactive
        )

        # Show summary
        self._show_capture_summary(workspace)

        if interactive:
            if not Confirm.ask("\n[bold]Save this workspace configuration?[/bold]"):
                console.print("[yellow]Capture cancelled[/yellow]")
                return None

        return workspace

    def _select_windows_interactive(self) -> List[WindowInfo]:
        """
        Interactively select windows to include.

        Returns:
            List of selected windows
        """
        # Group windows by desktop
        windows_by_desktop = self._group_windows_by_desktop()

        console.print("[bold]Select Windows to Include[/bold]\n")
        console.print("[dim]Use numbers to toggle selection, 'a' for all, 'n' for none, 'd' when done[/dim]\n")

        selected_indices = set()
        window_list = []

        # Build flat list with indices
        for desktop_idx in sorted(windows_by_desktop.keys()):
            windows = windows_by_desktop[desktop_idx]

            if len(windows_by_desktop) > 1:
                console.print(f"\n[bold magenta]Desktop {desktop_idx}[/bold magenta]")

            for window in windows:
                window_list.append(window)
                idx = len(window_list)

                # Display window info
                status = "[green]✓[/green]" if idx in selected_indices else " "
                exe_name = Path(window.exe_path).name if window.exe_path else "Unknown"

                console.print(
                    f"  {status} [{idx:2d}] {window.title[:50]:<50} "
                    f"[dim]({exe_name})[/dim]"
                )

        # Interactive selection loop
        while True:
            console.print()
            choice = Prompt.ask(
                "Toggle selection",
                default="d"
            ).lower().strip()

            if choice == 'd':  # Done
                break
            elif choice == 'a':  # Select all
                selected_indices = set(range(1, len(window_list) + 1))
                console.print("[green]Selected all windows[/green]")
            elif choice == 'n':  # Select none
                selected_indices.clear()
                console.print("[yellow]Deselected all windows[/yellow]")
            else:
                # Try to parse as numbers
                try:
                    # Handle ranges like "1-5" or comma-separated "1,3,5"
                    indices_to_toggle = set()

                    for part in choice.replace(',', ' ').split():
                        if '-' in part:
                            # Range
                            start, end = part.split('-')
                            start = int(start)
                            end = int(end)
                            indices_to_toggle.update(range(start, end + 1))
                        else:
                            # Single number
                            indices_to_toggle.add(int(part))

                    # Toggle selected indices
                    for idx in indices_to_toggle:
                        if 1 <= idx <= len(window_list):
                            if idx in selected_indices:
                                selected_indices.discard(idx)
                                console.print(f"[yellow]Deselected {idx}[/yellow]")
                            else:
                                selected_indices.add(idx)
                                console.print(f"[green]Selected {idx}[/green]")
                        else:
                            console.print(f"[red]Invalid index: {idx}[/red]")

                except (ValueError, AttributeError):
                    console.print("[red]Invalid input. Use numbers, ranges (1-5), or commands (a/n/d)[/red]")

            # Refresh display
            console.clear()
            console.print("[bold]Select Windows to Include[/bold]\n")

            for desktop_idx in sorted(windows_by_desktop.keys()):
                windows = windows_by_desktop[desktop_idx]

                if len(windows_by_desktop) > 1:
                    console.print(f"\n[bold magenta]Desktop {desktop_idx}[/bold magenta]")

                for window in windows:
                    idx = window_list.index(window) + 1
                    status = "[green]✓[/green]" if idx in selected_indices else " "
                    exe_name = Path(window.exe_path).name if window.exe_path else "Unknown"

                    console.print(
                        f"  {status} [{idx:2d}] {window.title[:50]:<50} "
                        f"[dim]({exe_name})[/dim]"
                    )

        # Return selected windows
        selected = [window_list[idx - 1] for idx in sorted(selected_indices)]
        return selected

    def _group_windows_by_desktop(self) -> Dict[int, List[WindowInfo]]:
        """
        Group windows by their virtual desktop.

        Returns:
            Dictionary mapping desktop index to list of windows
        """
        grouped = {}

        for window in self.captured_windows:
            desktop = self.vd_manager.get_window_desktop(window.hwnd)

            if desktop == -1:
                desktop = 0  # Default to first desktop if unknown

            if desktop not in grouped:
                grouped[desktop] = []

            grouped[desktop].append(window)

        return grouped

    def _filter_system_windows(self, windows: List[WindowInfo]) -> List[WindowInfo]:
        """
        Filter out likely system windows.

        Args:
            windows: List of all windows

        Returns:
            List of non-system windows
        """
        filtered = []
        system_processes = {
            'explorer.exe', 'searchui.exe', 'searchapp.exe',
            'shellexperiencehost.exe', 'systemsettings.exe',
            'textinputhost.exe', 'lockapp.exe'
        }

        for window in windows:
            if window.exe_path:
                exe_name = Path(window.exe_path).name.lower()

                # Skip system processes
                if exe_name in system_processes:
                    continue

                # Skip windows with no title (usually hidden)
                if not window.title or window.title.strip() == '':
                    continue

            filtered.append(window)

        return filtered

    def _create_workspace_from_windows(
        self,
        name: str,
        description: str,
        windows: List[WindowInfo],
        interactive: bool
    ) -> Workspace:
        """
        Create a workspace configuration from captured windows.

        Args:
            name: Workspace name
            description: Workspace description
            windows: List of windows to include
            interactive: If True, allow editing app details

        Returns:
            Workspace object
        """
        workspace = Workspace(name=name, description=description)

        console.print("\n[bold]Creating Application Configurations[/bold]\n")

        for idx, window in enumerate(windows, 1):
            # Get desktop index
            desktop = self.vd_manager.get_window_desktop(window.hwnd)
            if desktop == -1:
                desktop = 0

            # Get process info
            proc_info = get_process_info(window.pid)

            # Determine executable path
            exe_path = window.exe_path or (proc_info['exe'] if proc_info else None)

            if not exe_path:
                console.print(
                    f"[yellow]Warning: Could not determine executable for '{window.title}'[/yellow]"
                )
                exe_path = "TODO_EXECUTABLE_PATH"

            # Try to get command line arguments
            args = []
            if proc_info and 'cmdline' in proc_info:
                cmdline = proc_info['cmdline']
                if len(cmdline) > 1:
                    args = cmdline[1:]  # Skip the executable itself

            # Get working directory
            working_dir = None
            if proc_info and 'cwd' in proc_info:
                working_dir = proc_info['cwd']

            # Create app ID
            exe_name = Path(exe_path).stem if exe_path != "TODO_EXECUTABLE_PATH" else "app"
            app_id = f"{exe_name}_{idx}"

            # Interactive editing if requested
            if interactive:
                console.print(f"\n[cyan]Configuring: {window.title}[/cyan]")

                app_id = Prompt.ask(
                    "  App ID",
                    default=app_id
                )

                exe_path = Prompt.ask(
                    "  Executable path",
                    default=exe_path
                )

                args_str = Prompt.ask(
                    "  Arguments (space-separated)",
                    default=" ".join(args) if args else ""
                )
                args = args_str.split() if args_str else []

                working_dir = Prompt.ask(
                    "  Working directory",
                    default=working_dir or ""
                ) or None

                desktop = IntPrompt.ask(
                    "  Virtual desktop",
                    default=desktop
                )

            # Get window position and size
            rect = window.rect
            window_config = WindowConfig(
                x=rect[0],
                y=rect[1],
                width=rect[2] - rect[0],
                height=rect[3] - rect[1]
            )

            # Create app instance
            app = AppInstance(
                id=app_id,
                exe=exe_path,
                args=args,
                working_dir=working_dir,
                virtual_desktop=desktop,
                window=window_config
            )

            workspace.add_app(app)

            if not interactive:
                exe_name = Path(exe_path).name if exe_path != "TODO_EXECUTABLE_PATH" else "Unknown"
                console.print(f"  Added: {app_id} ({exe_name})")

        return workspace

    def _show_capture_summary(self, workspace: Workspace) -> None:
        """
        Show a summary of the captured workspace.

        Args:
            workspace: Captured workspace
        """
        console.print("\n[bold]Capture Summary[/bold]\n")

        # Basic info
        info_text = Text()
        info_text.append("Name: ", style="bold")
        info_text.append(workspace.name + "\n")
        info_text.append("Description: ", style="bold")
        info_text.append(workspace.description or "(none)" + "\n")
        info_text.append("Applications: ", style="bold")
        info_text.append(str(len(workspace.apps)) + "\n")
        info_text.append("Virtual Desktops: ", style="bold")
        info_text.append(str(workspace.get_required_desktops()))

        console.print(Panel(info_text, title="Workspace Info", border_style="cyan"))

        # Applications table
        if workspace.apps:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan")
            table.add_column("Executable")
            table.add_column("Desktop", justify="center")
            table.add_column("Position")
            table.add_column("Size")

            for app in workspace.apps:
                exe_name = Path(app.exe).name
                position = f"{app.window.x},{app.window.y}"
                size = f"{app.window.width}x{app.window.height}"

                table.add_row(
                    app.id,
                    exe_name,
                    str(app.virtual_desktop),
                    position,
                    size
                )

            console.print(table)

    def find_similar_windows(self, exe_path: str) -> List[WindowInfo]:
        """
        Find windows with similar executable paths.

        Args:
            exe_path: Executable path to match

        Returns:
            List of similar windows
        """
        exe_name = Path(exe_path).name.lower()
        similar = []

        for window in self.captured_windows:
            if window.exe_path:
                window_exe = Path(window.exe_path).name.lower()
                if window_exe == exe_name:
                    similar.append(window)

        return similar