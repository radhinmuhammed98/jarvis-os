"""
JARVIS Core Data Types and Structured Output Schema Definitions
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid
import time

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass
class Message:
    role: Role
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

class IntentType(str, Enum):
    CONVERSATION = "conversation"
    SYSTEM_COMMAND = "system_command"
    FILE_OPERATION = "file_operation"
    CODE_EXECUTION = "code_execution"
    UNKNOWN = "unknown"

@dataclass
class Intent:
    intent_type: IntentType
    confidence: float
    summary: str
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActionProposal:
    """
    Structured proposal for an action.
    JARVIS Core MUST ONLY generate ActionProposal objects and NEVER execute them directly.
    Execution must pass through the Intent Validator and Sandbox layer.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = ""
    description: str = ""
    target: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "medium"  # low, medium, high, critical
    requires_confirmation: bool = True
    created_at: float = field(default_factory=time.time)

@dataclass
class ResponseChunk:
    text: str = ""
    is_final: bool = False
    action_proposal: Optional[ActionProposal] = None
    intent: Optional[Intent] = None
