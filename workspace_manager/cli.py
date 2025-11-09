"""
Command-line interface for the workspace manager.
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.logging import RichHandler

from .config import ConfigManager, ConfigError
from .launcher import WorkspaceLauncher
from .capture import WorkspaceCapturer
from .models import Workspace, AppInstance, WindowConfig

# Configure console encoding for Windows
if sys.platform == 'win32':
    # Set console to UTF-8 mode
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
    except Exception:
        pass  # If it fails, continue with default encoding

# Configure logging with Rich
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)
console = Console(legacy_windows=True)  # Enable Windows legacy mode for better compatibility


class WorkspaceCLI:
    """Command-line interface for workspace management."""

    def __init__(self):
        """Initialize the CLI."""
        self.config_manager = ConfigManager()
        self.launcher = WorkspaceLauncher()
        self.capturer = WorkspaceCapturer()

    def run(self, args: list = None) -> int:
        """
        Run the CLI with given arguments.

        Args:
            args: Command-line arguments (uses sys.argv if None)

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        parser = self._create_parser()

        try:
            parsed_args = parser.parse_args(args)

            # Set logging level
            if parsed_args.verbose:
                logging.getLogger().setLevel(logging.DEBUG)
            elif parsed_args.quiet:
                logging.getLogger().setLevel(logging.ERROR)

            # Handle command
            if hasattr(parsed_args, 'func'):
                return parsed_args.func(parsed_args)
            else:
                parser.print_help()
                return 0

        except ConfigError as e:
            console.print(f"[red]Configuration Error: {e}[/red]")
            return 1

        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
            return 130

        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
            if parsed_args.verbose:
                console.print_exception()
            return 1

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            prog='workspace-manager',
            description='Windows 11 Workspace Manager - Manage and launch application workspaces'
        )

        # Global arguments
        parser.add_argument(
            '-c', '--config',
            default='workspaces.json',
            help='Configuration file path (default: workspaces.json)'
        )
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '-q', '--quiet',
            action='store_true',
            help='Suppress non-error output'
        )

        # Create subcommands
        subparsers = parser.add_subparsers(title='commands', dest='command')

        # Launch command
        launch_parser = subparsers.add_parser(
            'launch',
            help='Launch a workspace'
        )
        launch_parser.add_argument(
            'name',
            help='Name of workspace to launch'
        )
        launch_parser.add_argument(
            '-d', '--dry-run',
            action='store_true',
            help='Simulate launch without actually starting applications'
        )
        launch_parser.add_argument(
            '-s', '--sequential',
            action='store_true',
            help='Launch applications sequentially instead of in parallel'
        )
        launch_parser.add_argument(
            '-r', '--retry-failed',
            action='store_true',
            help='Retry failed applications after initial launch'
        )
        launch_parser.set_defaults(func=self.cmd_launch)

        # Capture command
        capture_parser = subparsers.add_parser(
            'capture',
            help='Capture current window state as a workspace'
        )
        capture_parser.add_argument(
            'name',
            nargs='?',
            help='Name for the captured workspace'
        )
        capture_parser.add_argument(
            '-i', '--interactive',
            action='store_true',
            default=True,
            help='Interactive mode for selecting windows (default)'
        )
        capture_parser.add_argument(
            '-a', '--all',
            action='store_true',
            help='Include all windows without prompting'
        )
        capture_parser.add_argument(
            '-o', '--overwrite',
            action='store_true',
            help='Overwrite existing workspace with same name'
        )
        capture_parser.set_defaults(func=self.cmd_capture)

        # List command
        list_parser = subparsers.add_parser(
            'list',
            help='List all workspaces'
        )
        list_parser.add_argument(
            '-d', '--detailed',
            action='store_true',
            help='Show detailed information for each workspace'
        )
        list_parser.set_defaults(func=self.cmd_list)

        # Show command
        show_parser = subparsers.add_parser(
            'show',
            help='Show details of a specific workspace'
        )
        show_parser.add_argument(
            'name',
            help='Name of workspace to show'
        )
        show_parser.add_argument(
            '-j', '--json',
            action='store_true',
            help='Output in JSON format'
        )
        show_parser.set_defaults(func=self.cmd_show)

        # Remove command
        remove_parser = subparsers.add_parser(
            'remove',
            help='Remove a workspace'
        )
        remove_parser.add_argument(
            'name',
            help='Name of workspace to remove'
        )
        remove_parser.add_argument(
            '-y', '--yes',
            action='store_true',
            help='Skip confirmation prompt'
        )
        remove_parser.set_defaults(func=self.cmd_remove)

        # Export command
        export_parser = subparsers.add_parser(
            'export',
            help='Export a workspace to a file'
        )
        export_parser.add_argument(
            'name',
            help='Name of workspace to export'
        )
        export_parser.add_argument(
            '-o', '--output',
            required=True,
            help='Output file path'
        )
        export_parser.set_defaults(func=self.cmd_export)

        # Import command
        import_parser = subparsers.add_parser(
            'import',
            help='Import a workspace from a file'
        )
        import_parser.add_argument(
            'file',
            help='File to import from'
        )
        import_parser.add_argument(
            '-o', '--overwrite',
            action='store_true',
            help='Overwrite existing workspace with same name'
        )
        import_parser.set_defaults(func=self.cmd_import)

        # Validate command
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate workspace configurations'
        )
        validate_parser.add_argument(
            'name',
            nargs='?',
            help='Name of workspace to validate (all if not specified)'
        )
        validate_parser.set_defaults(func=self.cmd_validate)

        return parser

    def cmd_launch(self, args) -> int:
        """Handle the launch command."""
        self.config_manager.config_file = Path(args.config)

        try:
            workspace = self.config_manager.get_workspace(args.name)

            if not workspace:
                console.print(f"[red]Workspace '{args.name}' not found[/red]")
                self._suggest_similar_workspace(args.name)
                return 1

            # Launch the workspace
            success = self.launcher.launch_workspace(
                workspace,
                dry_run=args.dry_run,
                sequential=args.sequential
            )

            # Retry failed apps if requested
            if args.retry_failed and not args.dry_run:
                failed_apps = self.launcher.get_failed_apps()
                if failed_apps:
                    console.print(f"\n[yellow]Retrying {len(failed_apps)} failed application(s)...[/yellow]")
                    self.launcher.retry_failed_apps(workspace)

            return 0 if success else 1

        except Exception as e:
            console.print(f"[red]Failed to launch workspace: {e}[/red]")
            return 1

    def cmd_capture(self, args) -> int:
        """Handle the capture command."""
        self.config_manager.config_file = Path(args.config)

        try:
            # Capture the workspace
            workspace = self.capturer.capture_workspace(
                workspace_name=args.name,
                interactive=args.interactive and not args.all,
                include_all=args.all
            )

            if not workspace:
                return 1

            # Save to configuration
            self.config_manager.add_workspace(workspace, overwrite=args.overwrite)

            console.print(f"\n[green]✓ Workspace '{workspace.name}' saved successfully[/green]")
            return 0

        except ConfigError as e:
            console.print(f"[red]{e}[/red]")
            return 1

        except Exception as e:
            console.print(f"[red]Failed to capture workspace: {e}[/red]")
            return 1

    def cmd_list(self, args) -> int:
        """Handle the list command."""
        self.config_manager.config_file = Path(args.config)

        try:
            workspaces = self.config_manager.list_workspaces()

            if not workspaces:
                console.print("[yellow]No workspaces defined[/yellow]")
                console.print("\nUse 'capture' to create a workspace from current window state")
                return 0

            console.print(f"\n[bold]Available Workspaces ({len(workspaces)})[/bold]\n")

            if args.detailed:
                # Detailed view
                collection = self.config_manager.load()

                for ws in collection.workspaces:
                    self._show_workspace_details(ws, compact=True)
                    console.print()
            else:
                # Simple list
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Name", style="cyan")
                table.add_column("Description")
                table.add_column("Apps", justify="right")
                table.add_column("Desktops", justify="right")

                collection = self.config_manager.load()

                for ws in collection.workspaces:
                    table.add_row(
                        ws.name,
                        ws.description or "[dim]No description[/dim]",
                        str(len(ws.apps)),
                        str(ws.get_required_desktops())
                    )

                console.print(table)

            return 0

        except Exception as e:
            console.print(f"[red]Failed to list workspaces: {e}[/red]")
            return 1

    def cmd_show(self, args) -> int:
        """Handle the show command."""
        self.config_manager.config_file = Path(args.config)

        try:
            workspace = self.config_manager.get_workspace(args.name)

            if not workspace:
                console.print(f"[red]Workspace '{args.name}' not found[/red]")
                self._suggest_similar_workspace(args.name)
                return 1

            if args.json:
                # JSON output
                import json
                print(json.dumps(workspace.to_dict(), indent=2))
            else:
                # Rich formatted output
                self._show_workspace_details(workspace)

            return 0

        except Exception as e:
            console.print(f"[red]Failed to show workspace: {e}[/red]")
            return 1

    def cmd_remove(self, args) -> int:
        """Handle the remove command."""
        self.config_manager.config_file = Path(args.config)

        try:
            # Check if workspace exists
            workspace = self.config_manager.get_workspace(args.name)

            if not workspace:
                console.print(f"[red]Workspace '{args.name}' not found[/red]")
                self._suggest_similar_workspace(args.name)
                return 1

            # Confirm removal
            if not args.yes:
                from rich.prompt import Confirm
                if not Confirm.ask(
                    f"[bold]Remove workspace '{args.name}'?[/bold]"
                ):
                    console.print("[yellow]Removal cancelled[/yellow]")
                    return 0

            # Remove workspace
            if self.config_manager.remove_workspace(args.name):
                console.print(f"[green]✓ Workspace '{args.name}' removed[/green]")
                return 0
            else:
                console.print(f"[red]Failed to remove workspace '{args.name}'[/red]")
                return 1

        except Exception as e:
            console.print(f"[red]Failed to remove workspace: {e}[/red]")
            return 1

    def cmd_export(self, args) -> int:
        """Handle the export command."""
        self.config_manager.config_file = Path(args.config)

        try:
            self.config_manager.export_workspace(args.name, args.output)
            console.print(f"[green]✓ Exported workspace '{args.name}' to {args.output}[/green]")
            return 0

        except ConfigError as e:
            console.print(f"[red]{e}[/red]")
            return 1

        except Exception as e:
            console.print(f"[red]Failed to export workspace: {e}[/red]")
            return 1

    def cmd_import(self, args) -> int:
        """Handle the import command."""
        self.config_manager.config_file = Path(args.config)

        try:
            self.config_manager.import_workspace(args.file, overwrite=args.overwrite)
            console.print(f"[green]✓ Imported workspace from {args.file}[/green]")
            return 0

        except ConfigError as e:
            console.print(f"[red]{e}[/red]")
            return 1

        except Exception as e:
            console.print(f"[red]Failed to import workspace: {e}[/red]")
            return 1

    def cmd_validate(self, args) -> int:
        """Handle the validate command."""
        self.config_manager.config_file = Path(args.config)

        try:
            collection = self.config_manager.load()

            if args.name:
                # Validate specific workspace
                workspace = collection.get_workspace(args.name)

                if not workspace:
                    console.print(f"[red]Workspace '{args.name}' not found[/red]")
                    return 1

                errors = self.config_manager.validate_workspace(workspace)

                if errors:
                    console.print(f"[red]Validation failed for '{args.name}':[/red]")
                    for error in errors:
                        console.print(f"  • {error}")
                    return 1
                else:
                    console.print(f"[green]✓ Workspace '{args.name}' is valid[/green]")
                    return 0

            else:
                # Validate all workspaces
                all_valid = True

                for workspace in collection.workspaces:
                    errors = self.config_manager.validate_workspace(workspace)

                    if errors:
                        console.print(f"[red]✗ {workspace.name}:[/red]")
                        for error in errors:
                            console.print(f"  • {error}")
                        all_valid = False
                    else:
                        console.print(f"[green]✓ {workspace.name}[/green]")

                return 0 if all_valid else 1

        except Exception as e:
            console.print(f"[red]Failed to validate: {e}[/red]")
            return 1

    def _show_workspace_details(self, workspace: Workspace, compact: bool = False) -> None:
        """Show detailed workspace information."""
        # Create info panel
        info = Text()
        info.append("Name: ", style="bold")
        info.append(workspace.name + "\n")
        info.append("Description: ", style="bold")
        info.append((workspace.description or "No description") + "\n")
        info.append("Applications: ", style="bold")
        info.append(str(len(workspace.apps)) + "\n")
        info.append("Virtual Desktops: ", style="bold")
        info.append(str(workspace.get_required_desktops()))

        console.print(Panel(info, title="Workspace Details", border_style="cyan"))

        # Show applications
        if workspace.apps and not compact:
            console.print("\n[bold]Applications:[/bold]\n")

            for app in workspace.apps:
                # App panel
                app_info = Text()
                app_info.append("ID: ", style="bold")
                app_info.append(app.id + "\n")
                app_info.append("Executable: ", style="bold")
                app_info.append(app.exe + "\n")

                if app.args:
                    app_info.append("Arguments: ", style="bold")
                    app_info.append(" ".join(app.args) + "\n")

                if app.working_dir:
                    app_info.append("Working Dir: ", style="bold")
                    app_info.append(app.working_dir + "\n")

                app_info.append("Desktop: ", style="bold")
                app_info.append(str(app.virtual_desktop) + "\n")
                app_info.append("Position: ", style="bold")
                app_info.append(f"({app.window.x}, {app.window.y})\n")
                app_info.append("Size: ", style="bold")
                app_info.append(f"{app.window.width}x{app.window.height}")

                console.print(Panel(app_info, title=app.id, border_style="dim"))

    def _suggest_similar_workspace(self, name: str) -> None:
        """Suggest similar workspace names."""
        all_names = self.config_manager.list_workspaces()

        if not all_names:
            return

        # Simple similarity check (starts with same letter)
        similar = [n for n in all_names if n[0].lower() == name[0].lower()]

        if similar:
            console.print("\n[dim]Did you mean one of these?[/dim]")
            for ws_name in similar[:3]:
                console.print(f"  • {ws_name}")


def main():
    """Main entry point."""
    cli = WorkspaceCLI()
    sys.exit(cli.run())