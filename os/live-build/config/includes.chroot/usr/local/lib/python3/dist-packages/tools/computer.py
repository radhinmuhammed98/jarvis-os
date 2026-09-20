"""
Explicit Registered Computer Control Tools (Milestone 07)
Integrates ComputerController operations with the JARVIS Tool Registry & Permission Policy.
"""

import time
from typing import Dict, Any, List, Optional
from tools.base import BaseTool, ToolResult
from system.computer import MockComputerController, BaseComputerController, ALLOWLISTED_APPLICATIONS

class AppDiscoveryTool(BaseTool):
    def __init__(self, controller: Optional[BaseComputerController] = None):
        self.controller = controller or MockComputerController()

    @property
    def tool_id(self) -> str:
        return "app_discovery"

    @property
    def name(self) -> str:
        return "Application Discovery Tool"

    @property
    def description(self) -> str:
        return "Lists available allowlisted system applications."

    @property
    def required_permissions(self) -> List[str]:
        return ["app:read"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        start = time.time()
        if dry_run:
            return ToolResult(success=True, output="[DRY-RUN] Discovered applications list simulated.", dry_run=True)

        apps = self.controller.discover_applications()
        return ToolResult(success=True, output=apps, execution_time_ms=(time.time() - start) * 1000)


class AppLaunchTool(BaseTool):
    def __init__(self, controller: Optional[BaseComputerController] = None):
        self.controller = controller or MockComputerController()

    @property
    def tool_id(self) -> str:
        return "app_launch"

    @property
    def name(self) -> str:
        return "Application Launch Tool"

    @property
    def description(self) -> str:
        return "Launches a validated allowlisted application."

    @property
    def required_permissions(self) -> List[str]:
        return ["app:launch"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target": {"type": "string"}
            },
            "required": ["target"]
        }

    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        start = time.time()
        target = parameters.get("target", "").lower().strip()

        if target not in ALLOWLISTED_APPLICATIONS:
            return ToolResult(
                success=False,
                output=None,
                error=f"Access DENIED: Application '{target}' is not in the validated allowlist."
            )

        if dry_run:
            return ToolResult(
                success=True,
                output=f"[DRY-RUN] Application launch for '{target}' simulated.",
                dry_run=True
            )

        try:
            res = self.controller.launch_application(target)
            return ToolResult(success=True, output=res, execution_time_ms=(time.time() - start) * 1000)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class AppCloseTool(BaseTool):
    def __init__(self, controller: Optional[BaseComputerController] = None):
        self.controller = controller or MockComputerController()

    @property
    def tool_id(self) -> str:
        return "app_close"

    @property
    def name(self) -> str:
        return "Application Close Tool"

    @property
    def description(self) -> str:
        return "Closes a running application instance."

    @property
    def required_permissions(self) -> List[str]:
        return ["app:close"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target": {"type": "string"}
            },
            "required": ["target"]
        }

    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        start = time.time()
        target = parameters.get("target", "").lower().strip()

        if target not in ALLOWLISTED_APPLICATIONS:
            return ToolResult(
                success=False,
                output=None,
                error=f"Access DENIED: Application '{target}' is not in the validated allowlist."
            )

        if dry_run:
            return ToolResult(
                success=True,
                output=f"[DRY-RUN] Application close for '{target}' simulated.",
                dry_run=True
            )

        try:
            res = self.controller.close_application(target)
            return ToolResult(success=True, output=res, execution_time_ms=(time.time() - start) * 1000)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class WindowControlTool(BaseTool):
    def __init__(self, controller: Optional[BaseComputerController] = None):
        self.controller = controller or MockComputerController()

    @property
    def tool_id(self) -> str:
        return "window_control"

    @property
    def name(self) -> str:
        return "Window Control Tool"

    @property
    def description(self) -> str:
        return "Minimizes, maximizes, or focuses application windows."

    @property
    def required_permissions(self) -> List[str]:
        return ["window:manage"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "action": {"type": "string"}  # "minimize", "maximize", "focus"
            },
            "required": ["target", "action"]
        }

    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        start = time.time()
        target = parameters.get("target", "").lower().strip()
        action = parameters.get("action", "").lower().strip()

        if dry_run:
            return ToolResult(
                success=True,
                output=f"[DRY-RUN] Window action '{action}' on '{target}' simulated.",
                dry_run=True
            )

        try:
            res = self.controller.set_window_state(target, action)
            return ToolResult(success=True, output=res, execution_time_ms=(time.time() - start) * 1000)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class VolumeControlTool(BaseTool):
    def __init__(self, controller: Optional[BaseComputerController] = None):
        self.controller = controller or MockComputerController()

    @property
    def tool_id(self) -> str:
        return "volume_control"

    @property
    def name(self) -> str:
        return "Volume Control Tool"

    @property
    def description(self) -> str:
        return "Sets system audio volume level or mute state."

    @property
    def required_permissions(self) -> List[str]:
        return ["volume:manage"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "level": {"type": "integer"},
                "mute": {"type": "boolean"}
            },
            "required": []
        }

    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        start = time.time()
        if dry_run:
            return ToolResult(
                success=True,
                output=f"[DRY-RUN] Volume control operation simulated.",
                dry_run=True
            )

        try:
            if "level" in parameters:
                res = self.controller.set_volume(parameters["level"])
            elif "mute" in parameters:
                res = self.controller.set_mute(parameters["mute"])
            else:
                return ToolResult(success=False, output=None, error="Specify either 'level' or 'mute'.")

            return ToolResult(success=True, output=res, execution_time_ms=(time.time() - start) * 1000)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
