"""
JARVIS Tool Factory Engine (Milestone 06)
Dynamically creates, sandbox-tests, security-audits, and registers new tools when an existing tool is missing.
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import time

from tools.base import BaseTool, ToolResult
from sandbox.runtime import SandboxRuntime
from sandbox.types import SandboxConfig, ResourceLimits
from tools.audit import AuditLogger

logger = logging.getLogger("jarvis-tool-factory")

PROHIBITED_IMPORTS = ["os", "sys", "subprocess", "shutil", "socket", "urllib", "requests", "importlib", "ctypes", "pickle"]

@dataclass
class CapabilitySpec:
    capability_name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_permissions: List[str]

@dataclass
class GeneratedToolManifest:
    tool_id: str
    name: str
    description: str
    version: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_permissions: List[str]
    dependencies: List[str]
    generated_code: str
    test_code: str

@dataclass
class ToolFactoryResult:
    success: bool
    manifest: Optional[GeneratedToolManifest] = None
    registered_tool: Optional[BaseTool] = None
    error: Optional[str] = None
    stage_failed: Optional[str] = None

class DynamicGeneratedTool(BaseTool):
    """Wrapper turning a validated GeneratedToolManifest into an executable BaseTool."""

    def __init__(self, manifest: GeneratedToolManifest, sandbox: SandboxRuntime):
        self.manifest = manifest
        self.sandbox = sandbox

    @property
    def tool_id(self) -> str:
        return self.manifest.tool_id

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def description(self) -> str:
        return self.manifest.description

    @property
    def required_permissions(self) -> List[str]:
        return self.manifest.required_permissions

    @property
    def input_schema(self) -> Dict[str, Any]:
        return self.manifest.input_schema

    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        if dry_run:
            return ToolResult(
                success=True,
                output=f"[DRY-RUN] Execution of generated tool '{self.tool_id}' simulated.",
                dry_run=True
            )

        code_runner = f"""
{self.manifest.generated_code}

params = {json.dumps(parameters)}
res = execute_tool(params)
print("TOOL_OUTPUT=" + json.dumps(res))
"""
        sb_res = self.sandbox.run_python_code(code_runner)

        if not sb_res.success:
            return ToolResult(
                success=False,
                output=None,
                error=f"Generated tool execution failed: {sb_res.stderr or sb_res.error}"
            )

        # Parse output
        output_str = ""
        for line in sb_res.stdout.splitlines():
            if line.startswith("TOOL_OUTPUT="):
                output_str = line.split("TOOL_OUTPUT=", 1)[1]

        try:
            parsed_output = json.loads(output_str) if output_str else sb_res.stdout
            return ToolResult(success=True, output=parsed_output)
        except Exception:
            return ToolResult(success=True, output=sb_res.stdout)


class ToolFactory:
    """
    JARVIS Tool Factory Engine.
    Pipeline: Request -> Spec -> Generate Code -> Security Audit -> Sandbox Test -> Save -> Register.
    """

    def __init__(self, storage_dir: str = "/tmp/jarvis_generated_tools", audit_logger: Optional[AuditLogger] = None):
        self.storage_dir = storage_dir
        self.audit = audit_logger or AuditLogger()
        self.sandbox = SandboxRuntime(
            SandboxConfig(
                network_enabled=False,
                limits=ResourceLimits(max_cpu_seconds=2, max_memory_mb=128, timeout_seconds=3.0)
            )
        )
        os.makedirs(self.storage_dir, exist_ok=True)

    def create_celsius_to_fahrenheit_tool() -> GeneratedToolManifest:
        """Pre-packaged generator for Celsius to Fahrenheit capability demonstration."""
        code = """import json

def execute_tool(params: dict) -> dict:
    c = float(params.get("celsius", 0))
    f = (c * 9/5) + 32
    return {"celsius": c, "fahrenheit": f}
"""
        test_code = """
params = {"celsius": 100}
res = execute_tool(params)
assert res["fahrenheit"] == 212.0, f"Expected 212.0, got {res['fahrenheit']}"
print("TEST_PASSED")
"""
        return GeneratedToolManifest(
            tool_id="celsius_to_fahrenheit",
            name="Celsius to Fahrenheit Converter",
            description="Converts temperature from Celsius to Fahrenheit.",
            version="1.0.0",
            input_schema={"type": "object", "properties": {"celsius": {"type": "number"}}, "required": ["celsius"]},
            output_schema={"type": "object", "properties": {"fahrenheit": {"type": "number"}}},
            required_permissions=["tool:celsius_to_fahrenheit"],
            dependencies=[],
            generated_code=code,
            test_code=test_code
        )

    def process_and_register(self, manifest: GeneratedToolManifest) -> ToolFactoryResult:
        self.audit.log("PROPOSED", manifest.tool_id, None, manifest.required_permissions, {}, "ToolFactory requested.")

        # Stage 1: Security Review (Prohibited Modules & Host Paths)
        for imp in PROHIBITED_IMPORTS:
            if f"import {imp}" in manifest.generated_code or f"from {imp}" in manifest.generated_code:
                err = f"Security Violation: Generated code attempts prohibited import '{imp}'"
                self.audit.log("REJECTED", manifest.tool_id, None, manifest.required_permissions, {}, err)
                return ToolFactoryResult(success=False, error=err, stage_failed="security_review")

        # Stage 2: Sandbox Testing
        test_script = f"""
{manifest.generated_code}
{manifest.test_code}
"""
        sb_res = self.sandbox.run_python_code(test_script)
        if not sb_res.success or "TEST_PASSED" not in sb_res.stdout:
            err = f"Sandbox Test Failed: {sb_res.stderr or 'Assertion or execution failure'}"
            self.audit.log("REJECTED", manifest.tool_id, None, manifest.required_permissions, {}, err)
            return ToolFactoryResult(success=False, error=err, stage_failed="sandbox_testing")

        self.audit.log("TESTED", manifest.tool_id, None, manifest.required_permissions, {}, "Sandbox tests passed.")

        # Stage 3: Save to local versioned storage
        tool_file = os.path.join(self.storage_dir, f"{manifest.tool_id}_v{manifest.version}.json")
        with open(tool_file, "w", encoding="utf-8") as f:
            json.dump({
                "tool_id": manifest.tool_id,
                "name": manifest.name,
                "description": manifest.description,
                "version": manifest.version,
                "input_schema": manifest.input_schema,
                "output_schema": manifest.output_schema,
                "required_permissions": manifest.required_permissions,
                "generated_code": manifest.generated_code
            }, f, indent=2)

        # Stage 4: Wrap into DynamicGeneratedTool
        tool_instance = DynamicGeneratedTool(manifest, self.sandbox)
        self.audit.log("APPROVED", manifest.tool_id, None, manifest.required_permissions, {}, "Tool approved and registered.")

        return ToolFactoryResult(
            success=True,
            manifest=manifest,
            registered_tool=tool_instance
        )
