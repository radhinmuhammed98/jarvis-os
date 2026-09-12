"""
Milestone 07 Test Suite: Computer Control Subsystem, Application Launch Validation,
Permission Pipeline Integration, and End-to-End Intent Mapping.
"""

import pytest
from system.computer import MockComputerController, ALLOWLISTED_APPLICATIONS
from tools import (
    ToolRegistry,
    PermissionPolicy,
    AuditLogger,
    ToolExecutor,
    AppLaunchTool,
    AppCloseTool,
    WindowControlTool,
    VolumeControlTool,
    AppDiscoveryTool
)
from core.service import JarvisCore
from core.config import CoreConfig
from core.types import ActionProposal, IntentCategory

@pytest.fixture
def computer_env():
    controller = MockComputerController()
    registry = ToolRegistry()

    registry.register_tool(AppDiscoveryTool(controller))
    registry.register_tool(AppLaunchTool(controller))
    registry.register_tool(AppCloseTool(controller))
    registry.register_tool(WindowControlTool(controller))
    registry.register_tool(VolumeControlTool(controller))

    policy = PermissionPolicy(granted_permissions=["app:read", "app:launch", "app:close", "window:manage", "volume:manage"])
    audit = AuditLogger()
    executor = ToolExecutor(registry, policy, audit)

    return controller, registry, policy, audit, executor

def test_open_chrome_intent_to_launch_tool(computer_env):
    """
    Integration test proving:
    'Open Chrome' -> ActionProposal -> Validation -> Permission -> AppLaunchTool
    """
    controller, registry, policy, audit, executor = computer_env
    core = JarvisCore(CoreConfig(provider="mock"))

    res = core.process_message("Open Chrome.")
    assert res["intent"].category == IntentCategory.ACTION_REQUEST
    assert res["action_proposal"] is not None
    assert res["action_proposal"].target.lower() == "chrome"

    # Process ActionProposal through ToolExecutor
    exec_result = executor.execute_proposal(res["action_proposal"])
    assert exec_result.success is True
    assert exec_result.output["status"] == "launched"
    assert controller.running_apps["chrome"] is True

    # Audit records check
    records = audit.get_records()
    event_types = [r.event_type for r in records]
    assert "PROPOSED" in event_types
    assert "APPROVED" in event_types
    assert "EXECUTED" in event_types

def test_chrome_is_slow_produces_no_action(computer_env):
    """
    Integration test proving:
    'Chrome is slow' -> Conversation / Information -> NO computer action
    """
    controller, registry, policy, audit, executor = computer_env
    core = JarvisCore(CoreConfig(provider="mock"))

    res = core.process_message("Chrome is slow today.")
    assert res["intent"].category != IntentCategory.ACTION_REQUEST
    assert res["action_proposal"] is None
    assert res["executed"] is False
    assert len(controller.running_apps) == 0

def test_unallowlisted_app_launch_rejection(computer_env):
    """Verify arbitrary path or unallowlisted application is rejected."""
    controller, registry, policy, audit, executor = computer_env

    proposal = ActionProposal(
        action_type="app_launch",
        description="Attempt launch /bin/bash",
        target="malicious_app",
        parameters={"target": "/bin/bash"}
    )

    res = executor.execute_proposal(proposal)
    assert res.success is False
    assert "not in the validated allowlist" in res.error

def test_window_operations_and_dry_run(computer_env):
    controller, registry, policy, audit, executor = computer_env

    # 1. Launch Chrome
    controller.launch_application("chrome")

    # 2. Minimize window
    win_proposal = ActionProposal(
        action_type="window_control",
        description="Minimize Chrome window",
        target="chrome",
        parameters={"target": "chrome", "action": "minimize"}
    )
    res = executor.execute_proposal(win_proposal)
    assert res.success is True
    assert res.output["window_state"]["minimized"] is True

    # 3. Dry-run maximize
    max_proposal = ActionProposal(
        action_type="window_control",
        description="Maximize Chrome window in dry run",
        target="chrome",
        parameters={"target": "chrome", "action": "maximize"}
    )
    dry_res = executor.execute_proposal(max_proposal, dry_run=True)
    assert dry_res.success is True
    assert dry_res.dry_run is True

def test_volume_control(computer_env):
    controller, registry, policy, audit, executor = computer_env

    proposal = ActionProposal(
        action_type="volume_control",
        description="Set volume to 80%",
        target="audio",
        parameters={"level": 80}
    )
    res = executor.execute_proposal(proposal)
    assert res.success is True
    assert controller.volume == 80
