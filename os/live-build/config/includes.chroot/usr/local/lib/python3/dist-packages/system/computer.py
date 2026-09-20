"""
JARVIS OS Computer Controller Platform Abstraction (Milestone 07)
Provides an abstract platform interface for application discovery, app lifecycle,
window management, and audio volume adjustment without arbitrary shell execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

ALLOWLISTED_APPLICATIONS = {
    "chrome": {"name": "Google Chrome", "exec": "google-chrome"},
    "firefox": {"name": "Mozilla Firefox", "exec": "firefox"},
    "spotify": {"name": "Spotify", "exec": "spotify"},
    "terminal": {"name": "Terminal", "exec": "x-terminal-emulator"},
    "vscode": {"name": "Visual Studio Code", "exec": "code"},
    "vlc": {"name": "VLC Media Player", "exec": "vlc"}
}

@dataclass
class WindowState:
    window_id: str
    title: str
    app_name: str
    is_minimized: bool = False
    is_maximized: bool = False
    is_focused: bool = False

class BaseComputerController(ABC):
    """Abstract Computer Controller platform interface."""

    @abstractmethod
    def discover_applications() -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def launch_application(self, app_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def close_application(self, app_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_window_state(self, app_id: str, action: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_volume(self, level: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_mute(self, mute: bool) -> Dict[str, Any]:
        pass


class MockComputerController(BaseComputerController):
    """
    In-Memory Mock Computer Controller for GUI-less head-less OS environments,
    CI testing, and safe demonstration.
    """

    def __init__(self):
        self.running_apps: Dict[str, bool] = {}
        self.windows: Dict[str, WindowState] = {}
        self.volume: int = 50
        self.is_muted: bool = False

    def discover_applications(self) -> List[Dict[str, str]]:
        return [
            {"app_id": key, "name": val["name"]}
            for key, val in ALLOWLISTED_APPLICATIONS.items()
        ]

    def launch_application(self, app_id: str) -> Dict[str, Any]:
        app_clean = app_id.lower().strip()
        if app_clean not in ALLOWLISTED_APPLICATIONS:
            raise ValueError(f"Application '{app_id}' is not in the validated allowlist.")

        self.running_apps[app_clean] = True
        self.windows[app_clean] = WindowState(
            window_id=f"win_{app_clean}",
            title=ALLOWLISTED_APPLICATIONS[app_clean]["name"],
            app_name=app_clean,
            is_focused=True
        )
        return {
            "app_id": app_clean,
            "status": "launched",
            "window_id": f"win_{app_clean}"
        }

    def close_application(self, app_id: str) -> Dict[str, Any]:
        app_clean = app_id.lower().strip()
        if app_clean not in ALLOWLISTED_APPLICATIONS:
            raise ValueError(f"Application '{app_id}' is not in the validated allowlist.")

        if not self.running_apps.get(app_clean, False):
            return {"app_id": app_clean, "status": "not_running"}

        self.running_apps[app_clean] = False
        self.windows.pop(app_clean, None)
        return {"app_id": app_clean, "status": "closed"}

    def set_window_state(self, app_id: str, action: str) -> Dict[str, Any]:
        app_clean = app_id.lower().strip()
        if app_clean not in self.windows:
            raise ValueError(f"No active window found for application '{app_id}'.")

        win = self.windows[app_clean]
        if action == "minimize":
            win.is_minimized = True
            win.is_focused = False
        elif action == "maximize":
            win.is_maximized = True
            win.is_focused = True
        elif action == "focus":
            win.is_focused = True
            win.is_minimized = False
        else:
            raise ValueError(f"Unknown window action '{action}'.")

        return {
            "app_id": app_clean,
            "action": action,
            "window_state": {
                "minimized": win.is_minimized,
                "maximized": win.is_maximized,
                "focused": win.is_focused
            }
        }

    def set_volume(self, level: int) -> Dict[str, Any]:
        clamped_level = max(0, min(100, level))
        self.volume = clamped_level
        return {"volume": self.volume, "muted": self.is_muted}

    def set_mute(self, mute: bool) -> Dict[str, Any]:
        self.is_muted = mute
        return {"volume": self.volume, "muted": self.is_muted}
