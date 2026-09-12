"""
JARVIS Sandbox Data Types and Resource Limits
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import time

@dataclass
class ResourceLimits:
    max_cpu_seconds: int = 5
    max_memory_mb: int = 256
    max_processes: int = 10
    max_output_bytes: int = 65536
    timeout_seconds: float = 10.0

@dataclass
class SandboxConfig:
    network_enabled: bool = False
    allow_host_filesystem: bool = False
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    environment: Dict[str, str] = field(default_factory=dict)

@dataclass
class SandboxResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: float
    resource_limit_exceeded: bool = False
    limit_type: Optional[str] = None
    dry_run: bool = False
    error: Optional[str] = None
