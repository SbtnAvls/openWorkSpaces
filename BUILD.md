# Build Instructions for Windows 11 Workspace Manager

This document provides instructions for building the Windows 11 Workspace Manager executable from source.

## Prerequisites

- Python 3.10 or higher (tested with Python 3.13)
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Build Steps

### 1. Install Dependencies

First, install all required dependencies including PyInstaller:

```bash
pip install -r requirements.txt
```

### 2. Run the Build Script

Execute the build script to create the standalone executable:

```bash
python build.py
```

The build script will:
- Clean previous build artifacts
- Install/verify dependencies
- Create version information file
- Build the executable using PyInstaller
- Create a release package
- Generate a ZIP archive

### 3. Build Output

After a successful build, you will find:

- **`dist/WorkspaceManager.exe`** - Standalone executable (CLI + GUI)
- **`dist/WorkspaceManager-v1.0.0/`** - Release package folder containing:
  - `WorkspaceManager.exe` - The executable
  - `README.md` - Documentation
  - `RELEASE_NOTES.txt` - Release notes
  - `workspaces.example.json` - Example configuration (if present)

- **`dist/WorkspaceManager-v1.0.0.zip`** - Compressed release package (~35MB)

## Build Configuration

### Version Information

Version is defined in `workspace_manager/__version__.py`:

```python
__version__ = "1.0.0"
__app_name__ = "Windows 11 Workspace Manager"
__description__ = "Manage and launch application workspaces on Windows 11"
```

### PyInstaller Spec File

The build configuration is defined in `workspace_manager.spec`. Key settings:

- **Console Mode**: `console=False` (GUI mode, no console window)
- **Single File**: All dependencies are bundled into a single executable
- **UPX Compression**: Enabled for smaller file size
- **Icon**: Can be customized by setting the `icon` parameter (currently None)

### Customizing the Build

#### Change Console Mode

To enable console output (useful for debugging):

Edit `workspace_manager.spec`:
```python
console=True,  # Show console window
```

#### Add an Icon

1. Create or obtain an `.ico` file (e.g., `assets/icon.ico`)
2. Edit `workspace_manager.spec`:
```python
icon='assets/icon.ico',
```

#### Change Output Name

Edit `workspace_manager.spec`:
```python
name='WorkspaceManager',  # Change to your preferred name
```

## Manual Build (without build.py)

If you prefer to build manually:

```bash
# Create version info
python -c "from workspace_manager.__version__ import __version__; print(__version__)"

# Run PyInstaller
pyinstaller workspace_manager.spec --clean

# The executable will be in dist/
```

## Troubleshooting

### Build Fails with ImportError

Make sure all dependencies are installed:
```bash
pip install -r requirements.txt --upgrade
```

### UnicodeEncodeError on Windows

The build script has been updated to use ASCII-safe characters. If you still encounter issues, check your console encoding:
```bash
chcp 65001  # Set to UTF-8
python build.py
```

### Large File Size

The executable is ~35MB due to:
- Python runtime (~15MB)
- GUI framework (customtkinter) (~5MB)
- Windows API libraries (pywin32) (~10MB)
- Other dependencies (~5MB)

To reduce size:
- Remove unused dependencies from `requirements.txt`
- Use `console=True` mode if GUI is not needed
- Consider creating separate CLI and GUI executables

### Missing DLLs

If the executable fails to run on another machine, ensure:
- Visual C++ Redistributables are installed
- Windows is up to date
- Try running from command line to see error messages

## Testing the Build

Test the executable before distribution:

```bash
# Test help command
dist/WorkspaceManager.exe --help

# Test list command
dist/WorkspaceManager.exe list

# Test GUI
dist/WorkspaceManager.exe gui
```

## Distribution

The recommended way to distribute:

1. Use the generated ZIP file: `dist/WorkspaceManager-v1.0.0.zip`
2. Include all files from the release package
3. Provide installation instructions (see RELEASE_NOTES.txt)

## Continuous Integration

For automated builds, you can:

1. Use GitHub Actions workflow:
```yaml
name: Build
on: [push, release]
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt
      - run: python build.py
      - uses: actions/upload-artifact@v3
        with:
          name: WorkspaceManager
          path: dist/WorkspaceManager-v*.zip
```

## Version History

- **v1.0.0** (2024) - Initial release
  - GUI for workspace management
  - CLI for command-line operations
  - Support for multiple virtual desktops
  - Visual window positioning
  - Application finder with icon extraction

## License

See LICENSE file for details.
