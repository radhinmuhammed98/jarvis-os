"""
JARVIS Validation Gate
Enforces security, completeness, and permission policy checks on ActionProposals.
STRICT RULE: Validation Gate NEVER executes any actions or calls system tools.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from core.types import ActionProposal, Intent, IntentCategory

logger = logging.getLogger("jarvis-validation-gate")

class ValidationGate:
    """
    Validation Gate between Intent Engine and potential execution pipeline.
    Validates that:
    1. ActionProposal is complete and unambiguous.
    2. Target is specified and valid.
    3. Confidence meets minimum required safety threshold.
    4. Permission policy checks pass (placeholder policy engine).
    """

    def __init__(self, min_confidence_threshold: float = 0.80):
        self.min_confidence_threshold = min_confidence_threshold

    def validate(
        self, intent: Intent, proposal: Optional[ActionProposal]
    ) -> Tuple[bool, str, Optional[ActionProposal]]:
        """
        Validates an ActionProposal.
        Returns (is_valid, reason, updated_proposal).
        Guarantees NO tool or system execution happens during validation.
        """
        if intent.category != IntentCategory.ACTION_REQUEST:
            return False, f"Intent is {intent.category.value}, not an action_request.", None

        if not proposal:
            return False, "No ActionProposal provided for action request.", None

        # Check target completeness
        if not proposal.target or proposal.target.lower() in ["it", "that", "this", "something"]:
            proposal.validated = False
            proposal.validation_reason = "Target is ambiguous or unspecified."
            return False, proposal.validation_reason, proposal

        # Check confidence threshold
        if proposal.confidence < self.min_confidence_threshold:
            proposal.validated = False
            proposal.validation_reason = f"Confidence {proposal.confidence} below required threshold {self.min_confidence_threshold}."
            return False, proposal.validation_reason, proposal

        # Permission policy check (Simulated policy approval)
        allowed, policy_reason = self._check_policy(proposal)
        if not allowed:
            proposal.validated = False
            proposal.validation_reason = f"Policy rejected action: {policy_reason}"
            return False, proposal.validation_reason, proposal

        proposal.validated = True
        proposal.validation_reason = "Action proposal successfully validated and awaiting user confirmation."
        logger.info(f"[ValidationGate] Proposal '{proposal.description}' VALIDATED. Execution deferred to Agent Sandbox.")
        return True, proposal.validation_reason, proposal

    def _check_policy(self, proposal: ActionProposal) -> Tuple[bool, str]:
        # Default safety policy rules
        if proposal.action_type == "file_delete" and proposal.target in ["/", "/etc", "/usr", "/var"]:
            return False, "Destructive system directory modification is prohibited."
        return True, "Permitted under standard user safety profile."
