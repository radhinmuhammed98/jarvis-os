"""
Audit Logging Subsystem for Tool Operations
Logs proposed, approved, rejected, dry-run, and executed tool operations.
"""

import logging
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

logger = logging.getLogger("jarvis-audit")

@dataclass
class AuditRecord:
    timestamp: float
    event_type: str  # PROPOSED, APPROVED, REJECTED, DRY_RUN, EXECUTED, ERROR
    tool_id: str
    action_proposal_id: Optional[str]
    caller_permissions: List[str]
    parameters: Dict[str, Any]
    details: str

class AuditLogger:
    """In-memory and file-based audit logger for tool security tracking."""

    def __init__(self):
        self._records: List[AuditRecord] = []

    def log(
        self,
        event_type: str,
        tool_id: str,
        action_proposal_id: Optional[str],
        caller_permissions: List[str],
        parameters: Dict[str, Any],
        details: str
    ) -> AuditRecord:
        record = AuditRecord(
            timestamp=time.time(),
            event_type=event_type,
            tool_id=tool_id,
            action_proposal_id=action_proposal_id,
            caller_permissions=caller_permissions,
            parameters=parameters,
            details=details
        )
        self._records.append(record)
        logger.info(f"[AUDIT] {event_type} | Tool: '{tool_id}' | Proposal: '{action_proposal_id}' | {details}")
        return record

    def get_records(self) -> List[AuditRecord]:
        return list(self._records)

    def clear(self):
        self._records.clear()
