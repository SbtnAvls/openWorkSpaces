# Release Guide for Windows 11 Workspace Manager

This document explains how to create new releases with both standalone executables and installer packages.

## Quick Release

To create a complete release with all packages (EXE, ZIP, and MSI):

```bash
python release.py
```

This single command will:
- Clean previous builds
- Install/update dependencies
- Build standalone EXE with PyInstaller
- Create portable ZIP package
- Build MSI installer with cx_Freeze
- Build setup executable with Inno Setup (if installed)
- Generate release summary

## Release Options

### Option 1: Complete Release (Recommended)

```bash
python release.py
```

**Generates:**
- `dist/WorkspaceManager.exe` - Standalone executable (~35 MB)
- `dist/WorkspaceManager-v1.0.0.zip` - Portable package
- `dist/WorkspaceManager-v1.0.0.msi` - Windows Installer
- `dist/installer/WorkspaceManager-v1.0.0-Setup.exe` - Inno Setup installer (if Inno Setup installed)
- `dist/RELEASE_SUMMARY.md` - Release documentation

### Option 2: EXE and ZIP Only

```bash
python build.py
```

**Generates:**
- `dist/WorkspaceManager.exe` - Standalone executable
- `dist/WorkspaceManager-v1.0.0.zip` - Portable package

### Option 3: MSI Only

```bash
python setup_msi.py bdist_msi
```

**Generates:**
- `dist/*.msi` - Windows Installer package

## Before Creating a Release

### 1. Update Version Number

Edit `workspace_manager/__version__.py`:

```python
__version__ = "1.1.0"  # Update version
__app_name__ = "Windows 11 Workspace Manager"
__author__ = "Your Name"  # Update if needed
```

### 2. Update Installer Scripts

#### For Inno Setup (`installer.iss`):

```ini
#define MyAppVersion "1.1.0"  ; Update version
```

#### For cx_Freeze MSI (`setup_msi.py`):

Version is automatically read from `__version__.py` - no changes needed!

### 3. Update Changelog (if you have one)

Document new features, bug fixes, and changes.

### 4. Test the Application

```bash
# Run tests (if you have them)
pytest tests/

# Manual testing
python main.py gui
python main.py list
```

## Creating a Release

### Step 1: Clean Previous Builds

```bash
# Manual cleanup
rm -rf build/ dist/

# Or let the scripts do it
python release.py  # Cleans automatically
```

### Step 2: Run Release Script

```bash
python release.py
```

Watch for any errors in the output. The script will show:
- ✓ Green checkmarks for successful steps
- ✗ Red X for errors
- ⚠ Yellow warnings for optional features

### Step 3: Verify Build Output

Check `dist/` directory:

```bash
ls -lh dist/
```

Expected files:
```
WorkspaceManager.exe                    (~35 MB)
WorkspaceManager-v1.0.0.zip            (~35 MB)
WorkspaceManager-v1.0.0.msi            (~35 MB)
WorkspaceManager-v1.0.0-Setup.exe      (~36 MB, if Inno Setup installed)
RELEASE_SUMMARY.md                      (Documentation)
```

### Step 4: Test the Builds

```bash
# Test standalone EXE
dist/WorkspaceManager.exe --help

# Test MSI (install in test environment)
# msiexec /i dist/WorkspaceManager-v1.0.0.msi

# Test Inno Setup installer
# Run the -Setup.exe file
```

### Step 5: Create Git Tag

```bash
git tag -a v1.0.0 -m "Release v1.0.0 - Your release notes here"
git push origin v1.0.0
```

### Step 6: Create GitHub Release (Optional)

1. Go to your GitHub repository
2. Click "Releases" > "Create a new release"
3. Select the tag you just created
4. Upload the files from `dist/`:
   - `WorkspaceManager-v1.0.0.zip`
   - `WorkspaceManager-v1.0.0.msi`
   - `WorkspaceManager-v1.0.0-Setup.exe` (if available)
5. Copy content from `dist/RELEASE_SUMMARY.md` to release notes
6. Publish release

## Installer Types

### 1. Standalone EXE
- **File**: `WorkspaceManager.exe`
- **Size**: ~35 MB
- **Pros**: No installation, portable, run anywhere
- **Cons**: No Start Menu entry, not in PATH
- **Use case**: USB drive, quick testing, portable use

### 2. ZIP Archive
- **File**: `WorkspaceManager-v1.0.0.zip`
- **Size**: ~35 MB
- **Pros**: Portable, includes documentation
- **Cons**: Manual extraction needed
- **Use case**: Distribution, archival

### 3. MSI Installer
- **File**: `WorkspaceManager-v1.0.0.msi`
- **Size**: ~35 MB
- **Pros**:
  - Windows native installer
  - Adds to Start Menu
  - Adds to PATH (optional)
  - Supports upgrades
  - Easy uninstall
- **Cons**: Installation required
- **Use case**: Permanent installation, enterprise deployment

### 4. Inno Setup Installer
- **File**: `WorkspaceManager-v1.0.0-Setup.exe`
- **Size**: ~36 MB
- **Pros**:
  - Full installation wizard
  - Desktop shortcuts
  - Custom installation options
  - Professional appearance
- **Cons**: Requires Inno Setup to build
- **Use case**: Consumer-friendly installation

## Customizing Installers

### Adding an Icon

1. Create or obtain a `.ico` file (recommended: 256x256 with multiple sizes)
2. Place it in `assets/icon.ico`
3. Update these files:

**workspace_manager.spec**:
```python
icon='assets/icon.ico',
```

**setup_msi.py**:
```python
"install_icon": "assets/icon.ico",
```

**installer.iss**:
```ini
SetupIconFile=assets\icon.ico
```

4. Rebuild

### Changing Installation Location

**setup_msi.py**:
```python
"initial_target_dir": r"[ProgramFilesFolder]\YourFolder",
```

**installer.iss**:
```ini
DefaultDirName={autopf}\YourFolder
```

### Changing Upgrade GUID

For MSI, edit `setup_msi.py`:
```python
"upgrade_code": "{YOUR-NEW-GUID-HERE}",
```

Generate a new GUID at: https://www.guidgenerator.com/

## Troubleshooting

### cx_Freeze MSI Build Fails

```bash
# Reinstall cx_Freeze
pip install --upgrade cx-Freeze

# Check for missing dependencies
python setup_msi.py bdist_msi --verbose
```

### PyInstaller EXE is Too Large

Edit `workspace_manager.spec`:
```python
excludes=[
    # Add more modules to exclude
    "test",
    "unittest",
    "xml",
    "email",
],
```

### Inno Setup Not Found

1. Download from: https://jrsoftware.org/isdl.php
2. Install to default location
3. Re-run `release.py`

### MSI Installation Requires Admin

Edit `setup_msi.py`:
```python
"all_users": False,  # User-level install (no admin)
```

## CI/CD Automation

### GitHub Actions Example

Create `.github/workflows/release.yml`:

```yaml
name: Release Build

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Build release packages
        run: python release.py

      - name: Upload release assets
        uses: actions/upload-artifact@v3
        with:
          name: release-packages
          path: |
            dist/*.exe
            dist/*.zip
            dist/*.msi
            dist/RELEASE_SUMMARY.md
```

## Version History

- **v1.0.0** (2024-11-09)
  - Initial release
  - MSI installer support
  - Inno Setup installer support
  - Automated release script

## Best Practices

1. **Always test before releasing**
   - Test on clean Windows installation
   - Test both install and uninstall
   - Verify shortcuts and PATH

2. **Keep version numbers consistent**
   - Update in `__version__.py` only
   - Scripts read from there automatically

3. **Document changes**
   - Update README.md
   - Keep changelog
   - Include in release notes

4. **Tag releases in Git**
   - Makes it easy to track
   - Enables CI/CD
   - Helps with troubleshooting

5. **Test upgrades**
   - Install old version
   - Install new version
   - Verify upgrade works smoothly

## Support

For issues with the build process:
1. Check the build log output
2. Try `python release.py` with verbose output
3. Check that all dependencies are installed
4. Verify Python version (3.10+)

For application issues:
1. Run in verbose mode: `WorkspaceManager.exe --verbose`
2. Check logs in Documents/WorkspaceManager/
3. Test with example configuration
