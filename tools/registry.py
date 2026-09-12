"""
JARVIS Central Tool Registry
Handles tool registration, discovery, enabling/disabling, and input schema validation.
Defaults to DENY for unregistered/unknown tools.
"""

import logging
from typing import Dict, Optional, List, Any, Tuple
from tools.base import BaseTool

logger = logging.getLogger("jarvis-tool-registry")

class ToolRegistry:
    """Central registry managing all registered JARVIS tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._enabled: Dict[str, bool] = {}

    def register_tool(self, tool: BaseTool):
        tid = tool.tool_id
        self._tools[tid] = tool
        self._enabled[tid] = True
        logger.info(f"Registered tool '{tid}' ({tool.name})")

    def unregister_tool(self, tool_id: str):
        self._tools.pop(tool_id, None)
        self._enabled.pop(tool_id, None)

    def set_enabled(self, tool_id: str, enabled: bool):
        if tool_id in self._tools:
            self._enabled[tool_id] = enabled

    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        if tool_id in self._tools and self._enabled.get(tool_id, False):
            return self._tools[tool_id]
        return None

    def list_tools(self) -> List[Dict[str, Any]]:
        result = []
        for tid, tool in self._tools.items():
            result.append({
                "tool_id": tid,
                "name": tool.name,
                "description": tool.description,
                "enabled": self._enabled.get(tid, False),
                "permissions": tool.required_permissions,
                "input_schema": tool.input_schema
            })
        return result

    def validate_inputs(self, tool: BaseTool, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates parameters against tool's declared schema structure.
        """
        schema = tool.input_schema
        required_keys = schema.get("required", [])

        for rk in required_keys:
            if rk not in parameters:
                return False, f"Missing required parameter '{rk}' for tool '{tool.tool_id}'."

        props = schema.get("properties", {})
        for param_key, param_val in parameters.items():
            if param_key in props:
                expected_type = props[param_key].get("type")
                if expected_type == "string" and not isinstance(param_val, str):
                    return False, f"Parameter '{param_key}' must be a string."
                elif expected_type == "integer" and not isinstance(param_val, int):
                    return False, f"Parameter '{param_key}' must be an integer."

        return True, "Parameters valid."
