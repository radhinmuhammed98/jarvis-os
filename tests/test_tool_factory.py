"""
Milestone 06 Test Suite: JARVIS Tool Factory, Dynamic Tool Generation, Security Review, and Sandbox Testing
"""

import pytest
import os
import shutil
from tools import (
    ToolRegistry,
    PermissionPolicy,
    AuditLogger,
    ToolExecutor,
    ToolFactory,
    GeneratedToolManifest
)
from core.types import ActionProposal

@pytest.fixture
def factory_env():
    storage = "/tmp/test_jarvis_factory_tools"
    shutil.rmtree(storage, ignore_errors=True)

    registry = ToolRegistry()
    policy = PermissionPolicy(granted_permissions=["tool:celsius_to_fahrenheit"])
    audit = AuditLogger()
    factory = ToolFactory(storage_dir=storage, audit_logger=audit)
    executor = ToolExecutor(registry, policy, audit)

    return registry, policy, audit, factory, executor, storage

def test_celsius_to_fahrenheit_tool_generation_and_execution(factory_env):
    registry, policy, audit, factory, executor, storage = factory_env

    # 1. Generate tool manifest for missing capability
    manifest = ToolFactory.create_celsius_to_fahrenheit_tool()

    # 2. Process through ToolFactory (Security review -> Sandbox testing -> Registration)
    factory_res = factory.process_and_register(manifest)
    assert factory_res.success is True
    assert factory_res.registered_tool is not None

    # Register in ToolRegistry
    registry.register_tool(factory_res.registered_tool)

    # 3. Execute generated tool via ToolExecutor ActionProposal
    proposal = ActionProposal(
        action_type="celsius_to_fahrenheit",
        description="Convert 100 Celsius to Fahrenheit",
        target="generated_tool",
        parameters={"celsius": 100}
    )
    result = executor.execute_proposal(proposal)
    assert result.success is True
    assert result.output["fahrenheit"] == 212.0

    # 4. Disable tool and verify refusal
    registry.set_enabled("celsius_to_fahrenheit", False)
    result_disabled = executor.execute_proposal(proposal)
    assert result_disabled.success is False
    assert "Access DENIED" in result_disabled.error

def test_malicious_import_tool_rejection(factory_env):
    registry, policy, audit, factory, executor, storage = factory_env

    malicious_manifest = GeneratedToolManifest(
        tool_id="exploit_tool",
        name="Exploit Tool",
        description="Attempts host path deletion",
        version="1.0.0",
        input_schema={},
        output_schema={},
        required_permissions=["exploit"],
        dependencies=[],
        generated_code="import os\nos.system('rm -rf /')",
        test_code="print('TEST_PASSED')"
    )

    res = factory.process_and_register(malicious_manifest)
    assert res.success is False
    assert res.stage_failed == "security_review"
    assert "prohibited import 'os'" in res.error

def test_failing_sandbox_test_rejection(factory_env):
    registry, policy, audit, factory, executor, storage = factory_env

    failing_manifest = GeneratedToolManifest(
        tool_id="broken_tool",
        name="Broken Tool",
        description="Fails unit test",
        version="1.0.0",
        input_schema={},
        output_schema={},
        required_permissions=["broken"],
        dependencies=[],
        generated_code="def execute_tool(p): return {'ok': False}",
        test_code="assert False, 'Test intentioned failure'"
    )

    res = factory.process_and_register(failing_manifest)
    assert res.success is False
    assert res.stage_failed == "sandbox_testing"
