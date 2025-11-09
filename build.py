#!/usr/bin/env python3
"""
Build script for Windows 11 Workspace Manager
Creates standalone executables using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Import version info
sys.path.insert(0, str(Path(__file__).parent))
from workspace_manager.__version__ import __version__, __app_name__, __description__

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_step(text):
    print(f"{Colors.OKCYAN}> {text}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}[WARNING] {text}{Colors.ENDC}")

def create_version_file():
    """Create version_info.txt for PyInstaller"""
    print_step("Creating version info file...")

    version_parts = __version__.split('.')

    version_info = f"""# UTF-8
#
# For more details about fixed file info:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_parts[0]}, {version_parts[1]}, {version_parts[2]}, 0),
    prodvers=({version_parts[0]}, {version_parts[1]}, {version_parts[2]}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u''),
        StringStruct(u'FileDescription', u'{__description__}'),
        StringStruct(u'FileVersion', u'{__version__}'),
        StringStruct(u'InternalName', u'WorkspaceManager'),
        StringStruct(u'LegalCopyright', u''),
        StringStruct(u'OriginalFilename', u'WorkspaceManager.exe'),
        StringStruct(u'ProductName', u'{__app_name__}'),
        StringStruct(u'ProductVersion', u'{__version__}')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""

    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)

    print_success("Version info file created")

def clean_build_dirs():
    """Clean up previous build artifacts"""
    print_step("Cleaning previous build artifacts...")

    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['version_info.txt']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")

    for file_name in files_to_clean:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"  Removed {file_name}")

    print_success("Cleanup complete")

def install_dependencies():
    """Install/update build dependencies"""
    print_step("Installing build dependencies...")

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print_error("Failed to install dependencies")
        print(result.stderr)
        return False

    print_success("Dependencies installed")
    return True

def build_executable():
    """Build the executable using PyInstaller"""
    print_step(f"Building {__app_name__} v{__version__}...")

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "workspace_manager.spec", "--clean"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print_error("Build failed")
        print(result.stderr)
        return False

    print_success("Build complete")
    return True

def create_release_package():
    """Create release package with executable and documentation"""
    print_step("Creating release package...")

    release_dir = Path(f"dist/WorkspaceManager-v{__version__}")
    release_dir.mkdir(parents=True, exist_ok=True)

    # Copy executable
    exe_file = Path("dist/WorkspaceManager.exe")
    if exe_file.exists():
        shutil.copy2(exe_file, release_dir / "WorkspaceManager.exe")
        print(f"  Copied WorkspaceManager.exe")
    else:
        print_warning("WorkspaceManager.exe not found")
        return False

    # Copy documentation
    docs_to_copy = ['README.md', 'LICENSE', 'workspaces.example.json']
    for doc in docs_to_copy:
        if Path(doc).exists():
            shutil.copy2(doc, release_dir / doc)
            print(f"  Copied {doc}")

    # Create release notes
    release_notes = f"""# {__app_name__} v{__version__}

## Installation

1. Extract all files to a folder of your choice
2. Run `WorkspaceManager.exe` to launch the GUI
3. Or use command line: `WorkspaceManager.exe list` to see available commands

## Configuration

The configuration file is automatically created at:
`C:\\Users\\<YourUsername>\\Documents\\WorkspaceManager\\workspaces.json`

You can use the included `workspaces.example.json` as a template.

## Quick Start

### GUI Mode
Simply double-click `WorkspaceManager.exe` or run:
```
WorkspaceManager.exe gui
```

### CLI Mode
```
# List workspaces
WorkspaceManager.exe list

# Launch a workspace
WorkspaceManager.exe launch <workspace-name>

# Capture current window state
WorkspaceManager.exe capture <workspace-name>

# Show all commands
WorkspaceManager.exe --help
```

## Documentation

See README.md for full documentation.

## Version {__version__} - Release Notes

- Initial release
- GUI for visual workspace management
- CLI for command-line operations
- Support for multiple virtual desktops
- Visual window positioning
- Application finder with icon extraction
- Auto-save configuration to Documents folder

"""

    with open(release_dir / "RELEASE_NOTES.txt", 'w', encoding='utf-8') as f:
        f.write(release_notes)

    print_success(f"Release package created at: {release_dir}")
    return True

def create_zip_archive():
    """Create ZIP archive of release package"""
    print_step("Creating ZIP archive...")

    release_dir = Path(f"dist/WorkspaceManager-v{__version__}")

    if not release_dir.exists():
        print_warning("Release directory not found")
        return False

    # Create zip file
    zip_path = Path(f"dist/WorkspaceManager-v{__version__}.zip")
    shutil.make_archive(
        str(zip_path.with_suffix('')),
        'zip',
        str(release_dir.parent),
        str(release_dir.name)
    )

    print_success(f"ZIP archive created: {zip_path}")

    # Show file size
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"  Size: {size_mb:.2f} MB")

    return True

def main():
    """Main build process"""
    print_header(f"{__app_name__} v{__version__} - Build Script")

    try:
        # Clean previous builds
        clean_build_dirs()

        # Install dependencies
        if not install_dependencies():
            sys.exit(1)

        # Create version file
        create_version_file()

        # Build executable
        if not build_executable():
            sys.exit(1)

        # Create release package
        if not create_release_package():
            sys.exit(1)

        # Create ZIP archive
        create_zip_archive()

        print_header("Build Complete!")
        print(f"{Colors.OKGREEN}Release package ready at:{Colors.ENDC}")
        print(f"  dist/WorkspaceManager-v{__version__}/")
        print(f"  dist/WorkspaceManager-v{__version__}.zip")
        print()

    except Exception as e:
        print_error(f"Build failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
