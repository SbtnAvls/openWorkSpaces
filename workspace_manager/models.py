"""
Data models for the workspace manager.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import json


@dataclass
class WindowConfig:
    """Configuration for window position and size."""
    x: int
    y: int
    width: int
    height: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'WindowConfig':
        """Create from dictionary."""
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 800),
            height=data.get("height", 600)
        )


@dataclass
class AppInstance:
    """Represents a single application instance in a workspace."""
    id: str
    exe: str
    args: List[str] = field(default_factory=list)
    working_dir: Optional[str] = None
    virtual_desktop: int = 0
    window: WindowConfig = field(default_factory=lambda: WindowConfig(0, 0, 800, 600))

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "exe": self.exe,
            "args": self.args,
            "working_dir": self.working_dir,
            "virtual_desktop": self.virtual_desktop,
            "window": self.window.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AppInstance':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            exe=data["exe"],
            args=data.get("args", []),
            working_dir=data.get("working_dir"),
            virtual_desktop=data.get("virtual_desktop", 0),
            window=WindowConfig.from_dict(data.get("window", {}))
        )


@dataclass
class Workspace:
    """Represents a complete workspace configuration."""
    name: str
    description: str = ""
    apps: List[AppInstance] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "apps": [app.to_dict() for app in self.apps]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Workspace':
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            apps=[AppInstance.from_dict(app) for app in data.get("apps", [])]
        )

    def add_app(self, app: AppInstance) -> None:
        """Add an application to the workspace."""
        self.apps.append(app)

    def remove_app(self, app_id: str) -> bool:
        """Remove an application by ID."""
        initial_count = len(self.apps)
        self.apps = [app for app in self.apps if app.id != app_id]
        return len(self.apps) < initial_count

    def get_app(self, app_id: str) -> Optional[AppInstance]:
        """Get an application by ID."""
        for app in self.apps:
            if app.id == app_id:
                return app
        return None

    def get_required_desktops(self) -> int:
        """Get the number of virtual desktops required."""
        if not self.apps:
            return 1
        return max(app.virtual_desktop for app in self.apps) + 1


@dataclass
class WorkspaceCollection:
    """Collection of all workspaces."""
    workspaces: List[Workspace] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "workspaces": [ws.to_dict() for ws in self.workspaces]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkspaceCollection':
        """Create from dictionary."""
        return cls(
            workspaces=[Workspace.from_dict(ws) for ws in data.get("workspaces", [])]
        )

    def add_workspace(self, workspace: Workspace) -> None:
        """Add a workspace to the collection."""
        self.workspaces.append(workspace)

    def remove_workspace(self, name: str) -> bool:
        """Remove a workspace by name."""
        initial_count = len(self.workspaces)
        self.workspaces = [ws for ws in self.workspaces if ws.name != name]
        return len(self.workspaces) < initial_count

    def get_workspace(self, name: str) -> Optional[Workspace]:
        """Get a workspace by name."""
        for ws in self.workspaces:
            if ws.name == name:
                return ws
        return None

    def list_workspace_names(self) -> List[str]:
        """Get list of all workspace names."""
        return [ws.name for ws in self.workspaces]