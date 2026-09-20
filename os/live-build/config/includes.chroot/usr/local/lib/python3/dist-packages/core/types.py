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

class IntentCategory(str, Enum):
    CONVERSATION = "conversation"
    QUESTION = "question"
    INFORMATION_REQUEST = "information_request"
    ACTION_REQUEST = "action_request"
    AMBIGUOUS = "ambiguous"
    CANCEL = "cancel"

# Backward compatibility mapping
IntentType = IntentCategory

@dataclass
class Intent:
    category: IntentCategory
    confidence: float
    summary: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_clarification: bool = False
    clarification_prompt: Optional[str] = None

    @property
    def intent_type(self) -> IntentCategory:
        return self.category

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
    confidence: float = 1.0
    risk_level: str = "medium"  # low, medium, high, critical
    requires_confirmation: bool = True
    validated: bool = False
    validation_reason: str = ""
    created_at: float = field(default_factory=time.time)

@dataclass
class ResponseChunk:
    text: str = ""
    is_final: bool = False
    action_proposal: Optional[ActionProposal] = None
    intent: Optional[Intent] = None
