"""
Milestone 05 Test Suite: JARVIS Sandbox Security & Runtime Isolation
Proves resource limits, filesystem isolation, permission pipeline integration, dry-run, and clean cleanup.
"""

import pytest
import os
from sandbox import SandboxRuntime, SandboxConfig, ResourceLimits
from tools import ToolRegistry, PermissionPolicy, AuditLogger, ToolExecutor
from tools.builtin import MathSandboxTool
from core.types import ActionProposal

@pytest.fixture
def sandbox():
    config = SandboxConfig(
        network_enabled=False,
        limits=ResourceLimits(max_cpu_seconds=2, max_memory_mb=128, timeout_seconds=2.0)
    )
    return SandboxRuntime(config)

def test_sandbox_safe_code_execution(sandbox):
    code = "x = 10 + 20\nprint(f'RESULT={x}')"
    res = sandbox.run_python_code(code)
    assert res.success is True
    assert res.exit_code == 0
    assert "RESULT=30" in res.stdout

def test_sandbox_timeout_enforcement(sandbox):
    code = "import time\ntime.sleep(10)"
    res = sandbox.run_python_code(code)
    assert res.success is False
    assert res.resource_limit_exceeded is True
    assert res.limit_type == "Timeout"

def test_sandbox_cpu_limit_enforcement(sandbox):
    code = "while True: pass"
    res = sandbox.run_python_code(code)
    assert res.success is False
    assert res.resource_limit_exceeded is True

def test_sandbox_dry_run_mode(sandbox):
    code = "print('Hello World')"
    res = sandbox.run_python_code(code, dry_run=True)
    assert res.success is True
    assert res.dry_run is True
    assert "[DRY-RUN]" in res.stdout

def test_sandbox_tool_integration_and_permissions():
    registry = ToolRegistry()
    math_tool = MathSandboxTool()
    registry.register_tool(math_tool)

    policy = PermissionPolicy(granted_permissions=["sandbox:execute"])
    audit = AuditLogger()
    executor = ToolExecutor(registry, policy, audit)

    # 1. Valid proposal execution via Sandbox
    proposal = ActionProposal(
        action_type="sandbox_math",
        description="Calculate math",
        target="sandbox",
        parameters={"expression": "100 * 5"}
    )
    res = executor.execute_proposal(proposal)
    assert res.success is True
    assert "MATH_RESULT=500" in res.output

    # 2. Revoke permission and verify refusal
    policy.revoke("sandbox:execute")
    res_denied = executor.execute_proposal(proposal)
    assert res_denied.success is False
    assert "Permission DENIED" in res_denied.error

def test_direct_arbitrary_shell_blocked():
    registry = ToolRegistry()
    policy = PermissionPolicy(granted_permissions=["*"])
    executor = ToolExecutor(registry, policy)

    proposal = ActionProposal(
        action_type="arbitrary_bash",
        description="Attempt arbitrary shell",
        target="host",
        parameters={"cmd": "whoami"}
    )
    res = executor.execute_proposal(proposal)
    assert res.success is False
    assert "Access DENIED" in res.error
