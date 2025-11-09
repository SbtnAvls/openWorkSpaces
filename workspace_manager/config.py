"""
Configuration management for workspace files.
Handles loading, saving, and validation of workspace configurations.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from .models import WorkspaceCollection, Workspace

logger = logging.getLogger(__name__)


def get_default_config_path() -> Path:
    """
    Get the default configuration file path in user's Documents folder.
    Creates the directory if it doesn't exist.

    Returns:
        Path to workspaces.json in Documents/WorkspaceManager/
    """
    # Get user's Documents folder
    documents = Path.home() / "Documents"

    # Create WorkspaceManager folder in Documents
    config_dir = documents / "WorkspaceManager"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Return path to workspaces.json
    return config_dir / "workspaces.json"


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class ConfigManager:
    """Manages workspace configuration files."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_file: Path to the configuration file. If None, uses default path in Documents.
        """
        if config_file is None:
            self.config_file = get_default_config_path()
        else:
            self.config_file = Path(config_file)
        self.collection: Optional[WorkspaceCollection] = None

    def ensure_config_exists(self) -> None:
        """Create an empty configuration file if it doesn't exist."""
        if not self.config_file.exists():
            logger.info(f"Creating new configuration file: {self.config_file}")
            empty_collection = WorkspaceCollection()
            self.save(empty_collection)

    def load(self) -> WorkspaceCollection:
        """
        Load workspaces from configuration file.

        Returns:
            WorkspaceCollection object

        Raises:
            ConfigError: If the file cannot be loaded or parsed
        """
        try:
            self.ensure_config_exists()

            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate basic structure
            if not isinstance(data, dict):
                raise ConfigError(f"Configuration file must contain a JSON object, got {type(data)}")

            if 'workspaces' not in data:
                logger.warning("No 'workspaces' key found, creating empty collection")
                data = {'workspaces': []}

            # Validate each workspace
            for idx, ws in enumerate(data.get('workspaces', [])):
                if not isinstance(ws, dict):
                    raise ConfigError(f"Workspace at index {idx} must be a JSON object")

                if 'name' not in ws:
                    raise ConfigError(f"Workspace at index {idx} missing required 'name' field")

                # Validate apps within workspace
                for app_idx, app in enumerate(ws.get('apps', [])):
                    if not isinstance(app, dict):
                        raise ConfigError(
                            f"App at index {app_idx} in workspace '{ws['name']}' must be a JSON object"
                        )

                    if 'id' not in app:
                        raise ConfigError(
                            f"App at index {app_idx} in workspace '{ws['name']}' missing 'id' field"
                        )

                    if 'exe' not in app:
                        raise ConfigError(
                            f"App '{app.get('id', 'unknown')}' in workspace '{ws['name']}' missing 'exe' field"
                        )

            self.collection = WorkspaceCollection.from_dict(data)
            logger.info(f"Loaded {len(self.collection.workspaces)} workspace(s) from {self.config_file}")
            return self.collection

        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {self.config_file}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")

    def save(self, collection: WorkspaceCollection) -> None:
        """
        Save workspaces to configuration file.

        Args:
            collection: WorkspaceCollection to save

        Raises:
            ConfigError: If the file cannot be saved
        """
        try:
            # Create backup if file exists
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.json.bak')
                logger.debug(f"Creating backup: {backup_file}")
                self.config_file.replace(backup_file)

            # Validate before saving
            data = collection.to_dict()

            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Write with pretty formatting
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.collection = collection
            logger.info(f"Saved {len(collection.workspaces)} workspace(s) to {self.config_file}")

        except Exception as e:
            # Try to restore backup if save failed
            backup_file = self.config_file.with_suffix('.json.bak')
            if backup_file.exists():
                logger.error(f"Save failed, restoring backup: {e}")
                backup_file.replace(self.config_file)
            raise ConfigError(f"Error saving configuration: {e}")

    def add_workspace(self, workspace: Workspace, overwrite: bool = False) -> None:
        """
        Add a workspace to the configuration.

        Args:
            workspace: Workspace to add
            overwrite: If True, overwrite existing workspace with same name

        Raises:
            ConfigError: If workspace exists and overwrite is False
        """
        if self.collection is None:
            self.load()

        existing = self.collection.get_workspace(workspace.name)
        if existing and not overwrite:
            raise ConfigError(
                f"Workspace '{workspace.name}' already exists. Use --overwrite to replace it."
            )

        if existing:
            logger.info(f"Overwriting existing workspace: {workspace.name}")
            self.collection.remove_workspace(workspace.name)

        self.collection.add_workspace(workspace)
        self.save(self.collection)

    def remove_workspace(self, name: str) -> bool:
        """
        Remove a workspace from the configuration.

        Args:
            name: Name of workspace to remove

        Returns:
            True if workspace was removed, False if not found
        """
        if self.collection is None:
            self.load()

        if self.collection.remove_workspace(name):
            self.save(self.collection)
            logger.info(f"Removed workspace: {name}")
            return True

        logger.warning(f"Workspace not found: {name}")
        return False

    def get_workspace(self, name: str) -> Optional[Workspace]:
        """
        Get a workspace by name.

        Args:
            name: Name of workspace

        Returns:
            Workspace object or None if not found
        """
        if self.collection is None:
            self.load()

        return self.collection.get_workspace(name)

    def list_workspaces(self) -> list[str]:
        """
        Get list of all workspace names.

        Returns:
            List of workspace names
        """
        if self.collection is None:
            self.load()

        return self.collection.list_workspace_names()

    def validate_workspace(self, workspace: Workspace) -> list[str]:
        """
        Validate a workspace configuration.

        Args:
            workspace: Workspace to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check workspace name
        if not workspace.name or not workspace.name.strip():
            errors.append("Workspace name cannot be empty")

        # Check for duplicate app IDs
        app_ids = [app.id for app in workspace.apps]
        if len(app_ids) != len(set(app_ids)):
            errors.append("Duplicate app IDs found in workspace")

        # Validate each app
        for app in workspace.apps:
            # Check ID
            if not app.id or not app.id.strip():
                errors.append(f"App ID cannot be empty")

            # Check executable
            if not app.exe or not app.exe.strip():
                errors.append(f"App '{app.id}' has empty executable path")

            # Check if executable exists (warning only)
            exe_path = Path(app.exe)
            if not exe_path.exists() and not any(app.exe.startswith(cmd) for cmd in ['cmd', 'powershell', 'wt']):
                logger.warning(f"App '{app.id}' executable not found: {app.exe}")

            # Check working directory if specified
            if app.working_dir:
                work_dir = Path(app.working_dir)
                if not work_dir.exists():
                    logger.warning(f"App '{app.id}' working directory not found: {app.working_dir}")

            # Check virtual desktop index
            if app.virtual_desktop < 0:
                errors.append(f"App '{app.id}' has invalid virtual desktop index: {app.virtual_desktop}")

            # Check window dimensions
            if app.window.width <= 0 or app.window.height <= 0:
                errors.append(f"App '{app.id}' has invalid window dimensions")

        return errors

    def export_workspace(self, name: str, output_file: str) -> None:
        """
        Export a single workspace to a file.

        Args:
            name: Name of workspace to export
            output_file: Path to output file

        Raises:
            ConfigError: If workspace not found or export fails
        """
        workspace = self.get_workspace(name)
        if not workspace:
            raise ConfigError(f"Workspace '{name}' not found")

        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(workspace.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"Exported workspace '{name}' to {output_path}")

        except Exception as e:
            raise ConfigError(f"Failed to export workspace: {e}")

    def import_workspace(self, input_file: str, overwrite: bool = False) -> None:
        """
        Import a workspace from a file.

        Args:
            input_file: Path to input file
            overwrite: If True, overwrite existing workspace with same name

        Raises:
            ConfigError: If import fails
        """
        try:
            input_path = Path(input_file)

            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            workspace = Workspace.from_dict(data)

            # Validate before importing
            errors = self.validate_workspace(workspace)
            if errors:
                raise ConfigError(f"Invalid workspace: {', '.join(errors)}")

            self.add_workspace(workspace, overwrite=overwrite)
            logger.info(f"Imported workspace '{workspace.name}' from {input_path}")

        except FileNotFoundError:
            raise ConfigError(f"Import file not found: {input_file}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in import file: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to import workspace: {e}")