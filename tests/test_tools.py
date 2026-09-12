"""
Milestone 04 Test Suite: Tool Registry, Permission System, Schema Validation, Audit Logging, and Dry-Run
"""

import pytest
from tools import (
    ToolRegistry,
    PermissionPolicy,
    AuditLogger,
    ToolExecutor,
    SystemInfoTool,
    TimeTool,
    EchoTool
)
from core.types import ActionProposal

@pytest.fixture
def setup_environment():
    registry = ToolRegistry()
    registry.register_tool(SystemInfoTool())
    registry.register_tool(TimeTool())
    registry.register_tool(EchoTool())

    policy = PermissionPolicy(granted_permissions=["system:read", "time:read", "echo:write"])
    audit = AuditLogger()
    executor = ToolExecutor(registry, policy, audit)
    return registry, policy, audit, executor

def test_registered_tool_execution(setup_environment):
    registry, policy, audit, executor = setup_environment
    proposal = ActionProposal(
        action_type="echo",
        description="Echo message",
        target="system",
        parameters={"message": "Hello JARVIS OS!"}
    )
    result = executor.execute_proposal(proposal)
    assert result.success is True
    assert result.output == "Hello JARVIS OS!"
    assert result.dry_run is False

    # Check audit log
    records = audit.get_records()
    event_types = [r.event_type for r in records]
    assert "PROPOSED" in event_types
    assert "APPROVED" in event_types
    assert "EXECUTED" in event_types

def test_unknown_tool_rejection_default_deny(setup_environment):
    registry, policy, audit, executor = setup_environment
    proposal = ActionProposal(
        action_type="arbitrary_shell_exec",
        description="Run arbitrary command",
        target="root",
        parameters={"cmd": "rm -rf /"}
    )
    result = executor.execute_proposal(proposal)
    assert result.success is False
    assert "unknown or disabled. Access DENIED" in result.error

    records = audit.get_records()
    assert records[-1].event_type == "REJECTED"

def test_missing_permission_rejection(setup_environment):
    registry, policy, audit, executor = setup_environment
    # Revoke system:read permission
    policy.revoke("system:read")

    proposal = ActionProposal(
        action_type="system_info",
        description="Get system info",
        target="system",
        parameters={}
    )
    result = executor.execute_proposal(proposal)
    assert result.success is False
    assert "Permission DENIED" in result.error

    records = audit.get_records()
    assert records[-1].event_type == "REJECTED"

def test_malformed_input_schema_rejection(setup_environment):
    registry, policy, audit, executor = setup_environment
    # Echo tool requires "message" string parameter
    proposal = ActionProposal(
        action_type="echo",
        description="Echo invalid param",
        target="system",
        parameters={"message": 12345}  # Integer instead of string
    )
    result = executor.execute_proposal(proposal)
    assert result.success is False
    assert "Schema validation failed" in result.error

    records = audit.get_records()
    assert records[-1].event_type == "REJECTED"

def test_dry_run_mode(setup_environment):
    registry, policy, audit, executor = setup_environment
    proposal = ActionProposal(
        action_type="time",
        description="Check time in dry run",
        target="system",
        parameters={}
    )
    result = executor.execute_proposal(proposal, dry_run=True)
    assert result.success is True
    assert result.dry_run is True
    assert "[DRY-RUN]" in result.output

    records = audit.get_records()
    event_types = [r.event_type for r in records]
    assert "DRY_RUN" in event_types
    assert "EXECUTED" not in event_types

def test_audit_logging_completeness(setup_environment):
    registry, policy, audit, executor = setup_environment
    proposal = ActionProposal(
        action_type="system_info",
        description="Audit test",
        target="system",
        parameters={}
    )
    executor.execute_proposal(proposal)
    records = audit.get_records()
    assert len(records) >= 3
    for r in records:
        assert r.tool_id == "system_info"
        assert r.action_proposal_id == proposal.id
