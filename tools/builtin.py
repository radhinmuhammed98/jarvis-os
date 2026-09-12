"""
Safe Demonstration Tools for JARVIS OS Milestone 04 & 05
"""

import time
import platform
import os
from typing import Dict, Any, List, Optional
from tools.base import BaseTool, ToolResult
from sandbox.runtime import SandboxRuntime
from sandbox.types import SandboxConfig, ResourceLimits

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


class MathSandboxTool(BaseTool):
    """
    Demonstration Sandbox Tool (Milestone 05)
    Evaluates a harmless mathematical Python expression inside the secure SandboxRuntime.
    """

    def __init__(self, sandbox_runtime: Optional[SandboxRuntime] = None):
        self.sandbox = sandbox_runtime or SandboxRuntime(
            SandboxConfig(
                network_enabled=False,
                limits=ResourceLimits(max_cpu_seconds=2, max_memory_mb=128, timeout_seconds=3.0)
            )
        )

    @property
    def tool_id(self) -> str:
        return "sandbox_math"

    @property
    def name(self) -> str:
        return "Sandbox Math Evaluator"

    @property
    def description(self) -> str:
        return "Evaluates mathematical Python expressions safely inside the isolated Sandbox runtime."

    @property
    def required_permissions(self) -> List[str]:
        return ["sandbox:execute"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            },
            "required": ["expression"]
        }

    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        expr = parameters.get("expression", "0")
        code = f"result = {expr}\nprint(f'MATH_RESULT={{result}}')"

        sb_result = self.sandbox.run_python_code(code, dry_run=dry_run)

        if not sb_result.success:
            return ToolResult(
                success=False,
                output=None,
                error=f"Sandbox execution failed: {sb_result.error or sb_result.stderr}",
                dry_run=sb_result.dry_run,
                execution_time_ms=sb_result.execution_time_ms
            )

        return ToolResult(
            success=True,
            output=sb_result.stdout,
            dry_run=sb_result.dry_run,
            execution_time_ms=sb_result.execution_time_ms
        )
