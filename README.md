# Windows 11 Workspace Manager

A powerful and intuitive workspace management tool for Windows 11 that allows you to define, capture, and launch custom application workspaces with full control over window positions, virtual desktops, and application parameters.

## Features

- **Workspace Definition**: Define custom workspaces with multiple applications
- **Virtual Desktop Support**: Automatically create and manage Windows 11 virtual desktops
- **Window Management**: Control exact window positions, sizes, and desktop placement
- **Workspace Capture**: Capture your current window layout as a reusable workspace
- **Interactive Configuration**: User-friendly interactive mode for workspace creation
- **Import/Export**: Share workspaces between systems
- **Validation**: Built-in configuration validation to ensure workspaces work correctly

## Requirements

- **Operating System**: Windows 11 (Windows 10 may work with limitations)
- **Python**: 3.10 or higher
- **Administrator privileges**: Not required, but recommended for some features

## Installation

### 1. Clone or Download

```bash
git clone https://github.com/yourusername/workspace-manager.git
cd workspace-manager
```

Or download and extract the ZIP file.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python main.py --help
```

## Quick Start

### Launch a Minimal Test Workspace

1. (Optional) Copy the example configuration to your Documents folder:
```bash
copy workspaces.example.json "%USERPROFILE%\Documents\WorkspaceManager\workspaces.json"
```

2. Launch the minimal test workspace:
```bash
python main.py launch minimal
```

This will open a simple Notepad window to verify everything is working.

**Note:** The configuration file will be created automatically in `Documents\WorkspaceManager\` when you create your first workspace using the GUI or CLI commands.

### Capture Your Current Setup

1. Arrange your windows as desired across virtual desktops
2. Run the capture command:
```bash
python main.py capture my_workspace
```
3. Follow the interactive prompts to select windows and configure the workspace

### Launch Your Workspace

```bash
python main.py launch my_workspace
```

## Usage

### Commands

#### `launch` - Launch a workspace
```bash
python main.py launch <workspace_name> [options]

Options:
  -d, --dry-run      Simulate launch without starting applications
  -s, --sequential   Launch apps one by one instead of in parallel
  -r, --retry-failed Retry failed applications
```

#### `capture` - Capture current window state
```bash
python main.py capture [workspace_name] [options]

Options:
  -i, --interactive  Interactive mode (default)
  -a, --all         Include all windows without prompting
  -o, --overwrite   Overwrite existing workspace
```

#### `list` - List all workspaces
```bash
python main.py list [options]

Options:
  -d, --detailed  Show detailed information
```

#### `show` - Show workspace details
```bash
python main.py show <workspace_name> [options]

Options:
  -j, --json  Output in JSON format
```

#### `remove` - Remove a workspace
```bash
python main.py remove <workspace_name> [options]

Options:
  -y, --yes  Skip confirmation
```

#### `export` - Export workspace to file
```bash
python main.py export <workspace_name> -o <output_file>
```

#### `import` - Import workspace from file
```bash
python main.py import <file> [options]

Options:
  -o, --overwrite  Overwrite existing workspace
```

#### `validate` - Validate workspace configuration
```bash
python main.py validate [workspace_name]
```

### Configuration File Format

The configuration is stored in `workspaces.json`, which is automatically saved in your Documents folder at:
`C:\Users\<YourUsername>\Documents\WorkspaceManager\workspaces.json`

The file will be created automatically when you create your first workspace.

```json
{
  "workspaces": [
    {
      "name": "development",
      "description": "My development environment",
      "apps": [
        {
          "id": "vscode",
          "exe": "C:\\Program Files\\VS Code\\Code.exe",
          "args": ["C:\\projects\\my-project"],
          "working_dir": "C:\\projects\\my-project",
          "virtual_desktop": 0,
          "window": {
            "x": 0,
            "y": 0,
            "width": 1920,
            "height": 1080
          }
        }
      ]
    }
  ]
}
```

### Field Descriptions

- **name**: Unique workspace identifier
- **description**: Optional description
- **apps**: List of applications to launch
  - **id**: Unique identifier within the workspace
  - **exe**: Path to executable (can be in PATH)
  - **args**: Command-line arguments (optional)
  - **working_dir**: Working directory (optional)
  - **virtual_desktop**: Target desktop index (0-based)
  - **window**: Window position and size
    - **x, y**: Top-left corner position
    - **width, height**: Window dimensions

## Examples

### Development Workspace

Create a development workspace with VS Code, terminals, and browser:

```json
{
  "name": "fullstack",
  "description": "Full stack development setup",
  "apps": [
    {
      "id": "editor",
      "exe": "code",
      "args": ["."],
      "working_dir": "C:\\projects\\myapp",
      "virtual_desktop": 0,
      "window": {"x": 0, "y": 0, "width": 1920, "height": 1080}
    },
    {
      "id": "backend_terminal",
      "exe": "wt.exe",
      "args": ["-d", "C:\\projects\\myapp\\backend"],
      "virtual_desktop": 1,
      "window": {"x": 0, "y": 0, "width": 960, "height": 1080}
    },
    {
      "id": "browser",
      "exe": "chrome.exe",
      "args": ["--new-window", "http://localhost:3000"],
      "virtual_desktop": 1,
      "window": {"x": 960, "y": 0, "width": 960, "height": 1080}
    }
  ]
}
```

### Productivity Workspace

Office applications setup:

```json
{
  "name": "office",
  "description": "Office productivity suite",
  "apps": [
    {
      "id": "outlook",
      "exe": "outlook.exe",
      "virtual_desktop": 0,
      "window": {"x": 0, "y": 0, "width": 960, "height": 1080}
    },
    {
      "id": "teams",
      "exe": "Teams.exe",
      "virtual_desktop": 0,
      "window": {"x": 960, "y": 0, "width": 960, "height": 1080}
    }
  ]
}
```

## Tips & Best Practices

### 1. Start Simple
Begin with a minimal workspace and gradually add complexity:
```bash
python main.py capture test_workspace
# Select just 2-3 windows
python main.py launch test_workspace
```

### 2. Use Capture for Complex Setups
Instead of manually writing JSON, arrange your windows and capture:
```bash
python main.py capture --interactive
```

### 3. Validate Before Launch
Always validate after manual edits:
```bash
python main.py validate my_workspace
```

### 4. Use Dry Run for Testing
Test without actually launching:
```bash
python main.py launch my_workspace --dry-run
```

### 5. Handle Path Variables
Use environment variables in paths by editing after capture:
- Replace `C:\\Users\\John` with `%USERPROFILE%`
- Replace absolute paths with relative ones where appropriate

## Known Limitations

### Virtual Desktop Limitations
- **Windows 11 API Restrictions**: Some virtual desktop operations may require additional permissions
- **Desktop Creation**: Creating desktops programmatically uses keyboard shortcuts (Win+Ctrl+D)
- **Window Movement**: Some applications resist being moved between desktops
- **UWP Apps**: Windows Store apps may not respond to window positioning

### Application Limitations
- **Startup Time**: Some applications take longer to create windows
- **Multiple Windows**: Apps that create multiple windows may not position correctly
- **Minimized Start**: Some apps start minimized and ignore positioning
- **Admin Apps**: Applications running as administrator may not be controllable

### Capture Limitations
- **Arguments**: Cannot always determine original command-line arguments
- **Working Directory**: May not detect the original working directory
- **Hidden Windows**: System and background windows are filtered out

## Troubleshooting

### Issue: "pyvda not available" Warning
**Solution**: Install pyvda:
```bash
pip install pyvda
```

### Issue: Windows Don't Move to Correct Desktop
**Causes**:
1. Application doesn't support virtual desktop moves
2. Not enough virtual desktops exist

**Solutions**:
- Ensure virtual desktops are created first
- Try running with administrator privileges
- Some apps work better with sequential launch mode:
```bash
python main.py launch workspace_name --sequential
```

### Issue: Window Positions Are Incorrect
**Causes**:
1. Multiple monitors with different resolutions
2. DPI scaling issues
3. Application overrides positioning

**Solutions**:
- Capture workspace with windows already positioned
- Adjust coordinates manually in JSON
- Use primary monitor for critical windows

### Issue: Applications Don't Launch
**Causes**:
1. Incorrect executable path
2. Missing dependencies
3. Permission issues

**Solutions**:
- Use full paths to executables
- Verify paths with: `where <program>`
- Check working directory exists
- Run as administrator if needed

### Issue: Capture Doesn't Find All Windows
**Causes**:
1. Windows are minimized
2. Windows are on other virtual desktops
3. System windows are filtered

**Solutions**:
- Restore all windows before capture
- Switch through all virtual desktops
- Use `--all` flag to include more windows

## Advanced Usage

### Programmatic Usage

```python
from workspace_manager.config import ConfigManager
from workspace_manager.launcher import WorkspaceLauncher

# Load and launch a workspace
config = ConfigManager()
workspace = config.get_workspace("development")

launcher = WorkspaceLauncher()
launcher.launch_workspace(workspace)
```

### Custom Window Filters

Edit `capture.py` to modify window filtering:

```python
def _filter_system_windows(self, windows):
    # Add your custom filtering logic
    custom_filter = ["myapp.exe", "special.exe"]
    return [w for w in windows if w.exe_path in custom_filter]
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is provided as-is for educational and personal use.

## Support

For issues, questions, or suggestions:
1. Check the troubleshooting section
2. Review existing issues on GitHub
3. Create a new issue with details about your environment and problem

## Changelog

### Version 1.0.0
- Initial release
- Full workspace management capabilities
- Virtual desktop support
- Interactive capture mode
- Import/export functionality

---

**Note**: This tool is designed for Windows 11. Windows 10 users may experience limited functionality, especially regarding virtual desktop features.