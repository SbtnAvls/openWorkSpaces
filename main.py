#!/usr/bin/env python3
"""
Windows 11 Workspace Manager

A powerful tool for managing and launching application workspaces on Windows 11.
Allows you to define, capture, and launch custom workspace configurations with
full control over window positions, virtual desktops, and application parameters.

Usage:
    python main.py [command] [options]

Commands:
    launch  - Launch a workspace
    capture - Capture current window state as a workspace
    list    - List all workspaces
    show    - Show details of a workspace
    remove  - Remove a workspace
    export  - Export a workspace to a file
    import  - Import a workspace from a file
    validate - Validate workspace configurations

Examples:
    python main.py launch development
    python main.py capture my_workspace --interactive
    python main.py list --detailed

For more help:
    python main.py --help
    python main.py [command] --help
"""

import sys
import os

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workspace_manager.cli import main

if __name__ == "__main__":
    main()