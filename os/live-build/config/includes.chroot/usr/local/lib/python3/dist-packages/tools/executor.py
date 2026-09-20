"""
Tool Executor Pipeline for JARVIS OS
Maps ActionProposals to registered tools, validates inputs, checks permissions,
logs audit events, and executes or simulates dry-run.
DEFAULT DENY for unknown tools / unpermitted requests.
"""

from typing import Optional, Dict, Any, Tuple
from core.types import ActionProposal
from tools.base import BaseTool, ToolResult
from tools.registry import ToolRegistry
from tools.permissions import PermissionPolicy
from tools.audit import AuditLogger

class ToolExecutor:
    """Executes validated ActionProposal objects through registered tools."""

    def __init__(self, registry: ToolRegistry, policy: Optional[PermissionPolicy] = None, audit_logger: Optional[AuditLogger] = None):
        self.registry = registry
        self.policy = policy or PermissionPolicy()
        self.audit_logger = audit_logger or AuditLogger()

    def execute_proposal(self, proposal: ActionProposal, dry_run: bool = False) -> ToolResult:
        """
        Processes ActionProposal.
        Step 1: Discover registered tool by proposal.action_type or proposal.target
        Step 2: Validate tool exists and is enabled (DEFAULT DENY)
        Step 3: Validate input schema
        Step 4: Check permissions (DEFAULT DENY)
        Step 5: Audit log decision
        Step 6: Execute tool or dry-run
        """
        tool_id = proposal.action_type
        params = proposal.parameters

        self.audit_logger.log(
            event_type="PROPOSED",
            tool_id=tool_id,
            action_proposal_id=proposal.id,
            caller_permissions=list(self.policy.granted_permissions),
            parameters=params,
            details=f"Received ActionProposal for tool '{tool_id}'."
        )

        # 1. Lookup Tool (DEFAULT DENY if unknown/disabled)
        tool = self.registry.get_tool(tool_id)
        if not tool:
            reason = f"Tool '{tool_id}' is unknown or disabled. Access DENIED."
            self.audit_logger.log(
                event_type="REJECTED",
                tool_id=tool_id,
                action_proposal_id=proposal.id,
                caller_permissions=list(self.policy.granted_permissions),
                parameters=params,
                details=reason
            )
            return ToolResult(success=False, output=None, error=reason)

        # 2. Schema Input Validation
        schema_valid, schema_reason = self.registry.validate_inputs(tool, params)
        if not schema_valid:
            reason = f"Schema validation failed: {schema_reason}"
            self.audit_logger.log(
                event_type="REJECTED",
                tool_id=tool_id,
                action_proposal_id=proposal.id,
                caller_permissions=list(self.policy.granted_permissions),
                parameters=params,
                details=reason
            )
            return ToolResult(success=False, output=None, error=reason)

        # 3. Permission Check (DEFAULT DENY)
        perm_ok, perm_reason = self.policy.check_permission(tool.required_permissions)
        if not perm_ok:
            self.audit_logger.log(
                event_type="REJECTED",
                tool_id=tool_id,
                action_proposal_id=proposal.id,
                caller_permissions=list(self.policy.granted_permissions),
                parameters=params,
                details=perm_reason
            )
            return ToolResult(success=False, output=None, error=perm_reason)

        # 4. Approval Audit
        self.audit_logger.log(
            event_type="APPROVED",
            tool_id=tool_id,
            action_proposal_id=proposal.id,
            caller_permissions=list(self.policy.granted_permissions),
            parameters=params,
            details=f"Proposal approved for tool '{tool_id}'."
        )

        # 5. Execution or Dry-Run
        if dry_run:
            result = tool.execute(params, dry_run=True)
            self.audit_logger.log(
                event_type="DRY_RUN",
                tool_id=tool_id,
                action_proposal_id=proposal.id,
                caller_permissions=list(self.policy.granted_permissions),
                parameters=params,
                details=f"Dry-run executed: {result.output}"
            )
            return result

        result = tool.execute(params, dry_run=False)
        self.audit_logger.log(
            event_type="EXECUTED",
            tool_id=tool_id,
            action_proposal_id=proposal.id,
            caller_permissions=list(self.policy.granted_permissions),
            parameters=params,
            details=f"Executed tool '{tool_id}' with success={result.success}."
        )
        return result
