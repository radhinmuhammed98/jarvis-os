"""
Base Tool Interface and Data Models for JARVIS OS Tool Subsystem
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time

@dataclass
class ToolResult:
    success: bool
    output: Any
    error: Optional[str] = None
    dry_run: bool = False
    execution_time_ms: float = 0.0

class BaseTool(ABC):
    """
    Abstract interface for all JARVIS OS tools.
    Every tool must define explicit schemas, required permissions, and safe execution.
    """

    @property
    @abstractmethod
    def tool_id(self) -> str:
        """Unique tool identifier (e.g., 'system_info', 'time', 'echo')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does."""
        pass

    @property
    @abstractmethod
    def required_permissions(self) -> List[str]:
        """List of permission strings required to execute this tool (e.g. ['system:read'])."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """Expected JSON schema / dict structure for input parameters."""
        pass

    @abstractmethod
    def execute(self, parameters: Dict[str, Any], dry_run: bool = False) -> ToolResult:
        """Execute tool logic or return dry-run simulation result."""
        pass
