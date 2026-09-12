"""
Safe Demonstration Tools for JARVIS OS Milestone 04
"""

import time
import platform
import os
from typing import Dict, Any, List
from tools.base import BaseTool, ToolResult

class SystemInfoTool(BaseTool):
    @property
    def tool_id(self) -> str:
        return "system_info"

    @property
    def name(self) -> str:
        return "System Information Tool"

    @property
    def description(self) -> str:
        return "Returns basic operating system and platform information."

    @property
    def required_permissions(self) -> List[str]:
        return ["system:read"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        start = time.time()
        if dry_run:
            return ToolResult(
                success=True,
                output="[DRY-RUN] System info query simulated.",
                dry_run=True,
                execution_time_ms=(time.time() - start) * 1000
            )

        info = {
            "os": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "cpu_cores": os.cpu_count() or 1
        }
        return ToolResult(
            success=True,
            output=info,
            execution_time_ms=(time.time() - start) * 1000
        )


class TimeTool(BaseTool):
    @property
    def tool_id(self) -> str:
        return "time"

    @property
    def name(self) -> str:
        return "System Time Tool"

    @property
    def description(self) -> str:
        return "Returns current system epoch time and ISO 8601 string."

    @property
    def required_permissions(self) -> List[str]:
        return ["time:read"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        start = time.time()
        if dry_run:
            return ToolResult(
                success=True,
                output="[DRY-RUN] Time query simulated.",
                dry_run=True,
                execution_time_ms=(time.time() - start) * 1000
            )

        now = time.time()
        output = {
            "timestamp": now,
            "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
        }
        return ToolResult(
            success=True,
            output=output,
            execution_time_ms=(time.time() - start) * 1000
        )


class EchoTool(BaseTool):
    @property
    def tool_id(self) -> str:
        return "echo"

    @property
    def name(self) -> str:
        return "Echo Tool"

    @property
    def description(self) -> str:
        return "Returns supplied text message back to caller."

    @property
    def required_permissions(self) -> List[str]:
        return ["echo:write"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            },
            "required": ["message"]
        }

    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        start = time.time()
        msg = parameters.get("message", "")
        if dry_run:
            return ToolResult(
                success=True,
                output=f"[DRY-RUN] Echo message '{msg}' simulated.",
                dry_run=True,
                execution_time_ms=(time.time() - start) * 1000
            )

        return ToolResult(
            success=True,
            output=msg,
            execution_time_ms=(time.time() - start) * 1000
        )
