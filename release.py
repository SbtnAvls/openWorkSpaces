#!/usr/bin/env python3
"""
Complete release script for Windows 11 Workspace Manager
Creates both standalone EXE and MSI installer packages
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Import version info
sys.path.insert(0, str(Path(__file__).parent))
from workspace_manager.__version__ import __version__, __app_name__

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
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_step(text):
    print(f"{Colors.OKCYAN}> {text}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}[WARNING] {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKBLUE}[INFO] {text}{Colors.ENDC}")

def run_command(cmd, description, ignore_errors=False):
    """Run a command and handle errors"""
    print_step(description)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=True
    )

    if result.returncode != 0 and not ignore_errors:
        print_error(f"Command failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        print(result.stderr)
        return False

    print_success(f"{description} - Complete")
    return True

def clean_all():
    """Clean all build artifacts"""
    print_step("Cleaning all build artifacts...")

    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['version_info.txt']

    import time

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    shutil.rmtree(dir_name)
                    print(f"  Removed {dir_name}/")
                    break
                except (PermissionError, OSError) as e:
                    if attempt < max_attempts - 1:
                        print_warning(f"  Retry {attempt + 1}/{max_attempts} - Files in use, waiting...")
                        time.sleep(2)
                    else:
                        print_warning(f"  Could not remove {dir_name}/ - Files may be in use")
                        print_info(f"  Close any Windows Explorer windows or running programs, then try again")
                        raise

    for file_name in files_to_clean:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                print(f"  Removed {file_name}")
            except (PermissionError, OSError):
                print_warning(f"  Could not remove {file_name}")

    print_success("Cleanup complete")

def install_dependencies():
    """Install/update all dependencies"""
    print_step("Installing build dependencies...")

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print_error("Failed to install dependencies")
        print(result.stderr)
        return False

    print_success("Dependencies installed")
    return True

def build_pyinstaller_exe():
    """Build standalone EXE with PyInstaller"""
    print_header("Building Standalone EXE (PyInstaller)")

    # Run the original build.py script
    result = subprocess.run(
        [sys.executable, "build.py"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print_error("PyInstaller build failed")
        print(result.stderr)
        return False

    print_success("PyInstaller EXE built successfully")
    return True

def build_msi_installer():
    """Build MSI installer with cx_Freeze"""
    print_header("Building MSI Installer (cx_Freeze)")

    print_step("Running cx_Freeze setup...")

    result = subprocess.run(
        [sys.executable, "setup_msi.py", "bdist_msi"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        # Check if it's the Python 3.13 issue
        if "bdist_msi is not supported on Python 3.13" in result.stderr:
            print_warning("MSI build skipped - cx_Freeze doesn't support Python 3.13 yet")
            print_info("  Use Inno Setup installer instead (installer.iss)")
            print_info("  Or use the standalone EXE + ZIP for distribution")
            return False

        print_error("MSI build failed")
        print(result.stderr)
        return False

    # Find the generated MSI file
    msi_files = list(Path("dist").glob("*.msi"))

    if not msi_files:
        print_error("MSI file not found in dist/")
        return False

    # Rename MSI to standard naming
    msi_file = msi_files[0]
    new_msi_name = f"WorkspaceManager-v{__version__}.msi"
    new_msi_path = Path("dist") / new_msi_name

    if new_msi_path.exists():
        os.remove(new_msi_path)

    msi_file.rename(new_msi_path)

    print_success(f"MSI installer created: {new_msi_path}")
    print_info(f"  Size: {new_msi_path.stat().st_size / (1024*1024):.2f} MB")

    return True

def check_inno_setup():
    """Check if Inno Setup is installed"""
    print_step("Checking for Inno Setup...")

    # Common Inno Setup installation paths
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]

    for path in inno_paths:
        if Path(path).exists():
            print_success(f"Found Inno Setup: {path}")
            return path

    print_warning("Inno Setup not found - Skipping .exe installer generation")
    print_info("  Download from: https://jrsoftware.org/isdl.php")
    print_info("  Then re-run this script to generate .exe installer")
    return None

def build_inno_installer():
    """Build installer using Inno Setup"""
    print_header("Building Setup Executable (Inno Setup)")

    inno_compiler = check_inno_setup()

    if not inno_compiler:
        return False

    print_step("Compiling Inno Setup script...")

    result = subprocess.run(
        [inno_compiler, "installer.iss"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print_error("Inno Setup compilation failed")
        print(result.stderr)
        return False

    # Find the generated setup file
    setup_files = list(Path("dist/installer").glob("*-Setup.exe"))

    if setup_files:
        setup_file = setup_files[0]
        print_success(f"Setup installer created: {setup_file}")
        print_info(f"  Size: {setup_file.stat().st_size / (1024*1024):.2f} MB")
        return True
    else:
        print_warning("Setup installer file not found")
        return False

def create_release_summary():
    """Create a summary file of all releases"""
    print_step("Creating release summary...")

    dist_path = Path("dist")

    summary = f"""# Release Package Summary - v{__version__}

## Generated Files

"""

    # List all files in dist
    files_info = []

    for item in dist_path.iterdir():
        if item.is_file():
            size_mb = item.stat().st_size / (1024 * 1024)
            files_info.append({
                'name': item.name,
                'size': size_mb,
                'type': 'File'
            })

    # Sort by name
    files_info.sort(key=lambda x: x['name'])

    # Add to summary
    summary += "### Standalone Executable\n"
    for info in files_info:
        if info['name'].endswith('.exe') and 'Setup' not in info['name']:
            summary += f"- **{info['name']}** ({info['size']:.2f} MB)\n"
            summary += f"  - Portable executable, no installation required\n"
            summary += f"  - Run directly or use command line\n\n"

    summary += "### Installers\n"
    for info in files_info:
        if info['name'].endswith('.msi'):
            summary += f"- **{info['name']}** ({info['size']:.2f} MB)\n"
            summary += f"  - Windows Installer package\n"
            summary += f"  - Adds to Start Menu and PATH\n"
            summary += f"  - Supports upgrades and uninstall\n\n"

    for info in files_info:
        if 'Setup' in info['name'] and info['name'].endswith('.exe'):
            summary += f"- **{info['name']}** ({info['size']:.2f} MB)\n"
            summary += f"  - Inno Setup installer\n"
            summary += f"  - Full installation wizard\n"
            summary += f"  - Desktop and Start Menu shortcuts\n\n"

    summary += "### Archives\n"
    for info in files_info:
        if info['name'].endswith('.zip'):
            summary += f"- **{info['name']}** ({info['size']:.2f} MB)\n"
            summary += f"  - Compressed portable package\n"
            summary += f"  - Extract and run\n\n"

    summary += f"""## Installation Methods

### Method 1: MSI Installer (Recommended)
1. Download `WorkspaceManager-v{__version__}.msi`
2. Double-click to run installer
3. Follow installation wizard
4. Application will be in Start Menu
5. Command available in PATH

### Method 2: Inno Setup Installer
1. Download `WorkspaceManager-v{__version__}-Setup.exe`
2. Run the setup executable
3. Choose installation location
4. Select desktop shortcut option
5. Launch after installation

### Method 3: Portable Executable
1. Download `WorkspaceManager-v{__version__}.zip`
2. Extract to any folder
3. Run `WorkspaceManager.exe`
4. No installation needed

### Method 4: Standalone EXE
1. Download `WorkspaceManager.exe`
2. Place in any folder
3. Run directly
4. No installation needed

## Usage

### GUI Mode
- Run `WorkspaceManager.exe` (or use Start Menu shortcut)
- Or command: `WorkspaceManager.exe gui`

### CLI Mode
```bash
# List workspaces
WorkspaceManager.exe list

# Launch a workspace
WorkspaceManager.exe launch <name>

# Capture current setup
WorkspaceManager.exe capture <name>

# Show help
WorkspaceManager.exe --help
```

## Configuration

Configuration is stored in:
`C:\\Users\\<YourUsername>\\Documents\\WorkspaceManager\\workspaces.json`

The file is created automatically on first use.

## Uninstallation

### If installed with MSI:
- Use Windows Settings > Apps > Installed Apps
- Or run: `msiexec /x WorkspaceManager-v{__version__}.msi`

### If installed with Inno Setup:
- Use Windows Settings > Apps > Installed Apps
- Or run uninstaller from Start Menu

### If using portable version:
- Simply delete the folder

---
Generated: {Path(__file__).name}
Version: {__version__}
"""

    with open(dist_path / "RELEASE_SUMMARY.md", 'w', encoding='utf-8') as f:
        f.write(summary)

    print_success("Release summary created")

def main():
    """Main release process"""
    print_header(f"{__app_name__} v{__version__} - Complete Release Builder")

    try:
        # Clean previous builds
        clean_all()

        # Install dependencies
        if not install_dependencies():
            sys.exit(1)

        # Build PyInstaller EXE
        if not build_pyinstaller_exe():
            print_error("PyInstaller build failed - Stopping")
            sys.exit(1)

        # Build MSI installer
        if not build_msi_installer():
            print_warning("MSI build failed - Continuing anyway")

        # Build Inno Setup installer (optional)
        build_inno_installer()  # Don't fail if this doesn't work

        # Create release summary
        create_release_summary()

        # Final summary
        print_header("Release Build Complete!")

        print(f"{Colors.OKGREEN}All release packages created successfully!{Colors.ENDC}\n")

        print(f"{Colors.BOLD}Available packages:{Colors.ENDC}")

        dist_path = Path("dist")
        for item in sorted(dist_path.iterdir()):
            if item.is_file() and not item.name.startswith('.'):
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"  - {item.name} ({size_mb:.2f} MB)")

        print(f"\n{Colors.OKBLUE}Release files location: dist/{Colors.ENDC}")
        print(f"{Colors.OKBLUE}Release summary: dist/RELEASE_SUMMARY.md{Colors.ENDC}\n")

    except KeyboardInterrupt:
        print_warning("\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Build failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
